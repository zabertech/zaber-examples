"""A collection of functions for plotting PVT sequence trajectories and paths."""

from matplotlib.axes import Axes
from matplotlib.lines import Line2D
import matplotlib.pyplot as plt
import numpy as np
from zaber_motion.ascii import PvtSequenceData

import pvt

MARKER_SIZE = 6
"""The default marker size for plots."""
MARKER_EDGE_WIDTH = 2
"""The default marker edge width for plots."""
DEFAULT_COLORS: list[str] = plt.rcParams["axes.prop_cycle"].by_key()["color"]
"""A list of default colors."""


def _plot_trajectory(
    axis: Axes,
    x_data: list[float],
    y_data: list[float],
    color: str | None = None,
    label: str | None = None,
) -> Line2D:
    """
    Plot a trajectory such as position or velocity as a continuous line and returns the handle.

    :param axis: The axis to plot on.
    :param x_data: The x-axis data.
    :param y_data: The y-axis data.
    :param color: The line color, or None to choose automatically.
    :param label: The legend-entry label, or None to leave blank.
    """
    return axis.plot(x_data, y_data, color=color, label=label)[0]


def _plot_points(
    axis: Axes,
    x_data: list[float],
    y_data: list[float],
    color: str | None = None,
    label: str | None = None,
) -> Line2D:
    """
    Plot a set of discrete points and returns the handle.

    :param axis: The axis to plot on.
    :param x_data: The x-axis data.
    :param y_data: The y-axis data.
    :param color: The line color, or None to choose automatically.
    :param label: The legend-entry label, or None to leave blank.
    """
    return axis.plot(
        x_data, y_data, "o", mew=MARKER_EDGE_WIDTH, ms=MARKER_SIZE, color=color, label=label
    )[0]


def _plot_discontinuity(
    axis: Axes,
    x_data: list[float],
    y_data: list[float],
    color: str | None = None,
    label: str | None = None,
) -> Line2D:
    """
    Plot a discontinuity and returns the handle.

    :param axis: The axis to plot on.
    :param x_data: The x-axis data.
    :param y_data: The y-axis data.
    :param color: The line color, or None to choose automatically.
    :param label: The legend-entry label, or None to leave blank.
    """
    return axis.plot(
        x_data,
        y_data,
        ":o",
        linewidth=0.5,
        markeredgewidth=1,
        markerfacecolor="None",
        color=color,
        label=label,
    )[0]


def plot_pvt_trajectory(
    sequence: pvt.Sequence,
    num_samples: int | None = None,
    axes: list[Axes] | None = None,
    show: bool = True,
) -> None:
    """
    Plot the position, velocity, and acceleration trajectories of a PVT sequence.

    :param sequence: The PVT sequence to plot.
    :param num_samples: The number of samples to use, or unspecified to use a default value.
    :param axes: The position, velocity, and acceleration axes object to plot onto,
        or None to create new ones.
    :param show: Whether to render the plot at the end of the function.
    """
    # Setup plots
    if axes is None:
        _, axes = plt.subplots(3, 1, sharex=True)
    for axis in axes:
        axis.axhline(0, linewidth=0.5, color="black")
    points = sequence.points

    # Create time array
    if num_samples is None:
        num_samples = 1000
    sampled_times = list(np.linspace(sequence.start_time, sequence.end_time, num_samples))
    point_times = [p.time for p in points]
    axes[2].set_xlabel("Time")

    for dim_index in range(sequence.dim):
        # Set the color for this dimension
        color = DEFAULT_COLORS[dim_index % len(DEFAULT_COLORS)]

        # Plot position
        _plot_trajectory(
            axes[0],
            sampled_times,
            [sequence.position(t)[dim_index] for t in sampled_times],
            color=color,
            label=f"axis {dim_index + 1} trajectory",
        )
        # Continue to use the same color for this dimension
        _plot_points(axes[0], point_times, [p.position[dim_index] for p in points], color)
        axes[0].set_ylabel("Position")

        # Plot velocity
        _plot_trajectory(
            axes[1],
            sampled_times,
            [sequence.velocity(t)[dim_index] for t in sampled_times],
            color,
        )
        _plot_points(axes[1], point_times, [p.velocity[dim_index] for p in points], color)
        axes[1].set_ylabel("Velocity")

        # Plot acceleration in segments since it is not continuous
        # between them
        previous_accel = None
        for i in range(len(point_times) - 1):
            # Plot segment
            segment_times = [point_times[i], point_times[i + 1] - 1e-12]
            segment_accelerations = [sequence.acceleration(t)[dim_index] for t in segment_times]
            _plot_trajectory(axes[2], segment_times, segment_accelerations, color)
            # Plot discontinuity
            if previous_accel is not None:
                _plot_discontinuity(
                    axes[2],
                    [point_times[i]] * 2,
                    [previous_accel, segment_accelerations[0]],
                    color,
                )
            previous_accel = segment_accelerations[1]
        axes[2].set_ylabel("Acceleration")

    # Show the plot
    axes[0].legend(ncol=sequence.dim, bbox_to_anchor=(0.5, 1.05), loc="lower center")
    if show:
        plt.show()


