# Simple GUI using SwiftUI

This example demonstrates using the [SwiftUI Framework](https://developer.apple.com/documentation/swiftui/)
to create a simple Interface to control a Zaber device.

<img src="img/screenshot.png" style="max-width:30rem;" alt="Screenshot">

## Hardware Requirements

Any Zaber linear motion device connected to a serial port.

## Dependencies / Software Requirements / Prerequisites

- MacOS 14.5+
- [XCode 16+](https://developer.apple.com/xcode/)

## Configuration / Parameters

The serial port to connect to can be entered into the input box after script startup.

Optionally, you can edit the following constants in the script before running the script:

- `DeviceConstants.deviceAddress`: The device address of the device you'd like to connect to
- `DeviceConstants.axisNumber`: The axis number of the axis you'd like to control on the device (`1` for most integrated devices)

## Running the Script

To run the script, open the project in XCode and press the `Start` button.
