"""Compression Test logic module."""

from dataclasses import dataclass

import numpy as np
from zaber_motion.ascii import Axis, IoPortType, TriggerAction, TriggerCondition

from force_mode_demo.models import LoadCellSetup
from force_mode_demo.plot import pos_force_extraction


@dataclass
class CompressionSettings:
    """Settings configuration for the Compression Test Demo.

    Attributes:
        safe_z: Safe z-height for the probe [mm].
        invert_dir: Invert feedback control direction.
        min_pos: Minimum position of the tracking range [mm].
        max_pos: Maximum position of the tracking range [mm].
        approach_speed: Maximum speed during the scanning stage [mm/s].
        contact_tolerance: Maximum analog input error accepted during scanning [N].
        contact_period: Duration analog input error must be within tolerance during scan [ms].
        stability_tolerance: Maximum analog input error accepted during settling [N].
        stability_period: Duration analog input error must be within tolerance during settle [ms].
        ki: Integral gain term for the PID controller.
        kp: Proportional gain term for the PID controller.
        loadcell: The load cell configuration.
    """

    safe_z: float
    invert_dir: bool
    min_pos: float
    max_pos: float
    approach_speed: float
    contact_tolerance: float  # [N]
    contact_period: int
    stability_tolerance: float  # [N]
    stability_period: int
    ki: float
    kp: float
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
        """Get the maximum possible duration of the compression cycle in seconds."""
        return (self.max_pos - self.min_pos) / self.approach_speed


def compression_init(target_force: float, force_axis: Axis, settings: CompressionSettings) -> None:
    """Initialize the force axis and oscilloscope for the compression test demo.

    Configures the oscilloscope to log the encoder position and load cell analog input.
    Also configures the motion tracking settings on the force axis based on the
    provided settings.

    Args:
        target_force: The target force to apply [N].
        force_axis: The Zaber axis used for force control.
        settings: Configuration settings for the compression test demo.
    """
    print("Initializing Compression Test Demo...")

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
    overload_trigger.enable()

    # Set up oscilloscope to log encoder position and load cell voltage
    scope = force_axis.device.oscilloscope
    scope.clear()
    scope.add_channel(force_axis.axis_number, "encoder.pos")
    scope.add_io_channel(IoPortType.ANALOG_INPUT, settings.loadcell.mcc_analog_in)

    # Calculate optimal timebase: ensure total logging time covers movement duration.
    timebase = max(0.1, settings.max_duration * 1000 / scope.get_buffer_size())
    scope.set_timebase(timebase)

    # Configure force tracking parameters
    force_axis.settings.set("motion.tracking.setpoint", setpoint)
    force_axis.settings.set("motion.tracking.ai", settings.loadcell.mcc_analog_in)
    force_axis.settings.set("motion.tracking.dir", int(settings.invert_dir))
    force_axis.settings.set("motion.tracking.scan.dir", int(settings.invert_dir))
    force_axis.settings.set("motion.tracking.limit.min", settings.min_pos, "mm")
    force_axis.settings.set("motion.tracking.limit.max", settings.max_pos, "mm")
    force_axis.settings.set("motion.tracking.scan.maxspeed", settings.approach_speed, "mm/s")
    force_axis.settings.set("motion.tracking.scan.tolerance", settings.contact_tolerance_v)
    force_axis.settings.set("motion.tracking.scan.period", settings.contact_period, "ms")
    force_axis.settings.set("motion.tracking.settle.tolerance", settings.stability_tolerance_v)
    force_axis.settings.set("motion.tracking.settle.period", settings.stability_period, "ms")
    force_axis.settings.set("motion.tracking.ki", settings.ki)
    force_axis.settings.set("motion.tracking.kp", settings.kp)

    # Set default values for move scan track once command
    force_axis.settings.set("motion.tracking.scan.offset", 0, "mm")
    force_axis.settings.set("motion.tracking.signal.valid.di", 0)


def compression_mvnt(force_axis: Axis, settings: CompressionSettings) -> tuple[np.ndarray, np.ndarray]:
    """Execute the compression test movement and record data.

    Moves the force axis from a safe height down until the specified force
    setpoint is reached and settled upon, then retracts. The entire process
    is recorded by the oscilloscope.

    Args:
        force_axis: The Zaber axis used for force control.
        settings: Configuration settings for the compression test demo.

    Returns:
        tuple[np.ndarray, np.ndarray]: A tuple containing two arrays:
            - displacement (relative Z-position in mm)
            - force (measured force in Newtons)
    """
    scope = force_axis.device.oscilloscope
    overload_trigger = force_axis.device.triggers.get_trigger(trigger_number=2)

    print("Running compression test operation...")
    force_axis.move_absolute(settings.safe_z, "mm")
    scope.start()
    force_axis.generic_command("move scan track once")
    force_axis.wait_until_idle()
    scope.stop()
    print("Compression test complete, retracting...")
    force_axis.move_absolute(settings.safe_z, "mm")

    overload_trigger.disable()
    print("Compression test operation completed")

    raw_data = scope.read()

    return pos_force_extraction(raw_data, settings.loadcell, force_axis)
