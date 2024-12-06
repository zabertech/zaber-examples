"""This program demonstrates how to use the "move track" command."""

from zaber_motion.ascii import Connection


SERIAL_PORT = "COM3"


def main() -> None:
    """Run the program."""
    with Connection.open_serial_port(SERIAL_PORT) as connection:
        device = connection.detect_devices()[0]
        axis = device.get_axis(1)
        if not axis.is_homed():
            raise RuntimeError("Axis must be homed before running this program")

        kp = axis.settings.get("motion.tracking.kp")
        ki = axis.settings.get("motion.tracking.ki")
        setpoint = axis.settings.get("motion.tracking.setpoint")
        print(f"Current PI settings: kp={kp}, ki={ki}, setpoint={setpoint}")

        while True:
            command = input("Command: ")
            match command:
                case "track":
                    axis.generic_command("move track")
                    print("Tracking...")
                case "stop" | "":
                    axis.stop()
                    print("Stopped")
                case "quit" | "q":
                    break
                case _:
                    print("Invalid command")


if __name__ == "__main__":
    main()
