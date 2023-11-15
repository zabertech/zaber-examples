"""
This script is used for determining a system's vibration frequency and damping ratio.

A move is performed with the stage while capturing target and measured position data. The result is
then plotted.
A theoretical damped vibration curve can be adjusted to overlay any observable vibrations in the
measured position
data. This allows determination of the vibration parameters for use with input shaping algorithms.

Note: this script requires a Zaber product with a direct reading encoder in order to properly
capture position data.
"""

import time
import sys
from typing import Any
from matplotlib import pyplot as plt
from matplotlib.widgets import TextBox
from zaber_motion import Units
from zaber_motion.ascii import Connection
from damped_vibration import DampedVibration
from step_response_data import StepResponseData

# ------------------- Script Settings ----------------------

COM_PORT = "COMx"  # The COM port with the connected Zaber device.
DEVICE_INDEX = 0  # The Zaber device index to test.
AXIS_INDEX = 1  # The Zaber axis index to test.
MOVE_DISTANCE = 1  # The move distance in mm to test.
SCOPE_TIMEBASE = 1  # The scope sampling period in ms.
# It may need to be increased if the whole move isn't captured.

# ------------------- Script Settings ----------------------


def update_vibration_plot(plot_series: Any, damped_vibration: DampedVibration) -> None:
    """
    Redraw the theoretical vibration curve in the plot.

    :param plot_series: The matplotlib Line2D object of the plotted curve
    :param damped_vibration: The class object from which to generate the vibration curve points.
    """
    periods = 10  # plot 10 periods of the vibration
    points_per_period = 50  # plot 50 points per period

    times, magnitudes = damped_vibration.get_plot_points(periods, periods * points_per_period)
    times = [x * 1000.0 for x in times]  # Convert to ms.

    plot_series.set_xdata(times)
    plot_series.set_ydata(magnitudes)
    plt.draw()


def update_vibration_parameter(
    value: str,
    value_name: str,
    plot_series: Any,
    damped_vibration: DampedVibration,
) -> None:
    """
    Update the vibration parameters when a textbox value has changed on the plot.

    :param value: The text in the textbox.
    :param value_name: A string to identify the textbox value.
    :param plot_series: The matplotlib Line2D object of the plotted curve
    :param damped_vibration: The class object from which to generate the vibration curve points.
    """
    float_value = float(value)  # make sure the string value from the textbox is a float

    if value_name == "period":
        damped_vibration.period = float_value / 1000.0  # convert from ms to s
        print(f"Updated period: {damped_vibration.period:.5f}s")

    elif value_name == "DAMPING_RATIO":
        damped_vibration.damping_ratio = float_value
        print(f"Updated damping ratio: {damped_vibration.damping_ratio:.3f}")

    elif value_name == "start_time":
        damped_vibration.start_time = float_value / 1000.0  # convert from ms to s
        print(f"Updated start time: {damped_vibration.start_time:.5f}s")

    elif value_name == "amplitude":
        damped_vibration.amplitude = float_value
        print(f"Updated amplitude: {damped_vibration.amplitude:.3f}um")

    else:
        return  # invalid parameter, don't update the plot

    print(
        f"Vibration Frequency: {damped_vibration.frequency:.3f}Hz, Damping Ratio: "
        f"{damped_vibration.damping_ratio:.3f}"
    )

    update_vibration_plot(plot_series, damped_vibration)


