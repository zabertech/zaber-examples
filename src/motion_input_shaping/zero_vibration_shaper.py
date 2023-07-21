"""
Contains the ZeroVibrationShaper class for re-use in other code.

Run the file directly to test the class functionality.
"""

# pylint: disable=invalid-name
# Allow short variable names

import math
import numpy as np


class ZeroVibrationShaper:
    """A class for implementing zero vibration input shaping theory."""

    def __init__(self, resonant_frequency: float, damping_ratio: float) -> None:
        """
        Initialize the class.

        :param resonant_frequency: The target vibration resonant frequency in Hz.
        :param damping_ratio: The target vibration damping ratio.
        """
        self.resonant_frequency = resonant_frequency
        self.damping_ratio = damping_ratio
        self.n = 1  # How many periods to wait before starting deceleration.

    @property
    def resonant_frequency(self) -> float:
        """Get the target resonant frequency for input shaping in Hz."""
        return self._resonant_frequency

    @resonant_frequency.setter
    def resonant_frequency(self, value: float) -> None:
        """Set the target resonant frequency for input shaping in Hz."""
        if value <= 0:
            raise ValueError(f"Invalid resonant frequency: {value}. Value must be greater than 0.")

        self._resonant_frequency = value
        self.n = 1  # Reset the value of n because it won't be valid anymore.

    @property
    def resonant_period(self) -> float:
        """Get the target resonant period for input shaping in s."""
        return 1.0 / self.resonant_frequency

    @property
    def damping_ratio(self) -> float:
        """Get the target damping ratio for input shaping."""
        return self._damping_ratio

    @damping_ratio.setter
    def damping_ratio(self, value: float) -> None:
        """Set the target damping ratio for input shaping."""
        if value < 0:
            raise ValueError(
                f"Invalid damping ratio: {value}. Value must be greater than or equal to 0."
            )

        self._damping_ratio = value
        self.n = 1  # Reset the value of n because it won't be valid anymore.

    @property
    def n(self) -> int:
        """Get the number of vibration periods to wait before starting deceleration."""
        return self._n

    @n.setter
    def n(self, value: int) -> None:
        """Set the number of vibration periods to wait before starting deceleration."""
        if value < 1 or value % 1 != 0:
            raise ValueError(f"Invalid number of periods: {value}. Must be a whole number >=1.")

        self._n = value

    def get_impulse_amplitudes(self) -> list[float]:
        """Get the unitless magnitude of both impulses to perform the input shaping."""
        k = math.exp(
            (-2 * math.pi * self.n * self.damping_ratio) / math.sqrt(1 - self.damping_ratio**2)
        )

        a1 = 1 / (1 + k)
        a2 = k / (1 + k)

        return [a1, a2]

    def get_impulse_times(self) -> list[float]:
        """Get the time of both impulses to perform the input shaping in seconds."""
        return [0, self.resonant_period * self.n]

    def get_minimum_acceleration(self, distance: float) -> float:
        """
        Get the minimum acceleration needed to perform the input shaping move.

        :param distance: The distance of the move. Return value will have the same units.
        """
        distance = abs(distance)

        a1, a2 = self.get_impulse_amplitudes()
        t1 = self.get_impulse_times()[1]

        return (
            2 * distance / ((t1**2) * (1 + (a1 / a2)))
        )  # minimum acceleration needed to complete move

    def get_deceleration(self, acceleration: float) -> float:
        """
        Get the trajectory deceleration needed to perform the input shaping move.

        :param acceleration: The trajectory acceleration.
        """
        a1, a2 = self.get_impulse_amplitudes()
        return acceleration * a2 / a1

    def get_maximum_speed(self, distance: float, acceleration: float) -> float:
        """
        Get the trajectory max speed needed to perform the input shaping move.

        :param distance: The trajectory distance for the move.
        :param acceleration: The trajectory acceleration for the move.
        """
        distance = abs(distance)

        t1 = self.get_impulse_times()[1]
        deceleration = self.get_deceleration(acceleration)

        a = (deceleration - acceleration) / (2 * deceleration * acceleration)
        b = -1 * t1
        c = distance

        # Special case when acceleration is equal to deceleration (no damping)
        if a == 0:
            return distance / t1

        return float(max(np.roots([a, b, c])))

    def calculate_n(self, distance: float, acceleration: float, max_speed_limit: float = -1) -> int:
        """
        Calculate the value of n needed to satisfy the input trajectory parameters.

        Based on target frequency and damping ratio.
        All distance units must be the same.

        :param distance: The trajectory distance.
        :param acceleration: The trajectory acceleration.
        :param max_speed_limit: An optional limit to place on maximum trajectory speed in the
        output motion.
        """
        self.n = 1  # always reset to 1

        # We need to increment n if the required acceleration is too high
        while self.get_minimum_acceleration(distance) > acceleration:
            self.n += 1

        # Also do the same check for max speed if a limit is specified
        if max_speed_limit != -1:
            while self.get_maximum_speed(distance, acceleration) > max_speed_limit:
                self.n += 1

        return self.n

    def shape_trapezoidal_motion(
        self, distance: float, acceleration: float, max_speed_limit: float = -1
    ) -> list[float]:
        """
        Calculate trajectory max speed and deceleration needed for input shaping.

        Based on target resonant frequency and damping ratio.
        All distance units must be the same.

        :param distance: The trajectory distance.
        :param acceleration: The trajectory acceleration.
        :param max_speed_limit: An optional limit to place on maximum trajectory speed in the
        output motion.
        """
        distance = abs(distance)
        acceleration = abs(acceleration)

        self.calculate_n(distance, acceleration, max_speed_limit)
        deceleration = self.get_deceleration(acceleration)
        max_speed = self.get_maximum_speed(distance, acceleration)

        return [deceleration, max_speed]


# Example code for using the class.
if __name__ == "__main__":
    shaper = ZeroVibrationShaper(10.0, 0.01)

    DIST = 25.0
    ACCEL = 500.0

    decel, speed = shaper.shape_trapezoidal_motion(DIST, ACCEL)

    print(
        f"Shaped Move 1: Distance: {DIST:.2f}, Acceleration: {ACCEL:.2f}, "
        f"Deceleration: {decel:.2f}, Max Speed: {speed:.2f}"
    )

    decel, speed = shaper.shape_trapezoidal_motion(DIST, ACCEL, 10)

    print(
        f"Shaped Move 2: Distance: {DIST:.2f}, Acceleration: {ACCEL:.2f}, "
        f"Deceleration: {decel:.2f}], Max Speed: {speed:.2f}"
    )
