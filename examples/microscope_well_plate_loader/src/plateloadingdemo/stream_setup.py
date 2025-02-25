"""This program does one-time setup of a stream for doing the raster scan of a well plate on the microscope."""

import re

from zaber_motion import Library, Measurement
from zaber_motion.ascii import Connection, DigitalOutputAction

from .utilities import MM, TS
from .settings import PORT, SCAN_SPEED
from .well_plates import WELL_PLATES, PLATE_TYPE

D_ON = DigitalOutputAction.ON
D_OFF = DigitalOutputAction.OFF

well_plate = WELL_PLATES[PLATE_TYPE]
row_num = well_plate["rows"] / SCAN_SPEED
col_num = well_plate["columns"] / SCAN_SPEED
pitch = well_plate["pitch"] * SCAN_SPEED
row_start = well_plate["row_offset"]
col_start = well_plate["column_offset"]


# Constants defining the raster scan
dwell_time = 0.1  # [s] pause time at each stop
pin = 1  # DO pin#


def main() -> None:
    with Connection.open_serial_port(PORT) as connection:
        device_list = connection.detect_devices()

        # Find and home the ADR.
        ADR = next((x for x in device_list if re.search("ADR", x.name) is not None), None)
        if not ADR:
            raise ValueError(f"No ADR detected on {PORT}.")

        if not ADR.all_axes.is_homed():
            ADR.all_axes.home(True)

        # Set up the X-Y scan stream.
        stream = ADR.streams.get_stream(1)
        stream.disable()
        stream_buffer = ADR.streams.get_buffer(1)
        stream_buffer.erase()

        # set up stream to store actions to stream buffer 1 and
        # to use the first two axes for unit conversion
        stream.setup_store(stream_buffer, 1, 2)

        for row_count in range(row_num):
            stream.line_absolute(Measurement(col_start, MM), Measurement((row_start + (pitch * row_count)), MM))
            stream.io.set_digital_output(pin, D_ON)  # set DO high
            stream.wait(dwell_time, TS)
            stream.io.set_digital_output(pin, D_OFF)  # set DO low

            for _ in range(col_num):
                stream.line_relative(Measurement(pitch, MM), Measurement(0))
                stream.io.set_digital_output(pin, D_ON)  # set DO high
                stream.wait(dwell_time, TS)
                stream.io.set_digital_output(pin, D_OFF)  # set DO low

        stream.disable()


if __name__ == "__main__":
    main()
