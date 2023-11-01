"""
This file contains the ShapedAxisStream class, which is to be re-used in your code.

Run the file directly to test the class out with a Zaber Device.
"""

# pylint: disable=too-many-arguments

import time
import sys
import numpy as np
from zaber_motion import Units, Measurement
from zaber_motion.ascii import Connection, Axis, Lockstep, StreamAxisDefinition, StreamAxisType
from zero_vibration_stream_generator import ZeroVibrationStreamGenerator, ShaperType
from plant import Plant


class ShapedAxisStream:
    """A Zaber device axis that performs streamed moves with input shaping vibration reduction."""

    def __init__(
        self,
        zaber_axis: Axis | Lockstep,
        plant: Plant,
        shaper_type: ShaperType = ShaperType.ZV,
        stream_id: int = 1,
    ) -> None:
        """
        Initialize the class for the specified axis.

        :param zaber_axis: The Zaber Motion Axis or Lockstep object
        :param plant: The Plant instance defining the system that the shaper is targeting
        :shaper_type: Type of input shaper to use
        :stream_id: Stream number on device to use to perform moves
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
                raise TypeError("Invalid Lockstep class was used to initialized ShapedLockstep.")

        self.axis = zaber_axis

        if isinstance(self.axis, Lockstep):
            # Get axis numbers that are used so that settings can be changed
            self._lockstep_axes = []
            for axis_number in self.axis.get_axis_numbers():
                self._lockstep_axes.append(self.axis.device.get_axis(axis_number))
            self._primary_axis = self._lockstep_axes[0]
        else:
            self._primary_axis = self.axis

        self.shaper = ZeroVibrationStreamGenerator(plant, shaper_type)
        self.stream = zaber_axis.device.get_stream(stream_id)

        self._max_speed_limit = -1.0

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
        decel_native = accel_native

        if acceleration == 0:  # Get the acceleration and deceleration if it wasn't specified
            if isinstance(self.axis, Lockstep):
                accel_native = min(self.get_setting_from_lockstep_axes("accel", Units.NATIVE))
                decel_native = min(self.get_setting_from_lockstep_axes("motion.decelonly", Units.NATIVE))
            else:
                accel_native = self.axis.settings.get("accel", Units.NATIVE)
                decel_native = self.axis.settings.get("motion.decelonly", Units.NATIVE)

        position_mm = self._primary_axis.settings.convert_from_native_units(
            "pos", position_native, Units.LENGTH_MILLIMETRES
        )
        accel_mm = self._primary_axis.settings.convert_from_native_units(
            "accel", accel_native, Units.ACCELERATION_MILLIMETRES_PER_SECOND_SQUARED
        )
        decel_mm = self._primary_axis.settings.convert_from_native_units(
            "accel", decel_native, Units.ACCELERATION_MILLIMETRES_PER_SECOND_SQUARED
        )

        start_position = self.axis.get_position(Units.LENGTH_MILLIMETRES)

        if isinstance(self.shaper, ZeroVibrationStreamGenerator):
            stream_segments = self.shaper.shape_trapezoidal_motion(
                position_mm,
                accel_mm,
                decel_mm,
                self.get_max_speed_limit(Units.VELOCITY_MILLIMETRES_PER_SECOND),
            )
        else:
            raise TypeError(
                "_move_relative_stream method requires a shaper to be an instance of "
                "ZeroVibrationStreamGenerator class."
            )

        self.stream.disable()
        if isinstance(self.axis, Lockstep):
            self.stream.setup_live_composite(
                StreamAxisDefinition(self.axis.lockstep_group_id, StreamAxisType.LOCKSTEP)
            )
        else:
            self.stream.setup_live(self.axis.axis_number)
        self.stream.cork()
        for segment in stream_segments:
            # Set acceleration making sure it is greater than zero by comparing 1 native accel unit
            if (
                self._primary_axis.settings.convert_to_native_units(
                    "accel", segment.accel, Units.ACCELERATION_MILLIMETRES_PER_SECOND_SQUARED
                )
                > 1
            ):
                self.stream.set_max_tangential_acceleration(
                    segment.accel, Units.ACCELERATION_MILLIMETRES_PER_SECOND_SQUARED
                )
            else:
                self.stream.set_max_tangential_acceleration(1, Units.NATIVE)

            # Set max speed making sure that it is at least 1 native speed unit
            if (
                self._primary_axis.settings.convert_to_native_units(
                    "maxspeed", segment.speed_limit, Units.VELOCITY_MILLIMETRES_PER_SECOND
                )
                > 1
            ):
                self.stream.set_max_speed(
                    segment.speed_limit, Units.VELOCITY_MILLIMETRES_PER_SECOND
                )
            else:
                self.stream.set_max_speed(1, Units.NATIVE)

            # set position for the end of the segment
            self.stream.line_absolute(
                Measurement(segment.position + start_position, Units.LENGTH_MILLIMETRES)
            )
        self.stream.uncork()

        if wait_until_idle:
            self.stream.wait_until_idle()

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


# Example code for using the class.
if __name__ == "__main__":
    AXIS_INDEX = 1  # The Zaber axis index to test.
    RESONANT_FREQUENCY = 10  # Input shaping resonant frequency in Hz.
    DAMPING_RATIO = 0.1  # Input shaping damping ratio.

    with Connection.open_serial_port("COMx") as connection:
        # Get all the devices on the connection
        device_list = connection.detect_devices()
        print(f"Found {len(device_list)} devices.")

        if len(device_list) < 1:
            print("No devices, exiting.")
            sys.exit(0)

        device = device_list[0]  # Get the first device on the port

        # Check if axis is part of lockstep group
        LOCKSTEP_INDEX = 0
        num_lockstep_groups_possible = device.settings.get("lockstep.numgroups")
        for group_num in range(1, int(num_lockstep_groups_possible) + 1):
            axis_nums = device.get_lockstep(group_num).get_axis_numbers()
            if AXIS_INDEX in axis_nums:
                print(f"Axis {AXIS_INDEX} is part of Lockstep group {group_num}.")
                LOCKSTEP_INDEX = group_num
                break

        zaber_object: Axis | Lockstep
        if LOCKSTEP_INDEX == 0:
            zaber_object = device.get_axis(AXIS_INDEX)
        else:
            zaber_object = device.get_lockstep(LOCKSTEP_INDEX)

        plant_var = Plant(
            RESONANT_FREQUENCY, DAMPING_RATIO
        )  # Initialize a Plant class with the frequency and damping ratio
        shaped_axis = ShapedAxisStream(zaber_object, plant_var, ShaperType.ZV)

        print("Performing unshaped moves.")
        shaped_axis.axis.move_absolute(0, Units.LENGTH_MILLIMETRES, True)
        time.sleep(0.2)
        shaped_axis.axis.move_relative(5, Units.LENGTH_MILLIMETRES, True)
        time.sleep(0.2)
        shaped_axis.axis.move_relative(-5, Units.LENGTH_MILLIMETRES, True)
        time.sleep(1)

        print("Performing shaped moves.")
        shaped_axis.move_relative(5, Units.LENGTH_MILLIMETRES, True)
        time.sleep(0.2)
        shaped_axis.move_relative(-5, Units.LENGTH_MILLIMETRES, True)
        time.sleep(1)

        print("Performing shaped moves with speed limit.")
        shaped_axis.set_max_speed_limit(5, Units.VELOCITY_MILLIMETRES_PER_SECOND)
        shaped_axis.move_relative(5, Units.LENGTH_MILLIMETRES, True)
        time.sleep(0.2)
        shaped_axis.move_relative(-5, Units.LENGTH_MILLIMETRES, True)
        time.sleep(1)

        print("Performing full travel shaped moves.")
        shaped_axis.reset_max_speed_limit()
        shaped_axis.move_max(True)
        time.sleep(0.2)
        shaped_axis.move_min(True)

        print("Complete.")
