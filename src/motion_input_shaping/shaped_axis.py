"""
This file contains the ShapedAxis class, which is to be re-used in your code.

Run the file directly to test the class out with a Zaber Device.
"""

# pylint: disable=too-many-arguments

import numpy as np
from zaber_motion import Units
from zaber_motion.ascii import Axis, Lockstep
from zero_vibration_shaper import ZeroVibrationShaper
from plant import Plant


class ShapedAxis:
    """A Zaber device axis that performs moves with input shaping vibration reduction theory."""

    def __init__(
        self,
        zaber_axis: Axis | Lockstep,
        plant: Plant,
    ) -> None:
        """
        Initialize the class for the specified axis.

        :param zaber_axis: The Zaber Motion Axis or Lockstep object
        :param plant: The Plant instance defining the system that the shaper is targeting.
        """
        if isinstance(zaber_axis, Axis):
            # Sanity check if the passed axis has a higher number than the number of axes on the
            # device.
            if zaber_axis.axis_number > zaber_axis.device.axis_count or zaber_axis is None:
                raise TypeError("Invalid Axis class was used to initialized ShapedAxis.")
        elif isinstance(zaber_axis, Lockstep):
            # Sanity check if the passed lockstep group number exceeds than the number of
            # lockstep groups on the device.
            if (
                zaber_axis.lockstep_group_id > zaber_axis.device.settings.get("lockstep.numgroups")
                or zaber_axis is None
            ):
                raise TypeError("Invalid Lockstep class was used to initialized ShapedAxis.")

        self.axis = zaber_axis

        if isinstance(self.axis, Lockstep):
            # Get axis numbers that are used so that settings can be changed
            self._lockstep_axes = []
            for axis_number in self.axis.get_axis_numbers():
                self._lockstep_axes.append(self.axis.device.get_axis(axis_number))
            self._primary_axis = self._lockstep_axes[0]
        else:
            self._primary_axis = self.axis

        self.shaper = ZeroVibrationShaper(plant)

        self._max_speed_limit = -1.0

        # Grab the current deceleration so we can reset it back to this value later if we want.
        if isinstance(self.axis, Lockstep):
            self._original_deceleration = self.get_setting_from_lockstep_axes(
                "motion.decelonly", Units.NATIVE
            )
        else:
            self._original_deceleration = [self.axis.settings.get("motion.decelonly", Units.NATIVE)]

        # Set the speed limit to the device's current maxspeed so it will never be exceeded
        self.reset_max_speed_limit()

    def get_max_speed_limit(self, unit: Units = Units.NATIVE) -> float:
        """
        Get the current velocity limit for which shaped moves will not exceed.

        :param unit: The value will be returned in these units.
        :return: The velocity limit.
        """
        return self._primary_axis.settings.convert_from_native_units(
            "maxspeed", self._max_speed_limit, unit
        )

    def set_max_speed_limit(self, value: float, unit: Units = Units.NATIVE) -> None:
        """
        Set the velocity limit for which shaped moves will not exceed.

        :param value: The velocity limit.
        :param unit: The units of the velocity limit value.
        """
        self._max_speed_limit = self._primary_axis.settings.convert_to_native_units(
            "maxspeed", value, unit
        )

    def reset_max_speed_limit(self) -> None:
        """Reset the velocity limit for shaped moves to the device's existing maxspeed setting."""
        if isinstance(self.axis, Lockstep):
            self.set_max_speed_limit(min(self.get_setting_from_lockstep_axes("maxspeed")))
        else:
            self.set_max_speed_limit(self.axis.settings.get("maxspeed"))

    def reset_deceleration(self) -> None:
        """Reset the trajectory deceleration to the value stored when the class was created."""
        if isinstance(self.axis, Lockstep):
            self.set_lockstep_axes_setting(
                "motion.decelonly", self._original_deceleration, Units.NATIVE
            )
        else:
            self.axis.settings.set("motion.decelonly", self._original_deceleration[0], Units.NATIVE)

    def is_homed(self) -> bool:
        """Check if all axes in lockstep group are homed."""
        if isinstance(self.axis, Lockstep):
            for axis in self._lockstep_axes:
                if not axis.is_homed():
                    return False
        else:
            if not self.axis.is_homed():
                return False
        return True

    def get_setting_from_lockstep_axes(
        self, setting: str, unit: Units = Units.NATIVE
    ) -> list[float]:
        """
        Get setting values from axes in the lockstep group.

        :param setting: The name of setting
        :param unit: The values will be returned in these units.
        :return: A list of setting values
        """
        values = []
        for axis in self._lockstep_axes:
            values.append(axis.settings.get(setting, unit))
        return values

    def set_lockstep_axes_setting(
        self, setting: str, values: list[float], unit: Units = Units.NATIVE
    ) -> None:
        """
        Set settings for all axes in the lockstep group.

        :param setting: The name of setting
        :param values: A list of values to apply as setting for each axis or a single value to
        apply to all
        :param unit: The values will be returned in these units.
        """
        if len(values) > 1:
            if len(values) != len(self._lockstep_axes):
                raise ValueError(
                    "Length of setting values does not match the number of axes. "
                    "The list must either be a single value or match the number of axes."
                )
            for n, axis in enumerate(self._lockstep_axes):
                axis.settings.set(setting, values[n], unit)
        else:
            for n, axis in enumerate(self._lockstep_axes):
                axis.settings.set(setting, values[0], unit)

    def get_lockstep_axes_positions(self, unit: Units = Units.NATIVE) -> list[float]:
        """
        Get positions from axes in the lockstep group.

        :param unit: The positions will be returned in these units.
        :return: A list of setting values
        """
        positions = []
        for axis in self._lockstep_axes:
            positions.append(axis.get_position(unit))
        return positions

    def move_relative(
        self,
        position: float,
        unit: Units = Units.NATIVE,
        wait_until_idle: bool = True,
        acceleration: float = 0,
        acceleration_unit: Units = Units.NATIVE,
    ) -> None:
        """
        Input-shaped relative move for the target resonant frequency and damping ratio.

        :param position: The amount to move.
        :param unit: The units for the position value.
        :param wait_until_idle: If true the command will hang until the device reaches idle state.
        :param acceleration: The acceleration for the move.
        :param acceleration_unit: The units for the acceleration value.
        """
        # Convert all to values to the same units
        position_native = self._primary_axis.settings.convert_to_native_units("pos", position, unit)
        accel_native = self._primary_axis.settings.convert_to_native_units(
            "accel", acceleration, acceleration_unit
        )

        if acceleration == 0:  # Get the acceleration if it wasn't specified
            if isinstance(self.axis, Lockstep):
                accel_native = min(self.get_setting_from_lockstep_axes("accel", Units.NATIVE))
            else:
                accel_native = self.axis.settings.get("accel", Units.NATIVE)

        position_mm = self._primary_axis.settings.convert_from_native_units(
            "pos", position_native, Units.LENGTH_MILLIMETRES
        )
        accel_mm = self._primary_axis.settings.convert_from_native_units(
            "accel", accel_native, Units.ACCELERATION_MILLIMETRES_PER_SECOND_SQUARED
        )

        # Apply the input shaping with all values of the same units
        deceleration_mm, max_speed_mm = self.shaper.shape_trapezoidal_motion(
            position_mm,
            accel_mm,
            self.get_max_speed_limit(Units.VELOCITY_MILLIMETRES_PER_SECOND),
        )

        # Check if the target deceleration is different from the current value
        deceleration_native = round(
            self._primary_axis.settings.convert_to_native_units(
                "accel", deceleration_mm, Units.ACCELERATION_MILLIMETRES_PER_SECOND_SQUARED
            )
        )

        if isinstance(self.axis, Lockstep):
            if (
                min(self.get_setting_from_lockstep_axes("motion.decelonly", Units.NATIVE))
                != deceleration_native
            ):
                if deceleration_native > 0:
                    self.set_lockstep_axes_setting(
                        "motion.decelonly", [deceleration_native], Units.NATIVE
                    )
                else:
                    self.set_lockstep_axes_setting("motion.decelonly", [1], Units.NATIVE)
        else:
            if self.axis.settings.get("motion.decelonly", Units.NATIVE) != deceleration_native:
                if deceleration_native > 0:
                    self.axis.settings.set("motion.decelonly", deceleration_native, Units.NATIVE)
                else:
                    self.axis.settings.set("motion.decelonly", 1, Units.NATIVE)

        # Perform the move
        self.axis.move_relative(
            position,
            unit,
            wait_until_idle,
            max_speed_mm,
            Units.VELOCITY_MILLIMETRES_PER_SECOND,
            accel_mm,
            Units.ACCELERATION_MILLIMETRES_PER_SECOND_SQUARED,
        )

    def move_absolute(
        self,
        position: float,
        unit: Units = Units.NATIVE,
        wait_until_idle: bool = True,
        acceleration: float = 0,
        acceleration_unit: Units = Units.NATIVE,
    ) -> None:
        """
        Input-shaped absolute move for the target resonant frequency and damping ratio.

        :param position: The position to move to.
        :param unit: The units for the position value.
        :param wait_until_idle: If true the command will hang until the device reaches idle state.
        :param acceleration: The acceleration for the move.
        :param acceleration_unit: The units for the acceleration value.
        """
        current_position = self.axis.get_position(unit)
        self.move_relative(
            position - current_position, unit, wait_until_idle, acceleration, acceleration_unit
        )

    def move_max(
        self,
        wait_until_idle: bool = True,
        acceleration: float = 0,
        acceleration_unit: Units = Units.NATIVE,
    ) -> None:
        """
        Input-shaped move to the max limit for the target resonant frequency and damping ratio.

        :param wait_until_idle: If true the command will hang until the device reaches idle state.
        :param acceleration: The acceleration for the move.
        :param acceleration_unit: The units for the acceleration value.
        """
        if isinstance(self.axis, Lockstep):
            current_axis_positions = self.get_lockstep_axes_positions(Units.NATIVE)
            end_positions = self.get_setting_from_lockstep_axes("limit.max", Units.NATIVE)
            # Move will be positive so find min relative move
            largest_possible_move = np.min(np.subtract(end_positions, current_axis_positions))
        else:
            current_position = self.axis.get_position(Units.NATIVE)
            end_position = self.axis.settings.get("limit.max", Units.NATIVE)
            largest_possible_move = end_position - current_position

        self.move_relative(
            largest_possible_move, Units.NATIVE, wait_until_idle, acceleration, acceleration_unit
        )

    def move_min(
        self,
        wait_until_idle: bool = True,
        acceleration: float = 0,
        acceleration_unit: Units = Units.NATIVE,
    ) -> None:
        """
        Input-shaped move to the min limit for the target resonant frequency and damping ratio.

        :param wait_until_idle: If true the command will hang until the device reaches idle state.
        :param acceleration: The acceleration for the move.
        :param acceleration_unit: The units for the acceleration value.
        """
        if isinstance(self.axis, Lockstep):
            current_axis_positions = self.get_lockstep_axes_positions(Units.NATIVE)
            end_positions = self.get_setting_from_lockstep_axes("limit.min", Units.NATIVE)
            # Move will be negative so find max relative move
            largest_possible_move = np.max(np.subtract(end_positions, current_axis_positions))
        else:
            current_position = self.axis.get_position(Units.NATIVE)
            end_position = self.axis.settings.get("limit.min", Units.NATIVE)
            largest_possible_move = end_position - current_position
        self.move_relative(
            largest_possible_move, Units.NATIVE, wait_until_idle, acceleration, acceleration_unit
        )
