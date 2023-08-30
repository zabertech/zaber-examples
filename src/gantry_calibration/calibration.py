"""The core math and functionality behind the calibration algorithm."""

import sys
from collections import namedtuple
import numpy as np


Point = namedtuple("Point", ["x", "y"])
PointPair = namedtuple("PointPair", ["expected", "actual"])


class Calibration:
    """Contains the calibration matrix and coefficients."""

    # pylint: disable=too-few-public-methods

    def __init__(self, x_order: int, y_order: int, points: list[list[PointPair]]) -> None:
        """Instantiate the object with expected and actual points."""
        self.x_order = x_order
        self.y_order = y_order
        self.points = points
        point_array = np.array(points)
        self.x_count = point_array.shape[0]
        self.y_count = point_array.shape[1]
        if self.x_order >= self.x_count:
            print(f"Error: x-axis order ({self.x_order}) must be less than count ({self.x_count})")
            sys.exit()
        if self.y_order >= self.y_count:
            print(f"Error: y-axis order ({self.y_order}) must be less than count ({self.y_count})")
            sys.exit()
        self._fit_coefficients()

    def map(self, point: Point) -> Point:
        """Map from expected coordinates to actual (calibrated) coordinates."""
        x_calibrated = 0.0
        y_calibrated = 0.0
        index = 0
        for n_x in range(self.x_order + 1):
            for n_y in range(self.y_order + 1):
                x_calibrated += self.x_coeff[index].item() * point.x**n_x * point.y**n_y
                y_calibrated += self.y_coeff[index].item() * point.x**n_x * point.y**n_y
                index += 1
        return Point(float(x_calibrated), float(y_calibrated))

    def _fit_coefficients(self) -> None:
        """Fit the actual points to calculate the coefficients for equations for x and y."""
        temp_xy_matrix = []
        temp_x_actual = []
        temp_y_actual = []
        for n_x in range(self.x_count):
            for n_y in range(self.y_count):
                point_pair = self.points[n_x][n_y]
                temp_xy_matrix.append(
                    self._make_xy_row(point_pair.expected.x, point_pair.expected.y)
                )
                temp_x_actual.append(point_pair.actual.x)
                temp_y_actual.append(point_pair.actual.y)
        xy_matrix = np.matrix(temp_xy_matrix)
        x_actual = np.matrix(temp_x_actual).T
        y_actual = np.matrix(temp_y_actual).T

        self.x_coeff = np.linalg.inv(xy_matrix.T * xy_matrix) * xy_matrix.T * x_actual
        self.y_coeff = np.linalg.inv(xy_matrix.T * xy_matrix) * xy_matrix.T * y_actual

    def _make_xy_row(self, x_i: float, y_i: float) -> list[float]:
        """Make one row of the xy matrix."""
        row: list[float] = []
        for n_x in range(self.x_order + 1):
            for n_y in range(self.y_order + 1):
                row.append(x_i**n_x * y_i**n_y)
        return row
