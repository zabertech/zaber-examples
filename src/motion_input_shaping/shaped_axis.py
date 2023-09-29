"""
This file contains the ShapedAxis class, which is to be re-used in your code.

Run the file directly to test the class out with a Zaber Device.
"""

# pylint: disable=too-many-arguments
# This is not an issue.

import time
import sys
from zaber_motion import Units, Measurement
from zaber_motion.ascii import Connection, Axis
from zero_vibration_shaper import ZeroVibrationShaper
from zero_vibration_stream_generator import ZeroVibrationStreamGenerator, ShaperType
from shaper_config import *


class ShapedAxis(Axis):
    """
    A Zaber device axis with extra functions.

    Used for performing moves with input shaping vibration reduction theory.
    """

    def __init__(self, zaber_axis: Axis, resonant_frequency: float, damping_ratio: float,
                 shaper_config: ShaperConfig) -> None:
        """
        Initialize the class for the specified axis.

        Set a max speed limit to the current maxspeed setting
        so the input shaping algorithm won't exceed that value.

        :param zaber_axis: The Zaber Motion Axis object
        :param resonant_frequency: The target resonant frequency for shaped moves [Hz]
        :param damping_ratio: The target damping ratio for shaped moves
        """
        # Sanity check if the passed axis has a higher number than the number of axes on the device.
        if zaber_axis.axis_number > zaber_axis.device.axis_count or zaber_axis is None:
            raise TypeError("Invalid Axis class was used to initialized ShapedAxis.")

        super().__init__(zaber_axis.device, zaber_axis.axis_number)
        self._shaper_mode = shaper_config.shaper_mode

        match self._shaper_mode:
            case ShaperMode.DECEL:
                self.shaper = ZeroVibrationShaper(resonant_frequency, damping_ratio)
            case ShaperMode.STREAM:
                self.shaper = ZeroVibrationStreamGenerator(resonant_frequency, damping_ratio,
                                                                shaper_type=shaper_config.settings.shaper_type)
                self.stream = zaber_axis.device.get_stream(shaper_config.settings.stream_id)

        self._max_speed_limit = -1.0

        # Grab the current deceleration so we can reset it back to this value later if we want.
        self._original_deceleration = super().settings.get("motion.decelonly", Units.NATIVE)

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

    def get_max_speed_limit(self, unit: Units = Units.NATIVE) -> float:
        """
        Get the current velocity limit for which shaped moves will not exceed.

        :param unit: The value will be returned in these units.
        :return: The velocity limit.
        """
        return super().settings.convert_from_native_units("maxspeed", self._max_speed_limit, unit)

    def set_max_speed_limit(self, value: float, unit: Units = Units.NATIVE) -> None:
        """
        Set the velocity limit for which shaped moves will not exceed.

        :param value: The velocity limit.
        :param unit: The units of the velocity limit value.
        """
        self._max_speed_limit = super().settings.convert_to_native_units("maxspeed", value, unit)

    def reset_max_speed_limit(self) -> None:
        """Reset the velocity limit for shaped moves to the device's existing maxspeed setting."""
        self.set_max_speed_limit(super().settings.get("maxspeed"))

    def reset_deceleration(self) -> None:
        """Reset the trajectory deceleration to the value stored when the class was created."""
        super().settings.set("motion.decelonly", self._original_deceleration, Units.NATIVE)

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
        position_native = super().settings.convert_to_native_units("pos", position, unit)
        accel_native = super().settings.convert_to_native_units(
            "accel", acceleration, acceleration_unit
        )

        if acceleration == 0:  # Get the acceleration if it wasn't specified
            accel_native = super().settings.get("accel", Units.NATIVE)

        position_mm = super().settings.convert_from_native_units(
            "pos", position_native, Units.LENGTH_MILLIMETRES
        )
        accel_mm = super().settings.convert_from_native_units(
            "accel", accel_native, Units.ACCELERATION_MILLIMETRES_PER_SECOND_SQUARED
        )

        # Apply the input shaping with all values of the same units
        deceleration_mm, max_speed_mm = self.shaper.shape_trapezoidal_motion(
            position_mm, accel_mm, self.get_max_speed_limit(Units.VELOCITY_MILLIMETRES_PER_SECOND)
        )

        # Check if the target deceleration is different from the current value
        deceleration_native = round(
            super().settings.convert_to_native_units(
                "accel", deceleration_mm, Units.ACCELERATION_MILLIMETRES_PER_SECOND_SQUARED
            )
        )

        if super().settings.get("motion.decelonly", Units.NATIVE) != deceleration_native:
            super().settings.set("motion.decelonly", deceleration_native, Units.NATIVE)

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
        position_native = super().settings.convert_to_native_units("pos", position, unit)
        accel_native = super().settings.convert_to_native_units(
            "accel", acceleration, acceleration_unit
        )

        if acceleration == 0:  # Get the acceleration if it wasn't specified
            accel_native = super().settings.get("accel", Units.NATIVE)

        position_mm = super().settings.convert_from_native_units(
            "pos", position_native, Units.LENGTH_MILLIMETRES
        )
        accel_mm = super().settings.convert_from_native_units(
            "accel", accel_native, Units.ACCELERATION_MILLIMETRES_PER_SECOND_SQUARED
        )

        start_position = super().get_position(Units.LENGTH_MILLIMETRES)

        stream_segments = self.shaper.shape_trapezoidal_motion(
            position_mm, accel_mm, accel_mm, self.get_max_speed_limit(Units.VELOCITY_MILLIMETRES_PER_SECOND)
        )
        self.stream.setup_live(self.axis_number)
        self.stream.cork()
        for segment in stream_segments:
            if super().settings.convert_to_native_units(
                    "accel", segment.accel, Units.VELOCITY_MILLIMETRES_PER_SECOND) > 1:
                self.stream.set_max_tangential_acceleration(segment.accel,
                                                            Units.ACCELERATION_MILLIMETRES_PER_SECOND_SQUARED)
            else:
                self.stream.set_max_tangential_acceleration(1, Units.NATIVE)

            if super().settings.convert_to_native_units(
                    "maxspeed", segment.speed_limit, Units.VELOCITY_MILLIMETRES_PER_SECOND) > 1:
                self.stream.set_max_speed(segment.speed_limit, Units.VELOCITY_MILLIMETRES_PER_SECOND)
            else:
                self.stream.set_max_speed(1, Units.NATIVE)

            self.stream.line_absolute(Measurement(segment.position + start_position, Units.LENGTH_MILLIMETRES))
        self.stream.uncork()

        if wait_until_idle:
            self.stream.wait_until_idle()

        self.stream.disable()

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
        current_position = super().get_position(Units.NATIVE)
        end_position = super().settings.get("limit.max", Units.NATIVE)
        self.move_relative_shaped(
            end_position - current_position,
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
        current_position = super().get_position(Units.NATIVE)
        end_position = super().settings.get("limit.min", Units.NATIVE)
        self.move_relative_shaped(
            end_position - current_position,
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
        axis = device.get_axis(
            1
        )  # Get the first axis from the device. This will become the ShapedAxis.
        shaped_axis = ShapedAxis(axis, 10,
                                 0.1, ShaperConfig(ShaperMode.DECEL))  # Initialize the ShapedAxis class with the frequency and damping ratio

        if (
            not shaped_axis.is_homed()
        ):  # The ShapedAxis has all the same functionality as the normal Axis class.
            shaped_axis.home()

        # Perform some unshaped Moves
        print("Performing unshaped moves.")

        shaped_axis.move_absolute(0, Units.LENGTH_MILLIMETRES, True)
        time.sleep(0.2)
        shaped_axis.move_relative(5, Units.LENGTH_MILLIMETRES, True)
        time.sleep(0.2)
        shaped_axis.move_relative(-5, Units.LENGTH_MILLIMETRES, True)
        time.sleep(1)

        # Perform some shaped Moves
        print("Performing shaped moves.")
        shaped_axis.move_relative_shaped(5, Units.LENGTH_MILLIMETRES, True)
        time.sleep(0.2)
        shaped_axis.move_relative_shaped(-5, Units.LENGTH_MILLIMETRES, True)
        time.sleep(1)

        # Perform some shaped Moves
        print("Performing shaped moves with speed limit.")
        shaped_axis.set_max_speed_limit(5, Units.VELOCITY_MILLIMETRES_PER_SECOND)
        shaped_axis.move_relative_shaped(5, Units.LENGTH_MILLIMETRES, True)
        time.sleep(0.2)
        shaped_axis.move_relative_shaped(-5, Units.LENGTH_MILLIMETRES, True)
        time.sleep(1)

        # Perform some shaped Moves
        print("Performing full travel shaped moves.")
        shaped_axis.reset_max_speed_limit()
        shaped_axis.move_max_shaped(True)
        time.sleep(0.2)
        shaped_axis.move_min_shaped(True)

        # Reset the deceleration to the original value in case the shaping algorithm changed it.
        # Deceleration is the only setting that may change.
        shaped_axis.reset_deceleration()

        print("Complete.")
