"""Example script for scanning ANSI standard microplates."""

from typing import Any, TypedDict
from random import shuffle
from zaber_motion.ascii import Connection
from zaber_motion import Units

SERIAL_PORT = "COMx"  # Change to appropriate comm port
DEVICE_NUMBER = 1  # The order of the device in the device chain


class WellPlate(TypedDict):
    """Parameters of a well plate."""

    rows: int  # Number of rows of a well plate (short-side)
    columns: int  # Number of columns of a well plate (long-side)
    pitch: float  # Distance in mm between center of two adjacent wells
    row_offset: float  # Distance in mm between center of well A1 and top edge of plate
    column_offset: float  # Distance in mm between center of well A1 and left edge of plate


WELL_PLATE: dict[str, WellPlate] = {
    "96": {
        "rows": 8,
        "columns": 12,
        "pitch": 9.00,
        "row_offset": 17.86,
        "column_offset": 10.16,
    },
    "384": {
        "rows": 16,
        "columns": 24,
        "pitch": 4.50,
        "row_offset": 8.99,
        "column_offset": 12.13,
    },
    "1536": {
        "rows": 32,
        "columns": 48,
        "pitch": 2.25,
        "row_offset": 7.87,
        "column_offset": 11.01,
    },
}

ROW_HOME_OFFSET: float = 0.00  # mm
COLUMN_HOME_OFFSET: float = 0.00  # mm
PLATE_TYPE: str = "96"  # "96" or "384" or "1536"


def do_task(*args: Any) -> None:
    """User editable function to do a task at each well plate."""
    print(f"Do task at well plate position using arguments: {args}")


def main() -> None:
    """Connect to Zaber Device and send commands."""
    well_plate = WELL_PLATE[PLATE_TYPE]

    rows = well_plate["rows"]
    columns = well_plate["columns"]
    pitch = well_plate["pitch"]
    row_offset = well_plate["row_offset"]
    column_offset = well_plate["column_offset"]

    print(f"Traversing {PLATE_TYPE} well plate")

    with Connection.open_serial_port(SERIAL_PORT) as connection:
        device_list = connection.detect_devices()
        print(f"Found {len(device_list)} devices")
        device = device_list[DEVICE_NUMBER]
        axis_lower = device.get_axis(1)
        axis_upper = device.get_axis(2)

        print("Homing both axes simultaneously")
        axis_lower.home(wait_until_idle=False)
        axis_upper.home(wait_until_idle=False)
        axis_lower.wait_until_idle()
        axis_upper.wait_until_idle()

        def move_to(row: int, column: int) -> None:
            """Move both axes of stage to position simultaneously."""
            axis_lower.move_absolute(
                ROW_HOME_OFFSET + row_offset + row * pitch,
                Units.LENGTH_MILLIMETRES,
                wait_until_idle=False,
            )
            axis_upper.move_absolute(
                COLUMN_HOME_OFFSET + column_offset + column * pitch,
                Units.LENGTH_MILLIMETRES,
                wait_until_idle=False,
            )
            axis_lower.wait_until_idle()
            axis_upper.wait_until_idle()

        def sequential() -> None:
            print("sequential")
            for row in range(rows):
                for column in range(columns):
                    move_to(row, column)
                    do_task(row, column)

        def fastest() -> None:
            print("fastest")
            for row in range(rows):
                if row % 2 == 0:
                    for column in range(columns):
                        move_to(row, column)
                        do_task(row, column)
                else:
                    for column in reversed(range(columns)):
                        move_to(row, column)
                        do_task(row, column)

        def random_access() -> None:
            print("random_access")
            position_list = []
            for row in range(rows):
                for column in range(columns):
                    position_list.append((row, column))
            shuffle(position_list)
            for row, column in position_list:
                move_to(row, column)
                do_task(row, column)

        # Execute each of the algorithms and traverse well plates
        sequential()
        fastest()
        random_access()


if __name__ == "__main__":
    main()
