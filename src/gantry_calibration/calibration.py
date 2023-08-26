"""The core math and functionality behind the calibration algorithm."""

from collections import namedtuple
import numpy as np


Point = namedtuple("Point", ["x", "y"])
PointPair = namedtuple("PointPair", ["expected", "actual"])


class Calibration:
    """Contains the calibration matrix and coefficients."""

    def __init__(self, points: list[PointPair]) -> None:
        """Instantiate the object with expected and actual points."""
        self.points = points

    def map(self, point: Point) -> Point:
        """Map from expected coordinates to actual coordinates."""
        return point
