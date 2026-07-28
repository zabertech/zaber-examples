"""Contains the FiberAlignment2D class to perform fiber alignment.

Tools to maximize an analog input signal with 2 Zaber axes.
"""

from dataclasses import dataclass

import numpy as np
from zaber_motion import Measurement, RotationDirection, Units
from zaber_motion.ascii import (
    Axis,
    Device,
    IoPortType,
    Stream,
    Trigger,
    TriggerAction,
    TriggerCondition,
    TriggerOperation,
)
from zaber_motion.exceptions import StreamMovementInterruptedException


@dataclass
class AlignmentResult:
    """A dataclass for alignment results."""

    position_1: float
    position_2: float
    signal: float
    success: float


class AlignmentSamples:
    """A class for output data from alignment."""

    def __init__(self) -> None:
        """Initialize the class."""
        self.position_1: list[float] = []
        self.position_2: list[float] = []
        self.signal: list[float] = []

    def add_sample(self, pos_1: float, pos_2: float, s: float) -> None:
        """Add a sample to the list of signals.

        :param pos_1: Position 1 value
        :param pos_2: Position 2 value
        :param s: Signal value
        """
        self.position_1.append(pos_1)
        self.position_2.append(pos_2)
        self.signal.append(s)


class DeviceAnalogInput:
    """A class to read the analog signal from a Zaber device."""

    def __init__(self, zaber_device: Device, analog_input_number: int, gain: float = 1, num_samples: int = 1) -> None:
        """Initialize the class.

        :param zaber_device: Zaber device object.
        :param analog_input_number: Analog input number on device.
        :param gain: Gain that multiply voltage by.
        :param num_samples: Number of samples to average when reading signal.
        """
        self.device = zaber_device
        self.io = zaber_device.io
        self.gain = gain
        self.analog_input_number = analog_input_number
        self.num_samples = num_samples

    def _get_sample(self) -> float:
        """Read the signal and multiply by the gain."""
        return self.io.get_analog_input(self.analog_input_number) * self.gain

    def get_signal(self) -> float:
        """Read the signal multiple times and return the average."""
        if self.num_samples == 1:
            return self._get_sample()
        else:
            samples: list[float] = []
            for _ in range(self.num_samples):
                samples.append(self._get_sample())
            return sum(samples) / len(samples)


