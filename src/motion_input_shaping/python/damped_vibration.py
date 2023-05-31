"""This file contains the DampedVibration class for re-use in other code."""

# pylint: disable=too-many-instance-attributes, too-many-arguments
# These are not issues here.

import math
import numpy as np


class DampedVibration:
    """Performs the calculations for creating theoretical damped vibration response curves."""

    def __init__(
        self,
        frequency: float = 1,
        damping_ratio: float = 0.1,
        amplitude: float = 1,
        start_time: float = 0,
        offset: float = 0,
    ) -> None:
        """
        Initialize the driving parameters for the curve.

        :param frequency: The vibration resonant frequency in Hz.
        :param damping_ratio: The vibration damping ratio.
        :param amplitude: The initial amplitude of the vibration. Units determine the output units
        of the vibration.
        :param start_time: The vibration starting time in seconds.
        :param offset: The y value about which the amplitude is centered on. Must have the same
        units as amplitude.
        """
        self.frequency = frequency
        self.damping_ratio = damping_ratio
        self.amplitude = amplitude
        self.start_time = start_time
        self.offset = offset

    @property
    def frequency(self) -> float:
        """Get the vibration resonant frequency in Hz."""
        return self._frequency

    @frequency.setter
    def frequency(self, value: float) -> None:
        """Set the vibration resonant frequency in Hz."""
        if value <= 0:
            raise ValueError(f"Invalid frequency: {value}. Value must be greater than 0.")

        self._frequency = value

    @property
    def period(self) -> float:
        """Get the vibration resonant period in s."""
        return 1.0 / self.frequency

    @period.setter
    def period(self, value: float) -> None:
        """Set the vibration resonant period in s."""
        if value <= 0:
            raise ValueError(f"Invalid period: {value}. Value must be greater than 0.")

        self.frequency = 1.0 / value

    @property
    def damping_ratio(self) -> float:
        """Get the vibration damping ratio."""
        return self._damping_ratio

    @damping_ratio.setter
    def damping_ratio(self, value: float) -> None:
        """Set the vibration damping ratio."""
        if value < 0:
            raise ValueError(
                f"Invalid damping ratio: {value}. Value must be greater than or equal to 0."
            )

        self._damping_ratio = value

    @property
    def amplitude(self) -> float:
        """Get the initial vibration amplitude."""
        return self._amplitude

    @amplitude.setter
    def amplitude(self, value: float) -> None:
        """Set the initial vibration amplitude."""
        self._amplitude = value

    @property
    def offset(self) -> float:
        """Get the vibration vertical offset."""
        return self._offset

    @offset.setter
    def offset(self, value: float) -> None:
        """Set the vibration vertical offset."""
        self._offset = value

    @property
    def start_time(self) -> float:
        """Get the vibration start_time in s."""
        return self._start_time

    @start_time.setter
    def start_time(self, value: float) -> None:
        """Set the vibration start_time in s."""
        self._start_time = value

    @property
    def omega(self) -> float:
        """Get the vibration resonant frequency in radian/s."""
        return self.frequency * 2 * math.pi

    @property
    def decay_rate(self) -> float:
        """Get the vibration decay rate in [radian/s]."""
        return self.omega * self.damping_ratio

    def get_exponent_decay(self, time_seconds: float) -> float:
        """
        Get the dimensionless exponential decay of the vibration for a given time.

        :param time_seconds: The relative time in seconds.
        """
        return float(math.e ** (-1 * self.decay_rate * time_seconds))

    def get_magnitude(self, time_x: float) -> float:
        """
        Get the magnitude of the vibration at a given time.

        :param time_x: The absolute time in seconds.
        """
        rel_time = time_x - self.start_time
        return (
            self.amplitude * math.sin(self.omega * rel_time) * self.get_exponent_decay(rel_time)
        ) + self.offset

    def get_plot_points(
        self, number_periods: float, number_points: int
    ) -> tuple[list[float], list[float]]:
        """
        Get a list of times and magnitudes for a given number of vibration periods.

        :param number_periods: The number of vibration periods from the start to return data points
        for.
        :param number_points: The total number of data points to return (determines resolution).
        """
        end_time = self.start_time + number_periods * self.period

        times = list(np.linspace(self.start_time, end_time, num=number_points))
        magnitudes = [self.get_magnitude(t) for t in times]

        return times, magnitudes

    def get_decay_magnitude(self, time_x: float) -> float:
        """
        Get the magnitude of the vibration's exponential decay curve at a given time.

        :param time_x: The absolute time in seconds.
        """
        rel_time = time_x - self.start_time
        return (self.amplitude * self.get_exponent_decay(rel_time)) + self.offset

    def get_decay_plot_points(
        self, number_periods: float, number_points: int
    ) -> tuple[list[float], list[float]]:
        """
        Get a list of times and decay curve magnitudes for a given number of vibration periods.

        :param number_periods: The number of vibration periods from the start to return data points
        for.
        :param number_points: The total number of data points to return (determines resolution).
        """
        end_time = self.start_time + number_periods * self.period

        times = list(np.linspace(self.start_time, end_time, num=number_points))
        magnitudes = [self.get_decay_magnitude(t) for t in times]

        return times, magnitudes
