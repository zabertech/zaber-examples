// Zaber Motion Library advanced async usage example for C#.
// Use "dotnet run" to run the program or open the .csproj file in Visual Studio and use the debugger to run it.
// See ../README.md for more information.

// This is an SDK-style project for simpler cross-platform compatibility.
// You do not have to set up your project exactly the same way.

using Zaber.Motion;
using Zaber.Motion.Ascii;

// Edit these constants to match your setup.
var Port = "COM10";
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
await using (var port = await Connection.OpenSerialPortAsync(Port))
{
    // There is no async GetDevice because it just instantiates a device object
    // without communicating with anything.
    var xDevice = port.GetDevice(XDeviceAddress);

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
        var yDevice = port.GetDevice(YDeviceAddress);
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
            await axes[index].MoveAbsoluteAsync(position, GridSpacingUnits, false);
        });

        // At this point the axes are moving and we may have many milliseconds or seconds to
        // do other work (not shown). Since this is all async code, the code for the other work
        // does not need to be written here; it could be running from some other async call
        // stack but sharing the same thread.

        // Here's another way to control multiple devices in parallel. Here we make a list of tasks
        // that wait for the device movements to finish, then wait for them all to complete.
        var tasks = Enumerable.Range(0, axes.Length).Select(index => axes[index].WaitUntilIdleAsync());
        await Task.WhenAll(tasks);

        // At this time the devices have reached one of the target points and have stopped moving.
        // Add a short delay at each point to simulate doing some work at the grid points.
        Console.WriteLine($"At point { string.Join(", ", coords.Select(n => n.ToString())) }");
        await Task.Delay(100);
    }
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
