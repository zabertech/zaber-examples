"""Configuration settings for the force mode demo."""

from force_mode_demo.models import DeviceSetup, LoadCellSetup

# Please replace the values here based on your particular load cell calibration data
LOAD_CELL_CONFIG = LoadCellSetup(
    lc_slope_n_per_v=3.62,  # Load cell calibration lc_slope_n_per_v [N/V]
    lc_offset_v=0.5,  # Load cell calibration lc_offset_v [V]
    lc_max_force_n=20.0,  # Maximum safe load for the load cell [N]
    mcc_analog_in=1,  # X-MCC analog input port connected to load cell
)

# Please replace the values here based on your wiring to the controller
XMCC_CONFIG = DeviceSetup(
    serial_port="COM5",  # Controller serial port (update as needed)
    force_axis_index=2,  # Controller axis index for the force axis
    translation_axis_index=1,  # Controller axis index for the translation axis
)
