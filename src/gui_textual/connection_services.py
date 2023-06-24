"""The business logic of connecting and communicating with devices."""

from zaber_motion.ascii import Connection, Device, Axis
from zaber_motion.exceptions import ConnectionFailedException, CommandFailedException


class ConnectionServices:
    """Provide connection services to devices in a singleton."""

    def __init__(self) -> None:
        """Initialize ConnectionServices."""
        self._connection: Connection | None = None
        self._device_list: list[Device] = []
        self._device: Device | None = None
        self._axis: Axis | None = None

    def open_serial(self, port: str) -> str:
        """Open a serial port."""
        self.close()
        try:
            self._connection = Connection.open_serial_port(port)
        except ConnectionFailedException:
            return "Unable to open serial port."
        self._connection.enable_alerts()
        self._device_list = self._connection.detect_devices()
        self._device = self._device_list[0]
        self._axis = self._device.get_axis(1)
        return f"Connected to {self._connection}"

    @property
    def is_connected(self) -> bool:
        """Check to see if serial port is connected."""
        return self._connection is not None

    def close(self) -> str:
        """Close serial port."""
        if self._connection:
            self._connection.close()
            self._connection = None
            self._device_list = []
            self._device = None
            self._axis = None
        return "Serial port closed."

    def home(self) -> str:
        """Home device."""
        if self._axis:
            self._axis.home()
            return "Homing device."
        return "No device connected; unable to home."

    def move_rel(self, rel: float) -> str:
        """Move device by relative distance in mm."""
        if not self._axis:
            return "No device connected; unable to move."
        try:
            self._axis.move_relative(rel, "mm")
        except CommandFailedException:
            return "Unable to move device; perhaps movement exceeded travel range?"
        return f"Moving device by {rel} mm"
