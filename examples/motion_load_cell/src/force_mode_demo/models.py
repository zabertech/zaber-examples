"""Data models for force mode demo."""

from dataclasses import dataclass

import numpy as np


@dataclass
class LoadCellSetup:
    """Load Cell Settings.

    Attributes:
        lc_slope_n_per_v: Load cell calibration lc_slope_n_per_v [N/V].
        lc_offset_v: Load cell calibration lc_offset_v [V].
        lc_max_force_n: Maximum safe load for the load cell [N].
        mcc_analog_in: X-MCC analog input port connected to load cell.
    """

    lc_slope_n_per_v: float  # [N/V]
    lc_offset_v: float  # [V]
    lc_max_force_n: float  # [N]
    mcc_analog_in: int

    def to_force(self, voltage: np.ndarray) -> np.ndarray:
        """Convert voltage (array) to force (array).

        Args:
            voltage: Array of measured voltage values [V].

        Returns:
            np.ndarray: Array of converted force values [N].
        """
        return (voltage - self.lc_offset_v) * self.lc_slope_n_per_v

    def to_voltage(self, force: float) -> float:
        """Convert absolute force to voltage.

        Args:
            force: The force value to convert [N].

        Returns:
            float: The corresponding voltage value [V].
        """
        return (force / self.lc_slope_n_per_v) + self.lc_offset_v

    def to_voltage_delta(self, force_delta: float) -> float:
        """Convert force tolerance (delta) to voltage tolerance (delta).

        Args:
            force_delta: The force tolerance value [N].

        Returns:
            float: The corresponding voltage tolerance value [V].
        """
        return force_delta / self.lc_slope_n_per_v


@dataclass
class DeviceSetup:
    """Controller settings.

    Attributes:
        serial_port: Controller serial port.
        force_axis_index: Controller axis index for the force axis.
        translation_axis_index: Controller axis index for the translation axis.
    """

    serial_port: str
    force_axis_index: int
    translation_axis_index: int
