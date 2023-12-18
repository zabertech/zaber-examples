"""
Helper classes and functions related to PVT.

This file contains sever helper classes for creating and
manipulating PVT points, segments, and sequences.
"""

# pylint: disable=too-many-lines

from __future__ import annotations
import csv
from dataclasses import dataclass
from enum import Enum, auto
from functools import partial
from itertools import accumulate
import math

import numpy as np
from numpy import float64
from numpy.typing import NDArray
from scipy.integrate import quad  # type: ignore
from scipy.interpolate import splev, splprep  # type: ignore
from scipy.linalg import solve_banded  # type: ignore
from scipy.optimize import bisect, newton  # type: ignore


@dataclass(frozen=True)
class Point:
    """A position-velocity-time point."""

    position: tuple[float, ...]
    """A vector representing the absolute position of the point."""
    velocity: tuple[float, ...]
    """A vector representing the velocity of the point."""
    time: float
    """The absolute time of the point."""

    @property
    def dim(self) -> int:
        """The dimension of the point."""
        return len(self.position)

    def __post_init__(self) -> None:
        """Complete initialization of the point."""
        assert self.dim == len(self.velocity), "Position must have the same dimension as velocity."


class Segment:
    """A PVT segment, formed from two PVT points."""

    def __init__(self, start_point: Point, end_point: Point) -> None:
        """
        Initialize the PVT segment.

        :param start_point: The start point of the sequence.
        :param end_point: The end point of the sequence.
        """
        assert start_point.dim == end_point.dim, "Points must have the same number of dimensions."
        self._start_point = start_point
        self._end_point = end_point
        self._calculate_coefficients()

    @property
    def start_point(self) -> Point:
        """The start point of the segment."""
        return self._start_point

    @property
    def end_point(self) -> Point:
        """The end point of the segment."""
        return self._end_point

    @property
    def dim(self) -> int:
        """The dimension of the points."""
        return self.start_point.dim

    def position(self, time: float) -> tuple[float, ...]:
        """
        Calculate the position at a given time.

        :param time: The time at which to calculate the position.
        """
        self._validate_time(time)
        delta_time = time - self.start_point.time
        return tuple(
            c[0] + c[1] * delta_time + c[2] * delta_time**2 + c[3] * delta_time**3
            for c in self._coefficients
        )

    def velocity(self, time: float) -> tuple[float, ...]:
        """
        Calculate the velocity at a given time.

        :param time: The time at which to calculate the velocity.
        """
        self._validate_time(time)
        delta_time = time - self.start_point.time
        return tuple(
            c[1] + 2 * c[2] * delta_time + 3 * c[3] * delta_time**2 for c in self._coefficients
        )

    def acceleration(self, time: float) -> tuple[float, ...]:
        """
        Calculate the acceleration at a given time.

        :param time: The time at which to calculate the acceleration.
        """
        self._validate_time(time)
        delta_time = time - self.start_point.time
        return tuple(2 * c[2] + 6 * c[3] * delta_time for c in self._coefficients)

    def _calculate_coefficients(self) -> None:
        """Calculate the polynomial coefficients."""

        def calculate_coefficients_1d(
            delta_time: float, pos_start: float, pos_end: float, vel_start: float, vel_end: float
        ) -> tuple[float, float, float, float]:
            """Calculate the coefficients in a single dimension."""
            delta_pos = pos_end - pos_start
            c0 = pos_start
            c1 = vel_start
            if delta_time > 0:
                c2 = 3 * delta_pos / delta_time**2 - (2 * vel_start + vel_end) / delta_time
                c3 = -2 * delta_pos / delta_time**3 + (vel_start + vel_end) / delta_time**2
            else:
                c2 = c3 = 0
            return (c0, c1, c2, c3)

        delta_time = self.end_point.time - self.start_point.time
        assert delta_time >= 0, "The time at point 2 must be greater than the time at point 1"
        self._coefficients = [
            calculate_coefficients_1d(
                delta_time,
                self.start_point.position[i],
                self.end_point.position[i],
                self.start_point.velocity[i],
                self.end_point.velocity[i],
            )
            for i in range(self.dim)
        ]

    def _validate_time(self, time: float) -> None:
        """
        Validate that a given time falls within the bounds defined by the segment.

        :param time: The time to validate.
        """
        time_min = self.start_point.time
        time_max = self.end_point.time
        assert (
            time_min <= time <= time_max + 1e-14
        ), f"Time {time} is outside of segment range ({time_min}, {time_max})"


