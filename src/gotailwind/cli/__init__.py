"""Asynchronous Python client for Tailwind garage door openers."""

import asyncio
import sys
from typing import Annotated

import typer
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from zeroconf import ServiceStateChange, Zeroconf
from zeroconf.asyncio import AsyncServiceBrowser, AsyncServiceInfo, AsyncZeroconf

from gotailwind.const import (
    TailwindDoorOperationCommand,
    TailwindDoorState,
)
from gotailwind.exceptions import (
    TailwindAuthenticationError,
    TailwindConnectionError,
    TailwindDoorDisabledError,
    TailwindDoorLockedOutError,
    TailwindUnsupportedFirmwareVersionError,
)
from gotailwind.tailwind import Tailwind

from .async_typer import AsyncTyper

cli = AsyncTyper(help="Tailwind CLI", no_args_is_help=True, add_completion=False)
console = Console()


@cli.error_handler(TailwindAuthenticationError)
def authentication_error_handler(_: TailwindAuthenticationError) -> None:
    """Handle authentication errors."""
    message = """
    The provided Tailwind device local access token is invalid.

    To find your Tailwind device's access token, surf to the following URL
    in your browser:

    https://web.gotailwind.com/client/integration/local-control-key

    You will be prompted to log in to your Tailwind account. After logging in,
    you will be presented with a 6 digit code. This code is your Tailwind
    device's local access token.
    """
    panel = Panel(
        message,
        expand=False,
        title="Authentication error",
        border_style="red bold",
    )
    console.print(panel)
    sys.exit(1)


@cli.error_handler(TailwindConnectionError)
def connection_error_handler(_: TailwindConnectionError) -> None:
    """Handle connection errors."""
    message = """
    Could not connect to the specified Tailwind device. Please make sure that
    the device is powered on, connected to the network and that you have
    specified the correct IP address or hostname.

    If you are not sure what the IP address or hostname of your Tailwind device
    is, you can use the scan command to find it:

    tailwind scan
    """
    panel = Panel(
        message,
        expand=False,
        title="Connection error",
        border_style="red bold",
    )
    console.print(panel)
    sys.exit(1)


@cli.error_handler(TailwindUnsupportedFirmwareVersionError)
def unsupported_firmware_version_error_handler(
    _: TailwindUnsupportedFirmwareVersionError,
) -> None:
    """Handle unsupported version errors."""
    message = """
    The specified Tailwind device is running an unsupported firmware version.

    The tooling currently only supports firmware versions 10.10 and higher.
    """
    panel = Panel(
        message,
        expand=False,
        title="Unsupported firmware version",
        border_style="red bold",
    )
    console.print(panel)
    sys.exit(1)


@cli.error_handler(TailwindDoorLockedOutError)
def door_locked_out_error_handler(_: TailwindDoorLockedOutError) -> None:
    """Handle locked out door operation errors."""
    console.print(
        Panel(
            "🔒 [red]Door is locked out and cannot be operated",
            expand=False,
            title="Door operation error",
            border_style="red bold",
        )
    )
    sys.exit(1)


@cli.error_handler(TailwindDoorDisabledError)
def door_disabled_error_handler(_: TailwindDoorDisabledError) -> None:
    """Handle disabled door operation errors."""
    console.print(
        Panel(
            "🛑 [red]Door is disabled and can not be operated",
            expand=False,
            title="Door operation error",
            border_style="red bold",
        )
    )
    sys.exit(1)


