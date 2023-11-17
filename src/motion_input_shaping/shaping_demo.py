"""This script demonstrates the use of the input shaping classes."""

import time
import sys
from zaber_motion import Units, CommandFailedException, LockstepNotEnabledException
from zaber_motion.ascii import Connection, Axis, Lockstep
from shaped_axis import ShapedAxis
from shaped_axis_stream import ShapedAxisStream
from plant import Plant
from zero_vibration_stream_generator import ShaperType

# ------------------- Script Settings ----------------------

COM_PORT = "COMx"  # The COM port with the connected Zaber device.
DEVICE_INDEX = 0  # The Zaber device index to test.
AXIS_INDEX = 1  # The Zaber axis index to test.
RESONANT_FREQUENCY = 5.07  # Input shaping resonant frequency in Hz.
DAMPING_RATIO = 0.1  # Input shaping damping ratio.
MOVE_DISTANCE = 5  # The move distance in mm to use in relative moves.
PAUSE_TIME = 1  # Amount of time in seconds to pause between moves.
STREAM_SHAPER_TYPE = ShaperType.ZV  # Input shaper type to use for ShapedAxisStream.
LIMITED_MOVE_SPEED = 5  # Speed limit in mm/s to use in demo of moves with speed limit


# ------------------- Script Settings ----------------------


def demo_shaping_class(
    shaped_axis: ShapedAxis | ShapedAxisStream,
    move_rel_distance: float,
    pause_time: float,
    limited_move_speed: float = 5,
) -> None:
    """
    Perform a series of moves to demo usage of ShapedAxis and ShapedAxisStream classes.

    :param shaped_axis: ShapedAxis or ShapedAxisStream class to perform moves with
    :param move_rel_distance: Distance to move in mm for move_relative demo
    :param pause_time: Time to pause between moves in seconds
    :param limited_move_speed: Speed limit in mm/s to apply for speed limiting demo
    """
    print("Performing shaped moves.")
    shaped_axis.move_relative(move_rel_distance, Units.LENGTH_MILLIMETRES, True)
    time.sleep(pause_time)
    shaped_axis.move_relative(-move_rel_distance, Units.LENGTH_MILLIMETRES, True)
    time.sleep(pause_time)

    print("Performing shaped moves with speed limit.")
    shaped_axis.set_max_speed_limit(limited_move_speed, Units.VELOCITY_MILLIMETRES_PER_SECOND)
    shaped_axis.move_relative(move_rel_distance, Units.LENGTH_MILLIMETRES, True)
    time.sleep(pause_time)
    shaped_axis.move_relative(-move_rel_distance, Units.LENGTH_MILLIMETRES, True)
    time.sleep(pause_time)
    shaped_axis.reset_max_speed_limit()

    print("Performing full travel shaped moves.")
    shaped_axis.move_max(True)
    time.sleep(pause_time)
    shaped_axis.move_min(True)

    # If using ShapedAxis, reset the deceleration to undo changes by the shaping algorithm.
    # Deceleration is the only setting that may change.
    if isinstance(shaped_axis, ShapedAxis):
        shaped_axis.reset_deceleration()


if __name__ == "__main__":
    with Connection.open_serial_port(COM_PORT) as connection:
        # Get all the devices on the connection
        device_list = connection.detect_devices()
        print(f"Found {len(device_list)} devices.")

        if len(device_list) < 1:
            print("No devices, exiting.")
            sys.exit(0)

        device = device_list[0]  # Get the first device on the port

        # Check if axis is part of lockstep group
        LOCKSTEP_INDEX = 0
        try:
            num_lockstep_groups_possible = device.settings.get("lockstep.numgroups")
            for group_num in range(1, int(num_lockstep_groups_possible) + 1):
                try:
                    axis_nums = device.get_lockstep(group_num).get_axis_numbers()
                    if AXIS_INDEX in axis_nums:
                        print(f"Axis {AXIS_INDEX} is part of Lockstep group {group_num}.")
                        LOCKSTEP_INDEX = group_num
                        break
                except LockstepNotEnabledException:
                    pass
        except CommandFailedException:
            # Unable to get lockstep.numgroups settings meaning device is not capable of lockstep.
            pass

        zaber_object: Axis | Lockstep
        if LOCKSTEP_INDEX == 0:
            zaber_object = device.get_axis(AXIS_INDEX)
        else:
            zaber_object = device.get_lockstep(LOCKSTEP_INDEX)

        plant_var = Plant(
            RESONANT_FREQUENCY, DAMPING_RATIO
        )  # Initialize a Plant class with the frequency and damping ratio

        # Initialize both input shaping axis classes
        shaped_axis_decel = ShapedAxis(zaber_object, plant_var)
        shaped_axis_stream = ShapedAxisStream(zaber_object, plant_var, STREAM_SHAPER_TYPE)

        if not shaped_axis_decel.is_homed():
            shaped_axis_decel.axis.home()

        print("Performing unshaped moves.")
        shaped_axis_decel.axis.move_absolute(0, Units.LENGTH_MILLIMETRES, True)
        time.sleep(PAUSE_TIME)
        shaped_axis_decel.axis.move_relative(MOVE_DISTANCE, Units.LENGTH_MILLIMETRES, True)
        time.sleep(PAUSE_TIME)
        shaped_axis_decel.axis.move_relative(-MOVE_DISTANCE, Units.LENGTH_MILLIMETRES, True)
        time.sleep(PAUSE_TIME)

        print("Demoing ShapedAxis.")
        try:
            demo_shaping_class(shaped_axis_decel, MOVE_DISTANCE, PAUSE_TIME, LIMITED_MOVE_SPEED)
        except Exception:
            # Reset deceleration in case any of any errors
            shaped_axis_decel.reset_deceleration()
            raise

        print("Demoing ShapedAxisStream.")
        demo_shaping_class(shaped_axis_stream, MOVE_DISTANCE, PAUSE_TIME, LIMITED_MOVE_SPEED)

        print("Complete.")