class GeometricPath:
    """An N-directional geometric path constructed from a sequence of position keypoints."""

    def __init__(self, position_sequences: list[list[float]]):
        """
        Initialize an N-dimensional geometric path from a list of position sequences.

        The path is generated as a B-Spline, and is parametrized by
        a normalized length variable u. That is, the path starts at
        u=0 and ends at u=1.

        :param position_sequences: A list of position sequences, one
        for each dimension.
        """
        self._dim = len(position_sequences)
        tck, u = splprep(  # pylint: disable=unbalanced-tuple-unpacking
            position_sequences, s=0, full_output=0
        )
        self._tck: tuple[NDArray[float64], list[NDArray[float64]], int] = tck
        self._u: list[float] = list(u)
        self._length_at_u = list(
            accumulate(
                (
                    self._calculate_segment_length(u0, uf)
                    for u0, uf in zip(self._u[:-1], self._u[1:])
                ),
                initial=0,
            )
        )

    @property
    def length(self) -> float:
        """The length of the path."""
        return self._length_at_u[-1]

    @property
    def parameterized_lengths(self) -> list[float]:
        """
        The sequence of parameterized lengths.

        These lengths correspond to the position keypoints
        used to construct the path.
        """
        return self._u.copy()

    def position(self, u: float) -> tuple[float, ...]:
        """
        Return the N-D path position at parameterized length u.

        :param u: The parameterized length u.
        """
        # By default, splev returns an array for each element. Pick
        # the one and only value by flattening the arrays.
        val = splev(u, self._tck)
        return tuple(val[i].flat[0] for i in range(self._dim))

    def direction(self, u: float) -> tuple[float, ...]:
        """
        Return the N-D path direction, as a unit vector, at parameterized distance u.

        :param u: The parameterized length u.
        """
        dx_du = self.dx_du(u)
        norm = sum(val**2 for val in dx_du) ** 0.5
        if norm == 0:
            assert all(dx_du_i == 0 for dx_du_i in dx_du)
            return tuple(0 for _ in dx_du)
        return tuple(val / norm for val in dx_du)

    def velocity(self, u: float, speed: float) -> tuple[float, ...]:
        """
        Return the velocity at the given parameterized length.

        :param u: The parameterized length u.
        :param speed: The tangential speed along the path.
        """
        dl_du = self.dl_du(u)
        return tuple(speed * dx_du / dl_du for dx_du in self.dx_du(u))

    def acceleration(self, u: float, speed: float, accel: float) -> tuple[float, ...]:
        """
        Return the acceleration at the given parameterized length.

        :param u: The parameterized length u.
        :param speed: The tangential speed along the path.
        :param accel: The tangential acceleration along the path.
        """
        dx_dl = self.dx_dl(u)
        d2x_dl2 = self.d2x_dl2(u)
        return tuple(
            speed**2 * d2x_dl2_i + accel * dx_dl_i for dx_dl_i, d2x_dl2_i in zip(dx_dl, d2x_dl2)
        )

    def _calculate_segment_length(self, u0: float, uf: float) -> float:
        """
        Calculate the path length between u0 and uf.

        :param u0: The start point of the measurement, in parameterized units.
        :param uf: The end point of the measurement, in parameterized units.
        """
        return float(quad(self.dl_du, u0, uf)[0])

    def segment_length(self, u0: float, uf: float) -> float:
        """
        Return the path length between u0 and uf.

        :param u0: The start point of the measurement, in parameterized units.
        :param uf: The end point of the measurement, in parameterized units.
        """
        first_index_after_u0 = next((i for i, u in enumerate(self._u) if u >= u0), len(self._u) - 1)
        last_index_before_uf = next(
            (i - 1 for i, u in enumerate(self._u) if u > uf), len(self._u) - 1
        )
        if last_index_before_uf >= first_index_after_u0 - 1 or last_index_before_uf < 0:
            return self._calculate_segment_length(u0, uf)

        length = self._calculate_segment_length(u0, self._u[first_index_after_u0])
        length += self._length_at_u[last_index_before_uf] - self._length_at_u[first_index_after_u0]
        length += self._calculate_segment_length(self._u[last_index_before_uf], uf)
        assert (uf >= u0) == (
            length >= 0
        ), f"{u0} {uf} {first_index_after_u0} {last_index_before_uf}"
        return length

    def calc_u_at_length(self, length: float) -> float:
        """
        Return the parameterization length for a given real length.

        :param length: The length at which we want to calculate u.
        """
        # Find an estimate of u via linear interpolation
        u_estimate = np.interp(length, self._length_at_u, self._u)
        i0 = next((i - 1 for i, u in enumerate(self._u) if u > u_estimate), len(self._u) - 1)
        u0 = self._u[i0]

        # Calculate u using an optimization algorithm
        delta_len = length - self._length_at_u[i0]
        u: float = newton(
            lambda u: self.segment_length(u0, u) - delta_len,
            u_estimate,
            self.dl_du,
            fprime2=self.d2l_du2,
        )
        return u

    def dx_du(self, u: float, derivative_number: float = 1) -> tuple[float, ...]:
        """
        Return the derivative of N-D path position with respect to u.

        :param u: The parameterized length u.
        :param derivative_number: The derivative (defaults to the first derivative).
        """
        # By default, splev returns an array for each element. Pick
        # the one and only value by flattening the arrays.
        val = splev(u, self._tck, derivative_number)
        return tuple(val[i].flat[0] for i in range(self._dim))

    def dl_du(self, u: float) -> float:
        """
        Return the derivative of path length with respect to the parameterization variable at u.

        :param u: The parameterized length u.
        """
        dx_du = self.dx_du(u)
        return float(sum(val**2 for val in dx_du) ** 0.5)

    def d2l_du2(self, u: float) -> float:
        """
        Return the second derivative of path length with respect to the parameterization variable.

        :param u: The parameterized length u.
        """
        dl_du = self.dl_du(u)
        dx_du = self.dx_du(u)
        d2p_du2 = self.dx_du(u, 2)
        if dl_du == 0:
            assert sum(2 * dx_du[i] * d2p_du2[i] for i in range(self._dim)) == 0
            return 0
        return sum(2 * dx_du[i] * d2p_du2[i] for i in range(self._dim)) / (2 * dl_du)

    def dx_dl(self, u: float) -> tuple[float, ...]:
        """
        Return the first derivative of x with respect to path length at u.

        :param u: The parameterized length u.
        """
        dl_du = self.dl_du(u)
        dx_du = self.dx_du(u)
        if dl_du == 0:
            assert all(dx_du_i == 0 for dx_du_i in dx_du)
            return tuple(0 for _ in dx_du)
        return tuple(dx_du_i / dl_du for dx_du_i in dx_du)

    def d2x_dl2(self, u: float) -> tuple[float, ...]:
        """
        Return the second derivative of x with respect to path length at u.

        :param u: The parameterized length u.
        """
        dl_du = self.dl_du(u)
        d2x_du2 = self.dx_du(u, 2)
        d2l_du2 = self.d2l_du2(u)
        dx_du = self.dx_du(u)
        if dl_du == 0:
            assert all(dx_du_i == 0 for dx_du_i in dx_du)
            return tuple(0 for _ in dx_du)
        d2u_dl2 = -d2l_du2 / dl_du**3
        return tuple(
            d2x_du2_i / dl_du**2 + dx_du_i * d2u_dl2 for dx_du_i, d2x_du2_i in zip(dx_du, d2x_du2)
        )


