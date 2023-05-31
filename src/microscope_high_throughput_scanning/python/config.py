"""Constants for defining optimized stage settings and example protocols."""

from typing import Any
from zaber_motion import Units

STAGE_TUNING: dict[str, Any] = {
    "X-ADR130": {
        "accel_upper": 23,  # Acceleration of upper axis [m/s^2]
        "accel_lower": 9,  # Lower axis [m/s^2]
        "non_default_settings": [
            ("cloop.settle.tolerance", 1, Units.LENGTH_MICROMETRES),  # Settle tolerance [um]
            ("cloop.timeout", 50, Units.TIME_MILLISECONDS),  # Settle period [ms]
            ("maxspeed", 750, Units.VELOCITY_MILLIMETRES_PER_SECOND),  # Maximum speed
        ],
    },
    "X-ASR100B120B-SE03D12": {
        "accel_upper": 10,
        "accel_lower": 5,
        "non_default_settings": [
            ("driver.current.run", 80),  # Higher run current for better acceleration
            ("cloop.timeout", 50, Units.TIME_MILLISECONDS),
            ("maxspeed", 100, Units.VELOCITY_MILLIMETRES_PER_SECOND),
            ("motion.accel.ramptime", 25),
        ],
    },
    "X-ASR305": {
        "accel_upper": 12,
        "accel_lower": 5,
        "non_default_settings": [
            ("driver.current.run", 2, Units.AC_ELECTRIC_CURRENT_AMPERES_RMS),
            ("cloop.settle.period", 50, Units.TIME_MILLISECONDS),
        ],
    },
}

SCAN_PROTOCOLS: dict[str, Any] = {
    "TDI_96_wellplate": {
        "exposure": 500,  # Exposure duration, microseconds
        "mag": 2.5,  # Effective system magnification
        "scanning_speed": 0,  # Scanning speed [mm/s], set to 0 to compute using Nyquist criterion
        "origin": (0, 0),  # Position when top left corner of FOV is aligned with the scan area
        "area": (106, 63),  # (X,Y) dimensions [mm] of the area to be scanned
        "mode": "TDI",  # Operating modes: TDI, area (stop-and-shoot), continuous
    },
    "area_coverslip": {
        "exposure": 50000,
        "mag": 5,
        "scanning_speed": 500,
        "origin": (40, 40),
        "area": (22, 22),
        "mode": "area",
    },
    "continuous_slide": {
        "exposure": 127,
        "mag": 2.5,
        "scanning_speed": 20,
        "origin": (50, 10),
        "area": (25, 60),
        "mode": "continuous",
    },
}

CAMERAS: dict[str, Any] = {
    "BFS200S6M": {
        "sensor_height": 8.8,
        "sensor_width": 13.2,  # in mm, long axis of a rectangular sensor
        "pixel_um": 2.4,  # Sensor pixel size in micron
    },
    "Dhyana9KTDI": {
        "sensor_height": 1.28,
        "sensor_width": 30,
        "pixel_um": 5,
    },
}
