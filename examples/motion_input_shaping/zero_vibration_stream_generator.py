"""
Contains the ZeroVibrationShaper class for re-use in other code.

Run the file directly to test the class functionality.
"""

import math
from enum import Enum
from dataclasses import dataclass
import numpy as np
from plant import Plant


class ShaperType(Enum):
    """Enumeration for different input shaper types."""

    ZV = 1
    ZVD = 2
    ZVDD = 3


@dataclass
class StreamSegment:
    """A class that contains information for a single segment of the stream trajectory."""

    position: float
    speed_limit: float
    accel: float
    duration: float


@dataclass
class AccelPoint:
    """Acceleration points used to define trajectories."""

    time: float
    acceleration: float


def trapezoidal_motion_generator(
    distance: float, acceleration: float, deceleration: float, max_speed_limit: float
) -> list[AccelPoint]:
    """
    Produce acceleration profile for basic trapezoidal motion.

    Returns list of time and acceleration points where acceleration changes.
    All acceleration changes are step changes for trapezoidal motion.

    :param distance: The trajectory distance.
    :param acceleration: The trajectory acceleration.
    :param deceleration: The trajectory deceleration.
    :param max_speed_limit: Maximum trajectory speed in the output motion.
    """
    direction = np.sign(distance)

    acceleration_distance = max_speed_limit**2 / (2 * acceleration)
    deceleration_distance = max_speed_limit**2 / (2 * deceleration)
    max_speed_distance = abs(distance) - acceleration_distance - deceleration_distance

    if max_speed_distance > 0:
        # Trapezoidal Motion
        max_speed = max_speed_limit
    else:
        # Max speed is not reached.
        max_speed_distance = 0
        max_speed = np.sqrt(abs(distance) / (1 / (2 * acceleration) + 1 / (2 * deceleration)))

    acceleration_duration = max_speed / acceleration
    max_speed_duration = max_speed_distance / max_speed
    deceleration_duration = max_speed / deceleration

    acceleration_endtime = acceleration_duration
    max_speed_endtime = acceleration_endtime + max_speed_duration
    deceleration_endtime = max_speed_endtime + deceleration_duration

    if max_speed_distance == 0:
        return [
            AccelPoint(0, acceleration * direction),
            AccelPoint(acceleration_endtime, deceleration * (-1 * direction)),
            AccelPoint(deceleration_endtime, 0),
        ]

    return [
        AccelPoint(0, acceleration * direction),
        AccelPoint(acceleration_endtime, 0),
        AccelPoint(max_speed_endtime, deceleration * (-1 * direction)),
        AccelPoint(deceleration_endtime, 0),
    ]


def calculate_acceleration_convolution(
    impulse_times: list[float],
    impulses: list[float],
    unshaped_trajectory: list[AccelPoint],
) -> list[AccelPoint]:
    """
    Perform the shaping by computing convolution of acceleration with the shaper impulses.

    This algorithm computes the result of the convolution without actually performing a convolution
    on a full timeseries dataset. This reduces the amount of computation and number of points
    generated and is also more accurate since it is not constrained by fixed timestep size.
    This algorithm only works if the acceleration changes are steps changes.
    Returns shaped segment times and accelerations.

    :param impulse_times: List of shaper impulse times
    :param impulses: List of shaper impulse magnitudes
    :param unshaped_trajectory: List of acceleration points
    """
    unshaped_time = [x.time for x in unshaped_trajectory]
    unshaped_acceleration = [x.acceleration for x in unshaped_trajectory]

    unshaped_accel_changes = np.diff(
        np.concatenate([np.array([0]), np.array(unshaped_acceleration)])
    )  # append a 0 to start of list of accelerations and take diff to get changes
    num_rows = len(unshaped_acceleration)

    # Create extra points based on number of impulses
    shaped_time = np.zeros(len(unshaped_acceleration) * len(impulses))
    accel_changes = np.zeros(len(unshaped_acceleration) * len(impulses))
    # for each impulse create a copy of the acceleration change delayed and scaled by the
    # impulse time and magnitude
    for n, impulse in enumerate(impulses):
        shaped_time[n * num_rows : (num_rows + n * num_rows)] = (
            np.array([unshaped_time]) + impulse_times[n]
        )
        accel_changes[n * num_rows : (num_rows + n * num_rows)] = (
            np.array([unshaped_accel_changes]) * impulse
        )

    # sort acceleration changes by time
    sort_index = shaped_time.argsort()
    shaped_time = shaped_time[sort_index]
    accel_changes = accel_changes[sort_index]

    # Final trajectory acceleration is cumulative sum of acceleration steps which gives the
    # superposition of the contribution from each impulse and is equivalent to the convolution
    shaped_acceleration = np.cumsum(accel_changes)  # Acceleration

    shaped_trajectory = []
    for n, accel in enumerate(shaped_acceleration):
        shaped_trajectory.append(AccelPoint(shaped_time[n], accel))

    return shaped_trajectory


