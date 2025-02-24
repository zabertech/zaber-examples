"""This file contains types and miscellaneous small functions to reduce the size of the main script."""

from dataclasses import dataclass
import re
from time import sleep
from typing import List, Tuple

import mecademicpy.robot as mdr
from zaber_motion import Units
from zaber_motion.ascii import Device, Axis
from zaber_motion.product import Process, ProcessController, ProcessControllerMode
from zaber_motion.microscopy import Illuminator, IlluminatorChannel

from .positions import Pounce, RobotSettings, StackerPosition
from .settings import ProcessControllerSettings, SpeedSettings, PORT

# Unit abbreviations
MM = Units.LENGTH_MILLIMETRES
MMS = Units.VELOCITY_MILLIMETRES_PER_SECOND
VOLTS = Units.VOLTAGE_VOLTS
TS = Units.TIME_SECONDS


@dataclass
class Tower:
    """Represents either one of the towers that hold well pates."""

    controller: ProcessController
    left: Process
    right: Process


@dataclass
class LEDs:
    """Represents the illuminator and its identified LEDs."""

    red: IlluminatorChannel
    white: IlluminatorChannel
    blue: IlluminatorChannel


@dataclass
class Stages:
    """Represents the Zaber motion axes that are used in the demo machine."""

    robot_axis: Axis
    """The range extender axes for the Mecademic robot arm."""

    x: Axis
    """ The horizontal axis of the well plate transport mechanism."""

    z: Axis
    """ The vertical axis of the well plate transport mechanism."""

    xy_lower: Axis
    """ The X axis (aligned with the other X axis of the machine) of the microscope scanning stage. """

    xy_upper: Axis
    """ The Y axis of the microscope scanning stage. """

    xy_controller: Device
    """ The controller of the microscope X-Y axes (used for the stream version of the raster scan). """


@dataclass
class Machine:
    """Encapsulates all the software-controlled elements of the demo machine."""

    robot: mdr.Robot
    stages: Stages
    leds: LEDs
    tower1: Tower
    tower2: Tower


def sca_init(sca: ProcessController) -> Tuple[Tower, Tower]:
    """Configures the Process Controller outputs and creates a convenient representation of the well plate towers."""
    s = ProcessControllerSettings

    for outputNum in range(1, 5):
        sca.get_process(outputNum).set_mode(ProcessControllerMode.MANUAL)
        sca.get_process(outputNum).settings.set("process.voltage.on", s.SOLENOID_VOLTAGE, VOLTS)

    tower1 = Tower(sca, sca.get_process(1), sca.get_process(2))
    tower2 = Tower(sca, sca.get_process(3), sca.get_process(4))

    return tower1, tower2


def robot_init(robot: mdr.Robot) -> None:
    """Sets initial configuration of the Mecademic robot arm."""
    s = SpeedSettings
    r = RobotSettings

    robot.SetGripperRange(0, r.GRIPPER_OPEN)
    robot.SetGripperVel(s.ROBOT_GRIPPER)
    robot.SetGripperForce(40)

    # this config helps ensure the robot will go to the correct positions when using cartesian moves
    robot.SetConf(1, 1, 1)
    robot.SetCartLinVel(s.ROBOT_LINEAR)
    robot.SetCartAngVel(s.ROBOT_ANGULAR)


def init_zaber_stages(stages: Stages) -> None:
    """Sets initial configuration of the Zaber motion axes."""
    s = SpeedSettings

    stages.robot_axis.settings.set("maxspeed", s.EXTENDER, MMS)
    stages.x.settings.set("maxspeed", s.LOADER_X, MMS)
    stages.z.settings.set("maxspeed", s.LOADER_Z_FAST, MMS)
    stages.xy_upper.settings.set("maxspeed", s.XY, MMS)
    stages.xy_lower.settings.set("maxspeed", s.XY, MMS)


def init_leds(leds: LEDs) -> None:
    """Sets initial configuration of the Zaber illuminator LEDs."""
    leds.blue.set_intensity(0.5)
    leds.white.set_intensity(0.5)
    leds.red.set_intensity(0.5)