def generate_velocities_continuous_acceleration(
    position_sequence: list[float],
    time_sequence: list[float],
    vel_start: float = 0,
    vel_end: float = 0,
) -> list[float]:
    """
    Generate velocities such that acceleration is continuous at each transition.

    This function solves for the velocities at each point that make the acceleration
    at the end of each segment equal to the acceleration at the start of the next.

    Each segment's trajectory is represented by a cubic polynomial, where:
    Δpᵢ(t) = c1ᵢ * t + c2ᵢ * t² + c3ᵢ * t³, and
    vᵢ(t) = c1ᵢ + 2 * c2ᵢ * t + 3 * c3ᵢ * t²
    aᵢ(t) = 2 * c2ᵢ + 6 * c3ᵢ * t

    Geneneration is done by solving the system Ax = b for x, where x is an array of PVT
    coefficients for each segment (i.e., [c1₁, c2₁, c3₁, ... c1ₙ, c2ₙ, c3ₙ]. A is
    a tridiagonal matrix, and b is an array. The system is formed by combining all of
    the following constraint equations:
    1. position at the start and end of each segment is as specified by the user
    2. velocity is continous at each segment transition
    3. acceleration is continuous at each segment transition
    4. velocity at the start and end of the sequence is as specified by the user
    """
    num_segments = len(time_sequence) - 1
    A = np.zeros((num_segments * 3, num_segments * 3))  # pylint: disable=invalid-name
    b = np.zeros((num_segments * 3, 1))
    # Initial boundary condition
    A[0, 0] = 1
    b[0] = vel_start
    for segment_index in range(num_segments):
        delta_time = time_sequence[segment_index + 1] - time_sequence[segment_index]
        delta_pos = position_sequence[segment_index + 1] - position_sequence[segment_index]
        # Position equation for segment
        row_start = segment_index * 3 + 1
        col_start = segment_index * 3
        A[row_start, col_start : col_start + 3] = [delta_time, delta_time**2, delta_time**3]
        b[row_start] = delta_pos
        if segment_index < num_segments - 1:
            # Middle segments, where velocity is unknown and accelerations are continuous
            A[row_start + 1, col_start + 1 : col_start + 4] = [delta_time, 2 * delta_time**2, -1]
            b[row_start + 1] = -delta_pos / delta_time
            A[row_start + 2, col_start + 2 : col_start + 5] = [delta_time, 1 / delta_time, -1]
            b[row_start + 2] = delta_pos / delta_time**2
        else:
            # Final segment
            A[row_start + 1, col_start + 1 : col_start + 3] = [delta_time, 2 * delta_time**2]
            b[row_start + 1] = vel_end - delta_pos / delta_time
    # Get banded form of matrix
    ab = np.array(
        [
            [0] + [A[i, i + 1] for i in range(num_segments * 3 - 1)],
            [A[i, i] for i in range(num_segments * 3)],
            [A[i + 1, i] for i in range(num_segments * 3 - 1)] + [0],
        ]
    )
    coefficients = solve_banded((1, 1), ab, b)
    # Generate velocities
    vel_sequence = [vel_start]
    for segment_index in range(1, num_segments):
        vel_sequence.append(float(coefficients[segment_index * 3]))
    vel_sequence.append(vel_end)
    return vel_sequence


