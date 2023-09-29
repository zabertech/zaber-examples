"""
This file contains the ShapedConfig class, to specify settings for a ShapedAxis or ShapedLockstep class.

Run the file directly to test the class out with a Zaber Device.
"""

# pylint: disable=too-many-arguments
# This is not an issue.

from zero_vibration_stream_generator import ShaperType
from enum import Enum
import warnings


class ShaperMode(Enum):
    DECEL = 1
    STREAM = 2


class Settings(dict):
    """
    Settings class that is a dictionary where parameters can be accessed like a class
    """

    def __getstate__(self):
        return self

    def __setstate__(self, state):
        self.update(state)

    def __setitem__(self, key, value):
        if key not in self:
            raise KeyError(f"{key} is not a setting.")
        elif not isinstance(value, type(self[key])):
            # be strict about the type of values
            raise KeyError(f"Value provided for {key} must by of type {type(self[key])}.")
        else:
            super().__setitem__(key, value)

    __getattr__ = dict.__getitem__
    __setattr__ = __setitem__
    __delattr__ = dict.__delitem__

    def copy(self, **extra_params):
        return Settings(**self, **extra_params)


class ShaperConfig:
    """
    Configuration to class to select a shaper mode and specify settings
    """

    def __init__(self, shaper_mode: ShaperMode, **kwargs):
        """
        :param ShaperMode: Method to use to create shaping
        :param kwargs: Settings specified as keyword pairs
        """
        self.shaper_mode = shaper_mode
        self._write_settings(kwargs)  # process key word arguments and

    @property
    def shaper_mode(self) -> ShaperMode:
        return self._shaper_mode

    @shaper_mode.setter
    def shaper_mode(self, mode: ShaperMode) -> None:
        self._shaper_mode = mode

        # Initialize settings dictionary with default values for specific mode.
        # The type is fixed after being set so type needs to be explicit here (e.g. use 1 for int and 1.0 for float)
        match self.shaper_mode:
            case ShaperMode.DECEL:
                self.settings = Settings()
            case ShaperMode.STREAM:
                self.settings = Settings(shaper_type=ShaperType.ZV, stream_id=1)

    def _write_settings(self, settings_dictionary: dict):
        """
        Save relevant settings
        """
        for key in settings_dictionary:
            if key in self.settings:
                self.settings[key] = settings_dictionary[key]
            else:
                # Ignore settings that don't match existing dictionary item  but show warning
                warnings.warn(f"{key} is not a setting used for {self.shaper_mode.name} input shaping mode. "
                              f"Setting was ignored.")

    def set(self, **kwargs):
        self._write_settings(kwargs)


