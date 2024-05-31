"""
Generate the missing parameters for a given PVT sequence.

This script can be used to generate a fully-defined PVT sequence
from position data, position-time data, velocity-time data, or position-velocity-time
data (with some velocity values missing).

Use the script settings to toggle visualization of the generated
sequence, and writing it to a CSV file compatible with Zaber
Launcher's PVT Viewer App.

Input data must be given in CSV form, with columns for time, position
in each dimension, and velocity in each dimension. Missing parameters
can only be generated in the following two cases:
- No velocity or time information is provided (i.e., there are
  no such columns or all values in corresponding columns are
  empty.) In this case, all velocity and time parameters will
  be generated.
- No position information is provided (i.e., there are no such columns
  or all values in the corresponding columns are empty.) In this case,
  all position values will be generated.
- Some or all velocity information is missing (i.e., there are no
  velocity columns at all, or there is a velocity column for
  each position column, and some or all values are empty.) In this
  case only the missing velocity parameters will be generated.

1-D, 2-D, and 3-D sample data is also provided and can be found in the
subdirectory "sample_data".
"""

import os

import pvt
from visualization import plot_path_and_trajectory

# ------------------- Script Settings ----------------------

DATA_DIRECTORY = "sample_data/position_velocity_time_data/"
"""The directory of the input file(s)"""
FILENAMES = ["wave_1d.csv", "spiral_2d.csv", "spiral_3d.csv"]
"""The names of the input files to read."""
TARGET_SPEED = 6
"""The target speed to use when generating velocities and times."""
TARGET_ACCEL = 10
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
        pvt_sequence = pvt.Sequence.from_csv(
            os.path.join(DATA_DIRECTORY, filename), TARGET_SPEED, TARGET_ACCEL
        )
        if SHOW_PLOTS:
            # Plot the sequence
            plot_path_and_trajectory(pvt_sequence)
        if OUTPUT_DIRECTORY is not None:
            # Write the file with the same name plus a _generated suffix
            base, extension = filename.rsplit(".", 1)
            output_filename = f"{base}_generated.{extension}"
            pvt_sequence.save_to_file(os.path.join(OUTPUT_DIRECTORY, output_filename))


if __name__ == "__main__":
    main()
