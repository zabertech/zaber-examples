"""
Gantry Calibration Algorithm Demo.

Usage:
    calibrate.py basic
    calibrate.py bilinear [<points>]
    focus_map.py biquadratic [<points>]
    focus_map.py bicubic [<points>]
    focus_map.py poly <order>
    focus_map.py -h | --help

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

Travel = namedtuple("Travel", ["min", "max"])  # Range of travel of x or y axis

TRAVEL_MIN = 0.0
TRAVEL_MAX = 1.0
TRAVEL_RANGE = TRAVEL_MAX - TRAVEL_MIN
ERROR_FRACTION = 0.1


def main() -> None:
    """Dispatch command for various interpolation methods."""
    print("*** Microscope Focus Map Algorithm ***")

    arguments = sys.argv[1:]
    args = docopt(__doc__, argv=arguments)

    if args["<points>"]:
        args["<points>"] = int(args["<points>"])

    if args["basic"]:
        basic_bilinear_interpolation()
    elif args["bilinear"]:
        polynomial_interpolation(1, args["<points>"])
    elif args["biquadratic"]:
        polynomial_interpolation(2, args["<points>"])
    elif args["bicubic"]:
        polynomial_interpolation(3, args["<points>"])
    elif args["poly"]:
        polynomial_interpolation(int(args["<order>"]), args["<points>"])


def basic_bilinear_interpolation() -> None:
    """Interpolate with four corner points."""
    x_travel = Travel(TRAVEL_MIN, TRAVEL_MAX)
    y_travel = Travel(TRAVEL_MIN, TRAVEL_MAX)
    points = generate_points(x_travel, 2, y_travel, 2)
    calibration = Calibration(points)
    plot(points, calibration.map, 3)


def polynomial_interpolation(order: int, num_points: int) -> None:
    """Interpolate with any order of polynomial."""

# todo: Need to figure out how to generate point pairs in a structured fashion so it is plottable.
# todo: Right now as a list of points it doesn't indicate spatial relationship between the points.
# todo: maybe use ndarray?
def generate_points(
    x_travel: Travel, x_count: int, y_travel: Travel, y_count: int
) -> list[PointPair]:
    """
    Generate random points for calibration algorithm.

    :param x_travel: Travel range of points on the x-axis
    :param x_count: Number of points to generate on the x-axis
    :param y_travel: Travel range of points on the y-axis
    :param y_count: Number of points to generate on the y-axis
    """

    def rand() -> float:
        """Generate random numbers within MAX_DEVIATION."""
        rng = np.random.default_rng()
        return rng.uniform(-ERROR_FRACTION * TRAVEL_RANGE, ERROR_FRACTION * TRAVEL_RANGE)

    x_range = np.linspace(x_travel.min, x_travel.max, x_count)
    y_range = np.linspace(y_travel.min, y_travel.max, y_count)

    points: list[PointPair] = []
    for y_position in y_range:
        for x_position in x_range:
            expected = Point(x_position, y_position)
            actual = Point(x_position + rand(), y_position + rand())
            points.append(PointPair(expected, actual))

    return points


def plot(point_pairs: list[PointPair], calibrate: Callable[[Point], Point], subscale: int) -> None:
    """
    Visualize results of calibration.

    :param point_pair: List of expected and actual points that determines the calibration
    :param calibrate: Function that maps a raw (or expected) point to a calibrated (or actual) point
    :param subscale: Subdivisions to use between points when drawing the mapping
    """
    for pair in point_pairs:
        plt.plot(pair.expected.x, pair.expected.y, "bo")
        plt.plot(pair.actual.x, pair.actual.y, "ro")



    plt.xlim(TRAVEL_MIN - 0.2 * TRAVEL_RANGE, TRAVEL_MAX + 0.2 * TRAVEL_RANGE)
    plt.ylim(TRAVEL_MIN - 0.2 * TRAVEL_RANGE, TRAVEL_MAX + 0.2 * TRAVEL_RANGE)
    plt.show()


if __name__ == "__main__":
    main()
