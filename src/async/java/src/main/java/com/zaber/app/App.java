package com.zaber.examples;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.concurrent.CompletableFuture;
import java.util.stream.IntStream;

import zaber.motion.Units;
import zaber.motion.ascii.Axis;
import zaber.motion.ascii.Connection;
import zaber.motion.ascii.Device;

/**
 * Zaber Motion Library async usage example for Java.
 * See ../README.md for more information.
 *
 * This is a Maven project for simplicity. You do not have to set up your
 * project exactly this way.
 * You can use the Zaber Motion Library with any Java IDE that support Maven
 * dependencies.
 */
public class App {
    /* Edit these constants to match your setup. */
    public static final String Port = "COM10";
    public static final int XDeviceAddress = 1;
    public static final int XAxisNumber = 1;
    public static final int YDeviceAddress = 1;
    public static final int YAxisNumber = 2;

    public static final int XGridPoints = 4;
    public static final int YGridPoints = 4;
    public static final int GridSpacing = 5;
    public static final Units GridSpacingUnits = UnitTable.GetUnit("mm");

    public static void main(String[] args) {
        // If you're using a try-with-resources block, you can't use the async
        // versions of the Connection.open... methods because the connection instance
        // will likely get disposed before the open method returns.
        try (Connection connection = Connection.openSerialPort("COM10")) {
            // Enabling alerts speeds up detection of the end of device movement, but may cause problems
            // for non-Zaber software communicating with the devices because it leaves them in a state
            // where they can generate spontaneous messages. It is recommended if you are only using
            // Zaber software (including the Zaber Motion Library).
            connection.enableAlerts();

            // There is no async GetDevice because it just instantiates a device object
            // without communicating with anything.
            Device xDevice = connection.getDevice(XDeviceAddress);

            // Everywhere you call .get() on the Future returned by a Zaber async function call, you have
            // the option to do some other processing in parallel. Instead of using .get() immediately, you
            // can call it later after doing something else.
            // You can also use CompletableFuture.allOf(...).get() to wait for multiple async operations to complete.
            xDevice.IdentifyAsync().get();
            Axis xAxis = xDevice.GetAxis(XAxisNumber);

            Axis yAxis;
            if (YDeviceAddress == XDeviceAddress) {
                yAxis = xDevice.GetAxis(YAxisNumber);
            } else {
                Device yDevice = connection.getDevice(YDeviceAddress);
                yDevice.IdentifyAsync().get();
                yAxis = yDevice.GetAxis(YAxisNumber);
            }

            // Home the devices and wait until done.
            CompletableFuture.allOf(xAxis.HomeAsync(), yAxis.HomeAsync()).get();

            // Start a thread to generate the grid coordinates asynchronously.
            ArrayList<int[]> buffer = new ArrayList<int[]>();
            new Thread(() -> Grid(XGridPoints, YGridPoints, buffer)).start();

            // Grid scan loop
            Axis[] axes = { xAxis, yAxis };
            for (;;) {
                // Get next coordinates from the worker thread.
                int[] coords;
                synchronized (buffer) {
                    if (buffer.isEmpty()) {
                        Thread.sleep(10);
                        continue;
                    }

                    coords = buffer.remove(0);
                }

                if (coords.length == 0) {
                    break;
                }

                // Send each axis its new target position and wait for acknowledgement.
                IntStream.range(0, axes.Length).stream().map(index -> {
                    int position = coords[index] * GridSpacing;
                    // Avoid the tempation to save the futures in an array and await them as a group in the
                    // case of movement commands, as the device may not be able to consume the commands as
                    // fast as you can send them, and a system error may occur. Two or three should
                    // be safe, as in the home command above.
                    // Again you can move the .get() calls to a later point in this loop if you want to,
                    // but doing so in this case would cause delays between starting the moves on different axes.
                    // It's better to do your extra processing after starting all the moves.
                    axes[index].MoveAbsoluteAsync(position, GridSpacingUnits, false).get();
                });

                // At this point the axes are moving and we may have many milliseconds or seconds to
                // do other work (not shown).

                // Now when we need to be sure the devices have stopped moving, we can wait until they are idle.
                axes.forEach(axis -> {
                    // Another opportunity to insert more code before the .get().
                    axis.WaitUntilIdleAsync().get();
                });

                // At this time the devices have all reached one of the target points and have stopped moving.
                // This is where you could insert some other code to do something like take a picture
                // or sample a well plate cell.
                System.out.println(String.format("At point %s.", Arrays.toString(coords)));
            }
        }
    }


    // This function could be synchronous and return just an array of coordinates, or
    // (more commonly) you could generate the coordinates in the device control loop
    // above. This is example is contrived to simulate reading the coordinates from
    // an external source.
    private static void Grid(int xPoints, int yPoints, ArrayList<int[]> buffer) {
        // Generates points in boustrophedon (serpentine, minimum-movement) order.
        int x = 0, y = 0;
        int xDirection = 1;
        while (y < yPoints) {
            while (x >= 0 && x < xPoints) {
                Thread.sleep(10); // Simulate true async coordinate generation.

                // Generating the points independently of sending the move commands like this
                // potentially causes extra device communication for unnecessary moves to the
                // same position, but it allows for a different program structure and the unnecessary
                // move commands could be filtered out later.  You could instead send the move
                // commands in the same double loop as the coordinate generation.
                synchronized (buffer) {
                    buffer.add(new int[] { x, y });
                }

                x += xDirection;
            }

            x -= xDirection;
            xDirection *= -1;
            y++;
        }

        // Signal the end of the coordinate stream.
        synchronized (buffer) {
            buffer.add(new int[] { });
        }
    }
}