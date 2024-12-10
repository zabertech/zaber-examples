# Tracking Motion Using PID Controller

This example demonstrates how Zaber stages can track analog input signals using a PID controller.
A PID controller is a control loop feedback mechanism widely used in industrial control systems.
It calculates the error between a desired setpoint and a measured process variable and applies a correction based on proportional, integral, and derivative terms.
In Zaber's case, the controller can move the stage to track the setpoint of the analog input signal.
Zaber only supports the PI controller, which is a simplified version of the PID controller without derivative term.

The following video demonstrates the concept:

![video.mp4](img/video.mp4)

In the video above there is a load cell mounted on a Zaber stage.
The stage is tracking the analog input signal from the load cell keeping a constant tension on the spring.
When disrupted, the stage moves to compensate for the change in the force until it reaches the setpoint again.

## Code

### Dependencies

The script uses `pdm` to manage the virtual environment and dependencies:

Instructions on how to install it can be found on the official `pdm` project page [here](https://github.com/pdm-project/pdm).

The dependencies are listed in `pyproject.toml`.

### Running the Script

Make sure to change `SERIAL_PORT` constant in `main.py` file to the serial port that your device is connected to.

Afterwards, you can run the example:

```shell
cd examples/motion_tracking/
pdm install
pdm run example
```

### Explanation

<https://github.com/zabertech/zaber-examples/blob/main/examples/motion_tracking/src/motion_tracking/main.py#L17-L32>

After establishing a connection with the device, the script prints the PI controller parameters.

Then based on the user input "track" the scripts starts the PI controller by issuing the `move track` command to the axis.
After that, the stage will track the analog input signal indefinitely until the user inputs "stop".

## Tuning the Controller

Properly tuning the controller requires a basic understanding of control theory and is beyond the scope of this example.
Typically, you adjust the Kp and Ki parameters to achieve the desired response.
You may also need to change the direction (setting `motion.tracking.dir`) if the input signal is inverted.
In this example, the Kp = 0, Ki = 1000, and the direction is set to 1.
We recommend using Oscilloscope application in Zaber Launcher to visualize the input signal and the stage position.

## Additional Information

There is also a `move track once` variant of the `move track` command that reaches the setpoint once and then stops.
For this variant a settings `motion.tracking.settle.tolerance` and `motion.tracking.settle.period` determines
when the stage is considered to have settled at the setpoint.

You can find the exhaustive list of commands and settings in the [ASCII Protocol Manual](https://www.zaber.com/protocol-manual?protocol=ASCII).