def create_stream_trajectory(trajectory: list[AccelPoint]) -> list[StreamSegment]:
    """
    Compute information needed to execute trajectory through streams.

    Returns list of StreamSegment objects.
    The final acceleration must be 0.

    :param trajectory: List of acceleration points to create trajectory from
    """
    trajectory_time = [x.time for x in trajectory]
    trajectory_acceleration = [x.acceleration for x in trajectory]

    stream_segments = []
    # trajectory is one row less than list of accelerations since first row would be the
    # initial position (zeros)
    previous_position = 0.0
    previous_velocity = 0.0
    for n in range(0, len(trajectory_acceleration) - 1):
        # Calculate position and velocity at end of each segment using equations for constant
        # acceleration since acceleration changes are steps.
        current_accel = trajectory_acceleration[n]
        dt = trajectory_time[n + 1] - trajectory_time[n]  # dt
        current_velocity = previous_velocity + trajectory_acceleration[n] * dt  # velocity
        current_position = (
            previous_position + (current_velocity + previous_velocity) / 2 * dt
        )  # position

        stream_segments.append(
            StreamSegment(
                current_position,
                max([abs(current_velocity), abs(previous_velocity)]),
                abs(current_accel),
                dt,
            )
        )

        # Record current values and previous positions for next step
        previous_position = current_position
        previous_velocity = current_velocity

    return stream_segments


class ZeroVibrationStreamGenerator:
    """A class for creating stream motion with zero vibration input shaping theory."""

    def __init__(self, plant: Plant, shaper_type: ShaperType = ShaperType.ZV) -> None:
        """
        Initialize the class.

        :param plant: The Plant instance defining the system that the shaper is targeting.
        :param shaper_type: Type of input shaper to use to generate impulses.
        """
        self.plant = plant
        self._shaper_type = shaper_type

    @property
    def shaper_type(self) -> ShaperType:
        """Get input shaper type."""
        return self._shaper_type

    @shaper_type.setter
    def shaper_type(self, value: ShaperType) -> None:
        """Set input shaper type."""
        self._shaper_type = value

    def get_impulse_amplitudes(self) -> list[float]:
        """Get shaper impulse magnitudes."""
        k = math.exp(
            (-1 * math.pi * self.plant.damping_ratio) / math.sqrt(1 - self.plant.damping_ratio**2)
        )  # Decay factor

        match self.shaper_type:
            case ShaperType.ZV:
                return [1 / (1 + k), k / (1 + k)]
            case ShaperType.ZVD:
                return [
                    1 / (1 + 2 * k + k**2),
                    2 * k / (1 + 2 * k + k**2),
                    k**2 / (1 + 2 * k + k**2),
                ]
            case ShaperType.ZVDD:
                return [
                    1 / (1 + 3 * k + 3 * k**2 + k**3),
                    3 * k / (1 + 3 * k + 3 * k**2 + k**3),
                    3 * k**2 / (1 + 3 * k + 3 * k**2 + k**3),
                    k**3 / (1 + 3 * k + 3 * k**2 + k**3),
                ]
            case _:
                raise ValueError(f"Shaper type {self.shaper_type} is not valid.")

    def get_impulse_times(self) -> list[float]:
        """Get shaper impulse times."""
        match self.shaper_type:
            case ShaperType.ZV:
                return [0, self.plant.resonant_period / 2]
            case ShaperType.ZVD:
                return [0, self.plant.resonant_period / 2, self.plant.resonant_period]
            case ShaperType.ZVDD:
                return [
                    0,
                    self.plant.resonant_period / 2,
                    self.plant.resonant_period,
                    self.plant.resonant_period * 3 / 2,
                ]
            case _:
                raise ValueError(f"Shaper type {self.shaper_type} is not valid.")

    def shape_trapezoidal_motion(
        self, distance: float, acceleration: float, deceleration: float, max_speed_limit: float
    ) -> list[StreamSegment]:
        """
        Create stream points for zero vibration trapezoidal motion.

        All distance, speed, and accel units must be consistent.

        :param distance: The trajectory distance.
        :param acceleration: The trajectory acceleration.
        :param deceleration: The trajectory deceleration.
        :param max_speed_limit: An optional limit to place on maximum trajectory speed in the
        output motion.
        """
        # Get time and magnitude of the impulses used for shaping
        impulses = self.get_impulse_amplitudes()
        impulse_times = self.get_impulse_times()

        unshaped_trajectory = trapezoidal_motion_generator(
            distance,
            acceleration,
            deceleration,
            max_speed_limit,
        )

        shaped_trajectory = calculate_acceleration_convolution(
            impulse_times, impulses, unshaped_trajectory
        )

        stream_segments = create_stream_trajectory(shaped_trajectory)

        # make sure end point position is exactly on target
        stream_segments[-1].position = distance

        return stream_segments


# Example code for using the class.
if __name__ == "__main__":
    plant_var = Plant(4.64, 0.04)
    shaper = ZeroVibrationStreamGenerator(plant_var, ShaperType.ZV)

    DIST = 600
    ACCEL = 2100
    MAX_SPEED = 1000

    trajectory_points = shaper.shape_trapezoidal_motion(DIST, ACCEL, ACCEL, MAX_SPEED)
    print("Accel, Position, Max Speed, Time")
    for point in trajectory_points:
        print(*[point.accel, point.position, point.speed_limit, point.duration], sep=", ")

    print("")
    print(
        f"Shaped Move: "
        f"Max Speed: {max(np.abs(point.speed_limit) for point in trajectory_points):.2f}, "
        f"Total Time: {sum((point.duration for point in trajectory_points)):.2f}, "
    )
