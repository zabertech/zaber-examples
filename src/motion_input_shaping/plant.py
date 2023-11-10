"""This file contains the Plant class that is used to define system parameters."""


class Plant:
    """A class that defines the parameters of a vibration system."""

    def __init__(self, resonant_frequency: float, damping_ratio: float) -> None:
        """
        Initialize the class.

        :param resonant_frequency: The system vibration resonant frequency in Hz.
        :param damping_ratio: The system vibration damping ratio.
        """
        self.resonant_frequency = resonant_frequency
        self.damping_ratio = damping_ratio

    @property
    def resonant_frequency(self) -> float:
        """Get the system resonant frequency for input shaping in Hz."""
        return self._resonant_frequency

    @resonant_frequency.setter
    def resonant_frequency(self, value: float) -> None:
        """Set the system resonant frequency for input shaping in Hz."""
        if value <= 0:
            raise ValueError(f"Invalid resonant frequency: {value}. Value must be greater than 0.")

        self._resonant_frequency = value

    @property
    def resonant_period(self) -> float:
        """Get the system resonant period for input shaping in s."""
        return 1.0 / self.resonant_frequency

    @property
    def damping_ratio(self) -> float:
        """Get the system damping ratio for input shaping."""
        return self._damping_ratio

    @damping_ratio.setter
    def damping_ratio(self, value: float) -> None:
        """Set the system damping ratio for input shaping."""
        if value < 0:
            raise ValueError(
                f"Invalid damping ratio: {value}. Value must be greater than or equal to 0."
            )
        self._damping_ratio = value
