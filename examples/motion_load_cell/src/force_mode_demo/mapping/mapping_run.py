"""Surface Mapping run module."""

from zaber_motion.ascii import Axis, Connection
from zaber_motion.exceptions import MovementFailedException

from force_mode_demo.config import LOAD_CELL_CONFIG, XMCC_CONFIG
from force_mode_demo.mapping import mapping_logic
from force_mode_demo.plot import pos_pos_plot

MAPPING_CONFIG = mapping_logic.MappingSettings(
    trans_maxspeed=20.0,  # Translation speed during surface scanning [mm/s]
    safe_z=123.5,  # Safe clearance height [mm]
    invert_force_dir=False,  # Invert feedback control direction
    min_track_height=133.6,  # Minimum limit for tracking range [mm]
    max_track_height=153.6,  # Maximum limit for tracking range [mm]
    approach_speed=1.0,  # Max speed during initial scanning/touching [mm/s]
    contact_tolerance=0.5,  # Acceptable force error during touching [N]
    contact_period=10,  # Time error must remain within tolerance during touch [ms]
    stability_tolerance=0.1,  # Acceptable force error during settling [N]
    stability_period=500,  # Time error must remain within tolerance during settle [ms]
    start_touch_height=149.0,  # Height to start touching at [mm]
    touch_ki=1,  # PID integral gain (Ki) for initial touch
    touch_kp=1,  # PID proportional gain (Kp) for initial touch
    track_ki=40,  # PID integral gain (Ki) for surface tracking
    track_kp=50,  # PID proportional gain (Kp) for surface tracking
    start_trans_pos=78.5,  # Start position for translation scan [mm]
    end_trans_pos=328.5,  # End position for translation scan [mm]
    loadcell=LOAD_CELL_CONFIG,
)

TARGET_FORCE = 5.0  # [N]


def mapping_run(
    target_force: float,
    force_axis: Axis,
    trans_axis: Axis,
    config: mapping_logic.MappingSettings,
) -> None:
    """Run the surface mapping demo with pre-configured settings.

    Initializes the surface mapping operation, executes the surface scanning motion with
    two-phase PID tuning (conservative touch → responsive tracking), and automatically
    generates a 2D surface profile plot. This function is called from the main
    menu interface.

    Args:
        target_force: Target force of load cell [N].
        force_axis: The Zaber axis used for force control (vertical).
        trans_axis: The Zaber axis used for translation (horizontal).
        config: Configuration settings for the surface mapping demo.
    """
    mapping_logic.mapping_init(target_force, force_axis, trans_axis, config)
    try:
        pos_z, pos_x = mapping_logic.mapping_mvnt(force_axis, trans_axis, config)
        pos_pos_plot(pos_x, pos_z)
    except MovementFailedException as e:
        print(f"Movement failed: {e}")
        trans_axis.stop()
        force_axis.stop()


def mapping_main() -> None:
    """Standalone entry point for the surface mapping demo.

    Establishes a serial connection to the XMCC_CONFIG controller and runs the surface
    mapping demonstration independently. Useful for surface scanning operations
    without using the main menu interface.
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

        mapping_run(TARGET_FORCE, force_axis, trans_axis, MAPPING_CONFIG)


if __name__ == "__main__":
    mapping_main()
