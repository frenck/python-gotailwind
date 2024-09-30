"""Asynchronous Python client for Tailwind garage door openers."""


class TailwindError(Exception):
    """Generic Tailwind exception."""


class TailwindConnectionError(TailwindError):
    """Tailwind connection exception."""


class TailwindConnectionTimeoutError(TailwindConnectionError):
    """Tailwind connection timeout exception."""


class TailwindResponseError(TailwindError):
    """Tailwind unexpected response exception."""


class TailwindAuthenticationError(TailwindResponseError):
    """Tailwind connection exception."""


class TailwindDoorUnknownError(TailwindError):
    """Tailwind unknown door exception."""


class TailwindDoorOperationError(TailwindError):
    """Tailwind door operation exception."""


class TailwindDoorAlreadyInStateError(TailwindDoorOperationError):
    """Tailwind already in state door exception."""


class TailwindDoorDisabledError(TailwindDoorOperationError):
    """Tailwind disabled door exception."""


class TailwindDoorLockedOutError(TailwindDoorOperationError):
    """Tailwind locked out door exception."""


class TailwindUnsupportedFirmwareVersionError(TailwindError):
    """Tailwind unsupported version exception."""
