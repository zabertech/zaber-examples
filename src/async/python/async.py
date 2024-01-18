""" Zaber Motion Library advanced async usage example for C#. """
""" See ../README.md for more information. """
import asyncio

from zaber_motion import UnitTable
from zaber_motion.ascii import Connection


# Edit these constants to match your setup.
Port = "COM10"
XDeviceAddress = 1
XAxisNumber = 1
YDeviceAddress = 1
YAxisNumber = 2

XGridPoints = 4
YGridPoints = 4
GridSpacing = 5
GridSpacingUnits = UnitTable.get_unit("mm")


async def main() -> None:
    # Connections are disposable because they hold system resources (ie a serial port or network connection).
    # In an asynchronous program we recommend the "await with" statement to automatically close and dispose
    # the Connection's resources when finished with it.
    # If you cannot encapsulate all Zaber device use in a single code block like this, you should make sure
    # you manually close and dispose the Connection instance when your program is finished talking to devices.
    async with Connection.open_serial_port_async(Port) as connection:
        # Enabling alerts speeds up detection of the end of device movement, but may cause problems
        # for non-Zaber software communicating with the devices because it leaves them in a state
        # where they can generate spontaneous messages. It is recommended if you are only using
        # Zaber software (including the Zaber Motion Library).
        await connection.enable_alerts_async()

        # There is no async GetDevice because it just instantiates a device object
        # without communicating with anything.
        x_device = connection.get_device(XDeviceAddress)

        # Everywhere you await a Zaber async function call, you have the option to do some other
        # processing in parallel. Instead of using "await" immediately, you can assign the function's
        # return value to a Task variable and then await it later after doing something else. You can
        # also use Task.WhenAll() to wait for multiple async operations to complete.
        await x_device.identify_async()
        x_axis = x_device.get_axis(XAxisNumber)

        if (YDeviceAddress == XDeviceAddress):
            y_axis = x_device.get_axis(YAxisNumber)
        else:
            y_device = connection.get_device(YDeviceAddress)
            await y_device.identify_async()
            y_axis = y_device.get_axis(YAxisNumber)

        # Home the devices and wait until done.
        await asyncio.gather(x_axis.home_async(), y_axis.home_async())

        # Grid scan loop
        axes = [x_axis, y_axis]
        async for coords in grid(XGridPoints, YGridPoints):
            # Here's one way of controlling the devices in parallel. This loop potentially sends the
            # move commands and waits for the acknowledgements on different threads.
            for index in range(len(axes)):
                position = coords[index] * GridSpacing
                # Avoid the tempation to save the tasks in an array and await them as a group in the
                # case of movement commands, as the device may not be able to consume the commands as
                # fast as you can send them, and a system error may occur. Two or three should
                # be safe, as in the home command above.
                # Again, you can move the await to a later point in the loop if you want to.
                await axes[index].move_absolute_async(position, GridSpacingUnits, False)

            # At this point the axes are moving and we may have many milliseconds or seconds to
            # do other work (not shown).

            # Now when we need to be sure the devices have stopped moving, we can wait until they are idle.
            for axis in axes:
                await axis.wait_until_idle_async()

            # At this time the devices have all reached one of the target points and have stopped moving.
            # This is where you could insert some other code to do something like take a picture
            # or sample a well plate cell.
            print(f"At point { ', '.join([str(n) for n in coords]) }")


async def grid(x_points, y_points):
    """ Generates points in boustrophedon (serpentine, minimum-movement) order. """
    x = 0
    y = 0
    xDirection = 1
    while y < y_points:
        while x >= 0 and x < x_points:
            await asyncio.sleep(0.01) # Simulate true async coordinate generation.

            # Generating the points independently of sending the move commands like this
            # potentially causes extra device communication for unnecessary moves to the
            # same position, but it allows for a different program structure and the unnecessary
            # move commands could be filtered out later.  You could instead send the move
            # commands in the same double loop as the coordinate generation.
            yield [x, y]
            x += xDirection


        x -= xDirection
        xDirection *= -1
        y += 1


if __name__ == "__main__":
    asyncio.run(main())