def plot_pvt_path(
    sequence: pvt.Sequence,
    axis_indices: list[int] | None = None,
    num_samples: int | None = None,
    axis: Axes | None = None,
    show: bool = True,
) -> None:
    """
    Plot the 2d or 3d path taken by a PVT sequence in three dimensions.

    :param sequence: The PVT sequence to plot.
    :param axis_indices: The zero-based indices of the PVT sequence data to plot for the x, y,
        and z axes (as applicable).
    :param num_samples: The number of samples to use, or unspecified to use a default value.
    :param axis: The axis object to plot onto, or None to create a new one.
    :param show: Whether to render the plot at the end of the function.
    """
    # General setup
    assert sequence.dim >= 2, "Sequence must have at least two dimensions to plot its path."
    points = sequence.points
    if axis_indices is None:
        # Use at most 3 dimensions
        axis_indices = list(range(min(sequence.dim, 3)))
    else:
        assert (
            2 <= len(axis_indices) <= 3
        ), "Invalid number of indices provided. Can only plot in 2 or 3 dimensions."

    # Setup plots
    if axis is None:
        if sequence.dim == 3:
            axis = plt.figure().add_subplot(projection="3d")
        else:
            axis = plt.figure().add_subplot()

    if sequence.dim == 2:
        axis.axhline(0, linewidth=0.5, color="black")
        axis.axis("equal")
    # Labels
    axis.set_xlabel(f"Axis {axis_indices[0] + 1} Position")
    axis.set_ylabel(f"Axis {axis_indices[1] + 1} Position")
    if sequence.dim > 2:
        axis.set_zlabel(f"Axis {axis_indices[2] + 1} Position")  # type: ignore

    # Create time array
    if num_samples is None:
        num_samples = 1000
    sampled_times = list(np.linspace(sequence.start_time, sequence.end_time, num_samples))

    # Plot position
    sampled_positions = [
        [sequence.position(t)[axis_index] for t in sampled_times] for axis_index in axis_indices
    ]
    line = axis.plot(*sampled_positions, label="generated path")[0]
    point_positions = [[p.position[axis_index] for p in points] for axis_index in axis_indices]
    axis.plot(*point_positions, "o", mew=MARKER_EDGE_WIDTH, ms=MARKER_SIZE, color=line.get_color())

    # Plot velocity arrows
    point_velocities = [[p.velocity[axis_index] for p in points] for axis_index in axis_indices]
    axis.quiver(*point_positions, *point_velocities, zorder=2, color="black")
    # Use a custom handle so we see the arrow in the legend instead of a solid line
    arrow_handle = Line2D(
        [0],
        [0],
        linestyle="",
        color="black",
        marker=r"$\rightarrow$",
        markersize=12,
        markeredgewidth=0.8,
    )

    # Show the plot
    axis.legend(
        ncol=2,
        handles=[line, arrow_handle],
        labels=["generated path", "velocity vector"],
        bbox_to_anchor=(0.5, 1 + 0.05 / 3),
        loc="lower center",
    )
    if show:
        plt.show()


def plot_path_and_trajectory(
    sequence_data: PvtSequenceData,
    times_relative: bool = True,
    axis_indices: list[int] | None = None,
    num_samples: int | None = None,
) -> None:
    """
    Plot the per-axis trajectories and path view on one figure.

    If the sequence only has 1 dimension, this function only plots
    the per-axis trajectories.

    :param sequence: The PVT sequence to plot.
    :param axis_indices: The zero-based indices of the PVT sequence data to plot for the x,
        y, and z axes (as applicable).
    :param num_samples: The number of samples to use, or unspecified to use a default value.
    """
    sequence = pvt.Sequence.from_sequence_data(sequence_data, times_relative)
    # Defer to plot_trajectory if sequence has only one dimension
    if sequence.dim == 1:
        plot_pvt_trajectory(sequence, num_samples, show=True)
        return

    # Setup combined figure
    fig = plt.figure(constrained_layout=True)
    fig.set_figwidth(fig.get_figheight() * 2)

    # Set the width ratio of the per-axis trajectory and
    # 2-d or 3-d path subplots
    trajectory_ratio = 3
    path_ratio = 3
    gs = fig.add_gridspec(3, trajectory_ratio + path_ratio)

    # Create subplots
    subplots: dict[str, Axes] = {
        "TopLeft": fig.add_subplot(gs[0, :trajectory_ratio]),
        "MiddleLeft": fig.add_subplot(gs[1, :trajectory_ratio]),
        "BottomLeft": fig.add_subplot(gs[2, :trajectory_ratio]),
        "Right": fig.add_subplot(
            gs[:, trajectory_ratio:], projection="3d" if sequence.dim > 2 else None
        ),
    }
    for subplot_key in ("TopLeft", "MiddleLeft"):
        # Remove ticks since they are shared with BottomLeft
        subplots[subplot_key].set_xticks([])

    # Plot the path and trajectories
    plot_pvt_trajectory(
        sequence,
        num_samples=num_samples,
        axes=[
            subplots[key].axes for key in ("TopLeft", "MiddleLeft", "BottomLeft")  # type: ignore
        ],
        show=False,
    )
    plot_pvt_path(
        sequence,
        num_samples=num_samples,
        axis=subplots["Right"].axes,  # type: ignore
        axis_indices=axis_indices,
        show=False,
    )
    plt.show()
