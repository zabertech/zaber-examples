"""Tactile Profiling run module."""

from zaber_motion.ascii import Axis, Connection
from zaber_motion.exceptions import MovementFailedException

from force_mode_demo.config import LOAD_CELL_CONFIG, XMCC_CONFIG
from force_mode_demo.plot import pos_force_plot
from force_mode_demo.tactile import tactile_logic

TACTILE_CONFIG = tactile_logic.TactileSettings(
    probing_speed=1.0,  # Probe movement speed [mm/s]
    safe_z=123.5,
    start_pos=143.6,  # Position of the start of the probe [mm]
    bottomout_pos=148.5,  # Target position to guarantee switch bottom-out [mm]
    bottomout_threshold=1.0,  # Force indicating switch has bottomed out [N]
    loadcell=LOAD_CELL_CONFIG,
)

TACTILE_LOCATIONS = [
    364.8,
    383.9,
    403.0,
    422.5,
    441.2,
]  # Location of the switches in the translation axis


def tactile_run(
    force_axis: Axis,
    config: tactile_logic.TactileSettings,
) -> None:
    """Run the tactile profiling demo to test mechanical switches.

    Initializes the tactile profiling operation, moves the probe down until the switch
    bottoms out (detected via trigger), and records the force-displacement data.

    Args:
        force_axis: The Zaber axis used for force control (vertical).
        config: Configuration settings for the tactile profiling demo.
    """
    tactile_logic.tactile_init(force_axis, config)
    try:
        pos, force = tactile_logic.tactile_mvnt(force_axis, config)
        pos_force_plot(pos, force)
    except MovementFailedException as e:
        print(f"Movement failed: {e}")
        force_axis.stop()


def tactile_main() -> None:
    """Standalone entry point for the tactile profiling demo.

    Establishes a serial connection to the XMCC_CONFIG controller and runs the tactile
    profiling demonstration independently, providing a menu to select which switch to test.
    """
    with Connection.open_serial_port(XMCC_CONFIG.serial_port) as connection:
        connection.enable_alerts()
        device = connection.detect_devices()[0]
        force_axis = device.get_axis(XMCC_CONFIG.force_axis_index)
        trans_axis = device.get_axis(XMCC_CONFIG.translation_axis_index)
        all_axes = [force_axis, trans_axis]

        for axis in all_axes:
            if not axis.is_homed():
                axis.home()

        while True:
            switch = input("Enter switch to use for tactile profiling demo (1-5) or 'q' to quit:").lower()
            if switch in ["1", "2", "3", "4", "5"]:
                trans_axis.move_absolute(TACTILE_LOCATIONS[int(switch) - 1], "mm")
                tactile_run(force_axis, TACTILE_CONFIG)
            elif switch == "q":
                print("Exiting tactile profiling demo.")
                break
            else:
                print("Invalid input. Please enter a number between 1 and 5.")


if __name__ == "__main__":
    tactile_main()
