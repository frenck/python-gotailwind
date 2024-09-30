"""Asynchronous Python client for Tailwind garage door openers."""

from __future__ import annotations

import asyncio
import socket
from dataclasses import dataclass
from typing import Any, Self, TypeVar

import backoff
import orjson
from aiohttp.client import ClientError, ClientSession
from aiohttp.hdrs import METH_POST
from yarl import URL

from gotailwind.const import (
    OPERATION_CYCLE_WAIT,
    OPERATION_WAIT_CYCLES,
    TailwindDoorOperationCommand,
    TailwindDoorState,
)

from .exceptions import (
    TailwindConnectionError,
    TailwindConnectionTimeoutError,
    TailwindDoorAlreadyInStateError,
    TailwindDoorDisabledError,
    TailwindDoorLockedOutError,
    TailwindDoorUnknownError,
)
from .models import (
    TailwindDeviceStatus,
    TailwindDeviceStatusRequest,
    TailwindDoor,
    TailwindDoorOperationRequest,
    TailwindDoorOperationRequestData,
    TailwindDoorOperationRequestDataValue,
    TailwindIdentifyRequest,
    TailwindLEDBrightnessRequest,
    TailwindLEDBrightnessRequestData,
    TailwindLEDBrightnessRequestDataValue,
    TailwindRequest,
)

_TailwindRequestT = TypeVar("_TailwindRequestT", bound=TailwindRequest[Any, Any])


@dataclass(kw_only=True)
class Tailwind:
    """Main class for handling connections with a Tailwind garage door opener."""

    host: str
    token: str
    request_timeout: float = 8
    session: ClientSession | None = None

    product: str = "iQ3"
    version: str = "0.1"

    _close_session: bool = False

    def __post_init__(self) -> None:
        """Initialize the Tailwind object."""
        self.url = URL.build(scheme="http", host=self.host, path="/json")

    @backoff.on_exception(
        backoff.expo,
        TailwindConnectionError,
        max_tries=3,
        logger=None,
    )
    async def request(
        self,
        request: _TailwindRequestT,
    ) -> _TailwindRequestT.response_type:  # type: ignore[name-defined]
        """Handle a request to a Tailwind device."""
        if self.session is None:
            self.session = ClientSession(json_serialize=orjson.dumps)  # type: ignore[arg-type]
            self._close_session = True
        try:
            async with asyncio.timeout(self.request_timeout):
                response = await self.session.request(
                    METH_POST,
                    self.url,
                    data=request.to_json(),
                    headers={"TOKEN": self.token},
                )
                response.raise_for_status()
        except asyncio.TimeoutError as exception:
            msg = "Timeout occurred while connecting to the Tailwind device"
            raise TailwindConnectionTimeoutError(msg) from exception
        except (
            ClientError,
            socket.gaierror,
        ) as exception:
            msg = "Error occurred while communicating to the Tailwind device"
            raise TailwindConnectionError(msg) from exception

        response_text = await response.text()
        return request.response_type.from_json(response_text)

    async def status(self) -> TailwindDeviceStatus:
        """Get the current status of the Tailwind device."""
        return await self.request(TailwindDeviceStatusRequest())  # type: ignore[no-any-return]

    async def door_status(self, *, door: int | str) -> TailwindDoor:
        """Get the door object for the given door id."""
        status = await self.status()
        if not (
            door_status := next(
                (
                    door_status
                    for door_status in status.doors.values()
                    if door in (door_status.index, door_status.door_id)
                ),
                None,
            )
        ):
            msg = f"Door {door} not found"
            raise TailwindDoorUnknownError(msg)
        return door_status

    async def identify(self) -> None:
        """Identify the Tailwind device."""
        await self.request(TailwindIdentifyRequest())

    async def status_led(self, *, brightness: int) -> None:
        """Configure the status LED of the Tailwind device."""
        await self.request(
            TailwindLEDBrightnessRequest(
                data=TailwindLEDBrightnessRequestData(
                    value=TailwindLEDBrightnessRequestDataValue(
                        brightness=brightness,
                    )
                )
            )
        )

    async def operate(
        self,
        *,
        door: int | str | TailwindDoor,
        operation: TailwindDoorOperationCommand,
    ) -> TailwindDoor:
        """Open the garage door."""
        if isinstance(door, TailwindDoor):
            door = door.index
        door_status = await self.door_status(door=door)

        if door_status.locked_out:
            msg = f"Door {door} is locked out"
            raise TailwindDoorLockedOutError(msg)

        if door_status.disabled:
            msg = f"Door {door} is disabled"
            raise TailwindDoorDisabledError(msg)

        if (
            operation == TailwindDoorOperationCommand.OPEN
            and door_status.state == TailwindDoorState.OPEN
        ) or (
            operation == TailwindDoorOperationCommand.CLOSE
            and door_status.state == TailwindDoorState.CLOSED
        ):
            msg = f"Door {door} is already in the requested state"
            raise TailwindDoorAlreadyInStateError(msg)

        await self.request(
            TailwindDoorOperationRequest(
                data=TailwindDoorOperationRequestData(
                    value=TailwindDoorOperationRequestDataValue(
                        index=door_status.index,
                        operation=operation,
                    )
                ),
            ),
        )

        # Wait for the door to open/close
        for _ in range(OPERATION_WAIT_CYCLES):
            await asyncio.sleep(OPERATION_CYCLE_WAIT)
            if (door_status := await self.door_status(door=door)) and (
                (
                    operation == TailwindDoorOperationCommand.CLOSE
                    and door_status.state == TailwindDoorState.CLOSED
                )
                or (
                    operation == TailwindDoorOperationCommand.OPEN
                    and door_status.state == TailwindDoorState.OPEN
                )
            ):
                return door_status

        return door_status

    async def close(self) -> None:
        """Close open client session."""
        if self.session and self._close_session:
            await self.session.close()

    async def __aenter__(self) -> Self:
        """Async enter.

        Returns
        -------
            The Tailwind object.

        """
        return self

    async def __aexit__(self, *_exc_info: object) -> None:
        """Async exit.

        Args:
        ----
            _exc_info: Exec type.

        """
        await self.close()
