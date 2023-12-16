"""Asynchronous Python client for Tailwind garage door openeners."""
from __future__ import annotations

import asyncio
from unittest.mock import patch

import pytest
from aiohttp import ClientResponse, ClientSession
from aresponses import Response, ResponsesMockServer
from syrupy.assertion import SnapshotAssertion

from gotailwind.const import TailwindDoorOperationCommand, TailwindDoorState
from gotailwind.exceptions import (
    TailwindAuthenticationError,
    TailwindConnectionError,
    TailwindDoorOperationError,
    TailwindDoorUnknownError,
    TailwindResponseError,
)
from gotailwind.models import TailwindIdentifyRequest
from gotailwind.tailwind import Tailwind

from . import load_fixture


async def test_status(
    aresponses: ResponsesMockServer, snapshot: SnapshotAssertion
) -> None:
    """Test getting status from Tailwind device."""
    aresponses.add(
        "example.com",
        "/json",
        "POST",
        aresponses.Response(
            status=200,
            text=load_fixture("device_status_open.json"),
        ),
    )
    async with Tailwind(host="example.com", token="12346") as tailwind:
        status = await tailwind.status()

    assert status == snapshot(name="object")
    assert status.to_json() == snapshot(name="json")
    assert status.mac_address == "3c:e9:0e:6d:21:84"


@pytest.mark.parametrize("door", [1, "door1"])
async def test_door_status(
    aresponses: ResponsesMockServer,
    snapshot: SnapshotAssertion,
    door: int | str,
) -> None:
    """Test getting door status from Tailwind device."""

    async def response_handler(request: ClientResponse) -> Response:
        """Response handler for this test."""
        data = await request.json()
        assert data == snapshot(name="request")
        return aresponses.Response(
            status=200,
            text=load_fixture("device_status_open.json"),
        )

    aresponses.add(
        "example.com",
        "/json",
        "POST",
        response_handler,
    )
    async with Tailwind(host="example.com", token="12346") as tailwind:
        status = await tailwind.door_status(door=door)

    assert status == snapshot(name="response")


async def test_door_status_unknown_door(
    aresponses: ResponsesMockServer,
) -> None:
    """Test getting non-existing door status from Tailwind device."""
    aresponses.add(
        "example.com",
        "/json",
        "POST",
        aresponses.Response(
            status=200,
            text=load_fixture("device_status_open.json"),
        ),
    )
    async with Tailwind(host="example.com", token="12346") as tailwind:
        with pytest.raises(TailwindDoorUnknownError, match="Door 42 not found"):
            await tailwind.door_status(door="42")


async def test_identify(
    aresponses: ResponsesMockServer, snapshot: SnapshotAssertion
) -> None:
    """Test the identify method."""

    async def response_handler(request: ClientResponse) -> Response:
        """Response handler for this test."""
        data = await request.json()
        assert data == snapshot(name="request")
        return aresponses.Response(
            status=200,
            text=load_fixture("ok_response.json"),
        )

    aresponses.add(
        "example.com",
        "/json",
        "POST",
        response_handler,
    )
    async with Tailwind(host="example.com", token="12346") as tailwind:
        await tailwind.identify()


async def test_status_led(
    aresponses: ResponsesMockServer, snapshot: SnapshotAssertion
) -> None:
    """Test the status led method."""

    async def response_handler(request: ClientResponse) -> Response:
        """Response handler for this test."""
        data = await request.json()
        assert data == snapshot(name="request")
        return aresponses.Response(
            status=200,
            text=load_fixture("ok_response.json"),
        )

    aresponses.add(
        "example.com",
        "/json",
        "POST",
        response_handler,
    )
    async with Tailwind(host="example.com", token="12346") as tailwind:
        await tailwind.status_led(brightness=42)


