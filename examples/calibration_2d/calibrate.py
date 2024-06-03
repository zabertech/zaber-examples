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
from typing import Callable, NamedTuple
import numpy as np
import matplotlib.pyplot as plt
from docopt import docopt
from calibration import Point, PointPair, Calibration

# Constants for generating random data points for demo purposes.
TRAVEL_MIN = 0.0  # Minimum limit for travel range
TRAVEL_MAX = 1.0  # Maximum limit for travel range
ERROR_FRACTION = 0.05  # Fraction of travel range as random error or deviation.


class Travel(NamedTuple):
    """Range of travel of each axis."""

    min: float
    max: float


def main() -> None:
    """Dispatch command for various interpolation methods."""
    print("*** Gantry Calibration Algorithm ***")

    arguments = sys.argv[1:]
    args = docopt(__doc__, argv=arguments)

    if args["basic"]:
        polynomial_interpolation(1, 1, 2, 2, annotation=True)
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


def polynomial_interpolation(
    x_order: int, y_order: int, x_points: int, y_points: int, annotation: bool = False
) -> None:
    """
    Interpolate with any order of polynomial.

    :param x_order: The order of polynomial to fit the x-axis
    :param y_order: The order of polynomial to fit the y-axis
    :param x_points: The number of points along the x-axis used for fitting
    :param y_points: The number of points along the y-axis used for fitting
    :param annotation: Display annotation of points
    """
    print(f"Order {x_order} x {y_order} interpolation using {x_points} x {y_points} points")
    x_travel = Travel(TRAVEL_MIN, TRAVEL_MAX)
    y_travel = Travel(TRAVEL_MIN, TRAVEL_MAX)
    points = generate_points(x_travel, y_travel, x_points, y_points, ERROR_FRACTION)
    calibration = Calibration(x_order, y_order, points)
    plot(points, calibration.map, 5, annotation)


def generate_points(
    x_travel: Travel, y_travel: Travel, x_count: int, y_count: int, error_fraction: float
) -> list[list[PointPair]]:
    """
    Generate random points for calibration algorithm.

    :param x_travel: Travel range of points on the x-axis
    :param y_travel: Travel range of points on the y-axis
    :param x_count: Number of points to generate on the x-axis
    :param y_count: Number of points to generate on the y-axis
    :param error_fraction: Fraction of travel range as random error or deviation.
    """

    def rand(travel: Travel) -> float:
        """Generate random numbers within range defined by error fraction of travel range."""
        rng = np.random.default_rng()
        travel_range = travel.max - travel.min
        error_range = error_fraction * travel_range
        return rng.uniform(-error_range, error_range)

    x_range = np.linspace(x_travel.min, x_travel.max, x_count)
    y_range = np.linspace(y_travel.min, y_travel.max, y_count)

    temp_array = []
    for x_position in x_range:
        row = []
        for y_position in y_range:
            expected = Point(x_position, y_position)
            actual = Point(x_position + rand(x_travel), y_position + rand(y_travel))
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
    fig = plt.figure()
    axes = fig.add_subplot(1, 1, 1)

    def annotate_point(point_pair: PointPair, subscript: int) -> None:
        """Optionally annotate points."""
        axes.annotate(
            f"(x{subscript}, y{subscript})",
            (point_pair.expected.x, point_pair.expected.y),
            xytext=(10, 10),
            textcoords="offset pixels",
            color="b",
        )
        axes.annotate(
            f"(x{subscript}', y{subscript}')",
            (point_pair.actual.x, point_pair.actual.y),
            xytext=(10, 10),
            textcoords="offset pixels",
            color="r",
        )

    def plot_line(point0: Point, point1: Point, style: str) -> None:
        """Plot a line segment between two points."""
        axes.plot([point0.x, point1.x], [point0.y, point1.y], style)

    def plot_calibrated(point0: Point, point1: Point, segments: int, style: str) -> None:
        """Plot a calibrated line or curve between two points with specified number of segments."""
        x_seg_range = np.linspace(point0.x, point1.x, segments + 1)
        y_seg_range = np.linspace(point0.y, point1.y, segments + 1)
        for seg_index in range(0, segments):
            raw0 = Point(x_seg_range[seg_index], y_seg_range[seg_index])
            raw1 = Point(x_seg_range[seg_index + 1], y_seg_range[seg_index + 1])
            cal0 = calibrate(raw0)
            cal1 = calibrate(raw1)
            plot_line(cal0, cal1, style)

    def plot_points_and_lines() -> None:
        point_array = np.array(points)
        x_count = point_array.shape[0]
        y_count = point_array.shape[1]

        # Plot points
        sub = 0
        for x_index in range(x_count):
            for y_index in range(y_count):
                pair = points[x_index][y_index]
                axes.plot(pair.expected.x, pair.expected.y, "bo")
                axes.plot(pair.actual.x, pair.actual.y, "ro")
                if annotation:
                    annotate_point(pair, sub)
                sub += 1

        # Plot horizontal lines
        for x_index in range(0, x_count - 1):
            for y_index in range(0, y_count):
                pair0 = points[x_index][y_index]
                pair1 = points[x_index + 1][y_index]
                plot_line(pair0.expected, pair1.expected, "b-")
                plot_calibrated(pair0.expected, pair1.expected, subscale, "r--")
        # Plot vertical lines
        for x_index in range(0, x_count):
            for y_index in range(0, y_count - 1):
                pair0 = points[x_index][y_index]
                pair1 = points[x_index][y_index + 1]
                plot_line(pair0.expected, pair1.expected, "b-")
                plot_calibrated(pair0.expected, pair1.expected, subscale, "r--")

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
        axes.set_xlim(travel_min_x - margin_x, travel_max_x + margin_x)
        axes.set_ylim(travel_min_y - margin_y, travel_max_y + margin_y)

    set_plot_limits()
    plot_points_and_lines()
    plt.show()


if __name__ == "__main__":
    main()
