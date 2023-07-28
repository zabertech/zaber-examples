"""
Microscope Focus Map Algorithm.

Usage:
    focus_map.py bilinear [<points>]
    focus_map.py biquadratic [<points>]
    focus_map.py bicubic [<points>]
    focus_map.py poly <order> [<points>]
    focus_map.py -h | --help

Options:
    -h --help           Show help screen.

For more information see README.md
"""

# Code adapted from:
# https://math.stackexchange.com/questions/99299/best-fitting-plane-given-a-set-of-points

import sys
from collections import namedtuple
import matplotlib.pyplot as plt
import numpy as np
from docopt import docopt

# Parameters affecting random point generation
TARGET_X_SLOPE = 2
TARGET_Y_SLOPE = 3
TARGET_OFFSET = 5
EXTENTS = 5
NOISE = 10

Point = namedtuple("Point", ["x", "y", "z"])


def generate_random_points(num_points: int) -> list[Point]:
    """Generate a number of points randomly."""
    points: list[Point] = []
    for _ in range(num_points):
        temp_x = np.random.uniform(2 * EXTENTS) - EXTENTS
        temp_y = np.random.uniform(2 * EXTENTS) - EXTENTS
        temp_z = (
            temp_x * TARGET_X_SLOPE
            + temp_y * TARGET_Y_SLOPE
            + TARGET_OFFSET
            + np.random.normal(scale=NOISE)  # type: ignore
        )
        points.append(Point(temp_x, temp_y, temp_z))
    return points


# pylint: disable=too-many-locals
def polynomial_interpolation(order: int, num_points: int | None = None) -> None:
    """Interpolate generic polynomial of any order."""
    if not num_points:
        num_points = (order + 1) ** 2
    print(f"Order {order} interpolation using {num_points} points")

    # Generate and plot the random points
    points = generate_random_points(num_points)

    plt.figure()
    axes = plt.subplot(111, projection="3d")  # type: ignore
    x_rand = [point.x for point in points]
    y_rand = [point.y for point in points]
    z_rand = [point.z for point in points]
    axes.scatter(x_rand, y_rand, z_rand, color="b")

    # Helper function for generating matrices for calculating best fit
    def make_xy_row(x_i: float, y_i: float) -> list[float]:
        """Make one row of the xy matrix."""
        row: list[float] = []
        for n_x in range(order + 1):
            for n_y in range(order + 1):
                row.append(x_i**n_x * y_i**n_y)
        return row

    # Generate the matrices for calculating best fit
    temp_xy = []
    temp_z = []
    for i in range(num_points):
        temp_xy.append(make_xy_row(points[i].x, points[i].y))
        temp_z.append(points[i].z)
    xy_matrix = np.matrix(temp_xy)
    z_matrix = np.matrix(temp_z).T

    # Calculate best fit, errors and residual
    coeff_matrix = (xy_matrix.T * xy_matrix).I * xy_matrix.T * z_matrix  # pylint: disable=no-member
    errors = z_matrix - xy_matrix * coeff_matrix
    residual = np.linalg.norm(errors)  # type: ignore
    print("errors: \n", errors)
    print("residual:", residual)

    # Generate grid based on best fit coefficients and plot
    def calculate_z(coeff, x_loc: float, y_loc: float) -> float:  # type: ignore
        """Calculate z based on x. y, and coefficient."""
        z_sum = 0.0
        index = 0
        for n_x in range(order + 1):
            for n_y in range(order + 1):
                z_sum += coeff[index] * x_loc**n_x * y_loc**n_y
                index += 1
        return z_sum

    # Plot fitted focus map
    xlim = axes.get_xlim()
    ylim = axes.get_ylim()
    x_grid, y_grid = np.meshgrid(np.arange(xlim[0], xlim[1]), np.arange(ylim[0], ylim[1]))
    z_grid = np.zeros(x_grid.shape)
    for row in range(x_grid.shape[0]):
        for col in range(x_grid.shape[1]):
            z_grid[row, col] = calculate_z(coeff_matrix, x_grid[row, col], y_grid[row, col])
    axes.plot_wireframe(x_grid, y_grid, z_grid, color="k")

    axes.set_xlabel("x")
    axes.set_ylabel("y")
    axes.set_zlabel("z")
    plt.show()


def main() -> None:
    """Dispatch command for various interpolation methods."""
    print("*** Microscope Focus Map Algorithm ***")

    arguments = sys.argv[1:]
    args = docopt(__doc__, argv=arguments)

    if args["<points>"]:
        args["<points>"] = int(args["<points>"])

    if args["bilinear"]:
        polynomial_interpolation(1, args["<points>"])
    elif args["biquadratic"]:
        polynomial_interpolation(2, args["<points>"])
    elif args["bicubic"]:
        polynomial_interpolation(3, args["<points>"])
    elif args["poly"]:
        polynomial_interpolation(int(args["<order>"]), args["<points>"])


if __name__ == "__main__":
    main()
