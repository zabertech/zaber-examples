# Gantry Calibration

*By Andrew Lau*

A Cartesian gantry or XY system serving a large area often requires calibration to achieve the
accuracy required.

This is a Python example showing how to take the expected and actual coordinates of a few points on
the gantry, and generate a mapping from desired coordinates to calibrated coordinates.

## Hardware Requirements
There is no hardware requirement for this example script, as it only demonstrates the algorithm
and visualizes the results in a plot.  However, the algorithm can be adapted to be used with any
Cartesian gantry or X-Y system, such as
[Zaber Technologies Gantry Systems](https://www.zaber.com/products/xy-xyz-gantry-systems/GANTRY)

## Dependencies / Software Requirements / Prerequisites
The script uses `pipenv` to manage virtual environment and dependencies:

    python3 -m pip install -U pipenv

The dependencies are listed in Pipfile.

## Running the Script
To run the script:

    cd src/gantry_calibration
    pipenv install
    pipenv run python calibrate.py

# How it works
The script consists of the following files,
- `main.py` - a script to be called on the command line, to generate random points
and demonstrates how `Calibration` works by plotting the coordinates before and after mapping.
- `calibration.py` - contains `Calibration` class, which can be used in other programs and applications
- `plot.py` - contains code to plot and visualize the effect of calibration.