def adr_move_away(stages: Stages) -> None:
    """Moves the ADR out of the way to prevent robot arm collisions."""
    stages.xy_upper.move_min(False)
    stages.xy_lower.move_max(False)

    stages.xy_upper.wait_until_idle()
    stages.xy_lower.wait_until_idle()


def pounce(robot: mdr.Robot, wait: bool) -> None:
    """Moves the robot arm to its neutral position."""
    p = Pounce

    robot.GripperOpen()
    robot.MoveJoints(p.J1, p.J2, p.J3, p.J4, p.J5, p.J6)
    if wait:
        robot.WaitIdle()


def home_all(machine: Machine) -> None:
    """Homes all Zaber stages."""
    p = StackerPosition

    stages = machine.stages
    if not stages.z.is_homed():  # Home loader Z-axis first to avoid potential crashes
        stages.z.home(wait_until_idle=True)

    # Home the other axes simultaneously then wait for them to finish.
    other_axes = [stages.x, stages.robot_axis, stages.xy_lower, stages.xy_upper]
    for axis in other_axes:
        if not axis.is_homed():
            axis.home(wait_until_idle=False)

    for axis in other_axes:
        axis.wait_until_idle()

    adr_move_away(stages)
    stages.robot_axis.move_absolute(p.EXTENDER_PICKUP_POS, MM)
    pounce(machine.robot, True)
    stages.x.move_absolute(p.LOADER_PICKUP_POS, MM)


def initialize_machine(robot: mdr.Robot, devices: List[Device]) -> Machine:
    """Finds and initializes the Zaber devices and combines them and the robot arm in a data structure."""

    # Search for Zaber devices within daisy-chain
    # Note they're all expected to be on the same serial port.
    # This approach to identifying the devices works because every component of the machine
    # is a different device type. When that's not true you may need to use serial numbers
    # or user data stored on the devices to identify the right ones.
    ADR = next((x for x in devices if re.search("ADR", x.name) is not None), None)
    if not ADR:
        raise ValueError(f"No ADR detected on {PORT}.")

    LCA = next((x for x in devices if re.search("LCA", x.name) is not None), None)
    if not LCA:
        raise ValueError(f"No LCA detected on {PORT}.")

    SCA = next((x for x in devices if re.search("SCA", x.name) is not None), None)
    if not SCA:
        raise ValueError(f"No SCA detected on {PORT}.")

    LSQ = next((x for x in devices if re.search("LSQ", x.name) is not None), None)
    if not LSQ:
        raise ValueError(f"No LSQ detected on {PORT}.")

    LRQ = next((x for x in devices if re.search("LRQ", x.name) is not None), None)
    if not LRQ:
        raise ValueError(f"No LRQ detected on {PORT}.")

    VSR = next((x for x in devices if re.search("VSR", x.name) is not None), None)
    if not VSR:
        raise ValueError(f"No VSR detected on {PORT}.")

    # Initialize Zaber Process Controller
    sca = ProcessController(SCA)
    tower1, tower2 = sca_init(sca)

    # Select and initialize the Zaber motion axes.
    zaber_stages = Stages(LRQ.get_axis(1), LSQ.get_axis(1), VSR.get_axis(1), ADR.get_axis(1), ADR.get_axis(2), ADR)
    init_zaber_stages(zaber_stages)

    # Select and initialize illuminator LEDs. Note the channel numbers here depend on what order the LEDs are
    # connected to the illuminator; if you plug them in to different connectors, you will have to change these numbers.
    illuminator = Illuminator(LCA)
    leds = LEDs(illuminator.get_channel(3), illuminator.get_channel(2), illuminator.get_channel(1))
    init_leds(leds)

    return Machine(robot, zaber_stages, leds, tower1, tower2)


def cycle_lights(leds: LEDs, dwell_time: float, number_of_lights: int) -> None:
    """Flashes the illuminator LEDs in the microscope as part of simulating data aquisition."""
    if number_of_lights >= 1:
        leds.red.on()
        sleep(dwell_time)
        leds.red.off()

    if number_of_lights >= 2:
        leds.white.on()
        sleep(dwell_time)
        leds.white.off()

    if number_of_lights >= 3:
        leds.blue.on()
        sleep(dwell_time)
        leds.blue.off()
