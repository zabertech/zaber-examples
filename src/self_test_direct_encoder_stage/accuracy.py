"""Self-accuracy script for rotary and linear devices. Requires -AE or -DE encoder.

Created 2022, Contributors: Nathan P
"""

from collections import namedtuple
import time

import matplotlib.pyplot as plt
from zaber_motion import Units
from zaber_motion.ascii import AxisType, Axis, Connection

SERIAL_PORT = "COMx"
AXIS = 1

# Accuracy test settings
AccTestSettings = namedtuple(
    "AccTestSettings",
    "test type n_points_override bi_directional repetitions "
    "pause_before_measure_s allowable_encoder_variation",
)
ACC_SETTINGS = AccTestSettings(
    test=True,
    type="Accuracy",
    n_points_override=10,
    bi_directional=True,
    repetitions=1,
    pause_before_measure_s=0.1,
    allowable_encoder_variation=1,
)

# Repeatability test settings
RepTestSettings = namedtuple(
    "RepTestSettings",
    "test type start_mm_deg step_mm_deg repetitions "
    "allowable_encoder_variation pause_before_measure_s bi_directional",
)
REP_SETTINGS = RepTestSettings(
    test=True,
    type="Repeatability",
    start_mm_deg=0,
    step_mm_deg=10,
    repetitions=10,
    pause_before_measure_s=0.1,
    allowable_encoder_variation=1,
    bi_directional=True,
)  # Always True

DEG = Units.ANGLE_DEGREES
MM = Units.LENGTH_MILLIMETRES
START_TIME = time.time()


def main() -> None:
    """Connect to stage and run specified tests."""
    with Connection.open_serial_port(SERIAL_PORT) as stage_port:
        device = stage_port.detect_devices()[0]
        stage = device.get_axis(AXIS)
        stage.home()

        # Get properties from stage
        rotary = stage.axis_type is AxisType.ROTARY
        name = stage.peripheral_name if stage.is_peripheral else stage.device.name

        assert "-DE" in name or "-AE" in name, f'Stage "{name}" does not have a direct encoder'

        if ACC_SETTINGS.test:
            print(f'\nRunning {"Rotary" if rotary else "Linear"} Accuracy Test')
            test_points = (
                get_rotary_acc_test_pts_array() if rotary else get_linear_acc_test_pts_array(stage)
            )
            data_list = run_test(stage, test_points, rotary, ACC_SETTINGS)
            stage.home(wait_until_idle=False)
            plot_accuracy(data_list)

        if REP_SETTINGS.test:
            print(f'\nRunning {"Rotary" if rotary else "Linear"} Repeatability Test')
            test_points = [
                REP_SETTINGS.start_mm_deg,
                REP_SETTINGS.start_mm_deg + REP_SETTINGS.step_mm_deg,
            ]
            stage.wait_until_idle()
            data_list = run_test(stage, test_points, rotary, REP_SETTINGS)
            plot_repeatability(data_list)


def run_test(
    stage: Axis,
    test_points_mm_deg: list[float],
    rotary: bool,
    settings: AccTestSettings | RepTestSettings,
) -> list[dict[str, float]]:
    """Run through the location 'test_points_mm_deg' and logs the position."""
    # pylint: disable=too-many-locals
    point_counter = 1
    data_list = []
    for rep in range(settings.repetitions):
        print(f"\nRep {rep + 1} of {settings.repetitions}")
        previous_errors = {}
        passes = (
            ["forward", "reverse"]
            if settings.type == "Accuracy" and settings.bi_directional
            else ["forward"]
        )

        for direction in passes:
            if settings.type == "Accuracy":
                print(f"\n{direction.title()} pass:\n")

            for target_pos_real in (
                reversed(test_points_mm_deg[:-1])
                if direction == "reverse"
                else test_points_mm_deg
                if rep == 0 or REP_SETTINGS.test
                else test_points_mm_deg[1:]
            ):
                # Only take measurement at '0' on the 1st pass to avoid 0 backlash results.

                # Move
                stage.move_absolute(target_pos_real, DEG if rotary else MM)
                time.sleep(settings.pause_before_measure_s)

                # Measure
                encoder_pos_z = stable_encoder_measurement(stage, settings)
                encoder_pos_real = stage.settings.convert_from_native_units(
                    "pos", encoder_pos_z, DEG if rotary else MM
                )
                position_error_real = (
                    encoder_pos_real - target_pos_real
                    if rotary
                    else (encoder_pos_real - target_pos_real) * 1000
                )

                # Record
                pos_z = stage.settings.get("pos")
                if direction == "forward":
                    previous_errors[pos_z] = position_error_real
                    backlash = 0.0
                else:
                    backlash = position_error_real - previous_errors[pos_z]
                data_list.append(
                    {
                        "Elapsed Time [s]": time.time() - START_TIME,
                        "Target Angle [deg]" if rotary else "Target Position [mm]": target_pos_real,
                        "Target Pos [ustep]": pos_z,
                        "Encoder Pos [ustep]": encoder_pos_z,
                        "Measured Angle [deg]"
                        if rotary
                        else "Measured Position [mm]": encoder_pos_real,
                        "Angular Error [deg]"
                        if rotary
                        else "Position Error [um]": position_error_real,
                        f'Backlash {"[deg]" if rotary else "[um]"}': backlash,
                    }
                )

                print(
                    f"{point_counter}. "
                    f'Error = {position_error_real:.3f} {"deg" if rotary else "µm"}'
                )
                point_counter += 1

    return data_list


