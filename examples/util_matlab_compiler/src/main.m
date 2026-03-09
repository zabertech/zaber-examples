function main()
    % Simple example of using the Zaber Motion Library to move a device.
    import zaber.motion.Units;
    import zaber.motion.ascii.Connection;

    connection = Connection.openSerialPort("COM5");
    cleanup = onCleanup(@() connection.close());

    connection.enableAlerts();

    deviceList = connection.detectDevices();
    fprintf('Found %d devices\n', length(deviceList));

    device = deviceList(1);
    axis = device.getAxis(1);

    disp("Moving...");
    if ~axis.isHomed()
        axis.home();
    end

    % Move to 10mm
    axis.moveAbsolute(10, Units.LengthMillimetres);

    % Move by an additional 5mm
    axis.moveRelative(5, Units.LengthMillimetres);

    input("Press Enter to continue...", "s");
end
