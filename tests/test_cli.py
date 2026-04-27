"""Tests for the Tailwind CLI."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from aioresponses import aioresponses
from typer.testing import CliRunner

from gotailwind.cli import cli
from gotailwind.cli.async_typer import AsyncTyper
from gotailwind.exceptions import (
    TailwindConnectionError,
    TailwindConnectionTimeoutError,
)

from . import load_fixture

runner = CliRunner()


def test_status() -> None:
    """Test the status command."""
    with aioresponses() as mocked:
        mocked.post(
            "http://192.168.1.100/json",
            status=200,
            body=load_fixture("device_status_open.json"),
            content_type="application/json",
        )
        result = runner.invoke(
            cli,
            ["status", "--host", "192.168.1.100", "--token", "123456"],
        )

    assert result.exit_code == 0
    assert "iQ3" in result.output
    assert "Tailwind device status" in result.output
    assert "Garage doors" in result.output


def test_identify() -> None:
    """Test the identify command."""
    with aioresponses() as mocked:
        mocked.post(
            "http://192.168.1.100/json",
            status=200,
            body=load_fixture("ok_response.json"),
            content_type="application/json",
        )
        result = runner.invoke(
            cli,
            ["identify", "--host", "192.168.1.100", "--token", "123456"],
        )

    assert result.exit_code == 0
    assert "Success" in result.output


@patch("gotailwind.tailwind.OPERATION_CYCLE_WAIT", 0)
def test_close_door() -> None:
    """Test the close command."""
    with aioresponses() as mocked:
        # door_close: status() to check number_of_doors
        mocked.post(
            "http://192.168.1.100/json",
            status=200,
            body=load_fixture("device_status_open.json"),
            content_type="application/json",
        )
        # door_close: door_status() -> status()
        mocked.post(
            "http://192.168.1.100/json",
            status=200,
            body=load_fixture("device_status_open.json"),
            content_type="application/json",
        )
        # operate: door_status() -> status() pre-check
        mocked.post(
            "http://192.168.1.100/json",
            status=200,
            body=load_fixture("device_status_open.json"),
            content_type="application/json",
        )
        # operate: send command
        mocked.post(
            "http://192.168.1.100/json",
            status=200,
            body=load_fixture("ok_response.json"),
            content_type="application/json",
        )
        # operate: polling door_status() -> status()
        mocked.post(
            "http://192.168.1.100/json",
            status=200,
            body=load_fixture("device_status_closed.json"),
            content_type="application/json",
        )
        result = runner.invoke(
            cli,
            [
                "close",
                "--host",
                "192.168.1.100",
                "--token",
                "123456",
                "--door",
                "1",
            ],
        )

    assert result.exit_code == 0
    assert "has been closed" in result.output


def test_close_door_already_closed() -> None:
    """Test closing a door that is already closed."""
    with aioresponses() as mocked:
        # status() call
        mocked.post(
            "http://192.168.1.100/json",
            status=200,
            body=load_fixture("device_status_closed.json"),
            content_type="application/json",
        )
        # door_status() call
        mocked.post(
            "http://192.168.1.100/json",
            status=200,
            body=load_fixture("device_status_closed.json"),
            content_type="application/json",
        )
        result = runner.invoke(
            cli,
            [
                "close",
                "--host",
                "192.168.1.100",
                "--token",
                "123456",
                "--door",
                "1",
            ],
        )

    assert result.exit_code == 1
    assert "already closed" in result.output


@patch("gotailwind.tailwind.OPERATION_CYCLE_WAIT", 0)
def test_open_door() -> None:
    """Test the open command."""
    with aioresponses() as mocked:
        # door_open: status() to check number_of_doors
        mocked.post(
            "http://192.168.1.100/json",
            status=200,
            body=load_fixture("device_status_closed.json"),
            content_type="application/json",
        )
        # door_open: door_status() -> status()
        mocked.post(
            "http://192.168.1.100/json",
            status=200,
            body=load_fixture("device_status_closed.json"),
            content_type="application/json",
        )
        # operate: door_status() -> status() pre-check
        mocked.post(
            "http://192.168.1.100/json",
            status=200,
            body=load_fixture("device_status_closed.json"),
            content_type="application/json",
        )
        # operate: send command
        mocked.post(
            "http://192.168.1.100/json",
            status=200,
            body=load_fixture("ok_response.json"),
            content_type="application/json",
        )
        # operate: polling door_status() -> status()
        mocked.post(
            "http://192.168.1.100/json",
            status=200,
            body=load_fixture("device_status_open.json"),
            content_type="application/json",
        )
        result = runner.invoke(
            cli,
            [
                "open",
                "--host",
                "192.168.1.100",
                "--token",
                "123456",
                "--door",
                "1",
            ],
        )

    assert result.exit_code == 0
    assert "has been opened" in result.output


def test_open_door_already_open() -> None:
    """Test opening a door that is already open."""
    with aioresponses() as mocked:
        # status() call
        mocked.post(
            "http://192.168.1.100/json",
            status=200,
            body=load_fixture("device_status_open.json"),
            content_type="application/json",
        )
        # door_status() call
        mocked.post(
            "http://192.168.1.100/json",
            status=200,
            body=load_fixture("device_status_open.json"),
            content_type="application/json",
        )
        result = runner.invoke(
            cli,
            [
                "open",
                "--host",
                "192.168.1.100",
                "--token",
                "123456",
                "--door",
                "1",
            ],
        )

    assert result.exit_code == 1
    assert "already open" in result.output


def test_door_invalid_number() -> None:
    """Test door commands with an invalid door number."""
    result = runner.invoke(
        cli,
        ["open", "--host", "192.168.1.100", "--token", "123456", "--door", "5"],
    )

    assert result.exit_code != 0
    assert "1 and 3" in result.output


def test_led_brightness() -> None:
    """Test the led command."""
    with aioresponses() as mocked:
        mocked.post(
            "http://192.168.1.100/json",
            status=200,
            body=load_fixture("ok_response.json"),
            content_type="application/json",
        )
        result = runner.invoke(
            cli,
            [
                "led",
                "--host",
                "192.168.1.100",
                "--token",
                "123456",
                "--brightness",
                "50",
            ],
        )

    assert result.exit_code == 0
    assert "brightness set to 50%" in result.output


def test_led_invalid_brightness() -> None:
    """Test the led command with an invalid brightness value."""
    result = runner.invoke(
        cli,
        [
            "led",
            "--host",
            "192.168.1.100",
            "--token",
            "123456",
            "--brightness",
            "150",
        ],
    )

    assert result.exit_code != 0
    assert "0 and 100" in result.output


def test_error_handler_matches_exact_type() -> None:
    """Test that the error handler matches exact exception types."""
    app = AsyncTyper()
    handler = MagicMock()

    @app.error_handler(TailwindConnectionError)
    def _handler(exc: TailwindConnectionError) -> None:
        handler(exc)

    # __call__ is the entry point that dispatches to error handlers.
    # CliRunner bypasses it (calls main() directly), so test directly.
    exc = TailwindConnectionError("test")
    with patch.object(type(app).__bases__[0], "__call__", side_effect=exc):
        app()

    handler.assert_called_once()


def test_error_handler_matches_subclass_via_mro() -> None:
    """Test that the error handler catches subclass exceptions via MRO.

    TailwindConnectionTimeoutError is a subclass of TailwindConnectionError.
    A handler registered for TailwindConnectionError should also catch
    TailwindConnectionTimeoutError.
    """
    app = AsyncTyper()
    handler = MagicMock()

    @app.error_handler(TailwindConnectionError)
    def _handler(exc: TailwindConnectionError) -> None:
        handler(exc)

    exc = TailwindConnectionTimeoutError("test")
    with patch.object(type(app).__bases__[0], "__call__", side_effect=exc):
        app()

    handler.assert_called_once()
    assert isinstance(handler.call_args[0][0], TailwindConnectionTimeoutError)


def test_error_handler_no_match_reraises() -> None:
    """Test that unhandled exceptions propagate via the error handler."""
    app = AsyncTyper()

    @app.error_handler(TailwindConnectionError)
    def _handler(_exc: TailwindConnectionError) -> None:
        pass

    with (
        patch.object(
            type(app).__bases__[0],
            "__call__",
            side_effect=ValueError("unhandled"),
        ),
        pytest.raises(ValueError, match="unhandled"),
    ):
        app()


def test_no_args_shows_help() -> None:
    """Test that running the CLI with no arguments shows help."""
    result = runner.invoke(cli, [])

    assert "Tailwind CLI" in result.output
    assert "status" in result.output
    assert "scan" in result.output
