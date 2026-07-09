"""Surface Mapping logic module."""

from dataclasses import dataclass

import numpy as np
from zaber_motion.ascii import Axis, IoPortType, TriggerAction, TriggerCondition

from force_mode_demo.models import LoadCellSetup
from force_mode_demo.plot import pos_pos_extraction


@dataclass
class MappingSettings:
    """Settings configuration for the Surface Mapping Demo.

    Attributes:
        trans_maxspeed: Translation movement speed during height tracking [mm/s].
        safe_z: Safe z-height for the probe [mm].
        invert_force_dir: Invert feedback control direction.
        min_track_height: Minimum position of the tracking range [mm].
        max_track_height: Maximum position of the tracking range [mm].
        approach_speed: Maximum speed during the scanning stage [mm/s].
        contact_tolerance: Maximum analog input error accepted during scanning [N].
        contact_period: Duration analog input error must be within tolerance during scan [ms].
        stability_tolerance: Maximum analog input error accepted during settling [N].
        stability_period: Duration analog input error must be within tolerance during settle [ms].
        touch_ki: Integral gain term for the PID controller during touching operation.
        touch_kp: Proportional gain term for the PID controller during touching operation.
        track_ki: Integral gain term for the PID controller during tracking operation.
        track_kp: Proportional gain term for the PID controller during tracking operation.
        start_trans_pos: Start position of the height tracking in the translation axis [mm].
        end_trans_pos: End position of the height tracking in the translation axis [mm].
        loadcell: The load cell configuration.
    """

    trans_maxspeed: float
    safe_z: float
    invert_force_dir: bool
    min_track_height: float
    max_track_height: float
    approach_speed: float
    contact_tolerance: float  # [N]
    contact_period: int
    stability_tolerance: float  # [N]
    stability_period: int
    start_touch_height: float
    touch_ki: float
    touch_kp: float
    track_ki: float
    track_kp: float
    start_trans_pos: float
    end_trans_pos: float
    loadcell: LoadCellSetup

    @property
    def contact_tolerance_v(self) -> float:
        """Convert contact tolerance to voltage."""
        return self.loadcell.to_voltage_delta(self.contact_tolerance)

    @property
    def stability_tolerance_v(self) -> float:
        """Convert stability tolerance to voltage."""
        return self.loadcell.to_voltage_delta(self.stability_tolerance)

    @property
    def max_duration(self) -> float:
        """Get the maximum possible duration of the mapping scan in seconds."""
        return abs(self.end_trans_pos - self.start_trans_pos) / self.trans_maxspeed


def mapping_init(
    target_force: float,
    force_axis: Axis,
    trans_axis: Axis,
    settings: MappingSettings,
) -> None:
    """Initialize axes and oscilloscope for the surface mapping demo.

    Configures the oscilloscope to log encoder positions of both axes.
    Configures the motion tracking settings on the force axis based on
    the provided settings to maintain a constant force.

    Args:
        target_force: Target force of load cell.
        force_axis: Zaber axis used for force control (vertical).
        trans_axis: Zaber axis used for translation (horizontal).
        settings: Configuration settings for the surface mapping demo.
    """
    if target_force > settings.loadcell.lc_max_force_n:
        err_msg = (
            f"Target force of {target_force}[N] exceeds maximum force "
            f"of load cell ({settings.loadcell.lc_max_force_n}[N])."
        )
        raise ValueError(err_msg)

    setpoint = settings.loadcell.to_voltage(target_force)

    # Overload trigger to disable device if load cell reading exceeds maximum force (safety cutoff)
    overload_trigger = force_axis.device.triggers.get_trigger(trigger_number=2)
    overload_trigger.fire_when_io(
        IoPortType.ANALOG_INPUT,
        settings.loadcell.mcc_analog_in,
        TriggerCondition.GT,
        settings.loadcell.to_voltage(settings.loadcell.lc_max_force_n),
    )
    overload_trigger.on_fire(TriggerAction.A, force_axis.axis_number, "driver disable")
    overload_trigger.on_fire(TriggerAction.B, trans_axis.axis_number, "driver disable")
    overload_trigger.enable()

    # Set up oscilloscope to log encoder positions
    scope = force_axis.device.oscilloscope
    scope.clear()
    scope.add_channel(force_axis.axis_number, "encoder.pos")
    scope.add_channel(trans_axis.axis_number, "encoder.pos")

    # Calculate optimal timebase: ensure total logging time covers movement duration
    # (with 5% margin).
    timebase = max(0.1, (settings.max_duration * 1000) / scope.get_buffer_size() * 1.05)
    scope.set_timebase(timebase)

    # Configure force tracking parameters
    force_axis.settings.set("motion.tracking.setpoint", setpoint)
    force_axis.settings.set("motion.tracking.ai", settings.loadcell.mcc_analog_in)
    force_axis.settings.set("motion.tracking.dir", int(settings.invert_force_dir))
    force_axis.settings.set("motion.tracking.scan.dir", int(settings.invert_force_dir))
    force_axis.settings.set("motion.tracking.limit.min", settings.start_touch_height, "mm")
    force_axis.settings.set("motion.tracking.limit.max", settings.max_track_height, "mm")
    force_axis.settings.set("motion.tracking.scan.maxspeed", settings.approach_speed, "mm/s")
    force_axis.settings.set("motion.tracking.scan.tolerance", settings.contact_tolerance_v)
    force_axis.settings.set("motion.tracking.scan.period", settings.contact_period, "ms")
    force_axis.settings.set("motion.tracking.settle.tolerance", settings.stability_tolerance_v)
    force_axis.settings.set("motion.tracking.settle.period", settings.stability_period, "ms")

    # Set default values for move scan track once command
    force_axis.settings.set("motion.tracking.scan.offset", 0, "mm")
    force_axis.settings.set("motion.tracking.signal.valid.di", 0)


