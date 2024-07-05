"""Scans all ports and returns list of Zaber devices on those ports.

Created 2022, Contributors: Nathan P
"""

import concurrent.futures

from zaber_motion.ascii import Connection
from zaber_motion import NoDeviceFoundException, Tools, SerialPortBusyException


class Scanner:
    """Class to scan available com ports and Zaber devices."""

    # pylint: disable=too-few-public-methods

    def __init__(self) -> None:
        """Initialize."""
        self.coms: dict[str, str] = {}

    def get_devices_and_coms(self) -> dict[str, str]:
        """Get available coms with connected device info."""
        # Pass each com port to a thread for device scanning
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            for com in Tools.list_serial_ports():
                executor.submit(self._scan_device_list, com)
        return self.coms

    def _scan_device_list(self, com: str) -> None:
        """Scan each available com port for devices and append list."""
        # pylint: disable=broad-exception-caught
        try:
            with Connection.open_serial_port(com) as connection:
                self.coms[com] = ", ".join(device.name for device in connection.detect_devices())
        except NoDeviceFoundException:
            pass
        except SerialPortBusyException:
            pass
        except Exception as err:
            print(err)


def main() -> None:
    """Run COM Port Scanner."""
    print("\nScanning...")
    for key, val in Scanner().get_devices_and_coms().items():
        print(key + ":", val)
