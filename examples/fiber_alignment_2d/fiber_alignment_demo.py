"""Script to demostrate the use of FiberAlignment2D class.

This sample code is for two Zaber peripherals controlled by an X-MCC controller.
The optical power meter is connected to the same X-MCC through an analog input.
Edit the script settings to fit your setup before running.

This code can be adapted to work for Zaber stages with integrated controllers.
The streamed_spiral_scan() method will not be compatible and should be replaced
with spiral_scan(). The first-light search will be significantly slower.
"""

from zaber_motion import Units
from zaber_motion.ascii import Connection

from fiber_alignment_2d import DeviceAnalogInput, FiberAlignment2D

# ------------------- Script Settings ----------------------

# System Configuration
SERIAL_PORT = "COMx"  # The COM port with the connected Zaber device.
DEVICE_INDEX = 1  # The Zaber device index.
AXIS_1_INDEX = 1  # The Zaber axis index for first axis.
AXIS_2_INDEX = 2  # The Zaber axis index for second axis.
ANALOG_INPUT_INDEX = 1  # The analog input index for power meter signal.
POWER_CONVERSION = 500  # Analog input conversion factor from voltage to power in (eg. uW/V or W/V).
NUM_SAMPLES = 5  # Number of analog input samples to average per reading.

# Search Settings
FIRST_LIGHT_THRESHOLD = 10  # Minimum power required for hill climb algorithm to work reliably.
FIRST_LIGHT_TRIGGER_THRESHOLD = 20  # Power at which to stop scan when using streamed_spiral_scan().
SEARCH_DISTANCE = 0.5  # Distance from starting point to search for first light in mm.
STEP_SIZE = 0.005  # Step size or path spacing to use in first light search in mm.
MIN_STEP_SIZE = 0.0001  # Smallest step size to use in hill climb search in mm.

# Streamed Motion Settings
STREAM_VELOCITY = 2  # Speed at which to perform streamed movement for streamed_spiral_scan in mm/s.
STREAM_ACCEL = 2  # Acceleration at which to perform streamed movement for streamed_spiral_scan in mm/s^2.

# ------------------- Script Settings ----------------------


def main() -> None:
    """Run fiber alignment demo with Zaber stages."""
    with Connection.open_serial_port(SERIAL_PORT) as connection:
        device_list = connection.detect_devices()
        print(f"Found {len(device_list)} devices")
        zaber_device = connection.get_device(DEVICE_INDEX)

        # Initialize axes, inputs, and FiberAlignment2D class.
        zaber_axis_1 = zaber_device.get_axis(AXIS_1_INDEX)
        zaber_axis_2 = zaber_device.get_axis(AXIS_2_INDEX)
        analog_input = DeviceAnalogInput(zaber_device, ANALOG_INPUT_INDEX, POWER_CONVERSION, NUM_SAMPLES)
        fiber_alignment = FiberAlignment2D(zaber_axis_1, zaber_axis_2, analog_input)

        # Change speed and accel for streamed movement.
        fiber_alignment.set_stream_max_speed(STREAM_VELOCITY, Units.VELOCITY_MILLIMETRES_PER_SECOND)
        fiber_alignment.set_stream_max_accel(
            STREAM_ACCEL,
            Units.ACCELERATION_METRES_PER_SECOND_SQUARED,
        )

        # Search for first light.
        # streamed_spiral_scan() is used to a perform high speed first light search and
        # spiral_scan() is used as a backup in case it fails.
        # If adapting this code for integrated devices without support for  streamed motion,
        # only use the spiral_scan().
        print("Searching for first light...")
        first_light_result = fiber_alignment.streamed_spiral_scan(
            FIRST_LIGHT_THRESHOLD,
            FIRST_LIGHT_TRIGGER_THRESHOLD,
            SEARCH_DISTANCE,
            STEP_SIZE,
            Units.LENGTH_MILLIMETRES,
        )
        if not (first_light_result.success):
            # If streamed scan fails, fall back to slower but more reliable step and measure search.
            print("Streamed first light search failed. Trying step and measure search...")
            first_light_result, _ = fiber_alignment.spiral_scan(
                FIRST_LIGHT_THRESHOLD,
                SEARCH_DISTANCE,
                STEP_SIZE,
                Units.LENGTH_MILLIMETRES,
                stop_at_threshold=True,
            )

        # Check that first light serach has succeeded and perform hill-climb optimization
        if first_light_result.success:
            print("Starting hill climb optimization for fine-tuning...")
            # Using pattern_search() for optimization. gradient_search() can be used as an alternative.
            hill_climb_result, _ = fiber_alignment.pattern_search(STEP_SIZE, MIN_STEP_SIZE, Units.LENGTH_MILLIMETRES)

            print("Alignment complete!")
            print(f"  Final Position: [{hill_climb_result.position_1:.5f}, {hill_climb_result.position_2:.5f}]")
            print(f"  Final Signal: {hill_climb_result.signal:.4f}")
        else:
            print("First light above specified threshold was not found.")


if __name__ == "__main__":
    print("Program start.")
    main()
    print("Program end.")
