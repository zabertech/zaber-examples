"""
Gantry Calibration Demo with Device Interaction.

Usage:
    interactive.py <port>
    interactive.py -h | --help

Options:
    -h --help           Show help screen.

For more information see README.md
"""

import sys
import numpy as np
from docopt import docopt

from calibration import Point, PointPair, Calibration
from calibrate import plot

from zaber_motion import Units
from zaber_motion.ascii import Axis, AxisType, Connection


def main() -> None:
    """Collect data points and then interactively move to calibrated locations."""
    print("*** Interactive Gantry Calibration ***")

    arguments = sys.argv[1:]
    args = docopt(__doc__, argv=arguments)

    with Connection.open_serial_port(args["<port>"]) as connection:
        # Collect input data
        x_axis, y_axis = select_axes(connection)
        raw_points = collect_points(x_axis, y_axis)

        # Reshape the points into a 2D array for the example Calibration class
        order = int(np.sqrt(len(raw_points))) - 1
        points = []
        for y in range(0, order + 1):
            row = raw_points[y * (order + 1):(y + 1) * (order + 1)]
            points.append(row)

        # Perform the calibration
        calibration = Calibration(order, order, points)
        print("Close the plot window to continue.")
        plot(points, calibration.map, 5, len(raw_points) == 4)

        # Use the calibration to correct device positions
        do_moves(x_axis, y_axis, calibration)


def select_axes(connection: Connection) -> tuple:
    """Select the axes to calibrate."""
    devices = connection.detect_devices()
    print("Detected linear motion axes:")
    axes = []
    for device in devices:
        for i in range(1, device.axis_count):
            axis = device.get_axis(i)
            if (axis.axis_type == AxisType.LINEAR):
                axes.append(axis)
                print(f"{len(axes)}: {device.name} axis {i} ({axis.identity.peripheral_name})")

    if (len(axes)) < 2:
        print("At least two linear axes are required for this demo.")
        sys.exit(1)

    print()
    x = None
    while x is None:
        print("Select the X axis:")
        x = int(input()) - 1
        if x is None or x < 0 or x >= len(axes):
            print("Invalid selection. Please try again.")
            x = None

    print()
    y = None
    while y is None:
        print("Select the Y axis:")
        y = int(input()) - 1
        if y is None or y < 0 or y >= len(axes) or y == x:
            print("Invalid selection. Please try again.")
            y = None

    return axes[x], axes[y]


def collect_points(x_axis: Axis, y_axis: Axis) -> list[PointPair]:
    """Collect points for calibration."""
    points = []
    print()
    print("--- Collecting data points for calibration ---")
    print()
    print("Move the axes using the knobs, or if you started Zaber Launcher before running this")
    print("script, you can use the Basic Controls or Terminal apps to move the axes.")
    print()
    print("You must enter 4, 9, 16 or 25 points in a square grid pattern; the quantity controls the type of interpolation used.")
    print()
    while True:
        input(f"Move the axes to point {len(points) + 1} and press Enter.")
        x_position = x_axis.get_position(Units.LENGTH_MILLIMETRES)
        y_position = y_axis.get_position(Units.LENGTH_MILLIMETRES)
        actual = Point(x_position, y_position)
        for point in points:
            if distance(point.actual, actual) < 0.01:
                print("Point is too close to an existing point. Please move to a new position.")
                continue

        print(f"Current device position reads as X: {x_position:.3f}mm, Y: {y_position:.3f}mm")
        print("Enter the expected positions in mm as two numbers separated by a space or comma,")
        line = input("or just press enter to end input: ")
        print()
        try:
            if line == "":
                if len(points) < 4:
                    print("You must enter at least 4 points to calibrate.")
                    continue

                if np.sqrt(len(points)) % 1 != 0:
                    print("You must enter 4, 9, 16 or 25 points in a square grid pattern.")
                    continue

                if len(points) > 25:
                    points = points[:25]

                break

            x_expected, y_expected = map(float, line.replace(',', ' ').split())

        except ValueError:
            print("Invalid input. Please try again.")
            continue

        expected = Point(x_expected, y_expected)
        points.append(PointPair(expected, actual))

    return points


def do_moves(x_axis: Axis, y_axis: Axis, calibration: Calibration) -> None:
    """Move to user-entered points."""
    print()
    print("Enter desired coordinates to move to, as two numbers separated by spaces or commas,")
    print("or press Enter to end the program.")
    print()
    while True:
        line = input()
        try:
            if line == "":
                break

            x_requested, y_requested = map(float, line.replace(',', ' ').split())

        except ValueError:
            print("Invalid input. Please try again.")
            continue

        target = calibration.map(Point(x_requested, y_requested))
        print(f"Requested position of X: {x_requested:.3f}mm, Y: {y_requested:.3f}mm maps to calibrated position of X: {target.x:.3f}mm, Y: {target.y:.3f}mm")
        x_axis.move_absolute(target.x, Units.LENGTH_MILLIMETRES, wait_until_idle=False)
        y_axis.move_absolute(target.y, Units.LENGTH_MILLIMETRES, wait_until_idle=False)
        x_axis.wait_until_idle()
        y_axis.wait_until_idle()
        print("Move complete. Enter more coordinates or press Enter to end the program.")
        print()


def distance(a: Point, b: Point) -> float:
    """Calculate the distance between two points."""
    return np.sqrt((a.x - b.x)**2 + (a.y - b.y)**2)


if __name__ == "__main__":
    main()
