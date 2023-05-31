"""Simple Zaber stage control using a HID joystick under Windows.

Demonstrates using the Python input library to read a HID joystick, then
translate the stick deflections to stage velocities and button presses to
home or stop commands.

This example expects to find a two-axis device on the designated serial port.
Edit the constants below to change this.

Created 2023, Contributors: Soleil Lapierre
"""

import logging
import math

from inputs import get_gamepad  # type: ignore

from zaber_motion import MotionLibException
from zaber_motion.ascii import Connection, Axis


log = logging.getLogger(__name__)

SERIAL_PORT = "COMx"

# Map joystick axes to Zaber (<device_addresse>, <axis_number>).
X_AXIS = (1, 1)
Y_AXIS = (1, 2)

# Constant for analog stick range from the inputs library.
MAX_DEFLECTION = 32768

# Define a dead zone that maps to zero, with linear increase from the edge.
DEAD_ZONE = MAX_DEFLECTION / 5


def scale_deflection(deflection: float) -> float:
    """Map stick deflection to the range -1 to 1, with dead zone and curve."""
    defl_abs = math.fabs(deflection)
    if defl_abs < 1:
        return 0

    sign = deflection / defl_abs
    scaled = (max(DEAD_ZONE, defl_abs) - DEAD_ZONE) / (MAX_DEFLECTION - DEAD_ZONE)
    log.info(str(scaled))
    return sign * math.pow(scaled, 3)


def read_loop(x_axis: Axis, y_axis: Axis) -> None:
    """Read joystick input and controls devices accordingly. Main loop of the program."""
    # The input library only generates events when controls change state, so
    # let's pre-populate our state tracking with default values for the
    # controls we use.
    # Note these control names are specific to the inputs library.
    input_states = {
        "BTN_SELECT": 0,
        "ABS_X": 0,
        "ABS_Y": 0,
        "BTN_EAST": 0,
        "BTN_WEST": 0,
    }

    # Get the max speeds of the axes for input scaling.
    # Not using units of measure to avoid the complication of
    # linear vs. rotary devices.
    max_speed_x = x_axis.settings.get("maxspeed")
    max_speed_y = y_axis.settings.get("maxspeed")

    end = False
    log.info("Use the left stick to move the X and Y axes.")
    log.info("Press the X button to home or the B button to stop.")
    log.info("Press the Start button to exit, or press CTRL-C.")
    while not end:
        joystick = get_gamepad()
        for event in joystick:
            if event.ev_type in ("Absolute", "Key"):
                input_states[event.code] = event.state
            else:
                continue  # Don't take any action for irrelevant events.

            # Exit if start button pressed.
            # Note as of this writing the inputs library has start and select swapped.
            if input_states["BTN_SELECT"] == 1:
                log.info("Exiting")
                return

            # Give buttons priority over moves.
            try:
                if input_states["BTN_WEST"] == 1:
                    log.info("Homing")
                    # Overlap the commands so homing completes faster.
                    x_axis.home(wait_until_idle=False)
                    y_axis.home(wait_until_idle=False)
                    x_axis.wait_until_idle()
                    y_axis.wait_until_idle()
                    log.info("Homing completed")
                elif input_states["BTN_EAST"] == 1:
                    log.info("Stopping")
                    x_axis.stop(wait_until_idle=False)
                    y_axis.stop(wait_until_idle=False)
                else:
                    x_speed = scale_deflection(input_states["ABS_X"]) * max_speed_x
                    y_speed = scale_deflection(input_states["ABS_Y"]) * max_speed_y
                    log.info("Changing velocities to %s and %s.", x_speed, y_speed)
                    x_axis.move_velocity(x_speed)
                    y_axis.move_velocity(y_speed)
            except MotionLibException:
                log.error("Error sending a move command:", exc_info=True)


def main() -> None:
    """Open Zaber device connections and initialize the program."""
    # Verify the expected devices exist.
    with Connection.open_serial_port(SERIAL_PORT) as connection:
        try:
            x_device = connection.get_device(X_AXIS[0])
            x_device.identify()
            x_axis = x_device.get_axis(X_AXIS[1])
        except MotionLibException:
            log.error("Failed to identify the X axis at address /%d %d", X_AXIS[0], X_AXIS[1])
            return

        try:
            if Y_AXIS[0] != X_AXIS[0]:
                y_device = connection.get_device(Y_AXIS[0])
                y_device.identify()
            else:
                y_device = x_device
            y_axis = y_device.get_axis(Y_AXIS[1])
        except MotionLibException:
            log.error("Failed to identify the Y axis at address /%d %d", Y_AXIS[0], Y_AXIS[1])
            return

        read_loop(x_axis, y_axis)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    main()
