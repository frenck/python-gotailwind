# pylint: disable=W0621
"""Asynchronous Python client for Tailwind garage door openers."""

import asyncio

from gotailwind import Tailwind, TailwindDoorOperationCommand, TailwindDoorState


async def main() -> None:
    """Show example of programmatically control a Tailwind garage door."""
    async with Tailwind(host="192.168.1.123", token="123456") as tailwind:
        # Get the device status
        status = await tailwind.status()

        # Print some information
        print(f"Device ID: {status.device_id}")
        print(f"Number of doors: {status.number_of_doors}")

        # Get the door object for the first door
        door = await tailwind.door_status(door=0)

        # Print current door status
        print(f"Door 1 is currently: {door.state}")

        # Change the door
        if door.state == TailwindDoorState.OPEN:
            door = await tailwind.operate(
                door=0, operation=TailwindDoorOperationCommand.CLOSE
            )
        else:
            door = await tailwind.operate(
                door=0, operation=TailwindDoorOperationCommand.OPEN
            )

        # Print current door status
        print(f"Door 1 is now: {door.state}")


if __name__ == "__main__":
    asyncio.run(main())
