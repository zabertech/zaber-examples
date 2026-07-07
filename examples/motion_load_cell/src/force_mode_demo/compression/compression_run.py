"""Compression Test run module."""

from zaber_motion.ascii import Axis, Connection
from zaber_motion.exceptions import MovementFailedException

from force_mode_demo.compression import compression_logic
from force_mode_demo.config import LOAD_CELL_CONFIG, XMCC_CONFIG
from force_mode_demo.plot import pos_force_plot

COMPRESSION_CONFIG = compression_logic.CompressionSettings(
    safe_z=123.5,  # Safe height above the part [mm]
    invert_dir=False,  # Invert feedback control direction
    min_pos=126.1,  # Minimum limit for tracking range [mm]
    max_pos=153.6,  # Maximum limit for tracking range [mm]
    approach_speed=3.0,  # Max speed during scanning [mm/s]
    contact_tolerance=0.7,  # Acceptable force error during scanning [N]
    contact_period=10,  # Time error must remain within tolerance during scan [ms]
    stability_tolerance=0.2,  # Acceptable force error during settling [N]
    stability_period=3000,  # Time error must remain within tolerance during settle [ms]
    ki=40,  # PID integral gain (Ki)
    kp=20,  # PID proportional gain (Kp)
    loadcell=LOAD_CELL_CONFIG,
)

COMPRESSION_POS = 41.5

TARGET_FORCE = 15.0  # [N]


def compression_run(
    target_force: float,
    force_axis: Axis,
    config: compression_logic.CompressionSettings,
) -> None:
    """Run the compression test demo with pre-configured settings.

    Initializes the compression test operation, executes the pressing motion, and
    automatically generates a force profile plot. This function is called from
    the main menu interface.

    Args:
        target_force: The target force to apply [N].
        force_axis: The Zaber axis used for force control.
        config: Configuration settings for the compression test demo.
    """
    compression_logic.compression_init(target_force, force_axis, config)
    try:
        pos_data, force_data = compression_logic.compression_mvnt(force_axis, config)
        pos_force_plot(pos_data, force_data)
    except MovementFailedException as e:
        print(f"Movement failed: {e}")
        force_axis.stop()


def compression_main() -> None:
    """Standalone entry point for the compression test demo.

    Establishes a serial connection to the XMCC_CONFIG controller and runs the compression
    test demonstration independently. Useful for testing the compression test
    operation without using the main menu interface.
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

        trans_axis.move_absolute(COMPRESSION_POS, "mm")
        compression_run(TARGET_FORCE, force_axis, COMPRESSION_CONFIG)


if __name__ == "__main__":
    compression_main()
