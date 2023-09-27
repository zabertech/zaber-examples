"""The core math and functionality behind the calibration algorithm."""

from typing import NamedTuple
import numpy as np


class Point(NamedTuple):
    """Define a point."""

    x: float
    y: float


class PointPair(NamedTuple):
    """The expected and actual coordinates of a point."""

    expected: Point
    actual: Point


class Calibration:
    """Contains the calibration matrix and coefficients."""

    def __init__(self, x_order: int, y_order: int, points: list[list[PointPair]]) -> None:
        """Instantiate the object with expected and actual points."""
        # Set the internal values of these properties before fitting coefficients.
        self._x_order = x_order
        self._y_order = y_order
        self._points = points

        # Default values, to be overwritten by _fit_coefficients() function.
        self._x_coeff = np.zeros((self.x_order + 1) * (self.y_order + 1))
        self._y_coeff = np.zeros((self.x_order + 1) * (self.y_order + 1))

        # Validate the polynomial orders and fit the coefficients
        self._fit_coefficients()

    @property
    def x_count(self) -> int:
        """Get the number of points for the x-axis."""
        return np.array(self.points).shape[0]

    @property
    def y_count(self) -> int:
        """Get the number of points for the y-axis."""
        return np.array(self.points).shape[1]

    @property
    def x_order(self) -> int:
        """Get the x-axis fit polynomial order."""
        return self._x_order

    @x_order.setter
    def x_order(self, value: int) -> None:
        """Set x-axis fit polynomial order and re-calculate the fit."""
        self._x_order = value
        self._fit_coefficients()

    @property
    def y_order(self) -> int:
        """Get the y-axis fit polynomial order."""
        return self._y_order

    @y_order.setter
    def y_order(self, value: int) -> None:
        """Set y-axis fit polynomial order and re-calculate the fit."""
        self._y_order = value
        self._fit_coefficients()

    @property
    def points(self) -> list[list[PointPair]]:
        """Get the data points."""
        return self._points

    @points.setter
    def points(self, value: list[list[PointPair]]) -> None:
        """Set the data points and re-calculate the fit."""
        self._points = value
        self._fit_coefficients()

    def map(self, point: Point) -> Point:
        """Map from expected coordinates to actual (calibrated) coordinates."""
        x_calibrated = 0.0
        y_calibrated = 0.0
        index = 0
        for n_x in range(self.x_order + 1):
            for n_y in range(self.y_order + 1):
                x_calibrated += self._x_coeff[index].item() * point.x**n_x * point.y**n_y
                y_calibrated += self._y_coeff[index].item() * point.x**n_x * point.y**n_y
                index += 1
        return Point(x_calibrated, y_calibrated)

    def _fit_coefficients(self) -> None:
        """Fit the actual points to calculate the coefficients for equations for x and y."""
        self._check_orders()

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

        self._x_coeff = np.linalg.inv(xy_matrix.T * xy_matrix) * xy_matrix.T * x_actual
        self._y_coeff = np.linalg.inv(xy_matrix.T * xy_matrix) * xy_matrix.T * y_actual

    def _make_xy_row(self, x_i: float, y_i: float) -> list[float]:
        """Make one row of the xy matrix."""
        row: list[float] = []
        for n_x in range(self.x_order + 1):
            for n_y in range(self.y_order + 1):
                row.append(x_i**n_x * y_i**n_y)
        return row

    def _check_orders(self) -> None:
        """Check the polynomial orders to make sure we have enough points for the computation."""
        if self.x_order >= self.x_count:
            raise ValueError(
                f"X-axis polynomial order ({self.x_order}) "
                f"must be less than the number of points ({self.x_count})."
            )

        if self.y_order >= self.y_count:
            raise ValueError(
                f"Y-axis polynomial order ({self.y_order}) "
                f"must be less than the number of points ({self.y_count})."
            )
