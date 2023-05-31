"""Example script for selecting a filter cube."""
import sys
import time

from zaber_motion.ascii import Connection

SERIAL_PORT = "COMx"

# Define the pocket # for each of your filtersets
FILTER_SETS = {"BFP": 1, "FITC": 2, "Cy3": 3, "TxRed": 4, "Cy7": 5, "Brightfield": 6}


def main() -> None:
    """Connect to a FCR and select a range of filter cubes."""
    with Connection.open_serial_port(SERIAL_PORT) as connection:
        device_list = connection.detect_devices()
        print(f"Found {len(device_list)} devices")
        try:
            device = next(x for x in device_list if "FCR" in x.name)
            cube_changer = device.get_axis(1)
        except StopIteration:
            print("No FCR available")
            sys.exit()

        if not cube_changer.is_homed():
            cube_changer.home()

        def select_cube(cube_name: str) -> None:
            """
            Move to the desired filter cube based on a name.

            :param cube_name: Name of the filter cube to select
            """
            pos = FILTER_SETS[cube_name]
            cube_changer.generic_command("move index " + str(pos))
            cube_changer.wait_until_idle()

        for key, _pos in FILTER_SETS.items():
            print(f"Moving to {key} channel")
            select_cube(key)
            time.sleep(1)


if __name__ == "__main__":
    main()