@cli.command("status")
async def status(
    host: Annotated[
        str,
        typer.Option(
            help="Tailwind device IP address or hostname",
            prompt="Host address",
            show_default=False,
        ),
    ],
    token: Annotated[
        str,
        typer.Option(
            help="Tailwind device access token",
            prompt="Access token",
            show_default=False,
            hide_input=True,
        ),
    ],
) -> None:
    """Get the status of a Tailwind device."""
    async with Tailwind(host=host, token=token) as tailwind:
        device_status = await tailwind.status()

    device_table = Table(title="\nTailwind device status", show_header=False)
    device_table.add_column("Property", style="cyan bold")
    device_table.add_column("Value", style="green")

    device_table.add_row("Product", device_status.product)
    device_table.add_row("Device ID", device_status.device_id)
    device_table.add_row("MAC address", device_status.mac_address)
    device_table.add_row("Protocol version", device_status.protocol_version)
    device_table.add_row("Firmware version", device_status.firmware_version)
    device_table.add_row("Number of doors", str(device_status.number_of_doors))
    device_table.add_row(
        "Night mode enabled", "Yes" if device_status.night_mode_enabled else "No"
    )
    device_table.add_row("LED brightness", f"{device_status.led_brightness}%")

    console.print(device_table)

    doors_table = Table(title="Garage doors", header_style="cyan bold", show_lines=True)
    doors_table.add_column("Door")
    doors_table.add_column("State", style="bold")
    doors_table.add_column("Locked out")
    doors_table.add_column("Disabled")

    for door in device_status.doors.values():
        doors_table.add_row(
            str(door.index + 1),
            "[red]Open" if door.state == TailwindDoorState.OPEN else "[green]Closed",
            "[red bold]Yes" if door.locked_out else "No",
            "[red bold]Yes" if door.disabled else "No",
        )

    console.print(doors_table)


@cli.command("identify")
async def identify(
    host: Annotated[
        str,
        typer.Option(
            help="Tailwind device IP address or hostname",
            prompt="Host address",
            show_default=False,
        ),
    ],
    token: Annotated[
        str,
        typer.Option(
            help="Tailwind device access token",
            prompt="Access token",
            show_default=False,
            hide_input=True,
        ),
    ],
) -> None:
    """Flash the Tailwind LED to identify the device."""
    with console.status("[cyan]Identifying...", spinner="toggle12"):
        async with Tailwind(host=host, token=token) as tailwind:
            await tailwind.identify()
    console.print("✅[green]Success!")


@cli.command("close")
async def door_close(
    host: Annotated[
        str,
        typer.Option(
            help="Tailwind device IP address or hostname",
            prompt="Host address",
            show_default=False,
        ),
    ],
    token: Annotated[
        str,
        typer.Option(
            help="Tailwind device access token",
            prompt="Access token",
            show_default=False,
            hide_input=True,
        ),
    ],
    door: Annotated[
        int,
        typer.Option(
            help="Door to close",
            prompt="Door",
            show_default=False,
            prompt_required=False,
        ),
    ] = 1,
) -> None:
    """Close a garage door."""
    msg = "Door must be an number between 1 and 3"
    try:
        door = int(door)
    except ValueError as err:
        raise typer.BadParameter(msg) from err

    if not 1 <= door <= 3:
        raise typer.BadParameter(msg)

    with console.status(f"[cyan]Closing door {door}...", spinner="toggle12"):
        async with Tailwind(host=host, token=token) as tailwind:
            device_status = await tailwind.status()
            if device_status.number_of_doors < door:
                msg = f"Door {door} does not exist on this Tailwind device"
                raise typer.BadParameter(msg)

            door_idx = door - 1
            door_status = await tailwind.door_status(door=door_idx)
            if door_status.state == TailwindDoorState.CLOSED:
                console.print(f"🤔 [red]Door {door} is already closed")
                raise typer.Exit(1)

            door_status = await tailwind.operate(
                door=door_idx, operation=TailwindDoorOperationCommand.CLOSE
            )

    if door_status.state != TailwindDoorState.CLOSED:
        console.print(f"😭 [red]Door {door} did not close")
        raise typer.Exit(1)

    console.print(f"✅[green]Success! Door {door} has been closed!")


@cli.command("open")
async def door_open(
    host: Annotated[
        str,
        typer.Option(
            help="Tailwind device IP address or hostname",
            prompt="Host address",
            show_default=False,
        ),
    ],
    token: Annotated[
        str,
        typer.Option(
            help="Tailwind device access token",
            prompt="Access token",
            show_default=False,
            hide_input=True,
        ),
    ],
    door: Annotated[
        int,
        typer.Option(
            help="Door to open",
            prompt="Door",
            show_default=False,
            prompt_required=False,
        ),
    ] = 1,
) -> None:
    """Open a garage door."""
    msg = "Door must be an number between 1 and 3"
    try:
        door = int(door)
    except ValueError as err:
        raise typer.BadParameter(msg) from err

    if not 1 <= door <= 3:
        raise typer.BadParameter(msg)

    with console.status(f"[cyan]Opening door {door}...", spinner="toggle12"):
        async with Tailwind(host=host, token=token) as tailwind:
            device_status = await tailwind.status()
            if device_status.number_of_doors < door:
                msg = f"Door {door} does not exist on this Tailwind device"
                raise typer.BadParameter(msg)

            door_idx = door - 1
            door_status = await tailwind.door_status(door=door_idx)
            if door_status.state == TailwindDoorState.OPEN:
                console.print(f"🤔 [red]Door {door} is already open")
                raise typer.Exit(1)

            door_status = await tailwind.operate(
                door=door_idx, operation=TailwindDoorOperationCommand.OPEN
            )

    if door_status.state != TailwindDoorState.OPEN:
        console.print(f"😭 [red]Door {door} did not open")
        raise typer.Exit(1)

    console.print(f"✅[green]Success! Door {door} has been opened!")


