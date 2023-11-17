"""
This script demonstrates an example of input shaping.

Shaped and unshaped moves are performed while capturing position data from the stage.
Both data sets are then plotted using matplotlib.
Note: this script requires a Zaber product with a direct reading encoder in order to properly
capture position data.
"""

import time
import sys
from matplotlib import pyplot as plt
from zaber_motion import Units, CommandFailedException, LockstepNotEnabledException
from zaber_motion.ascii import Connection, Axis, Lockstep
from shaped_axis import ShapedAxis
from shaped_axis_stream import ShapedAxisStream
from plant import Plant
from zero_vibration_stream_generator import ShaperType
from step_response_data import StepResponseData

# ------------------- Script Settings ----------------------

COM_PORT = "COMx"  # The COM port with the connected Zaber device.
DEVICE_INDEX = 0  # The Zaber device index to test.
AXIS_INDEX = 1  # The Zaber axis index to test.
MOVE_DISTANCE = 5  # The move distance in mm to test.
SCOPE_TIMEBASE = 1  # The scope sampling period in ms. Adjust if the whole move isn't captured.
RESONANT_FREQUENCY = 5.07  # Input shaping resonant frequency in Hz.
DAMPING_RATIO = 0.1  # Input shaping damping ratio.
STREAM_SHAPER_TYPE = ShaperType.ZV  # Input shaper type for ShapedAxisStream
SETTLING_TIME = 1  # Amount of time to wait between moves for vibrations to settle

# ------------------- Script Settings ----------------------


def plot(datasets: list[StepResponseData], labels: list[str], colors: list[str]) -> None:
    """
    Plot step response data.

    :param datasets: List of step response data to plot
    :param labels: List of legend labels for each step response data
    :param colors: List of plot colors for each step response data
    """
    # Set up the plot
    fig = plt.figure(1)

    # Plot motion trajectory
    ax_input = fig.add_subplot(2, 1, 1)
    ax_input.set_title("Input Motion")
    ax_input.set_xlabel("Time [ms]")
    ax_input.set_ylabel("Position [um]")
    ax_input.grid(True)

    for n, data in enumerate(datasets):
        ax_input.plot(
            data.get_time_stamps(),
            data.get_target_positions(False),
            label=f"Target Position ({labels[n]})",
            color=colors[n],
        )

    ax_input.legend(loc="lower right")

    # Plot response zoomed into to see residual vibration
    ax_response = fig.add_subplot(2, 1, 2)
    ax_response.set_title("Device Response")
    ax_response.set_xlabel("Time [ms]")
    ax_response.set_ylabel("Position [um]")
    ax_response.grid(True)

    # Setup the y axes so only the final approach is shown
    ylimits = [x.get_trajectory_settling_limits(True) for x in datasets]
    ax_response.set_ylim(min(x[0] for x in ylimits), max(x[1] for x in ylimits))

    # Plot datasets
    for n, data in enumerate(datasets):
        ax_response.plot(
            data.get_time_stamps(),
            data.get_target_positions(True),
            label=f"Target ({labels[n]})",
            color=colors[n],
            linestyle="--",
        )
        ax_response.plot(
            data.get_time_stamps(),
            data.get_measured_positions(True),
            label=f"Measured ({labels[n]})",
            color=colors[n],
        )

    ax_response.legend(loc="lower right")

    fig.tight_layout()

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

        # Check if axis is part of lockstep group
        LOCKSTEP_INDEX = 0
        try:
            num_lockstep_groups_possible = device.settings.get("lockstep.numgroups")
            for group_num in range(1, int(num_lockstep_groups_possible) + 1):
                try:
                    axis_nums = device.get_lockstep(group_num).get_axis_numbers()
                    if AXIS_INDEX in axis_nums:
                        print(f"Axis {AXIS_INDEX} is part of Lockstep group {group_num}.")
                        LOCKSTEP_INDEX = group_num
                        break
                except LockstepNotEnabledException:
                    pass
        except CommandFailedException:
            # Unable to get lockstep.numgroups settings meaning device is not capable of lockstep.
            pass

        zaber_object: Axis | Lockstep
        if LOCKSTEP_INDEX == 0:
            zaber_object = device.get_axis(AXIS_INDEX)
        else:
            zaber_object = device.get_lockstep(LOCKSTEP_INDEX)

        plant = Plant(RESONANT_FREQUENCY, DAMPING_RATIO)
        shaped_axis = ShapedAxis(zaber_object, plant)
        shaped_axis_stream = ShapedAxisStream(zaber_object, plant, STREAM_SHAPER_TYPE)

        # Home the axis and move to zero position
        if not shaped_axis.is_homed():
            shaped_axis.axis.home()

        shaped_axis.axis.move_absolute(0, Units.LENGTH_MILLIMETRES, True)
        time.sleep(SETTLING_TIME)

        # Get the first dataset with no shaping
        print("Performing unshaped move.")
        step_response_data_unshaped = StepResponseData(
            SCOPE_TIMEBASE, Units.TIME_MILLISECONDS, Units.LENGTH_MICROMETRES
        )

        step_response_data_unshaped.capture_data(
            shaped_axis.axis,
            lambda: shaped_axis.axis.move_relative(MOVE_DISTANCE, Units.LENGTH_MILLIMETRES, False),
            True,
        )

        time.sleep(SETTLING_TIME)

        # Get the second dataset with shaping
        print("Performing shaped move.")
        step_response_data_shaped = StepResponseData(
            SCOPE_TIMEBASE, Units.TIME_MILLISECONDS, Units.LENGTH_MICROMETRES
        )

        step_response_data_shaped.capture_data(
            shaped_axis.axis,
            lambda: shaped_axis.move_relative(MOVE_DISTANCE, Units.LENGTH_MILLIMETRES, False),
            True,
        )

        shaped_axis.reset_deceleration()

        time.sleep(SETTLING_TIME)

        # Get the second dataset with shaping
        print("Performing shaped move with streams.")
        step_response_data_shaped_stream = StepResponseData(
            SCOPE_TIMEBASE, Units.TIME_MILLISECONDS, Units.LENGTH_MICROMETRES
        )

        step_response_data_shaped_stream.capture_data(
            shaped_axis.axis,
            lambda: shaped_axis_stream.move_relative(
                MOVE_DISTANCE, Units.LENGTH_MILLIMETRES, False
            ),
            True,
        )

    plot(
        [
            step_response_data_unshaped,
            step_response_data_shaped,
            step_response_data_shaped_stream,
        ],
        ["Unshaped", "ShapedAxis", f"ShapedAxisStream ({STREAM_SHAPER_TYPE.name})"],
        ["black", "red", "blue"],
    )

    print("Complete.")