def get_linear_acc_test_pts_array(stage: Axis) -> list[float]:
    """Create an array of test points equally spaced throughout travel."""
    n_points = ACC_SETTINGS.n_points_override or 100
    start_pos_mm_deg = stage.settings.get("limit.min", MM)
    end_pos_mm_deg = stage.settings.get("limit.max", MM)
    step_size_mm_deg = (end_pos_mm_deg - start_pos_mm_deg) / n_points
    test_points_mm_deg = [(step_size_mm_deg * idx) for idx in range(n_points + 1)]
    return test_points_mm_deg


def get_rotary_acc_test_pts_array() -> list[float]:
    """Create an array of test points equally spaced throughout travel."""
    n_points = ACC_SETTINGS.n_points_override or 360
    start_pos_mm_deg = 0
    end_pos_mm_deg = 360
    step_size_mm_deg = (end_pos_mm_deg - start_pos_mm_deg) / n_points
    test_points_mm_deg = [(step_size_mm_deg * idx) for idx in range(n_points + 1)]
    return test_points_mm_deg


def stable_encoder_measurement(
    stage: Axis, settings: AccTestSettings | RepTestSettings, count: int = 1
) -> float:
    """Return encoder measurement once reading is stable."""
    measurements: list[float] = []
    while len(measurements) < 3:
        measurements.append(stage.settings.get("encoder.pos"))
        time.sleep(0.01)

    variation = max(measurements) - min(measurements)
    print(f"\tMeasurement = {measurements}\n\tVariation = {variation} usteps")

    if variation > settings.allowable_encoder_variation:
        if count == 100:
            # pylint: disable=broad-exception-raised
            raise Exception(f"Did not get stable encoder measurement in {count} attempts")
        return stable_encoder_measurement(stage, settings, count + 1)

    return measurements[-1]


def plot_accuracy(data_list: list[dict[str, float]]) -> None:
    """Plot accuracy, with forward/reverse pass separated."""
    target_pos_mm = [row["Target Position [mm]"] for row in data_list]
    error_um = [row["Position Error [um]"] for row in data_list]

    forward_pass_pts = (
        int(len(data_list) / 2) + 1 if ACC_SETTINGS.bi_directional else len(data_list)
    )

    plt.plot(target_pos_mm[:forward_pass_pts], error_um[:forward_pass_pts], marker=".")
    if ACC_SETTINGS.bi_directional:
        plt.plot(target_pos_mm[forward_pass_pts:], error_um[forward_pass_pts:], marker=".")
    plt.title("Accuracy")
    plt.legend(
        labels=["Forward Pass", "Reverse Pass"] if ACC_SETTINGS.bi_directional else ["Forward Pass"]
    )
    plt.xlabel("Target Position (mm)")
    plt.ylabel("Position Error (µm)")
    plt.show()


def plot_repeatability(data_list: list[dict[str, float]]) -> None:
    """Plot repeatability with home/away positions separated."""
    elapsed_time = [row["Elapsed Time [s]"] for row in data_list]
    error_um = [row["Position Error [um]"] for row in data_list]

    home_x = [elapsed_time[x] for x in range(0, len(data_list), 2)]
    home_y = [error_um[x] for x in range(0, len(data_list), 2)]
    away_x = [elapsed_time[x + 1] for x in range(0, len(data_list), 2)]
    away_y = [error_um[x + 1] for x in range(0, len(data_list), 2)]

    plt.plot(home_x, home_y, marker=".", ls="")
    plt.plot(away_x, away_y, marker=".", ls="")
    plt.title("Repeatability")
    plt.legend(labels=["Home", "Away"])
    plt.xlabel("Time (s)")
    plt.ylabel("Position Error (µm)")
    plt.show()


if __name__ == "__main__":
    main()
