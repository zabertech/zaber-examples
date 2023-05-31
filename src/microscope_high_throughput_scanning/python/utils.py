"""Utility functions for generating or computing the required inputs to the scanning script."""

from typing import Any
import math
import numpy as np
from numpy.typing import NDArray
import plotly.graph_objects as go  # type: ignore
from zaber_motion import Units
from zaber_motion.ascii import Axis


def trap_move(dist: float, accel: float, maxspeed: float) -> float:
    """Compute the time taken to complete a motion with a trapezoidal velocity profile."""
    t_1 = maxspeed / accel
    a_dist = min([0.5 * accel * pow(t_1, 2), dist / 2])
    t_2 = (dist - (2 * a_dist)) / maxspeed
    return t_1 + t_2


def optimal_scanning(
    protocol: dict[str, Any], cam: dict[str, Any], stage_tuning: dict[str, Any], overlap: float = 0
) -> tuple[str, int, int]:
    """Determine the fastest scan axis and dimensionality of the scanned grid.

    Estimates the time to complete assuming trapezoidal velocity profiles.
    """
    x_accel = stage_tuning["accel_upper"] * 1000
    y_accel = stage_tuning["accel_lower"] * 1000

    # Always scan perpendicular to the long axis of the sensor (width)
    scan_width = cam["sensor_width"] * (1 - overlap) / protocol["mag"]

    # For TDI cameras a focus move for every trigger is impractical
    if protocol["mode"] != "TDI":
        scan_height = cam["sensor_height"] / protocol["mag"]
    else:
        scan_height = cam["sensor_width"] / protocol["mag"]  # Use the sensor width as approx.

    # X snake
    if protocol["mode"] != "area":
        # Single move across the sample for TDI / continuous
        scan_time = trap_move(protocol["area"][0], x_accel, protocol["scanning_speed"])
    else:
        scan_time = trap_move(scan_height, x_accel, 1000) * math.ceil(
            protocol["area"][0] / scan_height
        )
    n_scans_x = math.ceil(protocol["area"][1] / scan_width)
    stepover_time = trap_move(scan_width, y_accel, 1000)

    snake_x = scan_time * n_scans_x + stepover_time * (n_scans_x - 1)

    # Y snake
    if protocol["mode"] != "area":
        # Single move across the sample for TDI / continuous
        scan_time = trap_move(protocol["area"][1], y_accel, protocol["scanning_speed"])
    else:
        scan_time = trap_move(scan_height, y_accel, 1000) * math.ceil(
            protocol["area"][1] / scan_height
        )
    n_scans_y = math.ceil(protocol["area"][0] / scan_width)
    stepover_time = trap_move(scan_width, x_accel, 1000)

    snake_y = scan_time * n_scans_y + stepover_time * (n_scans_y - 1)

    print(f"Time estimate: {min(snake_y, snake_x):.2f}s")

    if snake_y < snake_x:
        print("Fastest strategy: Y snake")
        n_frames = math.ceil(protocol["area"][1] / scan_height)
        return "Y", n_scans_y, n_frames
    print("Fastest strategy: X snake")
    n_frames = math.ceil(protocol["area"][1] / scan_height)
    return "X", n_scans_x, n_frames


def generate_focus_map(x_points: int, y_points: int, save_path: str = "") -> NDArray[Any]:
    """Generate and display a randomized bumpy focus map for testing.

    Returns an array of focus offsets with alternating direction every row.
    """
    fmap = np.random.randint(low=-5, high=5, size=(x_points, y_points))

    # (Optional) Load a saved map from a numpy array
    if save_path != "":
        try:
            fmap = np.load(save_path)
        except OSError:
            print("Focus map file not found")

    fig = go.Figure(data=[go.Surface(z=fmap)])
    fig.update_layout(
        title="Focus map",
        scene=dict(
            {
                "zaxis": {"nticks": 10, "range": [-50, 50]},
                "xaxis": {"autorange": "reversed"},
                "yaxis": {"autorange": "reversed"},
            }
        ),
    )
    fig.show()
    # Snake traversal of focus array
    snake_fmap = fmap.copy()
    snake_fmap[1::2] = fmap[1::2, ::-1]
    return snake_fmap


def synchronized_move(coord: tuple[float, float], x_axis: Axis, y_axis: Axis) -> None:
    """Move both axes to a target position simultaneously."""
    x_pos, y_pos = coord
    x_axis.move_absolute(x_pos, Units.LENGTH_MILLIMETRES, wait_until_idle=False)
    y_axis.move_absolute(y_pos, Units.LENGTH_MILLIMETRES, wait_until_idle=False)
    x_axis.wait_until_idle()
    y_axis.wait_until_idle()


def calculate_scanning_speed(cam: dict[str, Any], protocol: dict[str, Any]) -> float:
    """Calculate the maximum scanning speed using the parameters of the camera and scan protocol."""
    nyquist_speed = 2 * cam["pixel_um"] / (protocol["exposure"] * protocol["mag"]) * 1000
    exposure_limited = cam["sensor_height"] / (protocol["exposure"] / 1e6)

    max_speed = exposure_limited if protocol["mode"] == "TDI" else nyquist_speed
    print(f"Optimal scanning speed: {max_speed:.1f}mm/s")
    return float(max_speed)