def set_pid(force_axis: Axis, ki: float, kp: float) -> None:
    """Set PID controller tuning parameters for the force axis.

    Args:
        force_axis: Zaber axis to configure.
        ki: Integral gain term for the PID controller.
        kp: Proportional gain term for the PID controller.
    """
    force_axis.settings.set("motion.tracking.ki", ki)
    force_axis.settings.set("motion.tracking.kp", kp)


def mapping_mvnt(force_axis: Axis, trans_axis: Axis, settings: MappingSettings) -> tuple[np.ndarray, np.ndarray]:
    """Execute the surface mapping movement along a surface and record data.

    First gently touches the surface using a conservative PID tuning. Once
    contact is established, changes to a more responsive PID tuning and moves
    the translation axis to scan across the surface while the force axis
    maintains constant contact.

    Args:
        force_axis: The Zaber axis used for force control (vertical).
        trans_axis: The Zaber axis used for translation (horizontal).
        settings: Configuration settings for the surface mapping demo.

    Returns:
        tuple[np.ndarray, np.ndarray]: The recorded oscilloscope data containing
        encoder positions of both axes.
    """
    scope = force_axis.device.oscilloscope
    overload_trigger = force_axis.device.triggers.get_trigger(trigger_number=2)

    # Move both axes to the starting scan position
    force_axis.move_absolute(settings.safe_z, "mm", velocity=25, velocity_unit="mm/s")
    trans_axis.move_absolute(settings.start_trans_pos, "mm")

    # Apply conservative PID tuning for initial gentle touch
    set_pid(force_axis, settings.touch_ki, settings.touch_kp)

    # Move down until the probe touches the surface
    force_axis.move_absolute(settings.start_touch_height, "mm", velocity=25, velocity_unit="mm/s")
    print("start move scan track once")
    force_axis.generic_command("move scan track once")
    print("Touching start location...")
    force_axis.wait_until_idle()

    force_axis.settings.set("motion.tracking.limit.min", settings.min_track_height, "mm")
    force_axis.settings.set("accel", 0)  # Allowing unbounded acceleration
    # Apply responsive PID tuning for active surface tracking
    set_pid(force_axis, settings.track_ki, settings.track_kp)

    # Activate force tracking to maintain constant contact
    force_axis.generic_command("move track")
    print("Starting location reached, starting to map surface...")

    scope.start()
    trans_axis.move_absolute(
        settings.end_trans_pos,
        "mm",
        velocity=settings.trans_maxspeed,
        velocity_unit="mm/s",
    )
    print("Moving to end location...")
    trans_axis.wait_until_idle()

    scope.stop()
    force_axis.settings.set("accel", 620.7, "mm/s^2")  # Changing accelearation back to default value
    print("End location reached, moving back up...")
    force_axis.move_absolute(settings.safe_z, "mm")
    print("Surface mapping operation completed")

    overload_trigger.disable()

    raw_data = scope.read()
    return pos_pos_extraction(raw_data, force_axis, trans_axis)
