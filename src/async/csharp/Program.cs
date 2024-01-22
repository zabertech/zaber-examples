// Zaber Motion Library advanced async usage example for C#.
// See ../README.md for more information.

// This is an SDK-style project for simpler cross-platform compatibility.
// You do not have to set up your project exactly the same way.

using Zaber.Motion;
using Zaber.Motion.Ascii;

// Edit these constants to match your setup.
const string PORT = "COM4";
const int X_DEVICE_ADDRESS = 1;
const int X_AXIS_NUMBER = 1;
const int Y_DEVICE_ADDRESS = 1;
const int Y_AXIS_NUMBER = 2;

const int X_GRID_POINTS = 4;
const int Y_GRID_POINTS = 4;
const int GRID_SPACING = 5;
var GRID_SPACING_UNITS = UnitTable.GetUnit("mm");


// Connections are disposable because they hold system resources (ie a serial port or network connection).
// In an asynchronous program we recommend the "await using" statement to automatically close and dispose
// the Connection's resources when finished with it.
// However, this is not available in .NET Framework programs, so in that case you can use the normal using
// statement with a non-async connection open function.
// If you cannot encapsulate all Zaber device use in a single code block like this, you should make sure
// you manually close and dispose the Connection instance when your program is finished talking to devices.
//
// Note "await using" is only supported with ZML 5.0.0 or later under .NET or .NET Standard.
// For other configurations remove both "await" statements from this line.
await using (var connection = await Connection.OpenSerialPortAsync(PORT))
{
    // Enabling alerts speeds up detection of the end of device movement, but may cause problems
    // for non-Zaber software communicating with the devices because it leaves them in a state
    // where they can generate spontaneous messages. It is recommended if you are only using
    // Zaber software (including the Zaber Motion Library).
    connection.EnableAlerts();

    // There is no async GetDevice because it just instantiates a device object
    // without communicating with anything.
    var xDevice = connection.GetDevice(X_DEVICE_ADDRESS);

    // Everywhere you await a Zaber async function call, you have the option to do some other
    // processing in parallel. Instead of using "await" immediately, you can assign the function's
    // return value to a Task variable and then await it later after doing something else. You can
    // also use Task.WhenAll() to wait for multiple async operations to complete.
    var identifyTask = xDevice.IdentifyAsync();
    // Could do something else here.
    await identifyTask; // Block until IdentifyAsync() completes.
    var xAxis = xDevice.GetAxis(X_AXIS_NUMBER);

    Axis yAxis;
    if (Y_DEVICE_ADDRESS == X_DEVICE_ADDRESS)
    {
        yAxis = xDevice.GetAxis(Y_AXIS_NUMBER);
    }
    else
    {
        var yDevice = connection.GetDevice(Y_DEVICE_ADDRESS);
        await yDevice.IdentifyAsync();
        yAxis = yDevice.GetAxis(Y_AXIS_NUMBER);
    }

    // Home the devices and wait until done.
    // This is an example of overlapping async commands. Order of execution is not
    // guaranteed and with more than two or three there is a risk of a device error.
    await Task.WhenAll(xAxis.HomeAsync(), yAxis.HomeAsync());

    // Grid scan loop
    Axis[] axes = [xAxis, yAxis];
    await foreach (var coords in Grid(X_GRID_POINTS, Y_GRID_POINTS))
    {
        // Here's one way of controlling the devices in parallel. This loop potentially sends the
        // move commands and waits for the acknowledgements on different threads. There is a
        // risk of overlapping too many commands this way; it's only safe here because this
        // example only controls two axes. This pattern is not appropriate for more than three;
        // use a non-parallel loop in such cases.
        await Parallel.ForEachAsync(Enumerable.Range(0, axes.Length), async (index, _) =>
        {
            var position = coords[index] * GRID_SPACING;
            // Avoid the tempation to save the tasks in an array and await them as a group in the
            // case of movement commands, as the device may not be able to consume the commands as
            // fast as you can send them, and a system error may occur. Two or three should
            // be safe, as in the home command above.
            // Again, you can move the await to a later point in the loop if you want to.
            await axes[index].MoveAbsoluteAsync(position, GRID_SPACING_UNITS, false);
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

    // The connection will automatically be closed and disposed at the end of the "using" block.
    // With ZML versions prior to 5.0.0 the program could freeze here when disposing the Connection.
    // The workaround was to await any non-ZML task before disposing the Connection, for example:
    // await Task.Delay(0);
}


// This function could be synchronous and return IEnumerable instead, in which case you would have
// to use the result with the non-async "foreach" keyword above. This example has been made artificially
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
            // move commands could be filtered out later. You could instead send the move
            // commands in the same double loop as the coordinate generation.
            yield return new int[] { x, y };
            x += xDirection;
        }

        x -= xDirection;
        xDirection *= -1;
        y++;
    }
}