async def test_operate_open(
    aresponses: ResponsesMockServer, snapshot: SnapshotAssertion
) -> None:
    """Test operating the Tailwind doors."""

    async def response_handler(request: ClientResponse) -> Response:
        """Response handler for this test."""
        data = await request.json()
        assert data == snapshot(name="request")
        return aresponses.Response(
            status=200,
            text=load_fixture("ok_response.json"),
        )

    aresponses.add(
        "example.com",
        "/json",
        "POST",
        aresponses.Response(
            status=200,
            text=load_fixture("device_status_closed.json"),
        ),
    )
    aresponses.add(
        "example.com",
        "/json",
        "POST",
        response_handler,
    )
    aresponses.add(
        "example.com",
        "/json",
        "POST",
        aresponses.Response(
            status=200,
            text=load_fixture("device_status_closed.json"),
        ),
        repeat=2,
    )
    aresponses.add(
        "example.com",
        "/json",
        "POST",
        aresponses.Response(
            status=200,
            text=load_fixture("device_status_open.json"),
        ),
    )
    async with Tailwind(host="example.com", token="12346") as tailwind:
        status = await tailwind.operate(
            door="door1", operation=TailwindDoorOperationCommand.OPEN
        )

    assert status == snapshot(name="response")


async def test_operate_close(
    aresponses: ResponsesMockServer, snapshot: SnapshotAssertion
) -> None:
    """Test operating the Tailwind doors."""

    async def response_handler(request: ClientResponse) -> Response:
        """Response handler for this test."""
        data = await request.json()
        assert data == snapshot(name="request")
        return aresponses.Response(
            status=200,
            text=load_fixture("ok_response.json"),
        )

    aresponses.add(
        "example.com",
        "/json",
        "POST",
        aresponses.Response(
            status=200,
            text=load_fixture("device_status_open.json"),
        ),
    )
    aresponses.add(
        "example.com",
        "/json",
        "POST",
        response_handler,
    )
    aresponses.add(
        "example.com",
        "/json",
        "POST",
        aresponses.Response(
            status=200,
            text=load_fixture("device_status_open.json"),
        ),
        repeat=2,
    )
    aresponses.add(
        "example.com",
        "/json",
        "POST",
        aresponses.Response(
            status=200,
            text=load_fixture("device_status_closed.json"),
        ),
    )
    async with Tailwind(host="example.com", token="12346") as tailwind:
        status = await tailwind.operate(
            door="door1", operation=TailwindDoorOperationCommand.CLOSE
        )
        assert status == snapshot(name="response")


async def test_operate_took_to_long(
    aresponses: ResponsesMockServer, snapshot: SnapshotAssertion
) -> None:
    """Test operating the Tailwind doors."""

    async def response_handler(request: ClientResponse) -> Response:
        """Response handler for this test."""
        data = await request.json()
        assert data == snapshot(name="request")
        return aresponses.Response(
            status=200,
            text=load_fixture("ok_response.json"),
        )

    aresponses.add(
        "example.com",
        "/json",
        "POST",
        aresponses.Response(
            status=200,
            text=load_fixture("device_status_open.json"),
        ),
    )
    aresponses.add(
        "example.com",
        "/json",
        "POST",
        response_handler,
    )
    aresponses.add(
        "example.com",
        "/json",
        "POST",
        aresponses.Response(
            status=200,
            text=load_fixture("device_status_open.json"),
        ),
        repeat=2,
    )
    async with Tailwind(host="example.com", token="12346") as tailwind:
        with patch("gotailwind.tailwind.OPERATION_WAIT_CYCLES", 1):
            status = await tailwind.operate(
                door="door1", operation=TailwindDoorOperationCommand.CLOSE
            )

    # Reported state should still be open.
    assert status.state == TailwindDoorState.OPEN


async def test_operate_disabled(
    aresponses: ResponsesMockServer,
) -> None:
    """Test operating the Tailwind doors that are disabled."""
    aresponses.add(
        "example.com",
        "/json",
        "POST",
        aresponses.Response(
            status=200,
            text=load_fixture("device_status_disabled.json"),
        ),
    )
    async with Tailwind(host="example.com", token="12346") as tailwind:
        with pytest.raises(TailwindDoorOperationError, match="is disabled"):
            await tailwind.operate(
                door="door1", operation=TailwindDoorOperationCommand.OPEN
            )


async def test_operate_locked_out(
    aresponses: ResponsesMockServer,
) -> None:
    """Test operating the Tailwind doors that are in a locked out state."""
    aresponses.add(
        "example.com",
        "/json",
        "POST",
        aresponses.Response(
            status=200,
            text=load_fixture("device_status_locked_out.json"),
        ),
    )
    async with Tailwind(host="example.com", token="12346") as tailwind:
        with pytest.raises(TailwindDoorOperationError, match="is locked out"):
            await tailwind.operate(
                door="door1", operation=TailwindDoorOperationCommand.OPEN
            )