def plot(data: StepResponseData) -> None:
    """
    Plot the step response.

    :param data: The step response data
    """
    fig, axes = plt.subplots()
    plt.subplots_adjust(bottom=0.25)

    plt.title("Device Response")
    plt.xlabel("Time [ms]")
    plt.ylabel("Position [um]")
    plt.grid(True)

    # Plot all the data sets
    axes.plot(
        data.get_time_stamps(),
        data.get_target_positions(True),
        label="Target Position",
        color="black",
        linestyle="--",
    )
    axes.plot(
        data.get_time_stamps(),
        data.get_measured_positions(True),
        label="Measured Position",
        color="black",
    )

    # Leave this empty, we'll update values later
    (theor_plot,) = axes.plot([0], [1], label="Theoretical Vibration", color="red")

    # Create the theoretical vibration curve with arbitrary starting values
    vibration_theoretical = DampedVibration(100.0, 0.1, 50, 0)

    # Refresh the plot so it gets updated with a reasonable guess for the start time
    update_vibration_parameter(
        str(data.get_trajectory_end_time()),
        "start_time",
        theor_plot,
        vibration_theoretical,
    )

    # Create the regions for the input text boxes on the plot and initialize them
    box_height = 0.05
    box_width = 0.2

    axbox1 = fig.add_axes((0.2, 0.01, box_width, box_height))  # Left, Bottom, Width, Height
    axbox2 = fig.add_axes(
        (0.2, 0.02 + box_height, box_width, box_height)
    )  # Left, Bottom, Width, Height
    axbox3 = fig.add_axes((0.7, 0.01, box_width, box_height))  # Left, Bottom, Width, Height
    axbox4 = fig.add_axes(
        (0.7, 0.02 + box_height, box_width, box_height)
    )  # Left, Bottom, Width, Height

    text_box_start = TextBox(
        axbox1,
        "Start Time [ms]",
        textalignment="center",
        initial=str(vibration_theoretical.start_time * 1000.0),
    )
    text_box_amplitude = TextBox(
        axbox2,
        "Amplitude [um]",
        textalignment="center",
        initial=str(vibration_theoretical.amplitude),
    )
    text_box_period = TextBox(
        axbox3,
        "Period [ms]",
        textalignment="center",
        initial=str(vibration_theoretical.period * 1000.0),
    )
    text_box_damping_ratio = TextBox(
        axbox4,
        "Damping Ratio [-]",
        textalignment="center",
        initial=str(vibration_theoretical.damping_ratio),
    )

    # Setup the textbox callbacks for when the values get updated so the curve gets redrawn.
    text_box_start.on_submit(
        lambda v: update_vibration_parameter(v, "start_time", theor_plot, vibration_theoretical)
    )
    text_box_amplitude.on_submit(
        lambda v: update_vibration_parameter(v, "amplitude", theor_plot, vibration_theoretical)
    )
    text_box_period.on_submit(
        lambda v: update_vibration_parameter(v, "period", theor_plot, vibration_theoretical)
    )
    text_box_damping_ratio.on_submit(
        lambda v: update_vibration_parameter(v, "DAMPING_RATIO", theor_plot, vibration_theoretical)
    )

    print("Displaying plot...")
    axes.legend(loc="lower right")
    plt.show()


if __name__ == "__main__":
    # Open the connection and get the device + axis
    with Connection.open_serial_port(COM_PORT) as connection:
        device_list = connection.detect_devices()
        print(f"Found {len(device_list)} devices.")

        if len(device_list) < DEVICE_INDEX + 1:
            print(f"Not enough devices for specified device index ({DEVICE_INDEX}), exiting.")
            sys.exit(0)

        # Get the device and axis
        device = device_list[DEVICE_INDEX]

        if device.axis_count < AXIS_INDEX:
            print(f"Not enough axes for specified axis index ({AXIS_INDEX}), exiting.")
            sys.exit(0)

        axis = device.get_axis(AXIS_INDEX)

        # Home the axis and move to zero position
        if not axis.is_homed():
            axis.home()

        axis.move_absolute(0, Units.LENGTH_MILLIMETRES, True)
        time.sleep(0.2)

        # Capture the data
        print("Performing move.")

        step_response_data = StepResponseData(
            SCOPE_TIMEBASE, Units.TIME_MILLISECONDS, Units.LENGTH_MICROMETRES
        )
        step_response_data.capture_data(
            axis, lambda: axis.move_relative(MOVE_DISTANCE, Units.LENGTH_MILLIMETRES, False), True
        )

        print("Capture Complete.")

    # Show the plot
    plot(step_response_data)
    print("Complete.")
