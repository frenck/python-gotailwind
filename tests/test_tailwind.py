"""Asynchronous Python client for Tailwind garage door openers."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import patch

import pytest
from aiohttp import ClientSession
from aioresponses import CallbackResult, aioresponses
from syrupy.assertion import SnapshotAssertion

from gotailwind.const import TailwindDoorOperationCommand, TailwindDoorState
from gotailwind.exceptions import (
    TailwindAuthenticationError,
    TailwindConnectionError,
    TailwindDoorAlreadyInStateError,
    TailwindDoorOperationError,
    TailwindDoorUnknownError,
    TailwindResponseError,
    TailwindUnsupportedFirmwareVersionError,
)
from gotailwind.models import TailwindIdentifyRequest
from gotailwind.tailwind import Tailwind

from . import load_fixture


async def test_status(snapshot: SnapshotAssertion) -> None:
    """Test getting status from Tailwind device."""
    with aioresponses() as mocked:
        mocked.post(
            "http://example.com/json",
            status=200,
            body=load_fixture("device_status_open.json"),
            content_type="application/json",
        )
        async with Tailwind(host="example.com", token="12346") as tailwind:
            status = await tailwind.status()

    assert status == snapshot(name="object")
    assert status.to_json() == snapshot(name="json")
    assert status.mac_address == "3c:e9:0e:6d:21:84"


async def test_unsupported_firmware_version() -> None:
    """Test trying to use an unsupported firmware version."""
    with aioresponses() as mocked:
        mocked.post(
            "http://example.com/json",
            status=200,
            body=load_fixture("device_status_unsupported.json"),
            content_type="application/json",
        )
        async with Tailwind(host="example.com", token="12346") as tailwind:
            with pytest.raises(
                TailwindUnsupportedFirmwareVersionError,
                match="Unsupported firmware version",
            ):
                await tailwind.status()


@pytest.mark.parametrize("door", [1, "door1"])
async def test_door_status(
    snapshot: SnapshotAssertion,
    door: int | str,
) -> None:
    """Test getting door status from Tailwind device."""
    with aioresponses() as mocked:

        def request_callback(_url: Any, **kwargs: Any) -> CallbackResult:
            data = json.loads(kwargs.get("data", "null"))
            assert data == snapshot(name="request")
            return CallbackResult(
                status=200,
                body=load_fixture("device_status_open.json"),
                content_type="application/json",
            )

        mocked.post(
            "http://example.com/json",
            callback=request_callback,
        )
        async with Tailwind(host="example.com", token="12346") as tailwind:
            status = await tailwind.door_status(door=door)

    assert status == snapshot(name="response")


async def test_door_status_unknown_door() -> None:
    """Test getting non-existing door status from Tailwind device."""
    with aioresponses() as mocked:
        mocked.post(
            "http://example.com/json",
            status=200,
            body=load_fixture("device_status_open.json"),
            content_type="application/json",
        )
        async with Tailwind(host="example.com", token="12346") as tailwind:
            with pytest.raises(TailwindDoorUnknownError, match="Door 42 not found"):
                await tailwind.door_status(door="42")


async def test_identify(snapshot: SnapshotAssertion) -> None:
    """Test the identify method."""
    with aioresponses() as mocked:

        def request_callback(_url: Any, **kwargs: Any) -> CallbackResult:
            data = json.loads(kwargs.get("data", "null"))
            assert data == snapshot(name="request")
            return CallbackResult(
                status=200,
                body=load_fixture("ok_response.json"),
                content_type="application/json",
            )

        mocked.post(
            "http://example.com/json",
            callback=request_callback,
        )
        async with Tailwind(host="example.com", token="12346") as tailwind:
            await tailwind.identify()


async def test_status_led(snapshot: SnapshotAssertion) -> None:
    """Test the status led method."""
    with aioresponses() as mocked:

        def request_callback(_url: Any, **kwargs: Any) -> CallbackResult:
            data = json.loads(kwargs.get("data", "null"))
            assert data == snapshot(name="request")
            return CallbackResult(
                status=200,
                body=load_fixture("ok_response.json"),
                content_type="application/json",
            )

        mocked.post(
            "http://example.com/json",
            callback=request_callback,
        )
        async with Tailwind(host="example.com", token="12346") as tailwind:
            await tailwind.status_led(brightness=42)


async def test_operate_open(snapshot: SnapshotAssertion) -> None:
    """Test operating the Tailwind doors."""
    with aioresponses() as mocked:

        def request_callback(_url: Any, **kwargs: Any) -> CallbackResult:
            data = json.loads(kwargs.get("data", "null"))
            assert data == snapshot(name="request")
            return CallbackResult(
                status=200,
                body=load_fixture("ok_response.json"),
                content_type="application/json",
            )

        # Initial status check
        mocked.post(
            "http://example.com/json",
            status=200,
            body=load_fixture("device_status_closed.json"),
            content_type="application/json",
        )
        # Send operate command
        mocked.post(
            "http://example.com/json",
            callback=request_callback,
        )
        # Poll 1: still closed
        mocked.post(
            "http://example.com/json",
            status=200,
            body=load_fixture("device_status_closed.json"),
            content_type="application/json",
        )
        # Poll 2: still closed
        mocked.post(
            "http://example.com/json",
            status=200,
            body=load_fixture("device_status_closed.json"),
            content_type="application/json",
        )
        # Poll 3: opened
        mocked.post(
            "http://example.com/json",
            status=200,
            body=load_fixture("device_status_open.json"),
            content_type="application/json",
        )
        async with Tailwind(host="example.com", token="12346") as tailwind:
            status = await tailwind.operate(
                door="door1", operation=TailwindDoorOperationCommand.OPEN
            )

    assert status == snapshot(name="response")


async def test_operate_close(snapshot: SnapshotAssertion) -> None:
    """Test operating the Tailwind doors."""
    with aioresponses() as mocked:

        def request_callback(_url: Any, **kwargs: Any) -> CallbackResult:
            data = json.loads(kwargs.get("data", "null"))
            assert data == snapshot(name="request")
            return CallbackResult(
                status=200,
                body=load_fixture("ok_response.json"),
                content_type="application/json",
            )

        # Initial status check
        mocked.post(
            "http://example.com/json",
            status=200,
            body=load_fixture("device_status_open.json"),
            content_type="application/json",
        )
        # Send operate command
        mocked.post(
            "http://example.com/json",
            callback=request_callback,
        )
        # Poll 1: still open
        mocked.post(
            "http://example.com/json",
            status=200,
            body=load_fixture("device_status_open.json"),
            content_type="application/json",
        )
        # Poll 2: still open
        mocked.post(
            "http://example.com/json",
            status=200,
            body=load_fixture("device_status_open.json"),
            content_type="application/json",
        )
        # Poll 3: closed
        mocked.post(
            "http://example.com/json",
            status=200,
            body=load_fixture("device_status_closed.json"),
            content_type="application/json",
        )
        async with Tailwind(host="example.com", token="12346") as tailwind:
            status = await tailwind.operate(
                door="door1", operation=TailwindDoorOperationCommand.CLOSE
            )
            assert status == snapshot(name="response")


async def test_operate_took_too_long(snapshot: SnapshotAssertion) -> None:
    """Test operating the Tailwind doors."""
    with aioresponses() as mocked:

        def request_callback(_url: Any, **kwargs: Any) -> CallbackResult:
            data = json.loads(kwargs.get("data", "null"))
            assert data == snapshot(name="request")
            return CallbackResult(
                status=200,
                body=load_fixture("ok_response.json"),
                content_type="application/json",
            )

        # Initial status check
        mocked.post(
            "http://example.com/json",
            status=200,
            body=load_fixture("device_status_open.json"),
            content_type="application/json",
        )
        # Send operate command
        mocked.post(
            "http://example.com/json",
            callback=request_callback,
        )
        # Single poll: still open (OPERATION_WAIT_CYCLES patched to 1)
        mocked.post(
            "http://example.com/json",
            status=200,
            body=load_fixture("device_status_open.json"),
            content_type="application/json",
        )
        async with Tailwind(host="example.com", token="12346") as tailwind:
            with patch("gotailwind.tailwind.OPERATION_WAIT_CYCLES", 1):
                status = await tailwind.operate(
                    door="door1", operation=TailwindDoorOperationCommand.CLOSE
                )

        # Reported state should still be open.
        assert status.state == TailwindDoorState.OPEN


async def test_operate_disabled() -> None:
    """Test operating the Tailwind doors that are disabled."""
    with aioresponses() as mocked:
        mocked.post(
            "http://example.com/json",
            status=200,
            body=load_fixture("device_status_disabled.json"),
            content_type="application/json",
        )
        async with Tailwind(host="example.com", token="12346") as tailwind:
            with pytest.raises(TailwindDoorOperationError, match="is disabled"):
                await tailwind.operate(
                    door="door1", operation=TailwindDoorOperationCommand.OPEN
                )


async def test_operate_locked_out() -> None:
    """Test operating the Tailwind doors that are in a locked out state."""
    with aioresponses() as mocked:
        mocked.post(
            "http://example.com/json",
            status=200,
            body=load_fixture("device_status_locked_out.json"),
            content_type="application/json",
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
    fixture: str,
    operation: TailwindDoorOperationCommand,
) -> None:
    """Test operating the Tailwind doors that are already in the requested state."""
    with aioresponses() as mocked:
        mocked.post(
            "http://example.com/json",
            status=200,
            body=load_fixture(fixture),
            content_type="application/json",
        )
        async with Tailwind(host="example.com", token="12346") as tailwind:
            with pytest.raises(
                TailwindDoorAlreadyInStateError,
                match="already in the requested state",
            ):
                await tailwind.operate(door="door1", operation=operation)


async def test_operate_with_door_object() -> None:
    """Test operating with a door status object works."""
    with aioresponses() as mocked:
        mocked.post(
            "http://example.com/json",
            status=200,
            body=load_fixture("device_status_locked_out.json"),
            content_type="application/json",
            repeat=True,
        )
        async with Tailwind(host="example.com", token="12346") as tailwind:
            door_status = await tailwind.door_status(door="door1")
            with pytest.raises(TailwindDoorOperationError, match="is locked out"):
                await tailwind.operate(
                    door=door_status, operation=TailwindDoorOperationCommand.OPEN
                )


async def test_request_with_shared_session() -> None:
    """Test a passed in shared session works as expected."""
    with aioresponses() as mocked:
        mocked.post(
            "http://example.com/json",
            status=200,
            body=load_fixture("ok_response.json"),
            content_type="application/json",
        )
        async with ClientSession() as session:
            tailwind = Tailwind(host="example.com", token="123456", session=session)
            await tailwind.request(TailwindIdentifyRequest())
            await tailwind.close()


async def test_timeout() -> None:
    """Test request timeout."""
    with aioresponses() as mocked:
        mocked.post(
            "http://example.com/json",
            exception=TimeoutError(),
        )
        async with Tailwind(
            host="example.com",
            token="123456",
            request_timeout=1,
        ) as tailwind:
            with pytest.raises(TailwindConnectionError):
                await tailwind.request(TailwindIdentifyRequest())


async def test_http_error400() -> None:
    """Test HTTP 404 response handling."""
    with aioresponses() as mocked:
        mocked.post(
            "http://example.com/json",
            status=404,
            body="OMG PUPPIES!",
            content_type="text/plain",
        )

        async with Tailwind(host="example.com", token="123456") as tailwind:
            with pytest.raises(TailwindConnectionError):
                await tailwind.request(TailwindIdentifyRequest())


async def test_unauthenticated_response() -> None:
    """Test authentication failure."""
    with aioresponses() as mocked:
        mocked.post(
            "http://example.com/json",
            status=200,
            body=load_fixture("token_fail.json"),
            content_type="application/json",
        )

        async with Tailwind(host="example.com", token="123456") as tailwind:
            with pytest.raises(TailwindAuthenticationError):
                await tailwind.request(TailwindIdentifyRequest())


async def test_error_response() -> None:
    """Test error failure."""
    with aioresponses() as mocked:
        mocked.post(
            "http://example.com/json",
            status=200,
            body=load_fixture("fail_response.json"),
            content_type="application/json",
        )

        async with Tailwind(host="example.com", token="123456") as tailwind:
            with pytest.raises(TailwindResponseError, match="OMG Puppies!"):
                await tailwind.request(TailwindIdentifyRequest())
