"""
Gantry Calibration Algorithm Demo.

Usage:
    calibrate.py basic
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

    if args["basic"]:
        basic_calibration()
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


def basic_calibration() -> None:
    """Demonstrate basic bilinear calibration with annotation."""
    x_travel = Travel(TRAVEL_MIN, TRAVEL_MAX)
    y_travel = Travel(TRAVEL_MIN, TRAVEL_MAX)
    points = generate_points(x_travel, y_travel, 2, 2)
    calibration = Calibration(1, 1, points)
    plot(points, calibration.map, 5, annotation=True)


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


def plot(
    points: list[list[PointPair]],
    calibrate: Callable[[Point], Point],
    subscale: int,
    annotation: bool = False,
) -> None:
    """
    Visualize results of calibration.

    :param points: 2D array of expected and actual points that determines the calibration
    :param calibrate: Function that maps a raw (or expected) point to a calibrated (or actual) point
    :param subscale: Subdivisions to use between points when drawing the mapping to show curves
    :param annotation: Optional annotation for generating graphics for documentation.
    """
    # pylint: disable=too-many-locals
    point_array = np.array(points)
    x_count = point_array.shape[0]
    y_count = point_array.shape[1]

    def annotate_point(point_pair: PointPair, subscript: int) -> None:
        """Optionally annotate points."""
        plt.annotate(
            f"(x{subscript}, y{subscript})",
            (point_pair.expected.x, point_pair.expected.y),
            xytext=(10, 10),
            textcoords="offset pixels",
            color="b",
        )
        plt.annotate(
            f"(x{subscript}', y{subscript}')",
            (point_pair.actual.x, point_pair.actual.y),
            xytext=(10, 10),
            textcoords="offset pixels",
            color="r",
        )

    # Plot points
    sub = 0
    for x_index in range(x_count):
        for y_index in range(y_count):
            pair = points[x_index][y_index]
            plt.plot(pair.expected.x, pair.expected.y, "bo")
            plt.plot(pair.actual.x, pair.actual.y, "ro")
            if annotation:
                annotate_point(pair, sub)
            sub += 1

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

    def set_plot_limits() -> None:
        """Set x and y limits for the plot."""
        travel_x = [point_pair.expected.x for row in points for point_pair in row]
        travel_y = [point_pair.expected.y for row in points for point_pair in row]
        travel_min_x = min(travel_x)
        travel_max_x = max(travel_x)
        travel_min_y = min(travel_y)
        travel_max_y = max(travel_y)
        margin_factor = 0.2
        margin_x = (travel_max_x - travel_min_x) * margin_factor
        margin_y = (travel_max_y - travel_min_y) * margin_factor
        plt.xlim(travel_min_x - margin_x, travel_max_x + margin_x)
        plt.ylim(travel_min_y - margin_y, travel_max_y + margin_y)

    set_plot_limits()
    plt.show()


if __name__ == "__main__":
    main()
