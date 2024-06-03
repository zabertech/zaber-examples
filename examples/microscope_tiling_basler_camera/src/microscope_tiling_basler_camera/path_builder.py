"""PathBuilder module."""

import numpy as np
from numpy.typing import NDArray
from zaber_motion import Units
from .example_util import (
    convert_length_to_microns,
    convert_point_to_microns,
)


class PathBuilder:
    """PathBuilder provides functionality for generating paths for camera tiling."""

    MotionPath = list[list[tuple[float, float]]]

    def __init__(
        self,
        pixel_w_um: float,
        pixel_h_um: float,
        camera_rotation: float,
        cam_frame_width: float,
        cam_frame_height: float,
    ):
        """Construct PathBuilder instance."""
        self._pixel_w_um = pixel_w_um
        self._pixel_h_um = pixel_h_um
        self._rotation = camera_rotation
        self._rotation_matrix_2d = np.array(
            [
                [np.cos(camera_rotation), -np.sin(camera_rotation)],
                [np.sin(camera_rotation), np.cos(camera_rotation)],
            ]
        )
        self._frame_width = cam_frame_width
        self._frame_height = cam_frame_height

    def get_path_snake(
        self,
        top_left: NDArray[np.float64],
        bottom_right: NDArray[np.float64],
        units: Units,
        overlap_h: float,
        overlap_v: float,
    ) -> MotionPath:
        """
            Generate snaking grid path from top left to bottom right point.

            Each path point overlaps with its neighbouring tiles by overlap_h and overlap_v
            percentage. The path is a 2d list where each row of points is a horizontal row
            of the path.

        Args:
            top_left: top left corner of tiling region
            bottom_right: bottom right corner of tiling region
            units: units of measurement for top_left and bottom_right (must be LENGTH)
            overlap_h: desired horizontal overlap between images (decimal percentage)
            overlap_v: desired vertical overlap between images (decimal percentage)
        """
        frame_width_um: float = self._pixel_w_um * self._frame_width
        frame_height_um: float = self._pixel_h_um * self._frame_height
        sample_area_width_um: float = convert_length_to_microns(
            bottom_right[0] - top_left[0], units
        )
        sample_area_height_um: float = convert_length_to_microns(
            top_left[1] - bottom_right[1], units
        )

        # get num steps and compute horizontal and vertical coverage
        step_x_um: float = (1.0 - overlap_h) * frame_width_um
        step_y_um: float = (1.0 - overlap_v) * frame_height_um
        step_y_um = step_y_um / np.cos(self._rotation)  # adjust y step with rotation of camera
        steps_x, coverage_x = PathBuilder.get_steps_and_coverage(step_x_um, sample_area_width_um)
        steps_y, coverage_y = PathBuilder.get_steps_and_coverage(step_y_um, sample_area_height_um)

        top_left_microns: NDArray[np.float64] = convert_point_to_microns(top_left, units)
        bottom_right_microns: NDArray[np.float64] = convert_point_to_microns(bottom_right, units)
        x_left_um = top_left_microns[0] - (coverage_x - sample_area_width_um) / 2.0
        x_right_um = bottom_right_microns[0] + (coverage_x - sample_area_width_um) / 2.0
        y_top_um = top_left_microns[1] + (coverage_y - sample_area_height_um) / 2.0

        path: PathBuilder.MotionPath = []
        for y in range(steps_y):
            y_pos = y_top_um - y * step_y_um
            grid_row: list[tuple[float, float]] = []
            for x in range(steps_x):
                x_pos = 0.0
                if not y & 1:
                    x_pos = x_left_um + x * step_x_um
                else:
                    x_pos = x_right_um - x * step_x_um

                step_vec: NDArray[np.float64] = np.array([x_pos - x_left_um, 0.0])
                step_vec = self._rotation_matrix_2d @ step_vec
                grid_row.append((x_left_um + step_vec[0], y_pos + step_vec[1]))
            path.append(grid_row)
        return path

    @staticmethod
    def get_steps_and_coverage(step_um: float, distance_um: float) -> tuple[int, float]:
        """
            Get appropriate number of step_um size steps to cover distance_um.

        Args:
            step_um: step size in microns
            distance_um: distance to be covered in microns

        Returns:
            tuple[int, float]: number of steps, coverage of n steps of length step_um
        """
        steps: int = int(np.floor(distance_um / step_um) + 1)
        coverage = (steps - 1) * step_um
        if coverage < distance_um:
            steps += 1
            coverage = (steps - 1) * step_um
        return steps, coverage
