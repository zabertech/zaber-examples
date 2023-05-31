"""Uses Zaber microscope scanning stages to perform high-throughput imaging.

Supports TDI, Linescan, and Area scan cameras.
"""

from typing import Any
import re
import time

from zaber_motion import Units, Measurement
from zaber_motion.ascii import Connection, Axis, Stream
from numpy.typing import NDArray
import numpy as np

from config import STAGE_TUNING, SCAN_PROTOCOLS, CAMERAS
import utils

# Select our scan configuration and camera
SERIAL_PORT = "COMx"
PROTOCOL = SCAN_PROTOCOLS["continuous_slide"]
CAM = CAMERAS["BFS200S6M"]

MM = Units.LENGTH_MILLIMETRES
UM = Units.LENGTH_MICROMETRES


def main() -> None:
    """Connect to a Zaber microscope and running a high-throughput scanning protocol."""
    with Connection.open_serial_port(SERIAL_PORT) as connection:
        device_list = connection.detect_devices()

        # Find our XY and focus stages
        stage = next(x for x in device_list if re.search("A[DS]R", x.name) is not None)
        try:
            lda = next(x for x in device_list if "LDA" in x.name)
            focus = lda.get_axis(1)
        except StopIteration:
            print("No focus stage available")

        x_axis = stage.get_axis(2)
        y_axis = stage.get_axis(1)

        # Set optimized settings for the XY stage connected
        for param in STAGE_TUNING[stage.name]["non_default_settings"]:
            x_axis.settings.set(*param)
            y_axis.settings.set(*param)
        y_axis.settings.set(
            "accel",
            STAGE_TUNING[stage.name]["accel_lower"],
            Units.ACCELERATION_METRES_PER_SECOND_SQUARED,
        )
        x_axis.settings.set(
            "accel",
            STAGE_TUNING[stage.name]["accel_upper"],
            Units.ACCELERATION_METRES_PER_SECOND_SQUARED,
        )

        def area_mode(stream: Stream, scan_axis: Axis, direction: int, trigger_dist: float) -> None:
            """Add stream segments required for stop-and-shoot imaging."""
            stream.wait(1)  # Force stage to stop
            stream.set_digital_output(1, True)  # Trigger the camera
            stream.wait(max(PROTOCOL["exposure"] / 1000, 1))  # Wait for exposure to complete
            stream.set_digital_output(1, False)  # Turn off trigger
            stream.line_relative_on(
                [scan_axis.axis_number - 1], [Measurement(direction * trigger_dist, MM)]
            )

        def continuous_mode(
            stream: Stream, scan_axis: Axis, direction: int, trigger_dist: float
        ) -> None:
            """Add stream segments required for continuous scan imaging."""
            stream.set_digital_output(1, True)  # Trigger the camera
            stream.line_relative_on(
                [scan_axis.axis_number - 1],  # Move half distance to next point
                [Measurement(direction * trigger_dist / 2, MM)],
            )
            stream.set_digital_output(1, False)  # Turn off trigger
            stream.line_relative_on(
                [scan_axis.axis_number - 1],
                [Measurement(direction * trigger_dist / 2, MM)],
            )

        def generate_snake(
            protocol: dict[str, Any], scan_speed: float, focus_map: NDArray[Any] | None = None
        ) -> None:
            """Set stream buffers for a fast scan.

            Modes:
                -TDI: Linescan using Zaber triggers (must be pre-configured using TDI calculator)
                -continuous: Scanning motion with an area camera
                -area: Stop-and shoot imaging
            Options:
            -Set up a focus map stream for the LDA
            -Can be adapted to non-buffered motion by replacing streams with move_relative()
            """
            # Prepare stage stream buffers
            stream = stage.get_stream(1)
            buf = stage.get_stream_buffer(1)
            stream.disable()
            buf.erase()
            stream.setup_store(buf, 1, 2)
            if focus_map is not None:
                focus_stream = lda.get_stream(1)
                focus_stream.disable()
                buf = lda.get_stream_buffer(1)
                buf.erase()
                focus_stream.setup_store(buf, 1)

            # Determine the fastest scan axis and dimensionality of the scanned grid
            protocol["scanning_speed"] = scanning_speed
            axis, n_scans, frames = utils.optimal_scanning(protocol, CAM, STAGE_TUNING[stage.name])
            mode = protocol["mode"]

            scan_width = CAM["sensor_width"] / protocol["mag"]

            if axis == "Y":
                scan_axis = y_axis
                scan_length = protocol["area"][1]
                stepover = (Measurement(0, MM), Measurement(scan_width, MM))

            else:
                scan_axis = x_axis
                scan_length = protocol["area"][0]
                stepover = (Measurement(scan_width, MM), Measurement(0, MM))

            trigger_dist = CAM["sensor_height"] / protocol["mag"]
            for i in range(n_scans):
                direction = pow(-1, i % 2)
                # Need to move n-1 steps to cover full image
                stream.set_max_speed(scan_speed, Units.VELOCITY_MILLIMETRES_PER_SECOND)
                if mode == "TDI":
                    stream.line_relative_on(
                        [scan_axis.axis_number - 1],
                        [Measurement(direction * scan_length, MM)],
                    )
                for j in range(frames):
                    match mode:
                        case "area":
                            area_mode(stream, scan_axis, direction, trigger_dist)
                        case "continuous":
                            continuous_mode(stream, scan_axis, direction, trigger_dist)

                    if focus_map is not None:
                        # Prepare a focus move
                        z_pos = focus_map[i - 1, j - 1]
                        focus_stream.wait_digital_input(1, True)
                        # Wait for falling edge of exposure active pulse to move the focus
                        focus_stream.wait_digital_input(1, False)
                        focus_stream.line_relative(Measurement(z_pos, UM))

                # End of line turnaround
                # Note: you can also use stream.arc_relative_on() here
                # Arcs are generally slower due to the centrip_accel constraint
                # Arcs add extra travel to the scan which must fit within the stage limits
                if mode != "TDI":
                    stream.set_digital_output(1, True)  # Trigger the camera at the last position

                # Remove the speed limit for the stepover
                stream.set_max_speed(x_axis.settings.get("maxspeed"))

                if i < n_scans - 1:
                    stream.line_relative(*stepover)
                    if focus_map is not None:
                        # Prepare a focus move
                        z_pos = focus_map[i - 1, frames - 1]
                        focus_stream.wait_digital_input(1, True)
                        # Wait for falling edge of exposure active pulse to move the LDA
                        focus_stream.wait_digital_input(1, False)
                        focus_stream.line_relative(Measurement(z_pos, UM))

        def execute_scan(use_focus_map: bool = False) -> float:
            """Call the stored motion profile and run the scanning protocol."""
            print("Starting scan")
            utils.synchronized_move(PROTOCOL["origin"], x_axis, y_axis)
            if PROTOCOL["mode"] == "TDI":
                # Enable triggers
                stage.generic_command("trigger 1 enable")  # Camera trigger
                stage.generic_command("trigger 2 enable")  # Fwd scan direction
                stage.generic_command("trigger 3 enable")  # Reverse scan direction
            live = stage.get_stream(2)
            live.setup_live(1, 2)
            if use_focus_map:
                lda.io.set_digital_output(1, True)  # Used as a power supply for camera IO
                focus.move_absolute(20000, UM)  # Focus starting position. See autofocus example
                focus_stream = lda.get_stream(2)
                focus_stream.setup_live(1)
                focus_stream.call(lda.get_stream_buffer(1))

            start_time = time.time()
            live.call(stage.get_stream_buffer(1))
            x_axis.wait_until_idle()
            y_axis.wait_until_idle()
            delta_t = time.time() - start_time
            return delta_t

        # Compute scanning speed if unspecified
        maxspeed = x_axis.settings.get("maxspeed", Units.VELOCITY_MILLIMETRES_PER_SECOND)
        if PROTOCOL["mode"] == "area":
            scanning_speed = maxspeed
        elif PROTOCOL["scanning_speed"] == 0:
            scanning_speed = min(maxspeed, utils.calculate_scanning_speed(CAM, PROTOCOL))
        else:
            scanning_speed = PROTOCOL["scanning_speed"]

        # Compute and store optimal scan protocol. This only needs to be done ONCE
        # fmap = utils.generate_focus_map(10, 10)
        # np.save("focus_map.npy", fmap)
        generate_snake(PROTOCOL, scanning_speed)

        # Run Scan
        elapsed_time = execute_scan()
        print(f"Time to scan: {elapsed_time:.1f}s")
        print(f'Area rate: {np.prod(PROTOCOL["area"]) / elapsed_time:.1f} mm^2/s')


if __name__ == "__main__":
    main()
