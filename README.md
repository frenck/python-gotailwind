# Python: Asynchronous client for Tailwind garage door openers

[![GitHub Release][releases-shield]][releases]
[![Python Versions][python-versions-shield]][pypi]
![Project Stage][project-stage-shield]
![Project Maintenance][maintenance-shield]
[![License][license-shield]](LICENSE.md)

[![Build Status][build-shield]][build]
[![Code Coverage][codecov-shield]][codecov]
[![Quality Gate Status][sonarcloud-shield]][sonarcloud]
[![Open in Dev Containers][devcontainer-shield]][devcontainer]

[![Sponsor Frenck via GitHub Sponsors][github-sponsors-shield]][github-sponsors]

[![Support Frenck on Patreon][patreon-shield]][patreon]

Asynchronous Python client for Tailwind garage door openers.

## About

This package allows you to control and monitor [Tailwind devices](https://gotailwind.com/)
programmatically. It is mainly created to allow third-party programs to
automate the behavior of a Tailwind device.

Additionally, this package contains a CLI tool, which can be used standalone,
proving a command-line interface to control and monitor Tailwind devices.

Known compatible and tested Tailwind devices:

- [Tailwind iQ3](https://gotailwind.com/products/iq3-smart-garage-controller)

> [!IMPORTANT]
> This library requires your Tailwind device to run at least firmware version v10.10.

For the development of this package, the hardware was kindly sponsored
and provided by [Tailwind](https://gotailwind.com/); thank you! ❤️

## Installation

```bash
pip install gotailwind
```

In case you want to use the CLI tools, install the package with the following
extra:

```bash
pip install gotailwind[cli]
```

## CLI usage

The tailwind CLI tool provided in this library provides all the functionalities
this library provides but from the command line.

The CLI comes with built-in help, which can be accessed by using the `--help`

```bash
tailwind --help
```

To scan for Tailwind devices on your network:

```bash
tailwind scan
```

To get the status of a device:

```bash
tailwind status --host 192.168.1.123
```

To open a door:

```bash
tailwind open --host 192.168.1.123
```

For more details, access the built-in help of the CLI using the `--help` flag.

## Python usage

Using this library in Python:

```python
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
```

## Changelog & releases

This repository keeps a change log using [GitHub's releases][releases]
functionality. The format of the log is based on
[Keep a Changelog][keepchangelog].

Releases are based on [Semantic Versioning][semver], and use the format
of `MAJOR.MINOR.PATCH`. In a nutshell, the version will be incremented
based on the following:

- `MAJOR`: Incompatible or major changes.
- `MINOR`: Backwards-compatible new features and enhancements.
- `PATCH`: Backwards-compatible bugfixes and package updates.

## Contributing

This is an active open-source project. We are always open to people who want to
use the code or contribute to it.

We've set up a separate document for our
[contribution guidelines](CONTRIBUTING.md).

Thank you for being involved! :heart_eyes:

## Setting up a development environment

The easiest way to start is by opening a CodeSpace here on GitHub, or by using
the [Dev Container][devcontainer] feature of Visual Studio Code.

[![Open in Dev Containers][devcontainer-shield]][devcontainer]

This Python project is fully managed using the [Poetry][poetry] dependency manager. But also relies on the use of NodeJS for certain checks during development.

You need at least:

- Python 3.11+
- [Poetry][poetry-install]
- NodeJS 20+ (including NPM)

To install all packages, including all development requirements:

```bash
npm install
poetry install --extras cli
```

As this repository uses the [pre-commit][pre-commit] framework, all changes
are linted and tested with each commit. You can run all checks and tests
manually, using the following command:

```bash
poetry run pre-commit run --all-files
```

To run just the Python tests:

```bash
poetry run pytest
```

## Authors & contributors

The original setup of this repository is by [Franck Nijhof][frenck].

For a full list of all authors and contributors,
check [the contributor's page][contributors].

## License

MIT License

Copyright (c) 2023-2024 Franck Nijhof

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

[build-shield]: https://github.com/frenck/python-gotailwind/actions/workflows/tests.yaml/badge.svg
[build]: https://github.com/frenck/python-gotailwind/actions/workflows/tests.yaml
[codecov-shield]: https://codecov.io/gh/frenck/python-gotailwind/branch/master/graph/badge.svg
[codecov]: https://codecov.io/gh/frenck/python-gotailwind
[contributors]: https://github.com/frenck/python-gotailwind/graphs/contributors
[devcontainer-shield]: https://img.shields.io/static/v1?label=Dev%20Containers&message=Open&color=blue&logo=visualstudiocode
[devcontainer]: https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/frenck/python-gotailwind
[frenck]: https://github.com/frenck
[github-sponsors-shield]: https://frenck.dev/wp-content/uploads/2019/12/github_sponsor.png
[github-sponsors]: https://github.com/sponsors/frenck
[keepchangelog]: http://keepachangelog.com/en/1.0.0/
[license-shield]: https://img.shields.io/github/license/frenck/python-gotailwind.svg
[maintenance-shield]: https://img.shields.io/maintenance/yes/2024.svg
[patreon-shield]: https://frenck.dev/wp-content/uploads/2019/12/patreon.png
[patreon]: https://www.patreon.com/frenck
[poetry-install]: https://python-poetry.org/docs/#installation
[poetry]: https://python-poetry.org
[pre-commit]: https://pre-commit.com/
[project-stage-shield]: https://img.shields.io/badge/project%20stage-production%20ready-brightgreen.svg
[pypi]: https://pypi.org/project/gotailwind/
[python-versions-shield]: https://img.shields.io/pypi/pyversions/gotailwind
[releases-shield]: https://img.shields.io/github/release/frenck/python-gotailwind.svg
[releases]: https://github.com/frenck/python-gotailwind/releases
[semver]: http://semver.org/spec/v2.0.0.html
[sonarcloud-shield]: https://sonarcloud.io/api/project_badges/measure?project=frenck_python-gotailwind&metric=alert_status
[sonarcloud]: https://sonarcloud.io/summary/new_code?id=frenck_python-gotailwind
