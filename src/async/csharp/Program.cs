// Zaber Motion Library advanced async usage example for C#.
// See ../README.md for more information.

// This is an SDK-style project for simpler cross-platform compatibility.
// You do not have to set up your project exactly the same way.

using Zaber.Motion;
using Zaber.Motion.Ascii;

// Edit these constants to match your setup.
var Port = "COM4";
var XDeviceAddress = 1;
var XAxisNumber = 1;
var YDeviceAddress = 1;
var YAxisNumber = 2;

var XGridPoints = 4;
var YGridPoints = 4;
var GridSpacing = 5;
var GridSpacingUnits = UnitTable.GetUnit("mm");


// Connections are disposable because they hold system resources (ie a serial port or network connection).
// In an asynchronous program we recommend the "await using" statement to automatically close and dispose
// the Connection's resources when finished with it.
// However, this is not available .NET Framework programs, so in that case you can use the normal using statement.
// If you cannot encapsulate all Zaber device use in a single code block like this, you should make sure
// you manually close and dispose the Connection instance when your program is finished talking to devices.
//
// Note "await using" is only supported with ZML 5.0.0 or later under .NET or .NET Standard.
// For other configurations remove both "await" statements from this line.
await using (var connection = await Connection.OpenSerialPortAsync(Port))
{
    // Enabling alerts speeds up detection of the end of device movement, but may cause problems
    // for non-Zaber software communicating with the devices because it leaves them in a state
    // where they can generate spontaneous messages. It is recommended if you are only using
    // Zaber software (including the Zaber Motion Library).
    connection.EnableAlerts();

    // There is no async GetDevice because it just instantiates a device object
    // without communicating with anything.
    var xDevice = connection.GetDevice(XDeviceAddress);

    // Everywhere you await a Zaber async function call, you have the option to do some other
    // processing in parallel. Instead of using "await" immediately, you can assign the function's
    // return value to a Task variable and then await it later after doing something else. You can
    // also use Task.WhenAll() to wait for multiple async operations to complete.
    await xDevice.IdentifyAsync();
    var xAxis = xDevice.GetAxis(XAxisNumber);

    Axis yAxis;
    if (YDeviceAddress == XDeviceAddress)
    {
        yAxis = xDevice.GetAxis(YAxisNumber);
    }
    else
    {
        var yDevice = connection.GetDevice(YDeviceAddress);
        await yDevice.IdentifyAsync();
        yAxis = yDevice.GetAxis(YAxisNumber);
    }

    // Home the devices and wait until done.
    await Task.WhenAll(xAxis.HomeAsync(), yAxis.HomeAsync());

    // Grid scan loop
    Axis[] axes = [xAxis, yAxis];
    await foreach (var coords in Grid(XGridPoints, YGridPoints))
    {
        // Here's one way of controlling the devices in parallel. This loop potentially sends the
        // move commands and waits for the acknowledgements on different threads.
        await Parallel.ForEachAsync(Enumerable.Range(0, axes.Length), async (index, _) =>
        {
            var position = coords[index] * GridSpacing;
            // Avoid the tempation to save the tasks in an array and await them as a group in the
            // case of movement commands, as the device may not be able to consume the commands as
            // fast as you can send them, and a system error may occur. Two or three should
            // be safe, as in the home command above.
            // Again, you can move the await to a later point in the loop if you want to.
            await axes[index].MoveAbsoluteAsync(position, GridSpacingUnits, false);
        });

        // At this point the axes are moving and we may have many milliseconds or seconds to
        // do other work (not shown).

        // Now when we need to be sure the devices have stopped moving, we can wait until they are idle.
        foreach(var axis in axes)
        {
            await axis.WaitUntilIdleAsync();
        }

        // At this time the devices have all reached one of the target points and have stopped moving.
        // This is where you could insert some other code to do something like take a picture
        // or sample a well plate cell.
        Console.WriteLine($"At point { string.Join(", ", coords.Select(n => n.ToString())) }");
    }

    // With ZML versions prior to 5.0.0 the program could freeze when disposing the Connection.
    // The workaround was to await any non-ZML task before disposing the Connection.
    // await Task.Delay(0);
}


// This function could be synchronous and return IEnumerable instead, in which case you would have
// to use the result with the normal "foreach" keyword above. This example has been made artificially
// asynchronous to demonstrate the usage; a real-world example would be streaming the coordinates
// from a file or network connection.
static async IAsyncEnumerable<int[]> Grid(int xPoints, int yPoints)
{
    // Generates points in boustrophedon (serpentine, minimum-movement) order.
    int x = 0, y = 0;
    int xDirection = 1;
    while (y < yPoints)
    {
        while (x >= 0 && x < xPoints)
        {
            await Task.Delay(10); // Simulate true async coordinate generation.

            // Generating the points independently of sending the move commands like this
            // potentially causes extra device communication for unnecessary moves to the
            // same position, but it allows for a different program structure and the unnecessary
            // move commands could be filtered out later.  You could instead send the move
            // commands in the same double loop as the coordinate generation.
            yield return new int[] { x, y };
            x += xDirection;
        }

        x -= xDirection;
        xDirection *= -1;
        y++;
    }
}