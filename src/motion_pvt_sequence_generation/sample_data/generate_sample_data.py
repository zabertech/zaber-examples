"""Generate the PVT sample data used in the project."""

from abc import ABC, abstractmethod
import csv
from enum import Enum
import math


class ParameterSet(Enum):
    """An enum describing the allowable parameter combinations for automatic generation."""

    P = "position_data"
    PT = "position_time_data"
    VT = "velocity_time_data"
    PVT = "position_velocity_time_data"


class Trajectory(ABC):
    """A base class for trajectories that can generate position and velocity vectors from a time."""

    @abstractmethod
    def position(self, time: float) -> list[float]:
        """Return the position at a given time."""
        raise NotImplementedError

    @abstractmethod
    def velocity(self, time: float) -> list[float]:
        """Return the velocity at a given time."""
        raise NotImplementedError

    @property
    @abstractmethod
    def dim(self) -> int:
        """Return the dimension of the trajectory."""
        raise NotImplementedError


class Wave(Trajectory):
    """
    A constant-velocity wave trajectory.

    The governing equations of motion are:
    p(t) = A∙sin(2πt/T)
    v(t) = (2π/T)∙A∙cos(2πt/T)
    where,
    p is the position,
    v is the velocity,
    t is the time,
    A is the amplitude,
    T is the period
    """

    def __init__(self, amplitude: float, period: float):
        """Initialize the wave."""
        self._amplitude = amplitude
        self._period = period

    def angle(self, time: float) -> float:
        """Return the phase angle of the wave at the given time."""
        return 2 * math.pi / self._period * time

    def position(self, time: float) -> list[float]:
        """Return the position at a given time."""
        return [self._amplitude * math.sin(self.angle(time))]

    def velocity(self, time: float) -> list[float]:
        """Return the velocity at a given time."""
        return [
            2
            * math.pi
            * self._amplitude
            / self._period
            * math.cos(2 * math.pi / self._period * time)
        ]

    @property
    def dim(self) -> int:
        """Return the dimension of the trajectory."""
        return 1


class Spiral(Trajectory):
    """
    Generate the trajectory for a 2-dimensional spiral.

    The governing equations of motion are:
    px(t) = A∙(t/T)∙sin(2πt/T)
    py(t) = A∙(t/T)∙cos(2πt/T)
    vx(t) = (A/T)∙[(2πt/T)∙cos(2πt/T) + sin(2πt/T)]
    vx(t) = (A/T)∙[-(2πt/T)∙sin(2πt/T) + cos(2πt/T)]
    where,
    px and py are the x and y position, respectively,
    vx and vy are the x and y velocity, respectively,
    t is the time,
    A is the amplitude at time T,
    T is the period
    """

    def __init__(self, amplitude: float, period: float):
        """Initialize the spiral."""
        self._amplitude = amplitude
        self._period = period

    def angle(self, time: float) -> float:
        """Return the phase angle of the spiral at the given time."""
        return 2 * math.pi / self._period * time

    def position(self, time: float) -> list[float]:
        """Return the position at a given time."""
        angle = self.angle(time)
        return [
            self._amplitude * (time / self._period) * math.sin(angle),
            self._amplitude * (time / self._period) * math.cos(angle),
        ]

    def velocity(self, time: float) -> list[float]:
        """Return the velocity at a given time."""
        angle = self.angle(time)
        return [
            (self._amplitude / self._period) * (angle * math.cos(angle) + math.sin(angle)),
            (self._amplitude / self._period) * (-angle * math.sin(angle) + math.cos(angle)),
        ]

    @property
    def dim(self) -> int:
        """Return the dimension of the trajectory."""
        return 2


