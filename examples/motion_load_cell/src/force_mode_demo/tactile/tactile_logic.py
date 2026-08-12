"""Tactile Profiling logic module."""

from dataclasses import dataclass

import numpy as np
from zaber_motion.ascii import (
    Axis,
    IoPortType,
    TriggerAction,
    TriggerCondition,
)
from zaber_motion.exceptions import MovementInterruptedException

from force_mode_demo.models import LoadCellSetup
from force_mode_demo.plot import pos_force_extraction


@dataclass
class TactileSettings:
    """Settings configuration for the Tactile Profiling Demo.

    Attributes:
        probing_speed: Speed that the probe moves during the probing stage [mm/s].
        safe_z: Safe z-height for the probe [mm].
        start_pos: Position slightly above the switch in the force axis direction [mm].
        bottomout_pos: Position slightly below the switch's fully depressed position [mm].
        bottomout_threshold: Force when load cell triggers bottom out retract [N].
        loadcell: The load cell configuration.
    """

    probing_speed: float
    safe_z: float
    start_pos: float
    bottomout_pos: float
    bottomout_threshold: float  # [N]
    loadcell: LoadCellSetup

    @property
    def bottomout_threshold_v(self) -> float:
        """Convert bottom-out threshold to voltage."""
        return self.loadcell.to_voltage(self.bottomout_threshold)

    @property
    def max_duration(self) -> float:
        """Get the maximum possible duration of the press cycle in seconds."""
        return abs(self.bottomout_pos - self.start_pos) / self.probing_speed


def tactile_init(
    force_axis: Axis,
    settings: TactileSettings,
) -> None:
    """Initialize the force axis, trigger, and oscilloscope for the tactile profiling demo.

    Configures the bottom-out trigger to stop the force axis when the load cell
    reading exceeds a specified threshold. Also configures the oscilloscope to
    log the encoder position and load cell analog input.

    Args:
        force_axis: The Zaber axis used for force control.
        settings: Configuration settings for the tactile profiling demo.
    """
    if settings.bottomout_threshold > settings.loadcell.lc_max_force_n:
        err_msg = (
            f"Target force of {settings.bottomout_threshold}[N] exceeds maximum force "
            f"of load cell ({settings.loadcell.lc_max_force_n}[N])."
        )
        raise ValueError(err_msg)

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

    bottomout_trigger = force_axis.device.triggers.get_trigger(trigger_number=1)

    # Fire trigger when load cell reading exceeds bottom-out threshold
    bottomout_trigger.fire_when_io(
        IoPortType.ANALOG_INPUT,
        settings.loadcell.mcc_analog_in,
        TriggerCondition.GT,
        settings.bottomout_threshold_v,
    )
    bottomout_trigger.on_fire(TriggerAction.A, force_axis.axis_number, "stop")

    # Set up oscilloscope to log encoder position and load cell voltage
    scope = force_axis.device.oscilloscope
    scope.clear()
    scope.add_channel(force_axis.axis_number, "encoder.pos")
    scope.add_io_channel(IoPortType.ANALOG_INPUT, settings.loadcell.mcc_analog_in)

    # Calculate optimal timebase: ensure total logging time covers movement duration.
    timebase = max(0.1, settings.max_duration * 1000 / scope.get_buffer_size())
    scope.set_timebase(timebase)


def tactile_mvnt(force_axis: Axis, settings: TactileSettings) -> tuple[np.ndarray, np.ndarray]:
    """Execute the tactile profiling movement and record data.

    Moves the force axis down to press the switch until the bottom-out trigger
    is activated, then retracts. The oscilloscope logs the displacement and force
    throughout the movement.

    Args:
        force_axis: The Zaber axis used for force control.
        settings: Configuration settings for the tactile profiling demo.

    Returns:
        tuple[np.ndarray, np.ndarray]: A tuple containing two arrays:
            - displacement (relative Z-position in mm)
            - force (measured force in Newtons)
    """
    scope = force_axis.device.oscilloscope
    bottomout_trigger = force_axis.device.triggers.get_trigger(trigger_number=1)
    overload_trigger = force_axis.device.triggers.get_trigger(trigger_number=2)

    print("Running tactile profiling operation...")
    force_axis.move_absolute(settings.start_pos, "mm")

    bottomout_trigger.enable(count=1)
    scope.start()

    # Move down until switch bottoms out (stops motion via trigger)
    try:
        force_axis.move_absolute(
            settings.bottomout_pos,
            "mm",
            velocity=settings.probing_speed,
            velocity_unit="mm/s",
        )
    except MovementInterruptedException:
        print("Switch bottomed out, moving back up")

    scope.stop()
    force_axis.move_absolute(settings.safe_z, "mm")
    overload_trigger.disable()
    print("Tactile profiling operation completed")

    raw_data = scope.read()
    return pos_force_extraction(raw_data, settings.loadcell, force_axis)
