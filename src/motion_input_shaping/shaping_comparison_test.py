"""
This script demonstrates an example of input shaping.

Shaped and unshaped moves are performed while capturing position data from the stage.
Both data sets are then plotted using matplotlib.
Note: this script requires a Zaber product with a direct reading encoder in order to properly
capture position data.
"""

import time
import sys
from matplotlib import pyplot as plt  # type: ignore
from zaber_motion import Units
from zaber_motion.ascii import Connection
from shaped_axis import ShapedAxis  # Zaber axis with input shaping
from step_response_data import (
    StepResponseData,
)  # Helper class for getting data from the onboard Oscilloscope
from shaper_config import *

# ------------------- Script Settings ----------------------

COM_PORT = "COMx"  # The COM port with the connected Zaber device.
DEVICE_INDEX = 0  # The Zaber device index to test.
AXIS_INDEX = 1  # The Zaber axis index to test.
MOVE_DISTANCE = 5  # The move distance in mm to test.
SCOPE_TIMEBASE = 1  # The scope sampling period in ms. Adjust if the whole move isn't captured.
RESONANT_FREQUENCY = 5.07  # Input shaping resonant frequency in Hz.
DAMPING_RATIO = 0.1  # Input shaping damping ratio.

# ------------------- Script Settings ----------------------


def plot(data_unshaped: StepResponseData, data_shaped: StepResponseData) -> None:
    """
    Plot the shaped and unshaped step response.

    :param data_unshaped: The unshaped step response data
    :param data_shaped: The shaped step response data
    """
    # Setup the plot
    plt.figure(1)
    plt.title("Device Response")
    plt.xlabel("Time [ms]")
    plt.ylabel("Position [um]")
    plt.grid(True)

    # Setup the y axes so only the final approach is shown
    ylimits_unshaped = data_unshaped.get_trajectory_settling_limits(True)
    ylimits_shaped = data_shaped.get_trajectory_settling_limits(True)
    plt.ylim(
        min(ylimits_shaped[0], ylimits_unshaped[0]), max(ylimits_shaped[1], ylimits_unshaped[1])
    )

    # Plot both data sets
    plt.plot(
        data_unshaped.get_time_stamps(),
        data_unshaped.get_target_positions(True),
        label="Target Position (unshaped)",
        color="black",
        linestyle="--",
    )
    plt.plot(
        data_unshaped.get_time_stamps(),
        data_unshaped.get_measured_positions(True),
        label="Measured Position (unshaped)",
        color="black",
    )

    plt.plot(
        data_shaped.get_time_stamps(),
        data_shaped.get_target_positions(True),
        label="Target Position (shaped)",
        color="red",
        linestyle="--",
    )
    plt.plot(
        data_shaped.get_time_stamps(),
        data_shaped.get_measured_positions(True),
        label="Measured Position (shaped)",
        color="red",
    )

    plt.legend(loc="lower right")
    plt.show()


if __name__ == "__main__":
    # Open the connection and get the device + axis
    with Connection.open_serial_port(COM_PORT) as connection:
        device_list = connection.detect_devices()
        print(f"Found {len(device_list)} devices")

        if len(device_list) < DEVICE_INDEX + 1:
            print(f"Not enough devices for specified device index ({DEVICE_INDEX}), exiting.")
            sys.exit(0)

        # Get the device and setup the input shaping axis
        device = device_list[DEVICE_INDEX]

        if device.axis_count < AXIS_INDEX:
            print(f"Not enough axes for specified axis index ({AXIS_INDEX}), exiting.")
            sys.exit(0)

        shaped_axis = ShapedAxis(device.get_axis(AXIS_INDEX), RESONANT_FREQUENCY, DAMPING_RATIO,
                                 ShaperConfig(ShaperMode.DECEL))

        # Home the axis and move to zero position
        if not shaped_axis.is_homed():
            shaped_axis.home()

        shaped_axis.move_absolute(0, Units.LENGTH_MILLIMETRES, True)
        time.sleep(0.2)

        # Get the first dataset with no shaping
        print("Performing unshaped move.")
        step_response_data_unshaped = StepResponseData(
            SCOPE_TIMEBASE, Units.TIME_MILLISECONDS, Units.LENGTH_MICROMETRES
        )

        step_response_data_unshaped.capture_data(
            shaped_axis,
            lambda: shaped_axis.move_relative(MOVE_DISTANCE, Units.LENGTH_MILLIMETRES, False),
            True,
        )

        time.sleep(0.5)

        # Get the second dataset with shaping
        print("Performing shaped move.")
        step_response_data_shaped = StepResponseData(
            SCOPE_TIMEBASE, Units.TIME_MILLISECONDS, Units.LENGTH_MICROMETRES
        )

        step_response_data_shaped.capture_data(
            shaped_axis,
            lambda: shaped_axis.move_relative_shaped(
                MOVE_DISTANCE, Units.LENGTH_MILLIMETRES, False
            ),
            True,
        )

        shaped_axis.reset_deceleration()

    plot(step_response_data_unshaped, step_response_data_shaped)

    print("Complete.")