def generate_positions_continuous_acceleration(
    velocity_sequence: list[float],
    time_sequence: list[float],
    pos_start: float = 0,
    pos_end: float = 0,
) -> list[float]:
    """
    Generate positions such that acceleration is continuous at each transition.

    This function solves for the positions at each point that make the acceleration
    at the end of each segment equal to the acceleration at the start of the next.

    Each segment's trajectory is represented by a cubic polynomial, where:
    Δpᵢ(t) = vᵢ(0) * t + c2ᵢ * t² + c3ᵢ * t³, and
    vᵢ(t) = vᵢ(0) + 2 * c2ᵢ * t + 3 * c3ᵢ * t²
    aᵢ(t) = 2 * c2ᵢ + 6 * c3ᵢ * t

    Geneneration is done by solving the system Ax = b for x, where x is an array of PVT
    coefficients for each segment (i.e., [c2₁, c3₁, ... c2ₙ, c3ₙ]. A is
    a tridiagonal matrix, and b is an array. The system is formed by combining all of
    the following constraint equations:
    1. velocity at the start and end of each segment is as specified by the user
    2. acceleration is continuous at each segment transition
    3. acceleration at the start of the sequence is zero
    """

    def calculate_delta_position(c1: float, c2: float, c3: float, delta_time: float) -> float:
        """Calculate the position delta of a segment from its coefficients."""
        return float(c1 * delta_time + c2 * delta_time**2 + c3 * delta_time**3)

    num_segments = len(time_sequence) - 1
    A = np.zeros((num_segments * 2, num_segments * 2))  # pylint: disable=invalid-name
    b = np.zeros((num_segments * 2, 1))
    # Initial condition acceleration 0 is zero
    A[0, 0] = 1
    for segment_index in range(num_segments):
        delta_time = time_sequence[segment_index + 1] - time_sequence[segment_index]
        delta_vel = velocity_sequence[segment_index + 1] - velocity_sequence[segment_index]
        # Position equation for segment
        block_index = segment_index * 2
        A[block_index + 1, block_index : block_index + 2] = [2 * delta_time, 3 * delta_time**2]
        b[block_index + 1] = delta_vel
        if segment_index < num_segments - 1:
            # Middle segments, where accelerations are continuous
            A[block_index + 2, block_index + 1 : block_index + 3] = [3 * delta_time / 2, -1]
            b[block_index + 2] = -delta_vel / (2 * delta_time)
    # Get banded form of matrix
    ab = np.array(
        [
            [A[i, i] for i in range(num_segments * 2)],
            [A[i + 1, i] for i in range(num_segments * 2 - 1)] + [0],
        ]
    )
    coefficients = solve_banded((1, 0), ab, b)
    # Generate positions
    pos_sequence = [pos_start]
    for segment_index in range(num_segments):
        pos_sequence.append(
            pos_sequence[-1]
            + calculate_delta_position(
                velocity_sequence[segment_index],
                coefficients[segment_index * 2],
                coefficients[segment_index * 2 + 1],
                time_sequence[segment_index + 1] - time_sequence[segment_index],
            )
        )
    pos_sequence.append(pos_end)
    return pos_sequence


def interpolate_velocity_finite_difference(
    position_sequence: list[float], time_sequence: list[float]
) -> float:
    """
    Interpolate the velocity at a point.

    This functions uses the positions and time at the generation point and the preceding and
    proceeding points to interpolate an appropriate velocity value.

    Generation is done using a finite different scheme, using the positions and times of
    the point in question and the preceding and proceeding points in the sequence.

    See https://en.wikipedia.org/wiki/Cubic_Hermite_spline#Finite_difference.

    :param position_sequence: An array containing the position before, at, and after, the
        generation point.
    :param time_sequence: An array containing the time before, at, and after, the generation
        point.
    :return: The interpolated velocity.
    """
    # Setup
    sum_differences = 0.0
    num_differences = 0.0

    # Calculate the finite differences for the two segments involving the
    # point at which to generate a velocity.
    for index in range(2):
        delta_time = time_sequence[index + 1] - time_sequence[index]
        if delta_time > 0:
            num_differences += 1
            sum_differences += (
                position_sequence[index + 1] - position_sequence[index]
            ) / delta_time
    assert num_differences > 0, "All three points must not have the same time"

    # Return the average difference
    return sum_differences / num_differences


