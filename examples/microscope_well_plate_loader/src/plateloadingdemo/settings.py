from dataclasses import dataclass

# Change PORT to the name of the serial port your Zaber devices are connected to.
PORT = "COM3"

# Change this to the IP address of the Mecademic robot.
ROBOT_ADDRESS = "192.168.0.100"

# Set to 1 to visit all wells in the plate; 2 skips alternate rows and columns for faster simulaiton.
SCAN_SPEED = 2


@dataclass(frozen=True)
class SpeedSettings:
    """Speed constants for various parts of the system."""

    # [mm/s]
    LOADER_X = 700
    LOADER_Z_FAST = 40
    LOADER_Z_SLOW = 10
    EXTENDER = 110
    XY = 400
    ROBOT_LINEAR = 500
    ROBOT_GRIPPER = 20

    # [deg/s]
    ROBOT_ANGULAR = 150


# SOLENOIDS
# Note: Can likely reduce voltage with new springs (to be installed) with slightly lower spring constant
# Solenoids rated for 24V continuous operation, so higher voltage at intermittent duty cycle shouldn't be an issue
@dataclass(frozen=True)
class ProcessControllerSettings:
    """Constants for the process controllers in the towers."""

    # voltage [VDC]
    SOLENOID_VOLTAGE = 23.5  # Tower 1 & 2 solenoids

    # delay times [s]
    DELAY = 0.05  # Time delay between steps for debugging purposes - currently inserted after every move command
    DELAY_SOLENOIDS = 0.25  # Delay to allow solenoids to actuate