class FiberAlignment2D:
    """A class to perform 2D fiber alignment with 2 Zaber axes."""

    def __init__(
        self,
        zaber_axis_1: Axis,
        zaber_axis_2: Axis,
        signal_input: DeviceAnalogInput,
    ) -> None:
        """Initialize the class.

        :param zaber_axis_1: Zaber Motion Axis object for first axis.
        :param zaber_axis_2: Zaber Motion Axis object for second axis.
        :param signal_input: The DeviceAnalogInput instance for the signal to maximize.
        """
        self.zaber_axis_1 = zaber_axis_1
        self.zaber_axis_2 = zaber_axis_2
        self.signal_input = signal_input

        # Initialize settings for streamed movement.
        # Initialize stream max speed and accel to 0 to use default settings.
        self._stream_max_speed = 0
        self._stream_max_accel = 0

        # Determine which setting to use for current stage position when searching for first light
        # with streamed motion and triggers.
        # Use to "encoder.pos" if both axes have encoders and "pos" otherwise.
        if self._check_encoder(self.zaber_axis_1) and self._check_encoder(self.zaber_axis_2):
            self.trigger_position_setting = "encoder.pos"
        else:
            self.trigger_position_setting = "pos"

    def set_stream_max_speed(self, max_speed: float, speed_unit: Units = Units.NATIVE) -> None:
        """Set max tangential movement speed used in streams."""
        self._stream_max_speed = self.zaber_axis_1.settings.convert_to_native_units("maxspeed", max_speed, speed_unit)

    def set_stream_max_accel(self, max_accel: float, accel_unit: Units = Units.NATIVE) -> None:
        """Set max tangential and centripetal acceleration used in streams."""
        accel = self.zaber_axis_1.settings.convert_to_native_units("accel", max_accel, accel_unit)
        self._stream_max_accel = accel

    def get_stream_max_speed(self, speed_unit: Units = Units.NATIVE) -> float:
        """Set max tangential movement speed used in streams."""
        return self.zaber_axis_1.settings.convert_to_native_units("maxspeed", self._stream_max_speed, speed_unit)

    def get_stream_max_accel(self, accel_unit: Units = Units.NATIVE) -> float:
        """Set max tangential and centripetal acceleration used in streams."""
        return self.zaber_axis_1.settings.convert_to_native_units("accel", self._stream_max_accel, accel_unit)

    def _check_encoder(self, zaber_axis: Axis) -> bool:
        """Check if axis has an encoder using encoder.mode.

        encoder.mode 0 means there is no encoder and 5 means it is disabled.
        """
        encoder_mode = zaber_axis.settings.get("encoder.mode")
        return encoder_mode not in {0, 5}

    def _check_single_device(self) -> bool:
        """Check if axes and io are all on the same device."""
        axis_1_device = self.zaber_axis_1.device
        axis_2_device = self.zaber_axis_2.device
        io_device = self.signal_input.device

        return (axis_1_device == axis_2_device) and (axis_1_device == io_device)

    def move_absolute(
        self,
        position_1: float,
        position_2: float,
        position_unit: Units = Units.NATIVE,
        *,
        wait_until_idle: bool = True,
    ) -> None:
        """Absolute move for both axes simultaneously.

        :param position_1: The amount to move x-axis.
        :param position_2: The amount to move y-axis.
        :param position_unit: The units for the position value.
        :param wait_until_idle: If true the command will hang until the device reaches idle state.
        """
        self.zaber_axis_1.move_absolute(position_1, position_unit, wait_until_idle=False)
        self.zaber_axis_2.move_absolute(position_2, position_unit, wait_until_idle=False)
        if wait_until_idle:
            self.zaber_axis_1.wait_until_idle()
            self.zaber_axis_2.wait_until_idle()

    def _move_abs_and_measure(
        self,
        position_1: float,
        position_2: float,
        position_unit: Units = Units.NATIVE,
    ) -> float:
        """Perform absolute move and take signal measurement."""
        self.move_absolute(position_1, position_2, position_unit)
        return self.signal_input.get_signal()

    def _print_sample(
        self,
        position_1: float,
        position_2: float,
        signal: float,
    ) -> None:
        print(f"  Position: [{position_1:.5f}, {position_2:.5f}], Signal: {signal:.4f}")

    def raster_scan(
        self,
        threshold: float,
        search_distance: float,
        resolution: float,
        length_unit: Units = Units.NATIVE,
        *,
        stop_at_threshold: bool = True,
    ) -> tuple[AlignmentResult, AlignmentSamples]:
        """Search for intial signal that exceeds the specified threshold with raster motion.

        :param search_distance: Distance away from starting point to search.
        :param resolution: Spacing of points to measure.
        :param length_unit: Units for `search_distance` and `resolution`
        :param threshold: Signal threshold to find.
        :param scan_type: Type of motion profile to use for search.
        :param stop_at_threshold: Stop search at threshold wihtout completing entire scan.
        """
        samples = AlignmentSamples()

        num_steps = int(np.ceil(2 * search_distance / resolution))
        init_pos = [
            self.zaber_axis_1.get_position(length_unit),
            self.zaber_axis_2.get_position(length_unit),
        ]

        start_pos = [init_pos[0] - search_distance, init_pos[1] - search_distance]

        current_signal = self._move_abs_and_measure(start_pos[0], start_pos[1], length_unit)
        samples.add_sample(start_pos[0], start_pos[1], current_signal)

        for n in range(num_steps + 1):
            self.zaber_axis_1.move_absolute(start_pos[0] + n * resolution, length_unit)
            for k in range(num_steps + 1):
                c1 = start_pos[0] + n * resolution
                if n % 2 == 0:
                    c2 = start_pos[1] + k * resolution
                else:
                    # On every sencond pass reverse direction
                    c2 = start_pos[1] + (num_steps - k) * resolution
                current_signal = self._move_abs_and_measure(c1, c2, length_unit)
                samples.add_sample(c1, c2, current_signal)
                self._print_sample(c1, c2, current_signal)

                if stop_at_threshold and current_signal >= threshold:
                    print("Signal found. Stopping scan...")
                    result = AlignmentResult(c1, c2, current_signal, current_signal >= threshold)
                    return result, samples

        max_idx = np.argmax(samples.signal)
        max_pos1 = samples.position_1[max_idx]
        max_pos2 = samples.position_2[max_idx]

        print("Moving to max signal position and remeasuring signal...")
        current_signal = self._move_abs_and_measure(max_pos1, max_pos2, length_unit)
        samples.add_sample(max_pos1, max_pos2, current_signal)
        self._print_sample(max_pos1, max_pos2, current_signal)

        result = AlignmentResult(max_pos1, max_pos2, current_signal, current_signal >= threshold)

        return result, samples

    def spiral_scan(
        self,
        threshold: float,
        search_distance: float,
        resolution: float,
        length_unit: Units = Units.NATIVE,
        *,
        stop_at_threshold: bool = True,
    ) -> tuple[AlignmentResult, AlignmentSamples]:
        """Search for intial signal that exceeds the specified threshold with square spiral motion.

        :param search_distance: Distance away from starting point to search.
        :param resolution: Spacing of points to measure.
        :param length_unit: Units for `search_distance` and `resolution`
        :param threshold: Signal threshold to find.
        :param scan_type: Type of motion profile to use for search.
        :param stop_at_threshold: Stop search at threshold wihtout completing entire scan.
        """
        samples = AlignmentSamples()

        num_steps = int(np.ceil(2 * search_distance / resolution))
        init_pos = [
            self.zaber_axis_1.get_position(length_unit),
            self.zaber_axis_2.get_position(length_unit),
        ]

        c1, c2 = init_pos

        current_signal = self._move_abs_and_measure(c1, c2, length_unit)
        samples.add_sample(c1, c2, current_signal)
        self._print_sample(c1, c2, current_signal)

        if stop_at_threshold and current_signal > threshold:
            print("Signal found. Stopping scan...")
        else:
            dx, dy = resolution, 0
            step_limit = 1
            steps_in_dir = 0
            dir_changes = 0

            # Total points in a (numSteps+1)x(numSteps+1) grid
            total_points = (num_steps + 1) ** 2

            for _ in range(total_points - 1):
                c1 += dx
                c2 += dy

                current_signal = self._move_abs_and_measure(c1, c2, length_unit)

                samples.add_sample(c1, c2, current_signal)
                self._print_sample(c1, c2, current_signal)

                if stop_at_threshold and current_signal >= threshold:
                    print("Signal found. Stopping scan...")
                    result = AlignmentResult(c1, c2, current_signal, current_signal >= threshold)
                    return result, samples

                steps_in_dir += 1
                if steps_in_dir == step_limit:
                    steps_in_dir = 0
                    dx, dy = -dy, dx  # rotate 90 deg clockwise
                    dir_changes += 1
                    if dir_changes % 2 == 0:
                        step_limit += 1

        max_idx = np.argmax(samples.signal)
        max_pos1 = samples.position_1[max_idx]
        max_pos2 = samples.position_2[max_idx]

        print("Moving to max signal position and remeasuring signal...")
        current_signal = self._move_abs_and_measure(max_pos1, max_pos2, length_unit)
        samples.add_sample(max_pos1, max_pos2, current_signal)
        self._print_sample(max_pos1, max_pos2, current_signal)

        result = AlignmentResult(max_pos1, max_pos2, current_signal, current_signal >= threshold)

        return result, samples

    def streamed_spiral_scan(
        self,
        first_light_threshold: float,
        trigger_threshold: float,
        search_distance: float,
        stepover_size: float,
        length_unit: Units = Units.NATIVE,
    ) -> AlignmentResult:
        """Search for intial signal using continuous circular sprial motion.

        Uses a stream to perform a continuous spiral motion and triggers to stop the motion
        when the `trigger_threshold` is exceeded.
        This search requires all axes and analog input to be controlled from a single device.
        The triggers records the positions, stops the axes, and returns to recorded positions.
        The `trigger_threshold` should be set sufficiently above the `first_light_threshold` to
        account for noise and motion error so that the signal is reliably above the required
        `first_light_threshold` when returning to the position where the trigger was fired.
        The analog input signal is not sampled multiple times and average so will be noisier.

        :param first_light_threshold: Minimum acceptable signal for final position.
        :param trigger_threshold: Signal threshold at which to trigger the stages to stop.
        :param search_distance: Distance away from starting point to search.
        :param stepover_size: Spacing between each spiral revolution.
        :param length_unit: Units for `search_distance` and `stepover_size`
        """
        if trigger_threshold < first_light_threshold:
            raise ValueError(  # noqa: TRY003
                "trigger_threshold must be greater than first_light_threshold "
                f"(got trigger_threshold = {trigger_threshold}, "
                f"first_light_threshold = {first_light_threshold})"
            )

        if self._check_single_device():
            zaber_device = self.zaber_axis_1.device
        else:
            raise ValueError(  # noqa: TRY003
                "Axes and IO must be controlled by the same device to support methods with "
                "streamed movements and triggers"
            )

        start_pos_1 = self.zaber_axis_1.get_position()
        start_pos_2 = self.zaber_axis_2.get_position()
        current_signal = self.signal_input.get_signal()

        # Convert to native units using first axis
        search_distance_native = self.zaber_axis_1.settings.convert_to_native_units("pos", search_distance, length_unit)
        stepover_size_native = self.zaber_axis_1.settings.convert_to_native_units("pos", stepover_size, length_unit)

        if current_signal < trigger_threshold:
            triggered = False
            trigger_1, trigger_2 = self._create_streamed_scan_triggers(zaber_device, trigger_threshold)

            stream = zaber_device.streams.get_stream(1)
            stream.setup_live(self.zaber_axis_1.axis_number, self.zaber_axis_2.axis_number)
            try:
                self._streamed_spiral(
                    stream,
                    [start_pos_1, start_pos_2],
                    search_distance_native,
                    stepover_size_native,
                )
            except StreamMovementInterruptedException:
                if trigger_1.get_enabled_state().enabled:
                    # If trigger hasn't fired then the motion was stopped for an unknown reason.
                    # clean up and re-raise the exception.
                    trigger_1.disable()
                    trigger_2.disable()
                    raise

                triggered = True
                print("Stream interrupted by trigger.")

                # Move back to triggered position after coming to stop
                self.move_absolute(
                    zaber_device.settings.get("user.data.0"),
                    zaber_device.settings.get("user.data.1"),
                )

                # Delete saved positions
                zaber_device.settings.set("user.data.0", 0)
                zaber_device.settings.set("user.data.1", 0)
            except:
                raise
            finally:
                # Stop all axes in case it is still moving
                zaber_device.generic_command("stop")
                stream.disable()
                # Make sure triggers are disabled
                trigger_1.disable()
                trigger_2.disable()

            current_signal = self.signal_input.get_signal()
        else:
            triggered = True

        c1 = self.zaber_axis_1.get_position(length_unit)
        c2 = self.zaber_axis_2.get_position(length_unit)
        self._print_sample(c1, c2, current_signal)
        if current_signal >= first_light_threshold:
            print("Sucessfully found first-light.")
        elif triggered:
            print("First-light detected but final signal is below first_light_threshold.")
        else:
            print("Did not find first-light.")

        return AlignmentResult(c1, c2, current_signal, current_signal >= first_light_threshold)

    def _set_stream_settings(self, stream: Stream) -> None:
        """Set speeds and accelerations in stream."""
        if self._stream_max_speed > 0:
            stream.set_max_speed(self._stream_max_speed)
        if self._stream_max_accel > 0:
            stream.set_max_centripetal_acceleration(self._stream_max_accel)
            stream.set_max_tangential_acceleration(self._stream_max_accel)

    def _streamed_spiral(
        self,
        stream: Stream,
        center_position: list[float],
        search_distance: float,
        stepover_size: float,
    ) -> None:
        """Add stream segments for a spiral to stream buffer."""
        num_revolutions = int(np.ceil(search_distance / stepover_size))

        stream.cork()

        self._set_stream_settings(stream)

        # Move to starting position
        stream.line_absolute(
            Measurement(center_position[0] + 0.5 * stepover_size, Units.NATIVE),
            Measurement(center_position[1], Units.NATIVE),
        )

        # Create sprial with arc segments
        for n in range(num_revolutions):
            arc_centre_abs = [
                center_position[0] - 0.25 * stepover_size,
                center_position[1],
            ]
            stream.arc_absolute(
                RotationDirection.CW,
                Measurement(arc_centre_abs[0], Units.NATIVE),
                Measurement(arc_centre_abs[1], Units.NATIVE),
                Measurement(center_position[0] - (n + 1) * stepover_size, Units.NATIVE),
                Measurement(center_position[1], Units.NATIVE),
            )

            arc_centre_abs = [
                center_position[0] + 0.25 * stepover_size,
                center_position[1],
            ]
            stream.arc_absolute(
                RotationDirection.CW,
                Measurement(arc_centre_abs[0], Units.NATIVE),
                Measurement(arc_centre_abs[1], Units.NATIVE),
                Measurement(
                    center_position[0] + (0.5 + (n + 1)) * stepover_size,
                    Units.NATIVE,
                ),
                Measurement(center_position[1], Units.NATIVE),
            )

        stream.uncork()
        stream.wait_until_idle()
        print("Stream complete. Returning to starting position...")
        self.move_absolute(center_position[0], center_position[1])

    def _create_streamed_scan_triggers(
        self,
        zaber_device: Device,
        trigger_threshold: float,
    ) -> tuple[Trigger, Trigger]:
        """Set up and return triggers for streamed movement scanning.

        Set up triggers to stop the motion and record the axis positions to
        user.data.0 and user.data.1.
        The position is taken from the `self.trigger_position_channel` setting.

        :param zaber_device: Instance of Zaber Device for axes and IO.
        :param trigger_threshold: Signal threshold at which to fire triggers.
        """
        # Clear user data that will be used to store positions
        zaber_device.settings.set("user.data.0", 0)
        zaber_device.settings.set("user.data.1", 0)

        trigger_voltage = trigger_threshold / self.signal_input.gain

        # Set up trigger to stop motion.
        trigger_1 = zaber_device.triggers.get_trigger(1)
        trigger_1.fire_when_io(
            IoPortType.ANALOG_INPUT,
            2,
            TriggerCondition.GE,
            trigger_voltage,
        )
        trigger_1.on_fire(TriggerAction.A, 0, "stop")
        trigger_1.enable(1)

        # Set up trigger to write current position to user data.
        trigger_2 = zaber_device.triggers.get_trigger(2)
        trigger_2.fire_when_io(
            IoPortType.ANALOG_INPUT,
            2,
            TriggerCondition.GE,
            trigger_voltage,
        )
        trigger_2.on_fire_set_to_setting(
            TriggerAction.A,
            0,
            "user.data.0",
            TriggerOperation.SET_TO,
            self.zaber_axis_1.axis_number,
            self.trigger_position_setting,
        )
        trigger_2.on_fire_set_to_setting(
            TriggerAction.B,
            0,
            "user.data.1",
            TriggerOperation.SET_TO,
            self.zaber_axis_2.axis_number,
            self.trigger_position_setting,
        )
        trigger_2.enable(1)

        return trigger_1, trigger_2

    def pattern_search(
        self,
        start_step: float,
        min_step: float,
        length_unit: Units = Units.NATIVE,
        max_iterations: int = 100,
    ) -> tuple[AlignmentResult, AlignmentSamples]:
        """Find maximum signal using a pattern search.

        Halves the step size when no improvement is found until reaching the minimumm step size.

        :param start_step: Starting step siz.
        :param min_step: Minimum step size.
        :param length_unit: Units for `start_step` and `min_step`
        :param max_iterations: Maximum number of iterations before stopping.
        """
        samples = AlignmentSamples()

        current_step = start_step

        # Get initial position and signal
        c1 = self.zaber_axis_1.get_position(length_unit)
        c2 = self.zaber_axis_2.get_position(length_unit)
        current_signal = self.signal_input.get_signal()

        print(f"Pattern Search: Step Size = {current_step:.6f}")
        for i in range(max_iterations):
            samples.add_sample(c1, c2, current_signal)

            improved = False

            # Offset position in each axis in postive and negative direction
            offsets = [(current_step, 0), (-current_step, 0), (0, current_step), (0, -current_step)]

            best_t1, best_t2 = c1, c2
            best_s = current_signal

            for dx, dy in offsets:
                t1, t2 = c1 + dx, c2 + dy

                s = self._move_abs_and_measure(t1, t2, length_unit)
                samples.add_sample(t1, t2, s)

                if s > best_s:
                    best_s = s
                    best_t1, best_t2 = t1, t2
                    improved = True

            # Move to the best position found in this iteration and resample
            current_signal = self._move_abs_and_measure(best_t1, best_t2, length_unit)
            c1, c2 = best_t1, best_t2

            if improved:
                self._print_sample(c1, c2, current_signal)
            else:
                # No improvement at this step size
                print("  No improvement found.")
                if current_step <= min_step:
                    break
                current_step = max(min_step, current_step / 2.0)
                print(f"Pattern Search: Step Size = {current_step:.6f}")

            if i == max_iterations - 1:
                print("Maximum number of iterations reached.")
                print("Stopping Pattern Search...")
                self._print_sample(c1, c2, current_signal)
                result = AlignmentResult(c1, c2, current_signal, success=False)
                return result, samples

        # Record final measurement
        samples.add_sample(c1, c2, current_signal)
        print("Pattern Search Complete.")
        self._print_sample(c1, c2, current_signal)
        result = AlignmentResult(c1, c2, current_signal, success=True)
        return result, samples

    def gradient_search(
        self,
        start_step: float,
        min_step: float,
        length_unit: Units = Units.NATIVE,
        max_iterations: int = 100,
    ) -> tuple[AlignmentResult, AlignmentSamples]:
        """Find maximum signal using gradient ascent.

        Halves the step size when no improvement is found until reaching the minimum step size.

        :param start_step: Starting step size.
        :param min_step: Minimum step size.
        :param length_unit: Units for `start_step` and `min_step`
        :param max_iterations: Maximum number of iterations before stopping.
        """
        samples = AlignmentSamples()

        current_step = start_step

        # Get initial position and signal
        c1 = self.zaber_axis_1.get_position(length_unit)
        c2 = self.zaber_axis_2.get_position(length_unit)
        s_base = self.signal_input.get_signal()

        samples.add_sample(c1, c2, s_base)

        print(f"Gradient Search: Step Size = {current_step:.6f}")
        for i in range(max_iterations):
            # Estimate gradient for axis 1
            s_plus1 = self._move_abs_and_measure(c1 + current_step, c2, length_unit)
            grad1 = (s_plus1 - s_base) / current_step
            samples.add_sample(c1 + current_step, c2, s_plus1)

            # Estimate gradient for axis 2
            s_plus2 = self._move_abs_and_measure(c1, c2 + current_step, length_unit)
            grad2 = (s_plus2 - s_base) / current_step
            samples.add_sample(c1, c2 + current_step, s_plus2)

            # Calculate gradient magnitude
            norm = np.sqrt(grad1**2 + grad2**2)

            improved = False

            if norm == 0:
                print("  Gradient is zero.")
            else:
                # Move in the direction of the gradient
                new1 = c1 + (grad1 / norm) * current_step
                new2 = c2 + (grad2 / norm) * current_step

                s = self._move_abs_and_measure(new1, new2, length_unit)
                samples.add_sample(new1, new2, s)

                if s > s_base:
                    improved = True
                    c1 = new1
                    c2 = new2
                    s_base = s
                    self._print_sample(c1, c2, s_base)

            if not (improved):
                print("  No improvement found.")
                # Move back to best position and retake measurement
                s_base = self._move_abs_and_measure(c1, c2, length_unit)
                samples.add_sample(c1, c2, s_base)

                # Next step size
                if current_step <= min_step:
                    break
                current_step = max(min_step, current_step / 2.0)
                print(f"Gradient Search: Step Size = {current_step:.6f}")

            if i == max_iterations - 1:
                print("Maximum number of iterations reached.")
                print("Stopping Gradient Search...")
                self._print_sample(c1, c2, s_base)
                result = AlignmentResult(c1, c2, s_base, success=False)
                return result, samples

        print("Gradient Search Complete.")
        self._print_sample(c1, c2, s_base)
        result = AlignmentResult(c1, c2, s_base, success=True)
        return result, samples
