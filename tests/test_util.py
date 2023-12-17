"""Asynchronous Python client for Tailwind garage door openers."""

from gotailwind.util import tailwind_device_id_to_mac_address


def test_tailwind_device_id_to_mac_address() -> None:
    """Test tailwind_device_id_to_mac_address."""
    assert tailwind_device_id_to_mac_address("3c_e9_0e_6d_21_84") == "3c:e9:0e:6d:21:84"