class TranslatingSpiral(Spiral):
    """
    Generate the trajectory for a spiral that translates on the z axis.

    The governing equations of motion for x and y are
    the same as the Spiral, and for z are:
    pz(t) = 0.5∙A∙(1-cos(πt/2T))
    vz(t) = 0.25∙A∙π/T∙sin(πt/2T)
    where,
    pz is the z position,
    vz is the z velocity,
    t is the time,
    A is the amplitude at time T,
    T is the period
    """

    def position(self, time: float) -> list[float]:
        """Return the position at a given time."""
        return super().position(time) + [
            0.5 * self._amplitude * (1 - math.cos(self.angle(time) / 4))
        ]

    def velocity(self, time: float) -> list[float]:
        """Return the velocity at a given time."""
        return super().velocity(time) + [
            0.25 * self._amplitude * math.pi / self._period * math.sin(self.angle(time) / 4)
        ]

    @property
    def dim(self) -> int:
        """Return the dimension of the trajectory."""
        return 3


def generate_and_write(
    filename: str, parameter_set: ParameterSet, trajectory: Trajectory, times: list[float]
) -> None:
    """
    Generate a trajectory from the given model and write the values to a file.

    :param filename: The file name to write to.
    :param parameter_set: An enum describing which parameters to write.
    :param trajectory: The trajectory generator model.
    :param times: The times at which to generate the positions and velocities.
    """
    # Open file and write header
    with open(filename, "w", encoding="utf-8") as file:
        file_writer = csv.writer(file)
        # Write header
        match parameter_set:
            case ParameterSet.P:
                header = [f"Axis {i + 1} Position (cm)" for i in range(trajectory.dim)]
            case ParameterSet.PT:
                header = ["Time (s)"]
                header += [f"Axis {i + 1} Position (cm)" for i in range(trajectory.dim)]
            case ParameterSet.VT:
                header = ["Time (s)"]
                header += [f"Axis {i + 1} Velocity (cm/s)" for i in range(trajectory.dim)]
            case ParameterSet.PVT:
                header = ["Time (s)"]
                for i in range(trajectory.dim):
                    header += [f"Axis {i} Position (cm)"]
                    header += [f"Axis {i} Velocity (cm/s)"]
        file_writer.writerow(header)
        # Write data
        for time in times:
            position = trajectory.position(time)
            velocity = trajectory.velocity(time)
            match parameter_set:
                case ParameterSet.P:
                    row = position
                case ParameterSet.PT:
                    row = [time]
                    row += position
                case ParameterSet.VT:
                    row = [time]
                    row += velocity
                case ParameterSet.PVT:
                    row = [time]
                    for i in range(trajectory.dim):
                        row += [position[i]]
                        row += [velocity[i]]
            file_writer.writerow(row)


def generate_wave_1d(parameter_set: ParameterSet) -> None:
    """Generate the trajectory for a 1-dimensional wave."""
    # Parameters defining the wave
    period = 10
    amplitude = 10
    num_points = 6
    num_cycles = 2
    times = [i * period * num_cycles / num_points for i in range(num_points)]
    generate_and_write(
        f"{parameter_set.value}/wave_1d.csv", parameter_set, Wave(amplitude, period), times
    )


def generate_spiral_2d(parameter_set: ParameterSet) -> None:
    """Generate the trajectory for a 2-dimensional spiral."""
    # Parameters defining the wave
    period = 10
    amplitude = 10
    num_points = 6
    num_cycles = 2
    times = [i * period * num_cycles / num_points for i in range(num_points)]
    generate_and_write(
        f"{parameter_set.value}/spiral_2d.csv", parameter_set, Spiral(amplitude, period), times
    )


def generate_spiral_3d(parameter_set: ParameterSet) -> None:
    """Generate the trajectory for a 3-dimensional spiral."""
    # Parameters defining the wave
    period = 10
    amplitude = 10
    num_points = 6
    num_cycles = 2
    times = [i * period * num_cycles / num_points for i in range(num_points)]
    generate_and_write(
        f"{parameter_set.value}/spiral_3d.csv",
        parameter_set,
        TranslatingSpiral(amplitude, period),
        times,
    )


def main() -> None:
    """Generate all sample data."""
    for param_set in (ParameterSet.PVT, ParameterSet.PT, ParameterSet.VT, ParameterSet.P):
        generate_wave_1d(param_set)
        generate_spiral_2d(param_set)
        generate_spiral_3d(param_set)


if __name__ == "__main__":
    main()
