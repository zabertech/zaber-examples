"""Main entry point module."""

from zaber_motion.ascii import Axis, Connection

from force_mode_demo.compression import compression_run
from force_mode_demo.config import XMCC_CONFIG
from force_mode_demo.mapping import mapping_run
from force_mode_demo.tactile import tactile_run


def run_demo_menu(z_axis: Axis, x_axis: Axis) -> None:
    """Run the interactive command-line menu to select a demonstration.

    Args:
        z_axis: The Zaber axis used for force control (vertical).
        x_axis: The Zaber axis used for translation (horizontal).
    """
    while True:
        mode = input(
            "Tactile Profiling demo ('p')\nCompression Test demo ('c')\nSurface Mapping demo ('m')\nQuit ('q')\nInput: "
        ).lower()

        if mode == "p":
            # Tactile Profiling Demo loop
            while True:
                switch = input("Enter switch to use for tactile profiling demo (1-5) or 'q' to quit:").lower()
                if switch in ["1", "2", "3", "4", "5"]:
                    x_axis.move_absolute(tactile_run.TACTILE_LOCATIONS[int(switch) - 1], "mm")
                    tactile_run.tactile_run(z_axis, tactile_run.TACTILE_CONFIG)
                elif switch == "q":
                    print("Exiting tactile profiling demo.")
                    break
                else:
                    print("Invalid input. Please enter a number between 1 and 5.")

        # Compression Test Demo
        elif mode == "c":
            x_axis.move_absolute(compression_run.COMPRESSION_POS, "mm")
            compression_run.compression_run(compression_run.TARGET_FORCE, z_axis, compression_run.COMPRESSION_CONFIG)

        # Surface Mapping Demo
        elif mode == "m":
            mapping_run.mapping_run(mapping_run.TARGET_FORCE, z_axis, x_axis, mapping_run.MAPPING_CONFIG)

        elif mode == "q":
            print("Exiting demo.")
            break
        else:
            print("Invalid input. Please enter 'p', 'c', 'm', or 'q'.")


def main() -> None:
    """Run the main entry point for the force mode demo application.

    This function establishes a connection with the X-MCC controller, homes
    the necessary axes, and launches the interactive demo menu.
    """
    with Connection.open_serial_port(XMCC_CONFIG.serial_port) as connection:
        connection.enable_alerts()
        device = connection.detect_devices()[0]
        z_axis = device.get_axis(XMCC_CONFIG.force_axis_index)
        x_axis = device.get_axis(XMCC_CONFIG.translation_axis_index)
        all_axes = [z_axis, x_axis]

        for axis in all_axes:
            if not axis.is_homed():
                axis.home()

        run_demo_menu(z_axis, x_axis)


if __name__ == "__main__":
    main()
