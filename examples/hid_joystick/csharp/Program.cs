// This example was largely based on the "game loop" example from the HIDDevices package:
// https://github.com/DevDecoder/HIDDevices/blob/master/HIDDevices.Sample/Samples/GameLoopSample.cs

// This example program demonstrates using gamepad joysticks and buttons to interactively
// control Zaber stages. It will detect one gamepad attached to the system and map the
// four analog stick axes to velocities of the first four Zaber stages found on the
// selected serial port. The port default can be changed by editing the
// code or using the -p NAME command line argument.

using Microsoft.Extensions.Logging;
using System.Text;

using DevDecoder.HIDDevices;
using DevDecoder.HIDDevices.Controllers;

using Zaber.Motion;
using Zaber.Motion.Ascii;

using AsciiDevice = Zaber.Motion.Ascii.Device; // HIDDevices also defines the name Device.


namespace Joystick
{
    internal class Program
    {
        static void Main(string[] args)
        {
            HandleCommandLine(args);
            _deviceLog = CreateLogger<Devices>(LogLevel.Error);
            _log = CreateLogger<Program>(LogLevel.Information);

            // Get the first gamepad connected.
            using var devices = new Devices(_deviceLog);
            Gamepad? gamepad = null;

            // This input library detects devices asynchronously; start the process here.
            using var subscription = devices.Controllers<Gamepad>().Subscribe(g =>
            {
                if (gamepad?.IsConnected == true)
                {
                    return;
                }

                gamepad = g;
                g.Connect();
                _log.LogInformation($"{gamepad.Name} found!");
            });

            // Identify Zaber axes on the selected serial port.
            using var connection = Connection.OpenSerialPort(_port);
            var axes = DetectZaberStages(connection).ToArray();
            if (axes.Length < 1)
            {
                _log.LogError($"No movable Zaber axes detected on port {_port}!");
                return;
            }

            var numAxes = Math.Min(axes.Length, STICK_AXIS_NAMES.Length);
            var sb = new StringBuilder();
            sb.AppendLine("Gamepad axes will control stages as follows:");
            for (var i = 0; i < numAxes; i++)
            {
                var axis = axes[i].axis;
                var device = axis.Device;
                sb.Append($"{STICK_AXIS_NAMES[i, 0]} -> Device ");
                sb.Append($"{device.DeviceAddress} ({device.Name}) ");
                sb.AppendLine($"axis {axis.AxisNumber} ({axis.PeripheralName})");
            }
            sb.AppendLine("Press the X button to home all devices.");
            sb.AppendLine("Press the B button to stop all devices.");
            sb.AppendLine("Press the Start button or CTRL-C to end the program.");
            _log.LogInformation(sb.ToString());

            var timestamp = 0L;
            var stickPositions = new double[STICK_AXIS_INDICES.Count];
            Array.Fill(stickPositions, 0.0);

            try
            {
                while (true)
                {
                    if (gamepad?.IsConnected != true)
                    {
                        _log.LogError("No gamepad detected yet; waiting. Press CTRL-C to exit.");
                        Thread.Sleep(1000);
                        continue;
                    }
                    else
                    {
                        Thread.Sleep(15);
                    }

                    // Process any gamepad stick axis events since the last pass.
                    var stickChanged = false;
                    foreach (var value in gamepad?.ChangesSince(timestamp) ?? new List<ControlValue>())
                    {
                        timestamp = Math.Max(timestamp, value.Timestamp);

                        if (value.Value is double x && STICK_AXIS_INDICES.ContainsKey(value.PropertyName))
                        {
                            var axisIndex = STICK_AXIS_INDICES[value.PropertyName];
                            if (axisIndex < numAxes)
                            {
                                stickPositions[axisIndex] = x;
                                stickChanged = true;
                            }
                        }
                    }

                    try
                    {
                        // Handle buttons first.
                        if (gamepad!.Start)
                        {
                            _log.LogInformation("Start Button pressed; exiting.");
                            break;
                        }
                        else if (gamepad.XButton)
                        {
                            _log.LogInformation("Homing all devices.");
                            // Overlap the home commands so they will complete faster.
                            for (int i = 0; i < numAxes; i++)
                            {
                                axes[i].axis.Home(false);
                            }

                            for (int i = 0; i < numAxes; i++)
                            {
                                axes[i].axis.WaitUntilIdle();
                            }
                        }
                        else if (gamepad.BButton)
                        {
                            _log.LogInformation("Stopping all devices.");
                            for (int i = 0; i < numAxes; i++)
                            {
                                axes[i].axis.Stop(false);
                            }

                            for (int i = 0; i < numAxes; i++)
                            {
                                axes[i].axis.WaitUntilIdle();
                            }
                        }
                        else if (stickChanged)
                        {
                            // Translate stick deflections to axis velocities.
                            for (int i = 0; i < numAxes; i++)
                            {
                                var speed = axes[i].speed * ScaledDeflection(stickPositions[i]);
                                string message = $"Setting device {axes[i].axis.Device.DeviceAddress} axis {axes[i].axis.AxisNumber} speed to {speed}";
                                _log.LogInformation(message);
                                axes[i].axis.MoveVelocity(speed);
                            }
                        }
                    }
                    catch (MotionLibException e)
                    {
                        _log.LogError("There was an error sending commands to a device.", e);
                    }
                }
            }
            finally
            {
                gamepad?.Dispose();
            }
        }


