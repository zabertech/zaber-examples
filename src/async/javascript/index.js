const { Length, ascii: { Connection }} = require('@zaber/motion');

async function main() {
  const connection = await Connection.openSerialPort('COM4');
  try {
    await connection.enableAlerts();

    const deviceList = await connection.detectDevices();
    console.log(`Found ${deviceList.length} devices.`);

    const device = deviceList[0];

    const axis = device.getAxis(1);
    await axis.home();

    // Move to 10mm
    await axis.moveAbsolute(10, Length.mm);

    // Move by an additional 5mm
    await axis.moveRelative(5, Length.mm);

  } finally {
    // close the port to allow Node.js to exit
    await connection.close();
  }
}

main();
