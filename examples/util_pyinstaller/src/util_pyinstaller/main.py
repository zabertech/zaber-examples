"""Simple example of using the Zaber Motion Library to move a device."""

from zaber_motion import Units
from zaber_motion.ascii import Connection

with Connection.open_serial_port("/dev/tty.usbserial-A10NFZD7") as connection:
    connection.enable_alerts()

    device_list = connection.detect_devices()
    print(f"Found {len(device_list)} devices")

    device = device_list[0]
    axis = device.get_axis(1)

    print("Moving...")
    if not axis.is_homed():
        axis.home()

    # Move to 10mm
    axis.move_absolute(10, Units.LENGTH_MILLIMETRES)

    # Move by an additional 5mm
    axis.move_relative(5, Units.LENGTH_MILLIMETRES)

input("Press Enter to continue...")
