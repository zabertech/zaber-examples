"""Zaber Motion Library advanced async usage example for Python."""
import asyncio
from typing import AsyncIterator, List

from zaber_motion import Units, UnitTable
from zaber_motion.ascii import Connection

# See ../README.md for more information.

# Edit these constants to match your setup.
PORT = "COM4"
X_DEVICE_ADDRESS = 1
X_AXIS_NUMBER = 1
Y_DEVICE_ADDRESS = 1
Y_AXIS_NUMBER = 2

X_GRID_POINTS = 4
Y_GRID_POINTS = 4
GRID_SPACING = 5
GRID_SPACING_UNITS = UnitTable.get_unit("mm")


async def main() -> None:
    """Demonstrate async iteration and Zaber Motion Library usage."""
    # Connections are disposable because they hold system resources (ie a serial port or network
    # connection). In an asynchronous program we recommend the "async with" statement to
    # automatically close and dispose the Connection when finished with it.
    #
    # If you cannot encapsulate all Zaber device use in a single code block like this, you should
    # make sure you manually close and dispose the Connection instance when your program is
    # finished talking to devices.
    async with Connection.open_serial_port_async(PORT) as connection:
        # Enabling alerts speeds up detection of the end of device movement, but may cause problems
        # for non-Zaber software communicating with the devices because it leaves them in a state
        # where they can generate spontaneous messages. It is recommended if you are only using
        # Zaber software (including the Zaber Motion Library).
        await connection.enable_alerts_async()

        # There is no async GetDevice because it just instantiates a device object
        # without communicating with anything.
        x_device = connection.get_device(X_DEVICE_ADDRESS)

        # Everywhere you await a Zaber async function call, you have the option to do some other
        # processing in parallel. Instead of using "await" immediately, you can assign the
        # function's return value to a variable and then await it later after doing something else.
        # You can also use asyncio.gather(...) to wait for multiple async operations to complete.
        identify_task = x_device.identify_async()
        # Could do something else here.
        await identify_task  # Block until the identify_async() call completes.
        x_axis = x_device.get_axis(X_AXIS_NUMBER)

        if Y_DEVICE_ADDRESS == X_DEVICE_ADDRESS:
            y_axis = x_device.get_axis(Y_AXIS_NUMBER)
        else:
            y_device = connection.get_device(Y_DEVICE_ADDRESS)
            await y_device.identify_async()
            y_axis = y_device.get_axis(Y_AXIS_NUMBER)

        # Home the devices and wait until done.
        # This is an example of overlapping async commands. Order of execution is not
        # guaranteed and with more than two or three there is a risk of a device error.
        await asyncio.gather(x_axis.home_async(), y_axis.home_async())

        # Grid scan loop
        axes = [x_axis, y_axis]
        async for coords in grid(X_GRID_POINTS, Y_GRID_POINTS):
            # Here's one way of controlling the devices in parallel. This loop potentially sends the
            # move commands and waits for the acknowledgements on different threads.
            for index, axis in enumerate(axes):
                position = coords[index] * GRID_SPACING
                # Avoid the tempation to save the tasks in an array and await them as a group in the
                # case of movement commands, as the device may not be able to consume the commands
                # as fast as you can send them, and a system error may occur. Two or three should
                # be safe, as in the home command above.
                # Again, you can move the await to a later point in the loop if you want to.
                await axis.move_absolute_async(position, Units(GRID_SPACING_UNITS), False)

            # At this point the axes are moving and we may have many milliseconds or seconds to
            # do other work (not shown).

            # Now when we need to be sure the devices have stopped moving, we can wait until they
            # are idle.
            for axis in axes:
                await axis.wait_until_idle_async()

            # At this time the devices have all reached one of the target points and have stopped
            # moving. This is where you could insert some other code to do something like take a
            # picture or sample a well plate cell.
            print(f"At point { ', '.join([str(n) for n in coords]) }")

    # The connection will automatically be closed at the end of the "with" block.


# This function could be synchronous and return just an array of coordinates, or
# (more commonly) you could generate the coordinates in the device control loop
# above. This is example is contrived to simulate reading the coordinates from
# an external source.
async def grid(x_points: int, y_points: int) -> AsyncIterator[List[int]]:
    """Generate points in boustrophedon (serpentine, minimum-movement) order."""
    x = 0
    y = 0
    x_direction = 1
    while y < y_points:
        while 0 <= x < x_points:
            await asyncio.sleep(0.01)  # Simulate true async coordinate generation.

            # Generating the points independently of sending the move commands like this
            # potentially causes extra device communication for unnecessary moves to the
            # same position, but it allows for a different program structure and the
            # unnecessary move commands could be filtered out later.  You could instead
            # send the move commands in the same double loop as the coordinate generation.
            yield [x, y]
            x += x_direction

        x -= x_direction
        x_direction *= -1
        y += 1


if __name__ == "__main__":
    asyncio.run(main())
