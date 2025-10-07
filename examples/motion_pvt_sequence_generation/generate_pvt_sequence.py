"""
Generate the missing parameters for a given PVT sequence.

This script can be used to generate a fully-defined PVT sequence
from position data, position-time data or velocity-time data.

Use the script settings to toggle visualization of the generated
sequence, and writing it to a CSV file compatible with Zaber
Launcher's PVT Viewer App.

Input data must be given in CSV form, with columns for time, position
in each dimension, and velocity in each dimension. Missing parameters
can only be generated in the following three cases:
- No velocity or time information is provided (i.e., there are no such
  columns). In this case, all velocity and time parameters will be
  generated.
- No position information is provided (i.e., there is no such column).
  In this case, all position values will be generated.
- No velocity information is provided (i.e. there is no such column).
  In this case, all velocity values will be generated.

1-D, 2-D, and 3-D sample data is also provided and can be found in the
subdirectory "sample_data".
"""

import os

import pvt
from visualization import plot_path_and_trajectory
from zaber_motion import Measurement, Units
from zaber_motion.ascii import PvtSequence

# ------------------- Script Settings ----------------------

DATA_DIRECTORY = "sample_data/position_velocity_time_data/"
"""The directory of the input file(s)"""
FILENAMES = ["wave_1d.csv", "spiral_2d.csv", "spiral_3d.csv"]
"""The names of the input files to read."""
TARGET_SPEED = Measurement(6, Units.VELOCITY_CENTIMETRES_PER_SECOND)
"""The target speed to use when generating velocities and times."""
TARGET_ACCEL = Measurement(10, Units.ACCELERATION_CENTIMETRES_PER_SECOND_SQUARED)
"""The target aceleration to use when generating velocities and times."""
SHOW_PLOTS = True
"""Whether to plot the generated sequences."""
OUTPUT_DIRECTORY = ""
"""
The directory to write the generated CSV files to.

Specify this as None to not write the files, or as an empty string
to write to the current directory.
"""

# ------------------- Script Settings ----------------------


def main() -> None:
    """Generate complete PVT sequences from underdefined input data."""
    for filename in FILENAMES:
        # Generate the sequence
        sequence_data = pvt.sequence_data_from_csv(
            os.path.join(DATA_DIRECTORY, filename), TARGET_SPEED, TARGET_ACCEL
        )
        if sequence_data is None:
            return

        if SHOW_PLOTS:
            # Plot the sequence
            plot_path_and_trajectory(sequence_data, times_relative=True)
        if OUTPUT_DIRECTORY is not None:
            # Write the file with the same name plus a _generated suffix
            base, extension = filename.rsplit(".", 1)
            output_filename = f"{base}_generated.{extension}"
            PvtSequence.save_sequence_data(sequence_data, os.path.join(OUTPUT_DIRECTORY, output_filename))


if __name__ == "__main__":
    main()
