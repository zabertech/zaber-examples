"""This is the main demo program for the well plate loader."""

import threading
from time import sleep
from typing import Literal
import mecademicpy.robot as mdr

from zaber_motion import Library
from zaber_motion.ascii import Connection

from .settings import ROBOT_ADDRESS, SCAN_SPEED, ProcessControllerSettings, SpeedSettings, PORT
from .positions import AdrPosition, DropDown, StackerPosition, VsrPositions
from .well_plates import WELL_PLATES, PLATE_TYPE
from .utilities import (
    MM,
    MMS,
    LEDs,
    Machine,
    Stages,
    Tower,
    adr_move_away,
    cycle_lights,
    home_all,
    initialize_machine,
    pounce,
    robot_init,
)


# ===== XY SCAN FUNCTIONS =====


def raster_scan(stages: Stages, leds: LEDs) -> None:
    """Performs a raster scan on the microscope using discrete moves instead of a stream."""
    well_plate = WELL_PLATES[PLATE_TYPE]
    rows = well_plate["rows"] / SCAN_SPEED
    columns = well_plate["columns"] / SCAN_SPEED
    pitch = well_plate["pitch"] * SCAN_SPEED
    row_offset = well_plate["row_offset"]
    column_offset = well_plate["column_offset"]

    xy_axes = [stages.xy_lower, stages.xy_upper]
    for axis in xy_axes:
        axis.wait_until_idle()

    x_axis = stages.xy_lower
    y_axis = stages.xy_upper

    for row in range(rows):
        y_axis.move_absolute(row_offset + (row * pitch), MM, False)
        x_axis.move_absolute(column_offset, MM, False)
        for axis in xy_axes:
            axis.wait_until_idle()
        cycle_lights(leds, 0.1, 3)

        for _ in range(columns):
            x_axis.move_relative(pitch, MM, False)
            x_axis.wait_until_idle()
            cycle_lights(leds, 0.1, 3)

        x_axis.wait_until_idle()
        y_axis.wait_until_idle()


def call_xy_scan(stages: Stages) -> None:
    """Calls a stream version of the XY scan w/ no LEDs (alternative to the raster scan function above)."""
    stream = stages.xy_controller.streams.get_stream(1)
    xy_scan = stages.xy_controller.streams.get_buffer(1)
    stream.disable()
    stream.setup_live(1, 2)
    stream.call(xy_scan)
    stages.xy_controller.all_axes.wait_until_idle()


# ===== ROBOT FUNCTIONS =====


def grab_plate(robot: mdr.Robot) -> None:
    """Picks up a well plate with the robot arm, at the current position."""
    p = DropDown

    # move down 20 mm
    robot.MoveLinRelWrf(p.X, p.Y, p.Z, p.R1, p.R2, p.R3)
    robot.WaitIdle()

    # close grippers and wait to ensure grip
    robot.GripperClose()
    sleep(0.5)

    # move back up 20 mm
    robot.MoveLinRelWrf(p.X, p.Y, -p.Z, p.R1, p.R2, p.R3)
    robot.WaitIdle()


def release_plate(robot: mdr.Robot) -> None:
    """Releases the robot arm's grip on the current well plate."""
    p = DropDown

    robot.MoveLinRelWrf(p.X, p.Y, p.Z, p.R1, p.R2, p.R3)
    robot.WaitIdle()

    robot.GripperOpen()
    sleep(0.5)
    robot.WaitIdle()

    robot.MoveLinRelWrf(p.X, p.Y, -p.Z, p.R1, p.R2, p.R3)
    robot.WaitIdle()


def retract_stacker_fingers(tower: Tower) -> None:
    """Releases the tower's hold on the next well plate."""
    s = ProcessControllerSettings
    tower.left.on()
    tower.right.on()
    sleep(s.DELAY_SOLENOIDS)  # Wait for solenoid/slider action to complete
    sleep(s.DELAY)


def extend_stacker_fingers(tower: Tower) -> None:
    """Secures the tower's hold on any well plates present so they don't fall."""
    s = ProcessControllerSettings
    tower.left.off()
    tower.right.off()
    sleep(s.DELAY_SOLENOIDS)  # Wait for solenoid/slider action to complete
    sleep(s.DELAY)


# ===== PLATE EXCHANGE FUNCTIONS =====


def goto_xaxis_exchange_position(robot: mdr.Robot, stages: Stages, num_trays_on_vsr: int) -> None:
    """Gets LRQ (robot axis), LSQ (X axis), and robot into position for dropping off / picking up plates from VSR"""
    p = StackerPosition

    if num_trays_on_vsr == 2:
        height = 16
    else:
        height = 0

    stages.x.wait_until_idle()
    stages.robot_axis.wait_until_idle()

    stages.x.move_absolute(p.LOADER_PICKUP_POS, MM, wait_until_idle=False)
    stages.robot_axis.move_absolute(p.EXTENDER_PICKUP_POS, MM, wait_until_idle=False)
    stages.x.wait_until_idle()
    stages.robot_axis.wait_until_idle()

    robot.MoveLin(p.X, p.Y, p.Z + height, p.R1, p.R2, p.R3)
    robot.WaitIdle()


