"""Asynchronous Python client for Tailwind garage door openers."""


def tailwind_device_id_to_mac_address(device_id: str) -> str:
    """Convert a Tailwind device ID to a MAC address."""
    return ":".join([part.zfill(2) for part in device_id.strip("_").split("_")])
