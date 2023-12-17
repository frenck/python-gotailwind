"""Asynchronous Python client for Tailwind garage door openers."""

from enum import StrEnum, auto

from awesomeversion import AwesomeVersion, AwesomeVersionStrategy

OPERATION_WAIT_CYCLES = 120
OPERATION_CYCLE_WAIT = 0.5

MIN_REQUIRED_FIRMWARE_VERSION = AwesomeVersion(
    "10.10", ensure_strategy=AwesomeVersionStrategy.SIMPLEVER
)


class TailwindDoorState(StrEnum):
    """Enum for door state."""

    CLOSED = "close"
    OPEN = "open"


class TailwindDoorOperationCommand(StrEnum):
    """Enum for door operation."""

    CLOSE = auto()
    OPEN = auto()


class TailwindResponseResult(StrEnum):
    """Enum for different response types."""

    OK = "OK"
    ERROR = "Fail"
    AUTH_ERROR = "token fail"


class TailwindRequestType(StrEnum):
    """Enum for different request types."""

    SET = "set"
    GET = "get"
