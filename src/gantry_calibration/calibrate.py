"""
Gantry Calibration Algorithm Demo.

Usage:
    calibrate.py bilinear [<points>]
    calibrate.py biquadratic [<points>]
    calibrate.py bicubic [<points>]
    calibrate.py poly <x_order> <y_order> <x_points> <y_points>
    calibrate.py -h | --help

Options:
    -h --help           Show help screen.

For more information see README.md
"""

import sys
from typing import Callable
from collections import namedtuple
import numpy as np
import matplotlib.pyplot as plt  # type: ignore
from docopt import docopt
from calibration import Point, PointPair, Calibration

Travel = namedtuple("Travel", ["min", "max"])  # Range of travel of each axis

TRAVEL_MIN = 0.0
TRAVEL_MAX = 1.0
TRAVEL_RANGE = TRAVEL_MAX - TRAVEL_MIN
ERROR_FRACTION = 0.05


def main() -> None:
    """Dispatch command for various interpolation methods."""
    print("*** Gantry Calibration Algorithm ***")

    arguments = sys.argv[1:]
    args = docopt(__doc__, argv=arguments)

    if args["bilinear"]:
        if args["<points>"]:
            points = int(args["<points>"])
        else:
            points = 2
        polynomial_interpolation(1, 1, points, points)
    elif args["biquadratic"]:
        if args["<points>"]:
            points = int(args["<points>"])
        else:
            points = 3
        polynomial_interpolation(2, 2, points, points)
    elif args["bicubic"]:
        if args["<points>"]:
            points = int(args["<points>"])
        else:
            points = 4
        polynomial_interpolation(3, 3, points, points)
    elif args["poly"]:
        polynomial_interpolation(
            int(args["<x_order>"]),
            int(args["<y_order>"]),
            int(args["<x_points>"]),
            int(args["<y_points>"]),
        )


def polynomial_interpolation(x_order: int, y_order: int, x_points: int, y_points: int) -> None:
    """
    Interpolate with any order of polynomial.

    :param x_order: The order of polynomial to fit the x-axis
    :param y_order: The order of polynomial to fit the y-axis
    :param x_points: The number of points along the x-axis used for fitting
    :param y_points: The number of points along the y-axis used for fitting

    """
    print(f"Order {x_order} x {y_order} interpolation using {x_points} x {y_points} points")
    x_travel = Travel(TRAVEL_MIN, TRAVEL_MAX)
    y_travel = Travel(TRAVEL_MIN, TRAVEL_MAX)
    points = generate_points(x_travel, y_travel, x_points, y_points)
    calibration = Calibration(x_order, y_order, points)
    plot(points, calibration.map, 5)


def generate_points(
    x_travel: Travel, y_travel: Travel, x_count: int, y_count: int
) -> list[list[PointPair]]:
    """
    Generate random points for calibration algorithm.

    :param x_travel: Travel range of points on the x-axis
    :param y_travel: Travel range of points on the y-axis
    :param x_count: Number of points to generate on the x-axis
    :param y_count: Number of points to generate on the y-axis
    """

    def rand() -> float:
        """Generate random numbers within range defined by ERROR_FRACTION of TRAVEL_RANGE."""
        rng = np.random.default_rng()
        return rng.uniform(-ERROR_FRACTION * TRAVEL_RANGE, ERROR_FRACTION * TRAVEL_RANGE)

    x_range = np.linspace(x_travel.min, x_travel.max, x_count)
    y_range = np.linspace(y_travel.min, y_travel.max, y_count)

    temp_array = []
    for x_position in x_range:
        row = []
        for y_position in y_range:
            expected = Point(x_position, y_position)
            actual = Point(x_position + rand(), y_position + rand())
            row.append(PointPair(expected, actual))
        temp_array.append(row)

    return temp_array


def plot(points: list[list[PointPair]], calibrate: Callable[[Point], Point], subscale: int) -> None:
    """
    Visualize results of calibration.

    :param points: 2D array of expected and actual points that determines the calibration
    :param calibrate: Function that maps a raw (or expected) point to a calibrated (or actual) point
    :param subscale: Subdivisions to use between points when drawing the mapping to show curves
    """
    # pylint: disable=too-many-locals
    point_array = np.array(points)
    x_count = point_array.shape[0]
    y_count = point_array.shape[1]

    # Plot points
    for x_index in range(x_count):
        for y_index in range(y_count):
            pair = points[x_index][y_index]
            plt.plot(pair.expected.x, pair.expected.y, "bo")
            plt.plot(pair.actual.x, pair.actual.y, "ro")

    def plot_segment(point0: Point, point1: Point, style: str) -> None:
        """Plot a line segment between two points."""
        plt.plot([point0.x, point1.x], [point0.y, point1.y], style)

    # Plot major lines joining points
    for x_index in range(0, x_count - 1):
        for y_index in range(0, y_count):
            pair0 = points[x_index][y_index]
            pair1 = points[x_index + 1][y_index]
            plot_segment(pair0.expected, pair1.expected, "b-")

            x_seg_range = np.linspace(pair0.expected.x, pair1.expected.x, subscale + 1)
            y_seg_range = np.linspace(pair0.expected.y, pair1.expected.y, subscale + 1)
            for seg_index in range(0, subscale):
                raw0 = Point(x_seg_range[seg_index], y_seg_range[seg_index])
                raw1 = Point(x_seg_range[seg_index + 1], y_seg_range[seg_index])
                cal0 = calibrate(raw0)
                cal1 = calibrate(raw1)
                plot_segment(cal0, cal1, "r--")

    for x_index in range(0, x_count):
        for y_index in range(0, y_count - 1):
            pair0 = points[x_index][y_index]
            pair1 = points[x_index][y_index + 1]
            plot_segment(pair0.expected, pair1.expected, "b-")

            x_seg_range = np.linspace(pair0.expected.x, pair1.expected.x, subscale + 1)
            y_seg_range = np.linspace(pair0.expected.y, pair1.expected.y, subscale + 1)
            for seg_index in range(0, subscale):
                raw0 = Point(x_seg_range[seg_index], y_seg_range[seg_index])
                raw1 = Point(x_seg_range[seg_index], y_seg_range[seg_index + 1])
                cal0 = calibrate(raw0)
                cal1 = calibrate(raw1)
                plot_segment(cal0, cal1, "r--")

    plt.xlim(TRAVEL_MIN - 0.2 * TRAVEL_RANGE, TRAVEL_MAX + 0.2 * TRAVEL_RANGE)
    plt.ylim(TRAVEL_MIN - 0.2 * TRAVEL_RANGE, TRAVEL_MAX + 0.2 * TRAVEL_RANGE)
    plt.show()


if __name__ == "__main__":
    main()
