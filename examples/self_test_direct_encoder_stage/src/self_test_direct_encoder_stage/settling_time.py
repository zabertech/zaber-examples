"""Measure settling time with various settings and step sizes.

    - This script is intended for linear direct encoder stages, and is mostly used for direct drive
    - There is a trade-off between settle time and accuracy.
    - For higher accuracy it often helps to tighten the settle tolerance,
        but tightening too much could result in never settling.

Created 2022, Contributors: Nathan P
"""

from collections import namedtuple
import time

import matplotlib.pyplot as plt
from zaber_motion import Units, MovementFailedException
from zaber_motion.ascii import Axis, Connection, AxisType

SERIAL_PORT = "COMx"

# Test Settings
TestSettings = namedtuple(
    "TestSettings",
    "settle_tolerance_values_ustep start_positions_mm step_sizes_mm "
    "repetitions stability_tolerance_counts remove_backlash settings_to_test",
)
SETTINGS = TestSettings(
    settle_tolerance_values_ustep=[50, 100, 200, 500],
    start_positions_mm=[0],
    step_sizes_mm=[0.0001, 0.01, 1],
    repetitions=1,
    stability_tolerance_counts=10,
    remove_backlash=False,
    # These will only be used for direct drive stages
    settings_to_test=[
        {"accel": 2457600, "servo live load": 3},  # Stiff
        {"accel": 2457600, "servo live load": 2},  # Medium
        {"accel": 2457600, "servo live load": 1},  # Soft
    ],
)

START_TIME = time.time()


def main() -> None:
    """Connect to stage, run through test points, plot for each set of settings."""
    with Connection.open_serial_port(SERIAL_PORT) as stage_port:
        stage_device = stage_port.detect_devices()[0]
        stage = stage_device.get_axis(1)
        original_settle_tolerance = stage.settings.get("cloop.settle.tolerance")

        assert stage_device.firmware_version.major == 7, "Incompatible FW version"
        assert stage_device.firmware_version.minor >= 31, "Please update your Firmware"
        assert stage.axis_type != AxisType.ROTARY, "Rotary stages not compatible"

        if stage.settings.get("motor.type") == 1:
            print("\nStepper stage detected, not applying servo settings")
            servo_settings: list[dict[str, int]] = [{}]
        else:
            servo_settings = SETTINGS.settings_to_test

        for settings_dict in servo_settings:
            # Update stage servo settings
            settings_tag = ""
            if settings_dict:
                print("\nApplying servo settings")
                for key, value in settings_dict.items():
                    if key == "servo live load":
                        stage.generic_command(f"{key} {value}")
                    else:
                        stage.settings.set(key, value)
                    settings_tag += f"_{key}_{value}"
                settings_tag.lstrip("_")

            # Test with specified servo settings
            data_list = run_test(stage)

            # Plot
            plt.plot(
                [x["settle.tolerance [ustep]"] for x in data_list],
                [x["Settle Time [s]"] for x in data_list],
                marker=".",
                ls="",
            )
            plt.title("Settling Time")
            plt.legend(labels=[settings_tag or "Default Servo Settings"])
            plt.xlabel("settle.tolerance (ustep)")
            plt.ylabel("Settle Time (s)")
            if (
                max(SETTINGS.settle_tolerance_values_ustep)
                / min(SETTINGS.settle_tolerance_values_ustep)
                > 100
            ):
                plt.xscale("log")
            plt.show()

        stage.settings.set("cloop.settle.tolerance", original_settle_tolerance)

        print("\nTest complete!")


def run_test(stage: Axis) -> list[dict[str, float]]:
    """Run through all the test points and record settling time for each."""
    print("\nRunning Test:")
    point = 0
    points = (
        len(SETTINGS.settle_tolerance_values_ustep)
        * len(SETTINGS.start_positions_mm)
        * len(SETTINGS.step_sizes_mm)
        * SETTINGS.repetitions
    )
    data_list = []

    for settle_tol_value in SETTINGS.settle_tolerance_values_ustep:
        stage.settings.set("cloop.settle.tolerance", settle_tol_value)

        # Run through various moves
        for start_position in SETTINGS.start_positions_mm:
            run_number = 0
            for step_size in SETTINGS.step_sizes_mm:
                run_number += 1
                for repetition in range(SETTINGS.repetitions):
                    data_row = test_point(
                        stage,
                        start_position,
                        step_size,
                        repetition,
                        settle_tol_value,
                        run_number,
                        point,
                        points,
                    )
                    data_list.append(data_row)
                    point += 1

    return data_list


def test_point(  # pylint: disable=too-many-arguments
    stage: Axis,
    start_position: float,
    step_size: float,
    repetition: int,
    settle_tol_value: int,
    run_number: int,
    point: int,
    points: int,
) -> dict[str, float]:
    """Do a move and record the settle time."""
    move_safely_to_start(stage, start_position)
    wait_for_stability(stage)

    # Move
    start_time = time.time()
    try:
        stage.move_relative(step_size, Units.LENGTH_MILLIMETRES)
    except MovementFailedException as err:
        print(err)
        time.sleep(2)
        start_time = time.time()
        stage.move_relative(step_size, Units.LENGTH_MILLIMETRES)

    # Record
    move_time_s = time.time() - start_time
    settle_time_s = stage.settings.get("_cloop.settle.time") / 1000
    data_row = {
        "Elapsed Time [s]": time.time() - START_TIME,
        "Start Position [mm]": start_position,
        "settle.tolerance [ustep]": settle_tol_value,
        "Step Size [mm]": step_size,
        "Repetition": repetition,
        "Total Move Time [s]": move_time_s,
        "Settle Time [s]": settle_time_s,
        "Run Number": run_number,
    }

    print(
        f"{point} of {points}, "
        f"Settle Tol: {settle_tol_value}, "
        f"Start Pos: {start_position}, "
        f"Rep: {repetition + 1}, "
        f"Settle time: {settle_time_s: .4}, "
        f"Step Size: {step_size}"
    )

    return data_row


def wait_for_stability(stage: Axis) -> None:
    """Verify that the stage has stable position before performing a move."""
    stable_check = [
        0,
        SETTINGS.stability_tolerance_counts * 2,
    ]  # Init value just to make the while loop run the first time
    unstable_count = 0
    while max(stable_check) - min(stable_check) > SETTINGS.stability_tolerance_counts:
        unstable_count += 1
        stable_check = []
        for _ in range(50):
            stable_check.append(stage.settings.get("encoder.pos"))
        if unstable_count > 20:
            print(
                "WARNING - Did not reach stability after moving to start position!, "
                "moving on to next point"
            )
            stable_check = [0]
    time.sleep(0.5)


def move_safely_to_start(stage: Axis, start_pos_mm: float) -> None:
    """Slowly attempt to reach start position, with one possible failure recovery."""
    try:
        stage.move_velocity(-10, Units.VELOCITY_MILLIMETRES_PER_SECOND)
        stage.wait_until_idle()
        stage.move_absolute(start_pos_mm, Units.LENGTH_MILLIMETRES)
        if SETTINGS.remove_backlash:
            stage.move_relative(1, Units.LENGTH_MILLIMETRES)
    except MovementFailedException as err:
        print(f"Error moving to start, retrying. {err}")
        time.sleep(2)
        stage.move_velocity(-10, Units.VELOCITY_MILLIMETRES_PER_SECOND)
        stage.wait_until_idle()
        stage.move_absolute(start_pos_mm, Units.LENGTH_MILLIMETRES)
        if SETTINGS.remove_backlash:
            stage.move_relative(1, Units.LENGTH_MILLIMETRES)


if __name__ == "__main__":
    main()
