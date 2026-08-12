"""Plotting utilities for force mode demo."""

# pyright: reportUnknownMemberType=false
import matplotlib.pyplot as plt
import numpy as np
from zaber_motion.ascii import Axis, OscilloscopeData

from force_mode_demo.models import LoadCellSetup


def pos_force_extraction(
    recorded_data: list[OscilloscopeData], loadcell_setup: LoadCellSetup, force_axis: Axis
) -> tuple[np.ndarray, np.ndarray]:
    """Extract position and force data from the oscilloscope data.

    Args:
        recorded_data: List of oscilloscope data records.
        loadcell_setup: Calibration parameters for the load cell.
        force_axis: The Zaber axis used for force measurement.

    Returns:
        tuple[np.ndarray, np.ndarray]: A tuple containing two arrays:
            - position (relative Z-position in mm)
            - force (measured force in Newtons)
    """
    enc_raw = np.array(recorded_data[0].get_data())
    force_raw = np.array(recorded_data[1].get_data())

    conversion_factor = force_axis.settings.convert_from_native_units("pos", 1, "mm")
    pos = (enc_raw - enc_raw[0]) * conversion_factor
    force = loadcell_setup.to_force(force_raw)
    return pos, force


def pos_pos_extraction(
    recorded_data: list[OscilloscopeData], axis1: Axis, axis2: Axis
) -> tuple[np.ndarray, np.ndarray]:
    """Extract position and position data from the oscilloscope data.

    Args:
        recorded_data: List of oscilloscope data records.
        axis1: The first Zaber axis (e.g., vertical).
        axis2: The second Zaber axis (e.g., horizontal).

    Returns:
        tuple[np.ndarray, np.ndarray]: A tuple containing two arrays of
        relative positions in mm for axis1 and axis2 respectively.
    """
    enc1_raw = np.array(recorded_data[0].get_data())
    enc2_raw = np.array(recorded_data[1].get_data())

    conversion_factor1 = axis1.settings.convert_from_native_units("pos", 1, "mm")
    conversion_factor2 = axis2.settings.convert_from_native_units("pos", 1, "mm")

    pos1 = (enc1_raw - enc1_raw[0]) * conversion_factor1
    pos2 = (enc2_raw - enc2_raw[0]) * conversion_factor2
    return pos1, pos2


def pos_force_plot(position: np.ndarray, force: np.ndarray) -> None:
    """Plot encoder vs force data.

    Args:
        position: Array of scaled position data.
        force: Array of converted force data.
    """
    print("Plotting graph...")

    plt.figure(figsize=(12, 8))
    plt.plot(position, force, label="Measured Path", color="blue", linewidth=2)

    plt.title("Force Profile: Displacement (mm) vs. Force (N)", fontsize=14)
    plt.xlabel("Displacement (mm)", fontsize=12)
    plt.ylabel("Force (N)", fontsize=12)
    plt.legend()
    plt.tight_layout()

    plt.show()


def pos_pos_plot(position1: np.ndarray, position2: np.ndarray) -> None:
    """Plot encoder vs encoder data.

    Args:
        position1: Array of scaled position data.
        position2: Array of scaled position data.
    """
    print("Plotting graph...")

    plt.figure(figsize=(12, 8))
    plt.plot(position1, position2, label="Measured Path", color="blue", linewidth=2)

    plt.gca().invert_yaxis()
    plt.title("Position Profile: Position (mm) vs. Position (mm)", fontsize=14)
    plt.xlabel("Position (mm)", fontsize=12)
    plt.ylabel("Position (mm) [inverted axis]", fontsize=12)
    plt.legend()
    plt.tight_layout()

    plt.show()