@cli.command("led")
async def led(
    host: Annotated[
        str,
        typer.Option(
            help="Tailwind device IP address or hostname",
            prompt="Host address",
            show_default=False,
        ),
    ],
    token: Annotated[
        str,
        typer.Option(
            help="Tailwind device access token",
            prompt="Access token",
            show_default=False,
            hide_input=True,
        ),
    ],
    brightness: Annotated[
        int,
        typer.Option(
            help="Brightness of the status LED in %",
            prompt="Brightness",
            show_default=False,
        ),
    ] = 100,
) -> None:
    """Change the brightness of the status LED."""
    msg = "Brightness must be an number between 0 and 100"
    try:
        door = int(brightness)
    except ValueError as err:
        raise typer.BadParameter(msg) from err

    if not 0 <= door <= 100:
        raise typer.BadParameter(msg)

    with console.status(
        f"[cyan]Setting status LED brightness to {brightness}%...", spinner="toggle12"
    ):
        async with Tailwind(host=host, token=token) as tailwind:
            await tailwind.status_led(brightness=brightness)

    console.print(f"✅[green]Success! Status LED brightness set to {brightness}%")


@cli.command("scan")
async def test() -> None:
    """Scan for Tailwind devices on the network."""
    zeroconf = AsyncZeroconf()
    background_tasks = set()

    table = Table(
        title="\n\nFound Tailwind devices", header_style="cyan bold", show_lines=True
    )
    table.add_column("Addresses")
    table.add_column("Product")
    table.add_column("Device ID")
    table.add_column("Hardware version")
    table.add_column("Software version")

    def async_on_service_state_change(
        zeroconf: Zeroconf,
        service_type: str,
        name: str,
        state_change: ServiceStateChange,
    ) -> None:
        """Handle service state changes."""
        if state_change is not ServiceStateChange.Added:
            return

        future = asyncio.ensure_future(
            async_display_service_info(zeroconf, service_type, name)
        )
        background_tasks.add(future)
        future.add_done_callback(background_tasks.discard)

    async def async_display_service_info(
        zeroconf: Zeroconf, service_type: str, name: str
    ) -> None:
        """Retrieve and display service info."""
        info = AsyncServiceInfo(service_type, name)
        await info.async_request(zeroconf, 3000)
        if info is None:
            return

        if info.properties is None or not str(info.server).startswith("tailwind-"):
            console.print(
                f"[grey78]Found service {info.server}: is not a Tailwind device."
            )
            return

        console.print(
            f"[cyan bold]Found service {info.server}: is a Tailwind device 🎉"
        )

        table.add_row(
            f"{str(info.server).rstrip('.')}\n"
            + ", ".join(info.parsed_scoped_addresses()),
            info.properties[b"product"].decode(),  # type: ignore[union-attr]
            info.properties[b"device_id"].decode(),  # type: ignore[union-attr]
            info.properties[b"HW ver"].decode(),  # type: ignore[union-attr]
            info.properties[b"SW ver"].decode(),  # type: ignore[union-attr]
        )

    console.print("[green]Scanning for Tailwind devices...")
    console.print("[red]Press Ctrl-C to exit\n")

    with Live(table, console=console, refresh_per_second=4):
        browser = AsyncServiceBrowser(
            zeroconf.zeroconf,
            "_http._tcp.local.",
            handlers=[async_on_service_state_change],
        )

        try:
            forever = asyncio.Event()
            await forever.wait()
        except KeyboardInterrupt:
            pass
        finally:
            console.print("\n[green]Control-C pressed, stopping scan")
            await browser.async_cancel()
            await zeroconf.async_close()


if __name__ == "__main__":
    cli()
