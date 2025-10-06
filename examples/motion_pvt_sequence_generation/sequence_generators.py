"""
These functions have now been ported to Zaber Motion Library,
so the calls to them in this example code have been replaced by
equivalent calls to equivalent functions on zaber_motion.ascii.PvtSequence
class.

They remain here in case anyone is interested in reading and studying
their implementation: we assume that even the most technically proficient
user may find it easier to read and understand their implementation in
python than in golang.

That said, if anyone is curious, they can find the production go code here:
https://gitlab.com/ZaberTech/zaber-motion-lib/-/blob/master/internal/devices/stream_pvt_sequence_generators.go

The only real differences between these functions and their go
implementation is that in go, generate_times_and_velocities handles
sequences of 2 and 3 points whereas the python implementation can only
handle sequences of 4 or more.
"""

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

import pvt

def generate_times_and_velocities(  # pylint: disable=too-many-locals
    position_sequences: list[list[float]],
    target_speed: float,
    target_accel: float,
    resample_number: int | None = None,
) -> pvt.Sequence:
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
    generated_sequence = pvt.Sequence()
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
        pvt.Point(
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
                pvt.Point(
                    geo_path.position(u_calc[i]),
                    tuple(speed_limits[i] * d for d in geo_path.direction(u_calc[i])),
                    time,
                )
            )
            next_sample_index += 1

    return generated_sequence

def generate_velocities(
    time_sequence: list[float],
    position_sequences: list[list[float]],
    velocity_sequences: list[list[float | None]] | None,
) -> pvt.Sequence:
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
    generated_sequence = pvt.Sequence()

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
        generated_sequence.append_point(pvt.Point(positions, velocities, time))  # type: ignore
    return generated_sequence

def generate_positions(
    time_sequence: list[float],
    velocity_sequences: list[list[float]],
) -> pvt.Sequence:
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
    generated_sequence = pvt.Sequence()

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
        generated_sequence.append_point(pvt.Point(positions, velocities, time))
    return generated_sequence

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