        private static void HandleCommandLine(string[] args)
        {
            for (int i = 0; i < args.Length; i++)
            {
                // The only supported argument is "-p NAME" to set the serial port.
                if ((args[i] == "-p" || args[i] == "--port") && i < args.Length - 1)
                {
                    _port = args[i + 1];
                    i++;
                }
            }
        }


        private static ILogger<T> CreateLogger<T>(LogLevel minimum)
        {
            var loggerFactory = LoggerFactory.Create(builder =>
            {
                builder.SetMinimumLevel(minimum)
                       .AddSimpleConsole(options =>
                       {
                           options.IncludeScopes = false;
                       });
            });

            return loggerFactory.CreateLogger<T>();
        }


        private struct AxisAndSpeed
        {
            public Axis axis;
            public double speed;
        }


        private static IEnumerable<AxisAndSpeed> DetectZaberStages(Connection conn)
        {
            var axes = new List<AxisAndSpeed>();

            AsciiDevice[] devices = Array.Empty<AsciiDevice>();
            try
            {
                devices = conn.DetectDevices();
            }
            catch (MotionLibException)
            {
                _log!.LogError($"There was an error communicating with the connection.");
            }

            foreach (var device in devices)
            {
                for (var i = 0; i < device.AxisCount; i++)
                {
                    var axis = device.GetAxis(i + 1);
                    if (axis.Identity.AxisType != AxisType.Unknown)
                    {
                        try
                        {
                            var speed = axis.Settings.Get("maxspeed");
                            axes.Add(new AxisAndSpeed()
                            {
                                axis = axis,
                                speed = speed,
                            });
                        }
                        catch (MotionLibException)
                        {
                            _log!.LogWarning($"There was an error while querying device {device.DeviceAddress} axis {axis.AxisNumber}; ignoring.");
                        }
                    }
                }
            }

            return axes;
        }


        private static double ScaledDeflection(double deflection)
        {
            // The input library we're using scales the joystick axis deflections into the range [-1, 1]
            // but for a nicer user experience we want a dead zone and a cubic curve on the input to allow
            // finer control at low speeds.

            if (deflection == 0.0)
            {
                return 0.0;
            }

            const double DEAD_ZONE = 0.2;
            var sign = Math.Sign(deflection);
            var scaled = (Math.Max(DEAD_ZONE, Math.Abs(deflection)) - DEAD_ZONE) / (1.0 - DEAD_ZONE);
            return sign * Math.Pow(scaled, 3);
        }


        private static ILogger<Devices>? _deviceLog;
        private static ILogger<Program>? _log;
        private static string _port = "COMx";

        private static readonly string[,] STICK_AXIS_NAMES =
        {
            { "Left stick horizontal axis", "X" },
            { "Left stick vertical axis", "Y" },
            { "Right stick horizontal axis", "Rx" },
            { "Right stick vertical axis", "Ry" },
        };

        private static readonly Dictionary<string, int> STICK_AXIS_INDICES = new()
        {
            { "X", 0 },
            { "Y", 1 },
            { "Rx", 2 },
            { "Ry", 3 },
        };
	}
}
