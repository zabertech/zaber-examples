# Direct Encoder Stage Self Test

*By Nathan Paolini*

These are scripts that can be run to allow a Zaber stage with a Direct Encoder (DE) to analyze its own performance.

![accuracy_plot.png](img/accuracy_plot.png)

## Hardware Requirements
A linear or rotary DE stage.

## Dependencies
- Python 3.10 or newer
- The script uses `venv` to manage virtual environment and dependencies.
- The dependencies are listed in the requirements.txt file.

## Configuration
Edit the following constants in the script to fit your setup before running the script:
- `SERIAL_PORT`: the serial port that your device is connected to.
For more information on how to identify the serial port,
see [Find the right serial port name](https://software.zaber.com/motion-library/docs/guides/find_right_port).
- `AXIS`: the axis number to test.

## Running the Scripts

### Windows
To setup `venv`, run `setup_venv.bat`.

To run the scripts:

    cd src\self_test_direct_encoder_stage
    .venv\Scripts\python accuracy.py
    .venv\Scripts\python settling_time.py

### Linux / MacOS
To setup `venv`:

    cd src/self_test_direct_encoder_stage
    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt

To run the scripts:

    .venv/bin/python accuracy.py
    .venv/bin/python settling_time.py

# Script Purpose
Zaber stages with direct encoders allow the stage to report on its own performance.

- `accuracy.py` allows a DE stage to test it's open loop accuracy or repeatability.
- `settling_time.py` allows a DE stage to determine its move-and-settle time for a variety of settings and step sizes.
