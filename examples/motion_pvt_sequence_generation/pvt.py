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

import numpy as np

from zaber_motion import Measurement
from zaber_motion.ascii import PvtSequenceData, PvtSequence

@staticmethod
def sequence_data_from_csv(
    filename: str, target_speed: Measurement | None = None, target_accel: Measurement | None = None
) -> PvtSequenceData | None:
    """
    Return a PVT sequence data object loaded from CSV.

    This function will load all the given data and attempt to
    generate any missing parameters. Generation is only possible
    in the following cases:
    - No velocity or time information is provided (i.e., there are
      no such columns). In this case, all velocity and time parameters
      will be generated.
    - No position information is provided (i.e., there is no such column).
      In this case, all position values will be generated.
    - No velocity information is provided (i.e., there is no such column).
      In this case, all velocity values will be generated.

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
    data = PvtSequence.load_sequence_data(filename)

    contains_time_data = len(data.sequence_data.times.values) > 0
    contains_position_data = (
        len(data.sequence_data.positions) > 0 and len(data.sequence_data.positions[0].values) > 0
    )
    contains_velocity_data = (
        len(data.sequence_data.velocities) > 0 and len(data.sequence_data.velocities[0].values) > 0
    )

    gen_type = GenerationType.NONE
    if not contains_time_data:
        gen_type = GenerationType.TIME_AND_VELOCITY
        assert not contains_velocity_data and contains_position_data, (
            "Invalid csv structure. Time can only be generated if position is specified and "
            "velocity is unspecified."
        )
    elif not contains_velocity_data:
        gen_type = GenerationType.VELOCITY
        assert contains_position_data, (
            "Invalid csv structure. If velocity is unspecified, position must be specified."
        )
    elif not contains_position_data:
        gen_type = GenerationType.POSITION
        assert contains_velocity_data, (
            "Invalid csv structure. If position is unspecified, "
            "velocity and time must both be specified"
        )

    # Call the appropriate generation function
    match gen_type:
        case GenerationType.NONE:
            return data.sequence_data
        case GenerationType.TIME_AND_VELOCITY:
            assert (
                target_speed is not None and target_accel is not None
            ), "Target speed and accel must be defined to generate velocities and times"
            return PvtSequence.generate_velocities_and_times(
                data.sequence_data.positions,
                target_speed,
                target_accel,
            )
        case GenerationType.POSITION:
            return PvtSequence.generate_positions(
                data.sequence_data.velocities,
                data.sequence_data.times,
                times_relative=True,
            )
        case GenerationType.VELOCITY:
            return PvtSequence.generate_velocities(
                data.sequence_data.positions,
                data.sequence_data.times,
                velocities=None,
                times_relative=True,
            )
        case _:
            return data.sequence_data

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
    """
    A PVT sequence, formed from one or more PVT points.

    Used for plotting paths and trajectories in visualization.py
    """

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

    def append_point(self, point: Point = False) -> None:
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
        with open(filename, "w", encoding="utf-8", newline="") as file:
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
    def from_sequence_data(data: PvtSequenceData, times_relative: bool):
        """
        Return a PVT sequence from sequence data.

        This function generates a PVT sequence from a ZML PVT sequence data object.

        :param data: The sequence data object.
        :return: The PVT sequence with generated parameters.
        """
        points = []
        absolute_times = np.cumsum(data.times.values) if times_relative else data.times.values
        for i in range(len(data.times.values)):
            point: Point = Point(
                position=tuple(ms.values[i] for ms in data.positions),
                velocity=tuple(ms.values[i] for ms in data.velocities),
                time=absolute_times[i],
            )
            points.append(point)
        return Sequence(points)
