"""
Contains the ZeroVibrationShaper class for re-use in other code.

Run the file directly to test the class functionality.
"""

# pylint: disable=invalid-name
# Allow short variable names

import math
import numpy as np
from plant import Plant


class ZeroVibrationShaper:
    """A class for implementing zero vibration input shaping theory."""

    def __init__(self, plant: Plant) -> None:
        """
        Initialize the class.

        :param plant: The Plant instance defining the system that the shaper is targeting.
        """
        self.plant = plant
        self._n = 1  # How many periods to wait before starting deceleration.

    @property
    def n(self) -> int:
        """Get the number of vibration periods to wait before starting deceleration."""
        return self._n

    def get_impulse_amplitudes(self) -> list[float]:
        """Get the unitless magnitude of both impulses to perform the input shaping."""
        k = math.exp(
            (-2 * math.pi * self._n * self.plant.damping_ratio)
            / math.sqrt(1 - self.plant.damping_ratio**2)
        )

        a1 = 1 / (1 + k)
        a2 = k / (1 + k)

        return [a1, a2]

    def get_impulse_times(self) -> list[float]:
        """Get the time of both impulses to perform the input shaping in seconds."""
        return [0, self.plant.resonant_period * self._n]

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
        self._n = 1  # always reset to 1

        # We need to increment n if the required acceleration is too high
        while self.get_minimum_acceleration(distance) > acceleration:
            self._n += 1

        # Also do the same check for max speed if a limit is specified
        if max_speed_limit != -1:
            while self.get_maximum_speed(distance, acceleration) > max_speed_limit:
                self._n += 1

        return self._n

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
    plant_var = Plant(10.0, 0.01)
    shaper = ZeroVibrationShaper(plant_var)

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
        f"Deceleration: {decel:.2f}, Max Speed: {speed:.2f}"
    )