def goto_xystage_exchange_position(robot: mdr.Robot, stages: Stages) -> None:
    """This is the loading sequence to load or unload the ADR (XY stage)."""
    p = AdrPosition

    robot.WaitIdle()
    robot.MoveLin(p.X, p.Y, p.Z, p.R1, p.R2, p.R3)
    robot.WaitIdle()

    # go to XY exchange position
    stages.robot_axis.move_absolute(p.EXTENDER_MICROSCOPE_LOAD_POS, MM)
    stages.xy_lower.move_absolute(0, MM, wait_until_idle=False)
    stages.xy_upper.move_absolute(100, MM, wait_until_idle=False)

    stages.xy_lower.wait_until_idle()
    stages.xy_upper.wait_until_idle()


def xy_stage_plate_pickup(robot: mdr.Robot, stages: Stages) -> None:
    """Picks up the plate from the XY stage and moves it to the loader X axis."""
    goto_xystage_exchange_position(robot, stages)
    grab_plate(robot)
    adr_move_away(stages)
    goto_xaxis_exchange_position(robot, stages, 1)
    release_plate(robot)


def xy_stage_plate_dropoff(robot: mdr.Robot, stages: Stages, num_trays: int) -> None:
    """Picks up the plate from the loader X axis and moves it to the XY stage."""
    goto_xaxis_exchange_position(robot, stages, num_trays)
    grab_plate(robot)
    goto_xystage_exchange_position(robot, stages)
    release_plate(robot)


# VSR, gripper, and tower controls for loading and unloading plates into towers
# Tower number refers to the left (1) or right (2) tower
def tower_load(plate_type: Literal["first", "last", "standard"], machine: Machine, tower_number: int) -> None:
    p = StackerPosition
    v_pos = VsrPositions
    s = SpeedSettings

    if tower_number == 1:
        tower = machine.tower1
        loader_x_position = p.TOWER_1_POS
    elif tower_number == 2:
        tower = machine.tower2
        loader_x_position = p.TOWER_2_POS
    else:
        raise ValueError("Error - incorrect tower number entered.")

    if plate_type == "first" and tower_number == 1:
        first_position = v_pos.Z_TOP
        first_position_approach = v_pos.Z_TOP_APPROACH
        second_position = v_pos.Z_LID
        second_position_approach = v_pos.Z_LID_APPROACH

    elif plate_type == "first" and tower_number == 2:
        first_position = v_pos.Z_TOP
        first_position_approach = v_pos.Z_FINGER_APPROACH_WITH_LID
        second_position = v_pos.Z_TOP
        second_position_approach = v_pos.Z_TOP_APPROACH

    elif plate_type == "standard" and tower_number == 1:
        first_position = v_pos.Z_LID
        first_position_approach = v_pos.Z_FINGER_APPROACH
        second_position = v_pos.Z_NEXT_PLATE_LID
        second_position_approach = v_pos.Z_NEXT_PLATE_LID_APPROACH

    elif plate_type == "standard" and tower_number == 2:
        first_position = v_pos.Z_LID_TRANSFER
        first_position_approach = v_pos.Z_FINGER_APPROACH_WITH_LID
        second_position = v_pos.Z_TOP
        second_position_approach = v_pos.Z_TOP_APPROACH

    elif plate_type == "last" and tower_number == 1:
        first_position = v_pos.Z_LID
        first_position_approach = v_pos.Z_FINGER_APPROACH
        second_position = v_pos.Z_SKIP
        second_position_approach = v_pos.Z_SKIP

    elif plate_type == "last" and tower_number == 2:
        first_position = v_pos.Z_LID_TRANSFER
        first_position_approach = v_pos.Z_FINGER_APPROACH_WITH_LID
        second_position = v_pos.Z_TOP
        second_position_approach = v_pos.Z_TOP_APPROACH

    else:
        raise ValueError("Error - incorrect plate loading method entered.")

    # movement routine
    stages = machine.stages
    stages.x.move_absolute(loader_x_position, MM)

    if plate_type == "first" and tower_number == 2:
        stages.z.move_absolute(first_position_approach, MM)
    else:
        stages.z.move_absolute(first_position_approach, MM)
        stages.z.move_absolute(first_position, MM, True, s.LOADER_Z_SLOW, MMS)

    retract_stacker_fingers(tower)
    stages.z.move_absolute(second_position, MM, True, s.LOADER_Z_SLOW, MMS)
    extend_stacker_fingers(tower)
    stages.z.move_absolute(second_position_approach, MM, True, s.LOADER_Z_SLOW, MMS)
    stages.z.move_absolute(v_pos.Z_BOTTOM, MM)

    if plate_type == "last":
        stages.x.move_absolute(p.TOWER_2_POS, MM)
    else:
        stages.x.move_absolute(p.LOADER_PICKUP_POS, MM)


