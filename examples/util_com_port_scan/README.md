# COM Port Scan

*By Nathan Paolini*

This script quickly scans all active ports and displays which device is connected to which port.

## Dependencies

- Python 3.10 or newer
- The script uses `venv` to manage virtual environment and dependencies.
- The dependencies are listed in the requirements.txt file.

## Running the Script

### Windows

To setup `venv`, run `setup_venv.bat` in the `python` folder.

To run the script:

    cd src\util_com_port_scan
    .venv\Scripts\python com_port_scan.py

### Linux / MacOS

To setup `venv`:

    cd src/util_com_port_scan
    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt

To run the script:

    .venv/bin/python com_port_scan.py

## Script Purpose

This script scans all active ports and detects any connected Zaber devices.
This provides an easy output to show the user which stages are connected to which ports.
The relevant COM port numbers can then be specified when creating a connection in Zaber Launcher or in a script using Zaber Motion Library.

Note: if the devices are connected through a USB powered external USB hub, the hub may need to be plugged into computer
before plugging in the device chain; otherwise the devices may not be identified properly.
