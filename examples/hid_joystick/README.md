# Basic HID joystick control

*By Soleil Lapierre*

A simple example of controlling Zaber devices with a USB game controller (Windows, Python & C#).

![Gamepad](img/gamepad.jpg)

## Prerequisites

### Python

The Python example uses `pipenv` to manage virtual environment and dependencies:

    py -m pip install -U pipenv

The dependencies are listed in [`Pipfile`](./python/Pipfile).
This example uses the third-party [`inputs`](https://pypi.org/project/inputs/) library for HID interfacing.

### C\#

The C# example requires the .NET SDK 6.0 or later to be installed and can be compiled with
Visual Studio Community 2022 or the `dotnet build` command.

## Hardware

The example code is intended for use at least one Zaber stage. The Python example is hardcoded to expect
two stages or a two-axis stage; you can edit the code to change that.

You will need a HID-compatible joystick or Gamepad. On Windows, a Microsoft X-Box 360 wired USB controller
or compatible will work.

The examples haven't been tested on other platforms, but it is known that wired gamepads aren't supported
by Mac OS (BlueTooth ones are) and on both Mac and Linux you may have to tinker with permissions to make
them work.

## Configuration and Running the Scripts

### Python

Before running the Python example you should edit the source code to select the serial port and Zaber device
addresses and axis numbers you will be using.

- `SERIAL_PORT`: the serial port that your device is connected to.
For more information on how to identify the serial port,
see [Find the right serial port name](https://software.zaber.com/motion-library/docs/guides/communication/find_right_port).
- `X-AXIS`: Mapping the device and axis number corresponding to X-Axis of the joystick.
- `Y-AXIS`: Mapping the device and axis number corresponding to Y-Axis of the joystick.

To run the script:

    cd src/microplate-scanning-basic/python
    pipenv install
    pipenv run python scanning.py

### C\#

- `private static string _port`: the default serial port that your device is connected to.
For more information on how to identify the serial port,
see [Find the right serial port name](https://software.zaber.com/motion-library/docs/guides/communication/find_right_port).

You can change the port to connect to by using the `-p PORT` command-line argument, or by
editing the default `private static string _port` near the bottom of `Program.cs`.
This example will automatically assign detected Zaber stages to joystick axes.

## Not an Endorsement

We are not necessarily recommending either of the input libraries used in the examples; there
are several alternatives available for each language. Before developing an application, investigate
the different HID input libraries available for your language and platform.
