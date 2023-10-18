"""
This file contains the ShapedConfig class which is used to specify settings for a ShapedAxis or
ShapedLockstep class.

Run the file directly to test the class out with a Zaber Device.
"""

# pylint: disable=too-many-arguments
# This is not an issue.

import warnings
from enum import Enum
from typing import Any
from zero_vibration_stream_generator import ShaperType


class ShaperMode(Enum):
    """Enumeration for different shaper modes"""

    DECEL = 1
    STREAM = 2


class Settings(dict[str, Any]):
    """
    Settings class that is a dictionary where creating new entries is not allowed and the value
    type must match the type of the existing value
    """

    def __setitem__(self, key: str, value: Any) -> None:
        if key not in self:
            raise KeyError(f"{key} is not a setting.")

        if not isinstance(value, type(self[key])):
            # be strict about the type of values
            raise KeyError(f"Value provided for {key} must by of type {type(self[key])}.")

        super().__setitem__(key, value)


class ShaperConfig:
    """
    Configuration to class to select a shaper mode and specify settings
    """

    def __init__(self, shaper_mode: ShaperMode, **options: Any):
        """
        :param ShaperMode: Method to use to create shaping
        :param options: Settings specified as keyword pairs
        """
        self.shaper_mode = shaper_mode
        self._write_settings(options)  # process key word arguments and

    @property
    def shaper_mode(self) -> ShaperMode:
        """Get shaper mode"""
        return self._shaper_mode

    @shaper_mode.setter
    def shaper_mode(self, mode: ShaperMode) -> None:
        """Set shaper mode"""
        self._shaper_mode = mode

        # Initialize settings dictionary with default values for specific mode.
        # The type is fixed after being set so type needs to be explicit here
        # (e.g. use 1 for int and 1.0 for float)
        match self.shaper_mode:
            case ShaperMode.DECEL:
                self.settings = Settings()
            case ShaperMode.STREAM:
                self.settings = Settings(shaper_type=ShaperType.ZV, stream_id=1)

    def _write_settings(self, settings_dictionary: dict[str, Any]) -> None:
        """
        Save relevant settings to dictionary
        """
        for key in settings_dictionary:
            if key in self.settings:
                self.settings[key] = settings_dictionary[key]
            else:
                # Ignore settings that don't match existing dictionary item  but show warning
                warnings.warn(
                    f"{key} is not a setting used for {self.shaper_mode.name} input shaping mode. "
                    f"Setting was ignored."
                )

    def set(self, **options: Any) -> None:
        """Set settings using keyword arguments"""
        self._write_settings(options)
