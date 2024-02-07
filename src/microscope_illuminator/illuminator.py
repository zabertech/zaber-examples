"""Example script for turning lamp on and off."""

import sys
import time

from zaber_motion.ascii import Connection, WarningFlags, Axis

SERIAL_PORT = "COMx"


def main() -> None:
    """Connect to a Zaber X-LCA with a connected MLR3 and sequentially turn on specific channels."""
    with Connection.open_serial_port(SERIAL_PORT) as connection:
        channels = {}
        device_list = connection.detect_devices()
        try:
            device = next(x for x in device_list if "LCA" in x.name)
            for i in range(1, 5):
                lamp = device.get_axis(i)
                if WarningFlags.PERIPHERAL_INACTIVE not in lamp.warnings.get_flags():
                    # Channel is properly activated, list available channels
                    color = int(lamp.settings.get("lamp.wavelength.peak"))
                    if color == 0:
                        color_name = "white"
                    else:
                        color_name = str(color)

                    channels[color_name] = lamp
                    print(f"Channel # {i} is {lamp.peripheral_name}")

        except StopIteration:
            print("No LCA available")
            sys.exit()

        def set_intensity(
            channel: Axis, percent: float = 100, flux_watts: float | None = None
        ) -> None:
            """Set the intensity of MLR channels. Only do this once to minimize comms delays.

            :param channel: MLR lamp axis object
            :param percent: Value between 0 and 100 as a fraction of max LED intensity
            :param flux_watts: (Optional) If you know the luminous flux in watts directly
            """
            max_flux = channel.settings.get("lamp.flux.max")
            if flux_watts is not None:
                channel.settings.set("lamp.flux", flux_watts)
            else:
                channel.settings.set("lamp.flux", max_flux * percent / 100)

        def pulse_channel(channel: Axis, duration: float = 50) -> bool:
            """Pulse a MLR led channel for a given duration.

            :param channel: Axis object for the lamp to activate
            :param duration: On time in ms
            """
            channel.generic_command(f"lamp on {duration}")
            time.sleep(duration / 1000)
            return True

        for wavelength, led in channels.items():
            set_intensity(led, 98.7)
            if wavelength != "385":  # Don't flash UV during testing
                print(f"Pulsing channel {wavelength}")
                for i in range(10):
                    pulse_channel(led, 43.5)
                    time.sleep(0.1)


if __name__ == "__main__":
    main()
