"""This file contains constants for various Zaber stage and robot arm positions in the demo process."""

from dataclasses import dataclass


@dataclass(frozen=True)
class AdrPosition:
    """Robot position for pickup from microscope X-Y stage"""

    X: float = 185.31406
    Y: float = 68.01756
    Z: float = 294.111
    R1: float = -90.35625
    R2: float = -1.71118
    R3: float = -90.88401

    EXTENDER_MICROSCOPE_LOAD_POS: float = 286.32


@dataclass(frozen=True)
class StackerPosition:
    """Robot position for pickup from loader X axis"""

    X: float = 171.89973
    Y: float = -79.55782
    Z: float = 195.277
    R1: float = -82.6845
    R2: float = 87.83301
    R3: float = -98.17631

    TOWER_1_POS: float = 227.15
    TOWER_2_POS: float = 27.15

    LOADER_PICKUP_POS: float = 472.90
    EXTENDER_PICKUP_POS: float = 131.26


@dataclass(frozen=True)
class PouncePositions:
    """Robot intermediate position - defined as joint positions"""

    X: float = 110.66192
    Y: float = 5.3793
    Z: float = 296.50138
    R1: float = -168.99102
    R2: float = 77.08361
    R3: float = -14.49447


@dataclass(frozen=True)
class DropDown:
    """Robot arm relative movement for picking up or putting down a well plate."""

    X: float = 0
    Y: float = 0
    Z: float = -20
    R1: float = 0
    R2: float = 0
    R3: float = 0


@dataclass(frozen=True)
class Pounce:
    """Neutral position for the robot arm."""

    J1: float = -15.72246
    J2: float = -12.14003
    J3: float = 43.84291
    J4: float = 153.259
    J5: float = 36.57873
    J6: float = -337.08739


@dataclass(frozen=True)
class RobotSettings:
    """Constants for miscellaneous robot arm positions."""

    # gripper open position [mm]
    GRIPPER_OPEN = 5.6


@dataclass(frozen=True)
class VsrPositions:
    """Elevations of the loader Z axis (vertical stage) for different steps in the sequence."""

    Z_TOP: float = 40  # Top position, VSR holds entire stack
    Z_TOP_APPROACH: float = 38.5  # Just below top, VSR slightly below contacting stack
    Z_LID: float = 31.9  # Position to catch lid for lowest microplate
    Z_LID_APPROACH: float = 30.4  # Transfer position for speed adjustment
    Z_LID_TRANSFER: float = 23.4  # Position where weight is transferred gradually onto VSR - plate + lid approaching plate (bottom of Tower 2)
    Z_FINGER_APPROACH: float = 23  # Position where VSR can rapidly approach but does not yet contact the finger slopes
    Z_FINGER_APPROACH_WITH_LID: float = 19.5  # Same as line above, with offset for lid thickness
    Z_NEXT_PLATE_LID: float = 16  # Position to catch 2nd lid with plate + lid + plate 2 below
    Z_NEXT_PLATE_LID_APPROACH: float = 15  # Position to catch 2nd lid with plate + lid + plate 2 below
    Z_SKIP: float = 8  # Intermediate point for last plate in sequence
    Z_BOTTOM: float = 0  # Bottom position (for all lateral travel along X-axis)
