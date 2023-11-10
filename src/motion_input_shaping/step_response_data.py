"""This file contains the StepResponseData class for re-use in other code."""
from typing import Callable, Any
from zaber_motion import Units
from zaber_motion.ascii import Axis, Lockstep


class StepResponseData:
    """
    This is a helper class for using the Zaber Motion Library Oscilloscope for step response tests.

    It performs a specified motion with the device while logging target and measured positions.
    Note: this class requires a Zaber product with a direct encoder in order to properly
    capture position data.
    """

    def __init__(
        self,
        timebase: float,
        time_units: Units = Units.TIME_MILLISECONDS,
        length_units: Units = Units.LENGTH_MICROMETRES,
        max_capture_length: int = 0,
    ):
        """
        Initialize the class.

        :param timebase: The scope sampling time (spacing of datapoints).
        :param time_units: The time units for scope sampling time and captured data.
        :param length_units: The length units for captured position data.
        :param max_capture_length: The max number of datapoints to capture, or 0 to fill the
        memory completely.
        """
        self.timebase = timebase
        self.time_units = time_units
        self.length_units = length_units
        self.max_capture_length = max_capture_length

        self.time_stamps: list[float] = []
        self.target_positions: list[float] = []
        self.measured_positions: list[float] = []

    def capture_data(
        self,
        axis: Axis | Lockstep,
        motion_function: Callable[[], Any],
        return_to_start: bool = True,
    ) -> None:
        """
        Execute the movement and fill the class data fields with collected data.

        :param axis: The Zaber axis which will perform the movement collect data.
        :param motion_function: A function which specifies how the axis will move. The axis is
        passed as a parameter.
        :param return_to_start: If true, the axis will return to it's starting position after the
        data is captured.
        """
        if isinstance(axis, Lockstep):
            axis_number = axis.get_axis_numbers()[0]  # Scope primary axis
        else:
            axis_number = axis.axis_number

        # Setup the scope
        scope = axis.device.oscilloscope
        scope.clear()
        scope.add_channel(axis_number, "pos")
        scope.add_channel(axis_number, "encoder.pos")
        scope.set_timebase(self.timebase, self.time_units)

        # Get the starting position in case we want to move back
        starting_position = axis.get_position(self.length_units)

        # Start the scope and run the desired motion function
        print("Starting capture.")

        if self.max_capture_length > 0:
            scope.start(self.max_capture_length)
        else:
            scope.start()

        motion_function()
        print("Capture complete. Transferring data...")

        # Get the data
        data = scope.read()
        print("Scope data transfer complete.")

        # Return to the starting position
        if return_to_start:
            axis.move_absolute(starting_position, self.length_units, True)

        # Reset all the existing data
        self.time_stamps = []
        self.target_positions = []
        self.measured_positions = []

        # Populate the data in the class
        for data_channel in data:
            if data_channel.axis_number == axis_number and data_channel.setting == "pos":
                self.target_positions = data_channel.get_data(self.length_units)

                # Calculate the timestamps at each target position (they will be the same for all
                # channels
                for i in range(len(self.target_positions)):
                    self.time_stamps.append(data_channel.get_sample_time(i, self.time_units))

            if data_channel.axis_number == axis_number and data_channel.setting == "encoder.pos":
                self.measured_positions = data_channel.get_data(self.length_units)

    def get_time_stamps(self) -> list[float]:
        """Get the collected time data in class specified time units."""
        return self.time_stamps

    def get_target_positions(self, normalize: bool = False) -> list[float]:
        """
        Get the collected target position data in class specified time units.

        :param normalize: If true, the data will be normalized so the final position is always zero.
        """
        if normalize:
            return self._normalize_positions(self.target_positions)

        return self.target_positions

    def get_measured_positions(self, normalize: bool = False) -> list[float]:
        """
        Get the measured position data from the axes encoder in class specified time units.

        :param normalize: If true, the data will be normalized so the final position is always
        zero.
        """
        if normalize:
            return self._normalize_positions(self.measured_positions)

        return self.measured_positions

    def _normalize_positions(self, positions: list[float]) -> list[float]:
        """
        Normalize the input dataset so it will be zeroed around the final target position.

        :param positions: The position dataset to normalize.
        :return: The normalized dataset.
        """
        if len(self.target_positions) == 0:  # if we have no data then cancel early
            return list(positions)

        final_position = self.target_positions[-1]
        direction = (final_position - self.target_positions[0]) / abs(
            final_position - self.target_positions[0]
        )

        return [(x - final_position) * direction for x in positions]

    def get_trajectory_end_index(self) -> int:
        """
        Calculate the index when the trajectory in the dataset reaches it's final position.

        :return: The trajectory end time in the input time units
        """
        # Find the index when we reach the final position
        motion_end_index = 0

        for target_position in self.target_positions:
            if target_position == self.target_positions[-1]:
                break

            motion_end_index += 1

        return motion_end_index

    def get_trajectory_settling_limits(
        self, normalize: bool = False, buffer: float = 0.05
    ) -> list[float]:
        """
        Calculate Y axis limits to center the plot on the axes' final position after moving.

        :param normalize: If true, the data will be normalized so the final position is always zero.
        :param buffer: A fractional buffer value by which to expand the limits.
        :return: The min and max y values for the plot.
        """
        # Get the limits of the data set after the trajectory ends
        motion_end_index = self.get_trajectory_end_index()
        measured_final_position = self.get_measured_positions(normalize)[motion_end_index:]

        # Add a small buffer to the limits
        buffer = (max(measured_final_position) - min(measured_final_position)) * buffer / 2.0

        return [min(measured_final_position) - buffer, max(measured_final_position) + buffer]

    def get_trajectory_end_time(self) -> float:
        """
        Calculate the time when the trajectory in the dataset reaches its final position.

        :return: The trajectory end time in the input time units
        """
        return self.get_time_stamps()[self.get_trajectory_end_index()]
