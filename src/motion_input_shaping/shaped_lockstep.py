"""
This file contains the ShapedAxis class, which is to be re-used in your code.

Run the file directly to test the class out with a Zaber Device.
"""

# pylint: disable=too-many-arguments
# This is not an issue.

import time
import sys
import numpy as np
from zaber_motion import Units, Measurement
from zaber_motion.ascii import Connection, Lockstep, StreamAxisDefinition, StreamAxisType
from zero_vibration_shaper import ZeroVibrationShaper
from zero_vibration_stream_generator import ZeroVibrationStreamGenerator, ShaperType
from shaper_config import *


class ShapedLockstep(Lockstep):
    """
    A Zaber device axis with extra functions.

    Used for performing moves with input shaping vibration reduction theory.
    """

    def __init__(self, zaber_lockstep: Lockstep, resonant_frequency: float, damping_ratio: float,
                 shaper_config: ShaperConfig) -> None:
        """
        Initialize the class for the specified lockstep group.

        Set a max speed limit to the current maxspeed setting
        so the input shaping algorithm won't exceed that value.

        :param zaber_lockstep: The Zaber Motion Lockstep object
        :param resonant_frequency: The target resonant frequency for shaped moves [Hz]
        :param damping_ratio: The target damping ratio for shaped moves
        """
        # Sanity check if the passed lockstep group has a higher number than the number of lockstep groups on the device.
        if zaber_lockstep.lockstep_group_id > zaber_lockstep.device.settings.get(
            'lockstep.numgroups') or zaber_lockstep is None:
            raise TypeError("Invalid Lockstep class was used to initialized ShapedLockstep.")

        super().__init__(zaber_lockstep.device, zaber_lockstep.lockstep_group_id)
        self._shaper_mode = shaper_config.shaper_mode

        match self._shaper_mode:
            case ShaperMode.DECEL:
                self.shaper = ZeroVibrationShaper(resonant_frequency, damping_ratio)
            case ShaperMode.STREAM:
                self.shaper = ZeroVibrationStreamGenerator(resonant_frequency, damping_ratio,
                                                           shaper_type=shaper_config.settings.shaper_type)
                self.stream = zaber_lockstep.device.get_stream(shaper_config.settings.stream_id)

        self._max_speed_limit = -1.0

        # Get axis numbers that are used so that settings can be changed
        self.axes = list()
        for axis_number in self.get_axis_numbers():
            self.axes.append(zaber_lockstep.device.get_axis(axis_number))

        # Grab the current deceleration so we can reset it back to this value later if we want.
        self._original_deceleration = self.get_setting_from_lockstep_axes("motion.decelonly", Units.NATIVE)

        # Set the speed limit to the device's current maxspeed so it will never be exceeded
        self.reset_max_speed_limit()

    @property
    def resonant_frequency(self) -> float:
        """Get the target resonant frequency for input shaping in Hz."""
        return self.shaper.resonant_frequency

    @resonant_frequency.setter
    def resonant_frequency(self, value: float) -> None:
        """Set the target resonant frequency for input shaping in Hz."""
        self.shaper.resonant_frequency = value

    @property
    def damping_ratio(self) -> float:
        """Get the target damping ratio for input shaping."""
        return self.shaper.damping_ratio

    @damping_ratio.setter
    def damping_ratio(self, value: float) -> None:
        """Set the target damping ratio for input shaping."""
        self.shaper.damping_ratio = value

    def is_homed(self) -> bool:
        """Checks if all axes in lockstep group are homed"""
        for n in range(len(self.axes)):
            if not self.axes[n].is_homed():
                return False
        return True

    def get_setting_from_lockstep_axes(self, setting: str, unit: Units = Units.NATIVE) -> list[float]:
        """
        Gets setting values from axes in the lockstep group

        :param setting: The name of setting
        :param unit: The values will be returned in these units.
        :return: A list of setting values
        """
        values = []
        for axis in self.axes:
            values.append(axis.settings.get(setting, unit))
        return values

    def set_lockstep_axes_setting(self, setting: str, values: list[float], unit: Units = Units.NATIVE) -> None:
        """
        Sets settings for all axes in the lockstep group.

        :param setting: The name of setting
        :param values: A list of values to apply as setting for each axis or a single value to apply to all
        :param unit: The values will be returned in these units.
        """
        if len(values) > 1:
            if len(values) != len(self.axes):
                raise ValueError(f"Length of setting values does not match the number of axes. "
                                 f"The list must either be a single value or match the number of axes")
            for n in range(len(self.axes)):
                self.axes[n].settings.set(setting, values[n], unit)
        else:
            for n in range(len(self.axes)):
                self.axes[n].settings.set(setting, values[0], unit)

    def get_axis_positions(self, unit: Units = Units.NATIVE) -> list[float]:
        """
        Gets positions from axes in the lockstep group

        :param unit: The positions will be returned in these units.
        :return: A list of setting values
        """
        positions = []
        for axis in self.axes:
            positions.append(axis.get_position(unit))
        return positions

    def get_max_speed_limit(self, unit: Units = Units.NATIVE) -> float:
        """
        Get the current velocity limit for which shaped moves will not exceed.

        :param unit: The value will be returned in these units.
        :return: The velocity limit.
        """
        return self.axes[0].settings.convert_from_native_units("maxspeed", self._max_speed_limit, unit)

    def set_max_speed_limit(self, value: float, unit: Units = Units.NATIVE) -> None:
        """
        Set the velocity limit for which shaped moves will not exceed.

        :param value: The velocity limit.
        :param unit: The units of the velocity limit value.
        """
        self._max_speed_limit = self.axes[0].settings.convert_to_native_units("maxspeed", value, unit)

    def reset_max_speed_limit(self) -> None:
        """Reset the velocity limit for shaped moves to the device's existing maxspeed setting."""
        axis_max_speed = self.get_setting_from_lockstep_axes("maxspeed")
        self.set_max_speed_limit(np.min(axis_max_speed))

    def reset_deceleration(self) -> None:
        """Reset the trajectory deceleration to the value stored when the class was created."""
        self.set_lockstep_axes_setting("motion.decelonly", self._original_deceleration, Units.NATIVE)

    def move_relative_shaped(
        self,
        position: float,
        unit: Units = Units.NATIVE,
        wait_until_idle: bool = True,
        acceleration: float = 0,
        acceleration_unit: Units = Units.NATIVE,
    ) -> None:
        """
        Input-shaped relative move using function for specific shaper mode.

        :param position: The amount to move.
        :param unit: The units for the position value.
        :param wait_until_idle: If true the command will hang until the device reaches idle state.
        :param acceleration: The acceleration for the move.
        :param acceleration_unit: The units for the acceleration value.
        """
        match self._shaper_mode:
            case ShaperMode.DECEL:
                self._move_relative_shaped_decel(
                    position,
                    unit,
                    wait_until_idle,
                    acceleration,
                    acceleration_unit,
                )
            case ShaperMode.STREAM:
                self._move_relative_shaped_stream(
                    position,
                    unit,
                    wait_until_idle,
                    acceleration,
                    acceleration_unit,
                )

    def _move_relative_shaped_decel(
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
        position_native = self.axes[0].settings.convert_to_native_units("pos", position, unit)
        accel_native = self.axes[0].settings.convert_to_native_units(
            "accel", acceleration, acceleration_unit
        )

        if acceleration == 0:  # Get the acceleration if it wasn't specified
            accel_native = np.min(self.get_setting_from_lockstep_axes("accel", Units.NATIVE))

        position_mm = self.axes[0].settings.convert_from_native_units(
            "pos", position_native, Units.LENGTH_MILLIMETRES
        )
        accel_mm = self.axes[0].settings.convert_from_native_units(
            "accel", accel_native, Units.ACCELERATION_MILLIMETRES_PER_SECOND_SQUARED
        )

        # Apply the input shaping with all values of the same units
        deceleration_mm, max_speed_mm = self.shaper.shape_trapezoidal_motion(
            position_mm, accel_mm, self.get_max_speed_limit(Units.VELOCITY_MILLIMETRES_PER_SECOND))

        # Check if the target deceleration is different from the current value
        deceleration_native = round(
            self.axes[0].settings.convert_to_native_units(
                "accel", deceleration_mm, Units.ACCELERATION_MILLIMETRES_PER_SECOND_SQUARED
            )
        )

        if np.min(self.get_setting_from_lockstep_axes("motion.decelonly", Units.NATIVE)) != deceleration_native:
            self.set_lockstep_axes_setting("motion.decelonly", [deceleration_native], Units.NATIVE)

        # Perform the move
        super().move_relative(
            position,
            unit,
            wait_until_idle,
            max_speed_mm,
            Units.VELOCITY_MILLIMETRES_PER_SECOND,
            accel_mm,
            Units.ACCELERATION_MILLIMETRES_PER_SECOND_SQUARED,
        )

    def _move_relative_shaped_stream(
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
        position_native = self.axes[0].settings.convert_to_native_units("pos", position, unit)
        accel_native = self.axes[0].settings.convert_to_native_units(
            "accel", acceleration, acceleration_unit
        )

        if acceleration == 0:  # Get the acceleration if it wasn't specified
            accel_native = np.min(self.get_setting_from_lockstep_axes("accel", Units.NATIVE))

        position_mm = self.axes[0].settings.convert_from_native_units(
            "pos", position_native, Units.LENGTH_MILLIMETRES
        )
        accel_mm = self.axes[0].settings.convert_from_native_units(
            "accel", accel_native, Units.ACCELERATION_MILLIMETRES_PER_SECOND_SQUARED
        )

        start_position = super().get_position(Units.LENGTH_MILLIMETRES)

        stream_segments = self.shaper.shape_trapezoidal_motion(
            position_mm, accel_mm, accel_mm, self.get_max_speed_limit(Units.VELOCITY_MILLIMETRES_PER_SECOND)
        )
        self.stream.disable()
        self.stream.setup_live_composite(StreamAxisDefinition(self.lockstep_group_id, StreamAxisType.LOCKSTEP))
        self.stream.cork()
        for segment in stream_segments:
            # Set acceleration making sure it is greater than zero by comparing 1 native accel unit
            if self.axes[0].settings.convert_to_native_units("accel",
                                                             segment.accel,
                                                             Units.ACCELERATION_MILLIMETRES_PER_SECOND_SQUARED) > 1:
                self.stream.set_max_tangential_acceleration(segment.accel,
                                                            Units.ACCELERATION_MILLIMETRES_PER_SECOND_SQUARED)
            else:
                self.stream.set_max_tangential_acceleration(1, Units.NATIVE)

            # Set max speed making sure that it is at least 1 native speed unit
            if self.axes[0].settings.convert_to_native_units("maxspeed",
                                                             segment.speed_limit,
                                                             Units.VELOCITY_MILLIMETRES_PER_SECOND) > 1:
                self.stream.set_max_speed(segment.speed_limit, Units.VELOCITY_MILLIMETRES_PER_SECOND)
            else:
                self.stream.set_max_speed(1, Units.NATIVE)

            # set position for the end of the segment
            self.stream.line_absolute(Measurement(segment.position + start_position, Units.LENGTH_MILLIMETRES))
        self.stream.uncork()

        if wait_until_idle:
            self.stream.wait_until_idle()

    def move_absolute_shaped(
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
        current_position = super().get_position(unit)
        self.move_relative_shaped(
            position - current_position, unit, wait_until_idle, acceleration, acceleration_unit
        )

    def move_max_shaped(
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
        current_axis_positions = self.get_axis_positions(Units.NATIVE)
        end_positions = self.get_setting_from_lockstep_axes("limit.max", Units.NATIVE)
        # Move will be positive so find min relative move
        largest_possible_move = np.min(np.subtract(end_positions, current_axis_positions))
        self.move_relative_shaped(
            largest_possible_move,
            Units.NATIVE,
            wait_until_idle,
            acceleration,
            acceleration_unit,
        )

    def move_min_shaped(
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
        current_axis_positions = self.get_axis_positions(Units.NATIVE)
        end_positions = self.get_setting_from_lockstep_axes("limit.min", Units.NATIVE)
        # Move will be negative so find max relative move
        largest_possible_move = np.max(np.subtract(end_positions, current_axis_positions))
        self.move_relative_shaped(
            largest_possible_move,
            Units.NATIVE,
            wait_until_idle,
            acceleration,
            acceleration_unit,
        )


# Example code for using the class.
if __name__ == "__main__":
    with Connection.open_serial_port("COMx") as connection:
        # Get all the devices on the connection
        device_list = connection.detect_devices()
        print(f"Found {len(device_list)} devices.")

        if len(device_list) < 1:
            print("No devices, exiting.")
            sys.exit(0)

        device = device_list[0]  # Get the first device on the port
        lockstep = device.get_lockstep(
            1
        )  # Get the first lockstep group from the device. This will become the ShapedLockstep.
        shaped_lockstep = ShapedLockstep(
            lockstep, 10, 0.1, ShaperConfig(ShaperMode.DECEL)
        )  # Initialize the ShapedLockstep class with the frequency and damping ratio

        if (
            not shaped_lockstep.is_homed()
        ):  # The ShapedLockstep has all the same functionality as the normal Lockstep class.
            shaped_lockstep.home()

        # Perform some unshaped Moves
        print("Performing unshaped moves.")

        shaped_lockstep.move_absolute(0, Units.LENGTH_MILLIMETRES, True)
        time.sleep(0.2)
        shaped_lockstep.move_relative(5, Units.LENGTH_MILLIMETRES, True)
        time.sleep(0.2)
        shaped_lockstep.move_relative(-5, Units.LENGTH_MILLIMETRES, True)
        time.sleep(1)

        # Perform some shaped Moves
        print("Performing shaped moves.")
        shaped_lockstep.move_relative_shaped(5, Units.LENGTH_MILLIMETRES, True)
        time.sleep(0.2)
        shaped_lockstep.move_relative_shaped(-5, Units.LENGTH_MILLIMETRES, True)
        time.sleep(1)

        # Perform some shaped Moves
        print("Performing shaped moves with speed limit.")
        shaped_lockstep.set_max_speed_limit(5, Units.VELOCITY_MILLIMETRES_PER_SECOND)
        shaped_lockstep.move_relative_shaped(5, Units.LENGTH_MILLIMETRES, True)
        time.sleep(0.2)
        shaped_lockstep.move_relative_shaped(-5, Units.LENGTH_MILLIMETRES, True)
        time.sleep(1)

        # Perform some shaped Moves
        print("Performing full travel shaped moves.")
        shaped_lockstep.reset_max_speed_limit()
        shaped_lockstep.move_max_shaped(True)
        time.sleep(0.2)
        shaped_lockstep.move_min_shaped(True)

        # Reset the deceleration to the original value in case the shaping algorithm changed it.
        # Deceleration is the only setting that may change.
        shaped_lockstep.reset_deceleration()

        print("Complete.")