@pytest.mark.parametrize(
    ("fixture", "operation"),
    [
        ("device_status_open.json", TailwindDoorOperationCommand.OPEN),
        ("device_status_closed.json", TailwindDoorOperationCommand.CLOSE),
    ],
)
async def test_operate_already_in_state(
    aresponses: ResponsesMockServer,
    fixture: str,
    operation: TailwindDoorOperationCommand,
) -> None:
    """Test operating the Tailwind doors that are already in the requested state."""
    aresponses.add(
        "example.com",
        "/json",
        "POST",
        aresponses.Response(
            status=200,
            text=load_fixture(fixture),
        ),
    )
    async with Tailwind(host="example.com", token="12346") as tailwind:
        with pytest.raises(
            TailwindDoorOperationError, match="already in the requested state"
        ):
            await tailwind.operate(door="door1", operation=operation)


async def test_operate_with_door_object(
    aresponses: ResponsesMockServer,
) -> None:
    """Test opering with a door status object works."""
    aresponses.add(
        "example.com",
        "/json",
        "POST",
        aresponses.Response(
            status=200,
            text=load_fixture("device_status_locked_out.json"),
        ),
        repeat=2,
    )
    async with Tailwind(host="example.com", token="12346") as tailwind:
        door_status = await tailwind.door_status(door="door1")
        with pytest.raises(TailwindDoorOperationError, match="is locked out"):
            await tailwind.operate(
                door=door_status, operation=TailwindDoorOperationCommand.OPEN
            )


async def test_request_with_shared_session(aresponses: ResponsesMockServer) -> None:
    """Test a passed in shared session works as expected."""
    aresponses.add(
        "example.com",
        "/json",
        "POST",
        aresponses.Response(
            status=200,
            text=load_fixture("ok_response.json"),
        ),
    )
    async with ClientSession() as session:
        tailwind = Tailwind(host="example.com", token="123456", session=session)
        await tailwind.request(TailwindIdentifyRequest())
        await tailwind.close()


async def test_timeout(aresponses: ResponsesMockServer) -> None:
    """Test request timeout."""

    # Faking a timeout by sleeping
    async def response_handler(_: ClientResponse) -> Response:
        """Response handler for this test."""
        await asyncio.sleep(8)
        return aresponses.Response(
            status=200,
            text=load_fixture("ok_response.json"),
        )

    aresponses.add(
        "example.com",
        "/json",
        "POST",
        response_handler,
    )
    async with Tailwind(
        host="example.com",
        token="123456",
        request_timeout=1,
    ) as tailwind:
        with pytest.raises(TailwindConnectionError):
            await tailwind.request(TailwindIdentifyRequest())


async def test_http_error400(aresponses: ResponsesMockServer) -> None:
    """Test HTTP 404 response handling."""
    aresponses.add(
        "example.com",
        "/json",
        "POST",
        aresponses.Response(text="OMG PUPPIES!", status=404),
    )

    async with Tailwind(host="example.com", token="123456") as tailwind:
        with pytest.raises(TailwindConnectionError):
            await tailwind.request(TailwindIdentifyRequest())


async def test_unauthenticated_response(aresponses: ResponsesMockServer) -> None:
    """Test authentication failure."""
    aresponses.add(
        "example.com",
        "/json",
        "POST",
        aresponses.Response(
            status=200,
            text=load_fixture("token_fail.json"),
        ),
    )

    async with Tailwind(host="example.com", token="123456") as tailwind:
        with pytest.raises(TailwindAuthenticationError):
            await tailwind.request(TailwindIdentifyRequest())


async def test_error_response(aresponses: ResponsesMockServer) -> None:
    """Test error failure."""
    aresponses.add(
        "example.com",
        "/json",
        "POST",
        aresponses.Response(
            status=200,
            text=load_fixture("fail_response.json"),
        ),
    )

    async with Tailwind(host="example.com", token="123456") as tailwind:
        with pytest.raises(TailwindResponseError, match="OMG Puppies!"):
            await tailwind.request(TailwindIdentifyRequest())
