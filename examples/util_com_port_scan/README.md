# COM Port Scan

*By Nathan Paolini*

This script quickly scans all active ports and displays which device is connected to which port.

## Dependencies / Software Requirements / Prerequisites

The script uses `pdm` to manage virtual environment and dependencies:

Instructions on how to install it can be found on the official `pdm` project page [here](https://github.com/pdm-project/pdm).

The dependencies are listed in `pyproject.toml`.

## Running the Script

```shell
cd examples/gui_pyqt6/
pdm install
pdm run example
```

## Script Purpose

This script scans all active ports and detects any connected Zaber devices.
This provides an easy output to show the user which stages are connected to which ports.
The relevant COM port numbers can then be specified when creating a connection in Zaber Launcher or in a script using Zaber Motion Library.

Note: if the devices are connected through a USB powered external USB hub, the hub may need to be plugged into computer
before plugging in the device chain; otherwise the devices may not be identified properly.
