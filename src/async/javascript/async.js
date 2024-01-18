const { UnitTable, ascii: { Connection }} = require('@zaber/motion');

// Edit these constants to match your setup.
const PORT = "COM4";
const X_DEVICE_ADDRESS = 1;
const X_AXIS_NUMBER = 1;
const Y_DEVICE_ADDRESS = 1;
const Y_AXIS_NUMBER = 2;

const X_GRID_POINTS = 4;
const Y_GRID_POINTS = 4;
const GRID_SPACING = 5;
const GRID_SPACING_UNITS = UnitTable.getUnit("mm");


async function main() {
  // Javascript's "with" statement is not widely used and is unsupported in some environments.
  // Another way to ensure a system resource (the connection instance in this case) is closed is to
  // put all usage of it inside a try block and close it in the finally block. This structure
  // is only useful in a small program like this where all usage of the resource is in one place.
  // In a larger program you might store the connection in an object and explicitly close it
  // when your program shuts down.
  // Note the call to open the connection in this example is not inside the try block because
  // it would not make sense to close it in the finally block if it failed to open. Therefore
  // this example will throw an unhandled exception if the port cannot be opened. (It will also
  // throw all exceptions as unhandled because there is no catch block, but it will close the
  // connection first.)
  const connection = await Connection.openSerialPort(PORT);
  try {
    // Enabling alerts speeds up detection of the end of device movement, but may cause problems
    // for non-Zaber software communicating with the devices because it leaves them in a state
    // where they can generate spontaneous messages. It is recommended if you are only using
    // Zaber software (including the Zaber Motion Library).
    await connection.enableAlerts();

    // GetDevice is not async because it just instantiates a device object
    // without communicating with anything.
    const xDevice = connection.getDevice(X_DEVICE_ADDRESS);

    // Everywhere you await a Zaber async function call, you have the option to do some other
    // processing in parallel. Instead of using "await" immediately, you can assign the function's
    // returned Promise to a variable and then await it later after doing something else. You can
    // also use await Promise.All() to wait for multiple async operations to complete.
    await xDevice.identify();
    const xAxis = xDevice.getAxis(X_AXIS_NUMBER);

    let yAxis;
    if (Y_DEVICE_ADDRESS == X_DEVICE_ADDRESS) {
      yAxis = xDevice.getAxis(Y_AXIS_NUMBER);
    } else {
      const yDevice = connection.getDevice(Y_DEVICE_ADDRESS);
      // Unlike the other languages supported by the Zaber Motion Library, there are no
      // synchronous versions of the asynchronous methods. This is because asynchronous programming
      // is the default in JavaScript.
      await yDevice.identify();
      yAxis = yDevice.getAxis(Y_AXIS_NUMBER);
    }

    // Home the devices and wait until done.
    await Promise.all([xAxis.home(), yAxis.home()]);

    // Grid scan loop
    const axes = [xAxis, yAxis];
    for await (const coords of grid(X_GRID_POINTS, Y_GRID_POINTS)) {
      // Here's one way of controlling the devices in parallel. This loop sends the
      // move commands and waits for the acknowledgements for each axis independently.
      for (let index of axes.keys()) {
        var position = coords[index] * GRID_SPACING;
        // Avoid the tempation to save the tasks in an array and await them as a group in the
        // case of movement commands, as the device may not be able to consume the commands as
        // fast as you can send them, and a system error may occur. Two or three should
        // be safe, as in the home command above.
        // Again, you can move the await to a later point in the loop if you want to.
        await axes[index].moveAbsolute(position, GRID_SPACING_UNITS, false);
      };

      // At this point the axes are moving and we may have many milliseconds or seconds to
      // do other work (not shown).

      // Now when we need to be sure the devices have stopped moving, we can wait until they are idle.
      for (const axis of axes) {
        await axis.waitUntilIdle();
      }

      // At this time the devices have all reached one of the target points and have stopped moving.
      // This is where you could insert some other code to do something like take a picture
      // or sample a well plate cell.
      console.log(`At point ${coords.map(n => n.toString()).join(', ')}`);
    }

  } finally {
    // close the port to allow Node.js to exit
    await connection.close();
  }
}


// This function could be synchronous and return just an array of coordinates, or
// (more commonly) you could generate the coordinates in the device control loop
// above. This is example is contrived to simulate reading the coordinates from
// an external source.
async function* grid(xPoints, yPoints) {
    // Generates points in boustrophedon (serpentine, minimum-movement) order.
    let x = 0, y = 0;
    let xDirection = 1;
    while (y < yPoints) {
      while (x >= 0 && x < xPoints) {
        await new Promise(r => setTimeout(r, 10)); // Simulate true async coordinate generation with a sleep.

        // Generating the points independently of sending the move commands like this
        // potentially causes extra device communication for unnecessary moves to the
        // same position, but it allows for a different program structure and the unnecessary
        // move commands could be filtered out later.  You could instead send the move
        // commands in the same double loop as the coordinate generation.
        yield await Promise.resolve([x, y]);
        x += xDirection;
      }

      x -= xDirection;
      xDirection *= -1;
      y++;
    }
}

main();