class CSVData:
    """A helper class to read sequences from CSV files."""

    _time_index: int | None
    """The index of the time column."""
    _position_indices: list[int]
    """The indices of the position columns."""
    _velocity_indices: list[int]
    """The indices of the position columns."""
    _time_sequence: list[float]
    """The sequence of time values read from the file."""
    _position_sequences: list[list[float]]
    """An array of position sequences, one for each dimension"""
    _velocity_sequences: list[list[float | None]]
    """An array of velocity sequences, one for each dimension."""

    @property
    def contains_time_data(self) -> bool:
        """Return whether the data contains time values."""
        return self._time_index is not None and any(t is not None for t in self._time_sequence)

    @property
    def contains_position_data(self) -> bool:
        """Return whether the data contains position values."""
        if len(self._position_indices) > 0:
            for sequence in self._position_sequences:
                if any(p is not None for p in sequence):
                    return True
        return False

    @property
    def contains_velocity_data(self) -> bool:
        """Return whether the data contains velocity values."""
        if len(self._velocity_indices) > 0:
            for sequence in self._velocity_sequences:
                if any(v is not None for v in sequence):
                    return True
        return False

    @property
    def contains_complete_velocity_data(self) -> bool:
        """Return whether or not all velocity values are specified."""
        if len(self._velocity_indices) == 0:
            return False
        for sequence in self._velocity_sequences:
            if any(v is None for v in sequence):
                return False
        return True

    @property
    def time_sequence(self) -> list[float]:
        """Return the time data, if it exists."""
        assert self.contains_time_data, "No time data was read from the file"
        return self._time_sequence

    @property
    def position_sequences(self) -> list[list[float]]:
        """Return the position data, if it exists."""
        assert self.contains_position_data, "No position data was read from the file"
        return self._position_sequences

    @property
    def velocity_sequences(self) -> list[list[float | None]]:
        """Return the velocity data, if it exists."""
        assert self.contains_velocity_data, "No velocity data was read from the file"
        return self._velocity_sequences

    def __init__(self, filename: str) -> None:
        """
        Initialize the CSVData instance and read in the data.

        :param filename: The name of the CSV file.
        """
        with open(filename, "r", encoding="utf-8") as file:
            reader = csv.reader(file)
            self._read_header(next(reader))
            for row in reader:
                self._read_row(row)

    def _read_header(self, header: list[str]) -> None:
        """Read the header row."""
        # Read indices
        self._time_index = next(
            (i for i, col_name in enumerate(header) if "time" in col_name.lower()),
            None,
        )
        self._position_indices = [
            i for i, col_name in enumerate(header) if "pos" in col_name.lower()
        ]
        self._velocity_indices = [
            i for i, col_name in enumerate(header) if "vel" in col_name.lower()
        ]
        # Setup sequence arrays
        self._time_sequence = []
        self._position_sequences = [[] for _ in self._position_indices]
        self._velocity_sequences = [[] for _ in self._velocity_indices]

    def _read_row(self, row: list[str]) -> None:
        """Read a data row."""
        # Read time.
        if self._time_index is not None:
            self._time_sequence.append(float(row[self._time_index]))
        # Read position.
        for dim_index, pos_column_index in enumerate(self._position_indices):
            self._position_sequences[dim_index].append(float(row[pos_column_index]))
        # Read velocity. This must support None values.
        for dim_index, vel_column_index in enumerate(self._velocity_indices):
            val = row[vel_column_index]
            self._velocity_sequences[dim_index].append(float(val) if val != "" else None)