# ===== MAIN LOADING CODE =====


def stack(machine: Machine, starting_plates: int) -> None:
    p = StackerPosition

    # Assume each plate has associated lid, tower #2 is empty, and holder is empty
    tower1_plates = tower1_lids = starting_plates
    tower2_plates = tower2_lids = 0
    holder_plates = holder_lid = 0

    pounce(machine.robot, True)
    if tower1_plates <= 1:
        raise ValueError("Error - Starting plate count must be greater than one.")

    while tower1_lids > 0:
        # CASE 1 - First plate removed from stack (no plate in holder)
        #   Action: Get the first plate and deliver to robot
        if tower1_plates == starting_plates:
            # Unload first plate from tower 1
            tower_load("first", machine, 1)
            holder_plates += 1
            tower1_plates -= 1

            xy_stage_plate_dropoff(machine.robot, machine.stages, 1)
            holder_plates -= 1

            # run raster scan on XY stage drop off tray once it is done
            raster_scan(machine.stages, machine.leds)
            # Comment out the above line and uncomment the below to use the stream scan instead.
            # call_xy_scan(machine.stages)

            xy_stage_plate_pickup(machine.robot, machine.stages)
            holder_plates += 1

        # CASE 2 - Processed plate in holder, at least 1 plate (and 2 lids) remaining in Tower 1
        # Actions:
        # 1. return to Tower 1 and pick up lid with next plate
        # 2. deliver new plate to robot
        # 3. deliver completed plate+lid to Tower 2
        # 4. pick up new plate from robot

        elif holder_plates > 0 and tower1_plates > 0:
            # move robot to neutral position
            pounce(machine.robot, False)

            # get lid and next plate while still holding tray
            tower_load("standard", machine, 1)
            holder_lid += 1
            holder_plates += 1
            tower1_plates -= 1
            tower1_lids -= 1

            xy_stage_plate_dropoff(machine.robot, machine.stages, 2)
            holder_plates -= 1

            # load "finished" plate into tower #2
            if tower2_plates == 0:  # If this is the first plate to enter the stack
                t1 = threading.Thread(target=raster_scan, args=[machine.stages, machine.leds])
                t2 = threading.Thread(target=tower_load, args=["first", machine, 2])
                t2.start()
                t1.start()
                t1.join()
                t2.join()

            else:  # Else, one or more plates are already in the stack
                t1 = threading.Thread(target=raster_scan, args=[machine.stages, machine.leds])
                t2 = threading.Thread(target=tower_load, args=["first", machine, 2])
                t2.start()
                t1.start()
                t1.join()
                t2.join()

            machine.stages.xy_controller.all_axes.wait_until_idle()
            xy_stage_plate_pickup(machine.robot, machine.stages)

            tower2_lids += 1
            tower2_plates += 1
            holder_lid -= 1

            machine.stages.x.move_absolute(p.LOADER_PICKUP_POS, MM)

        # CASE 3 - Processed plate in holder, but no plates remain in Tower 1 (1 lid left)
        #   Action: return to Tower 1 and pick up lid only, deliver completed plate + lid directly to Tower 2
        elif holder_plates > 0 and tower1_plates == 0 or tower1_lids == 1:  # Only one lid remains in Tower 1
            tower_load("last", machine, 1)
            holder_lid += 1
            tower1_lids -= 1

            tower_load("last", machine, 2)
            tower2_lids += 1
            tower2_plates += 1
            holder_lid -= 1
            holder_plates -= 1

    machine.stages.x.move_absolute(p.LOADER_PICKUP_POS, MM)  # Move to robot loading position once complete
    print("\n ----- Unloading test sequence (with lids) complete. ----- \n")
    print(f"{tower2_plates} microplates and lids have been processed and are now ready for pickup in Tower 2.\n")

    sleep(1)


def main() -> None:
    # Connect and set up robot arm
    robot = mdr.Robot()
    robot.Connect(address=ROBOT_ADDRESS, enable_synchronous_mode=False)
    robot_init(robot)

    # Connect to Zaber devices and run the main program.
    with Connection.open_serial_port(PORT) as connection:
        connection.enable_alerts()
        devices = connection.detect_devices()

        machine = initialize_machine(robot, devices)
        home_all(machine)

        machine.stages.xy_lower.move_max(False)
        machine.stages.xy_upper.move_min(False)
        machine.stages.robot_axis.move_absolute(150, MM)
        pounce(machine.robot, True)

        n = int(input("Enter number of trays in tower 1: "))
        stack(machine, n)


if __name__ == "__main__":
    main()