class Sequence:
    """A PVT sequence, formed from one or more PVT points."""

    def __init__(self, points: list[Point] | None = None) -> None:
        """
        Initialize the PVT sequence.

        :param points: A list of PVT points from which to create the sequence.
        """
        if points is None:
            points = []
        self._points: list[Point] = []
        self._segments: list[Segment] = []
        for point in points:
            self.append_point(point)

    @property
    def dim(self) -> int:
        """Get the dimension of the sequence."""
        return self.points[0].dim

    @property
    def points(self) -> list[Point]:
        """Get a copy of the points in the sequence."""
        return self._points.copy()

    @property
    def start_time(self) -> float:
        """Get the start time of the sequence."""
        assert len(self._points) > 0, "There are no points in the sequence."
        return self._points[0].time

    @property
    def end_time(self) -> float:
        """Get the end time of the sequence."""
        assert len(self._points) > 0, "There are no points in the sequence."
        return self._points[-1].time

    def append_point(self, point: Point) -> None:
        """
        Append a point to the PVT sequence.

        :param point: The PVT point to append.
        """
        if len(self._points) > 0:
            # Try to append the segment first to ensure it passes validation
            self._segments.append(Segment(self._points[-1], point))
        self._points.append(point)

    def position(self, time: float) -> tuple[float, ...]:
        """
        Calculate the position at a given time in the sequence.

        :param time: The time at which to calculate the position.
        """
        segment = self._get_segment_at_time(time)
        return segment.position(time)

    def velocity(self, time: float) -> tuple[float, ...]:
        """
        Calculate the velocity at a given time in the sequence.

        :param time: The time at which to calculate the velocity.
        """
        segment = self._get_segment_at_time(time)
        return segment.velocity(time)

    def acceleration(self, time: float) -> tuple[float, ...]:
        """
        Calculate the acceleration at a given time in the sequence.

        :param time: The time at which to calculate the acceleration.
        """
        segment = self._get_segment_at_time(time)
        return segment.acceleration(time)

    def save_to_file(self, filename: str) -> None:
        """
        Save the sequence to a file.

        :param filename: The full name of the file, including the path.
        """
        # Generate names for each axis
        axis_names = [f"Axis {i + 1}" for i in range(self.dim)]
        # Write the data to the file
        with open(filename, "w", encoding="utf-8") as file:
            file_writer = csv.writer(file)
            # Construct header, alternating position and velocity values
            header = ["Time"]
            for dim_index in range(self.dim):
                header += [f"{axis_names[dim_index]} Position"]
                header += [f"{axis_names[dim_index]} Velocity"]
            file_writer.writerow(header)
            # Write the data
            for point in self._points:
                row = [point.time]
                for dim_index in range(self.dim):
                    row += [point.position[dim_index], point.velocity[dim_index]]
                file_writer.writerow(row)

    def _validate_time(self, time: float) -> None:
        """
        Validate that a given time falls within the bounds defined by the sequence.

        :param time: The time to validate.
        """
        assert len(self._points) > 0, "There are no points in the sequence"
        time_min = self._points[0].time
        time_max = self._points[-1].time
        assert (
            time_min <= time <= time_max + 1e-14
        ), f"Time {time} is outside of sequence range ({time_min}, {time_max})"

    def _get_segment_at_time(self, time: float) -> Segment:
        """
        Get the segment corresponding to the given time.

        :param time: The time at which to get the segment.
        """
        self._validate_time(time)
        if time < self._points[-1].time:
            # Return the index of the last point whose time is less than or equal to the given time
            index = next(i for i in range(len(self._points)) if time < self._points[i].time) - 1
        else:
            # Return the index of the last segment
            index = len(self._segments) - 1
        return self._segments[index]

    @staticmethod
    def from_parameter_sequences(
        time_sequence: list[float],
        position_sequences: list[list[float]],
        velocity_sequences: list[list[float]],
    ) -> Sequence:
        """
        Return a PVT sequence from parameter sequences.

        This function generates a PVT sequence from time,
        position, and velocity arrays.

        :param time_sequence: The sequence of time values.
        :param position_sequences: An array of position sequences, one
            for each dimension.
        :param velocity_sequences: An array of velocity sequences, one
            for each dimension.
        :return: The PVT sequence with generated parameters.
        """
        sequence = Sequence()
        dim = len(position_sequences)
        for point_index, time in enumerate(time_sequence):
            positions = tuple(position_sequences[i][point_index] for i in range(dim))
            velocities = tuple(velocity_sequences[i][point_index] for i in range(dim))
            sequence.append_point(Point(positions, velocities, time))
        return sequence

    @staticmethod
    def from_csv(
        filename: str, target_speed: float | None = None, target_accel: float | None = None
    ) -> Sequence:
        """
        Return a PVT sequence with data loaded from a CSV file.

        This function will load all the given data and attempt to
        generate any missing parameters. Generation is only possible
        in the following cases:
        - No velocity or time information is provided (i.e., there are
          no such columns or all values in corresponding columns are
          empty.) In this case, all velocity and time parameters will
          be generated.
        - No position information is provided (i.e., there are no such
          columns or all values in the corresponding columns are empty.)
          In this case, all position values will be generated.
        - Some or all velocity information is missing (i.e., there are no
          velocity columns at all, or there is a velocity column for
          each position column, and some or all values are empty.) In this
          case only the missing velocity parameters will be generated.

        This function assumes the file has a header row with all
        necessary columns, and that position and velocity columns
        are ordered according to their axis number (i.e., if position
        column 1 comes first, then so must velocity column 1.)
        Additionally:
        - Position columns must have a header containing the keyword "pos"
        - Velocity columns must have a header containing the keyword "vel"
        - The time column must have a header containing the keyword "time"
        No information is read from the header names except their identifying
        keyword.

        The function also assumes units are consistent with one another.
        That is, if position is given in units P / T, then time is given in
        units of T, and velocity is given in units of P / T².

        :param filename: The name of the csv file to load.
        :param target_speed: The target speed used for generating velocities and times.
        :param target_accel: The target acceleration used for generating velocities and times.
        :return: The generated PVT sequence.
        """

        class GenerationType(Enum):
            """An enum describing what parameters to generate."""

            NONE = auto()
            """Don't generate any parameters."""
            TIME_AND_VELOCITY = auto()
            """Generate time and velocity."""
            POSITION = auto()
            """Generate position only."""
            VELOCITY = auto()
            """Generate velocity only."""

        # Read the data and do some sanity checks
        data = CSVData(filename)
        gen_type = GenerationType.NONE
        if not data.contains_time_data:
            gen_type = GenerationType.TIME_AND_VELOCITY
            assert not data.contains_velocity_data, (
                "Invalid csv structure. Time can only be generated if"
                "velocity is also unspecified."
            )
        elif not data.contains_velocity_data:
            gen_type = GenerationType.VELOCITY
            assert data.contains_position_data, (
                "Invalid csv structure. If velocity is unspecified, " "position must be specified."
            )
        elif not data.contains_complete_velocity_data:
            gen_type = GenerationType.VELOCITY
        if not data.contains_position_data:
            gen_type = GenerationType.POSITION
            assert data.contains_time_data and data.contains_complete_velocity_data, (
                "Invalid csv structure. If position is unspecified, "
                "velocity and time must both be specified"
            )

        # Call the appropriate generation function
        match gen_type:
            case GenerationType.NONE:
                return Sequence.from_parameter_sequences(
                    data.time_sequence,
                    data.position_sequences,
                    data.velocity_sequences,  # type: ignore
                )
            case GenerationType.TIME_AND_VELOCITY:
                assert (
                    target_speed is not None and target_accel is not None
                ), "Target speed and accel must be defined to generate velocities and times"
                return Sequence.generate_times_and_velocities(
                    data.position_sequences, target_speed, target_accel
                )
            case GenerationType.POSITION:
                return Sequence.generate_positions(
                    data.time_sequence,
                    data.velocity_sequences,  # type: ignore
                )
            case GenerationType.VELOCITY:
                return Sequence.generate_velocities(
                    data.time_sequence,
                    data.position_sequences,
                    data.velocity_sequences,
                )

    @staticmethod
    def generate_times_and_velocities(  # pylint: disable=too-many-locals
        position_sequences: list[list[float]],
        target_speed: float,
        target_accel: float,
        resample_number: int | None = None,
    ) -> Sequence:
        """
        Return a PVT sequence from a sequence of position keypoints.

        This function generates the velocity and time parameters,
        using a target speed and acceleration

        This function fits a geometric spline over the position
        information, and then calculates the velocity and time
        information by traversing it using a trapezoidal motion
        profile.

        This generation scheme attempts to keep speed and acceleration
        less than the specified target values, but does not guarantee it.
        Generally speaking, a higher resample number will bring the
        generated trajectory closer to respecting these limits.

        :param position_sequences: The position sequences for each axis.
        :param target_speed: The target speed used for generating velocities and times.
        :param target_accel: The target acceleration used for generating velocities and times.
        :param resample_num: The number of points to resample the sequence by, or None to use
            the specified points.
        :return: The generated PVT sequence.
        """
        # Setup
        dim = len(position_sequences)
        generated_sequence = Sequence()
        geo_path = GeometricPath(position_sequences)
        u_sample = (
            geo_path.parameterized_lengths
            if resample_number is None
            else (
                [0]
                + [
                    geo_path.calc_u_at_length(i * geo_path.length / (resample_number - 1))
                    for i in range(1, resample_number - 1)
                ]
                + [1]
            )
        )

        def generate_calculation_points(
            u_sample: list[float], geo_path: GeometricPath
        ) -> tuple[list[float], dict[int, list[int]]]:
            """
            Generate a list of critical points used for calculating the speed profile.

            This function generates a list of calculation points by:
            - Adding intermediate points between the sample points, and
            - Adding critical points, or points where one or more axis changes direction
            """
            # For each sample point, use N points in calculations
            u_calc = [0.0]
            for u_prev, u_next in zip(u_sample[:-1], u_sample[1:]):
                parameterized_sublength = (u_next - u_prev) / 10
                for i in range(1, 10):
                    u_calc.append(u_prev + parameterized_sublength * i)
                u_calc.append(u_next)

            # Find points where axes change directions
            reversals: dict[int, list[int]] = {}
            segment_index = 0
            while segment_index < len(u_calc) - 1:
                initial_direction = geo_path.direction(u_calc[segment_index])
                final_direction = geo_path.direction(u_calc[segment_index + 1])
                u_inserts = {}
                for d in range(dim):
                    if initial_direction[d] * final_direction[d] < 0:
                        if dim > 1:
                            u_inserts[d] = newton(
                                partial(lambda u, d: geo_path.dx_du(u)[d], d=d),
                                (u_calc[segment_index] + u_calc[segment_index + 1]) / 2,
                                partial(lambda u, d: geo_path.dx_du(u, 2)[d], d=d),
                                fprime2=partial(lambda u, d: geo_path.dx_du(u, 3)[d], d=d),
                            )
                        else:
                            u_inserts[d] = bisect(
                                partial(lambda u, d: geo_path.dx_du(u)[d], d=d),
                                u_calc[segment_index],
                                u_calc[segment_index + 1],
                            )
                for d, u_insert in sorted(u_inserts.items(), key=lambda item: item[1]):
                    if math.isclose(u_insert, u_calc[segment_index]):
                        reversals.setdefault(segment_index, [])
                        reversals[segment_index].append(d)
                    else:
                        segment_index += 1
                        reversals.setdefault(segment_index, [])
                        reversals[segment_index].append(d)
                        u_calc = u_calc[:segment_index] + [u_insert] + u_calc[segment_index:]
                segment_index += 1
            return u_calc, reversals

        u_calc, reversals = generate_calculation_points(u_sample, geo_path)

        # Calculate speed limits from end point
        segment_lengths = [
            geo_path.segment_length(u_calc[i], u_calc[i + 1]) for i in range(len(u_calc) - 1)
        ]
        speed_limits = [target_speed for _ in u_calc]
        speed_limits[0] = speed_limits[-1] = 0
        for i in reversed(range(1, len(speed_limits) - 1)):
            # Calculate the speed limit from max deceleration over the path length
            speed_limits[i] = min(
                speed_limits[i],
                (speed_limits[i + 1] ** 2 + 2 * target_accel * segment_lengths[i]) ** 0.5,
            )
            # Calculate the speed limit from total acceleration
            if i in reversals and len(reversals[i]) == dim:
                speed_limits[i] = min(speed_limits[i], 0)
            elif (
                denominator := sum(d2xi_dl2**2 for d2xi_dl2 in geo_path.d2x_dl2(u_calc[i]))
            ) != 0:
                speed_limits[i] = min(speed_limits[i], (target_accel**2 / denominator) ** (1 / 4))

        # Calculate speed limits from start point and assemble sequence
        time = 0.0
        generated_sequence.append_point(
            Point(
                geo_path.position(u_sample[0]),
                tuple(speed_limits[0] * d for d in geo_path.direction(u_sample[0])),
                time,
            )
        )
        next_sample_index = 1
        for i in range(1, len(speed_limits)):
            # Calculate the speed limit from max acceleration over the path length
            speed_limits[i] = min(
                speed_limits[i],
                (speed_limits[i - 1] ** 2 + 2 * target_accel * segment_lengths[i - 1]) ** 0.5,
            )
            if (average_speed := sum(speed_limits[i - 1 : i + 1]) / 2) == 0:
                time += (segment_lengths[i - 1] / target_accel) ** 0.5
            else:
                time += segment_lengths[i - 1] / average_speed
            if u_calc[i] >= u_sample[next_sample_index]:
                generated_sequence.append_point(
                    Point(
                        geo_path.position(u_calc[i]),
                        tuple(speed_limits[i] * d for d in geo_path.direction(u_calc[i])),
                        time,
                    )
                )
                next_sample_index += 1

        return generated_sequence

    @staticmethod
    def generate_velocities(
        time_sequence: list[float],
        position_sequences: list[list[float]],
        velocity_sequences: list[list[float | None]] | None,
    ) -> Sequence:
        """
        Return a PVT sequence from position-time data or position-velocity-time data.

        This function calculates velocities by enforcing acceleration be
        continuous at each segment transition. For more information, see
        the function generate_velocities_continuous_acceleration().

        :param time_sequence: The sequence of time values.
        :param position_sequences: An array of position sequences, one
            for each dimension.
        :param velocity_sequences: An array of velocity sequences, one
            for each dimension. This must either have the same size as
            position_sequences, or be None to denote all values be generated.
        :return: The PVT sequence with generated parameters.
        """
        # Setup
        sequence_dim = len(position_sequences)
        sequence_length = len(time_sequence)
        generated_sequence = Sequence()

        # Generate velocities
        if velocity_sequences is None:
            # Generate all velocities
            velocity_sequences = []
            for dim in range(sequence_dim):
                velocity_sequences.append(
                    generate_velocities_continuous_acceleration(  # type: ignore
                        position_sequences[dim], time_sequence, 0, 0
                    )
                )
        else:
            # Generate some velocities
            for dim in range(sequence_dim):
                # Set zero velocity at endpoints
                for endpoint_index in (0, sequence_length - 1):
                    if velocity_sequences[dim][endpoint_index] is None:
                        velocity_sequences[dim][endpoint_index] = 0
                # Generate the rest
                gen_start_index = None
                for point_index in range(1, sequence_length - 1):
                    # Check for the first undefined velocity in a sequence of undefined velocities
                    if gen_start_index is None and velocity_sequences[dim][point_index] is None:
                        gen_start_index = point_index - 1
                    # Check for the end of a sequence of undefined velocities
                    if (
                        gen_start_index is not None
                        and velocity_sequences[dim][point_index + 1] is not None
                    ):
                        velocity_sequences[dim][
                            gen_start_index : point_index + 2
                        ] = generate_velocities_continuous_acceleration(
                            position_sequences[dim][gen_start_index : point_index + 2],
                            time_sequence[gen_start_index : point_index + 2],
                            velocity_sequences[dim][gen_start_index],  # type: ignore
                            velocity_sequences[dim][point_index + 1],  # type: ignore
                        )
                        gen_start_index = None
        # Append the points
        for point_index in range(sequence_length):
            positions = [position_sequences[i][point_index] for i in range(sequence_dim)]
            velocities = [velocity_sequences[i][point_index] for i in range(sequence_dim)]
            time = time_sequence[point_index]
            generated_sequence.append_point(Point(positions, velocities, time))  # type: ignore
        return generated_sequence

    @staticmethod
    def generate_positions(
        time_sequence: list[float],
        velocity_sequences: list[list[float]],
    ) -> Sequence:
        """
        Return a PVT sequence from position-time data.

        This function calculates positions by enforcing acceleration be
        continuous at each segment transition. For more information, see
        the function generate_positions_continuous_acceleration().

        :param time_sequence: The sequence of time values.
        :param velocity_sequences: An array of velocity sequences, one
            for each dimension.
        :return: The PVT sequence with generated parameters.
        """
        # Setup
        sequence_dim = len(velocity_sequences)
        sequence_length = len(time_sequence)
        generated_sequence = Sequence()

        # Generate positions
        position_sequences = []
        for dim in range(sequence_dim):
            position_sequences.append(
                generate_positions_continuous_acceleration(
                    velocity_sequences[dim], time_sequence, 0, 0
                )
            )

        # Append the points
        for point_index in range(sequence_length):
            positions = tuple(position_sequences[i][point_index] for i in range(sequence_dim))
            velocities = tuple(velocity_sequences[i][point_index] for i in range(sequence_dim))
            time = time_sequence[point_index]
            generated_sequence.append_point(Point(positions, velocities, time))
        return generated_sequence
