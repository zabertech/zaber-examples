"""Creates flask HTTP server that serves the files and moves the device."""

import os
import sys
from flask import Flask, send_from_directory, send_file, typing as flask
from zaber_motion.ascii import Connection
from zaber_motion import (
    MotionLibException,
    MovementInterruptedException,
    ConnectionClosedException,
    ConnectionFailedException,
    RequestTimeoutException,
)

connection = Connection.open_serial_port(os.getenv("PORT") or "/dev/ttyUSB0")  # change serial port
device = connection.detect_devices()[0]
print("Device", device)

app = Flask(__name__)

HORIZONTAL_AXIS = 1
VERTICAL_AXIS = 2


@app.get("/")
def index() -> flask.ResponseReturnValue:
    """Serve index file."""
    return send_file("index.html", mimetype="text/html")


@app.route("/static/<path:path>")
def serve_static(path: str) -> flask.ResponseReturnValue:
    """Serve static directory."""
    return send_from_directory("static", path)


@app.post("/home")
def home() -> flask.ResponseReturnValue:
    """Home all axes."""
    device.all_axes.home()
    return ("", 204)


@app.post("/stop")
def move_stop() -> flask.ResponseReturnValue:
    """Stop all axes."""
    device.all_axes.stop()
    return ("", 204)


@app.post("/left")
def left() -> flask.ResponseReturnValue:
    """Move stage left."""
    device.get_axis(HORIZONTAL_AXIS).move_min()
    return ("", 204)


@app.post("/right")
def move_right() -> flask.ResponseReturnValue:
    """Move stage right."""
    device.get_axis(HORIZONTAL_AXIS).move_max()
    return ("", 204)


@app.post("/down")
def move_down() -> flask.ResponseReturnValue:
    """Move stage down."""
    device.get_axis(VERTICAL_AXIS).move_min()
    return ("", 204)


@app.post("/up")
def move_up() -> flask.ResponseReturnValue:
    """Move stage up."""
    device.get_axis(VERTICAL_AXIS).move_max()
    return ("", 204)


@app.get("/position")
def get_position() -> flask.ResponseReturnValue:
    """Return axes positions."""
    position = [device.get_axis(axis + 1).get_position("mm") for axis in range(2)]
    return ({"position": position}, 200)


@app.errorhandler(MotionLibException)
def handle_exception(err: MotionLibException) -> flask.ResponseReturnValue:
    """Handle motion library exceptions."""
    if isinstance(err, MovementInterruptedException):
        return ("", 204)
    if isinstance(err, (ConnectionClosedException, ConnectionFailedException)):
        sys.exit(1)

    if isinstance(err, RequestTimeoutException):
        code = 503
    else:
        code = 500
    return (err.message, code)


if __name__ == "__main__":
    from waitress import serve

    serve(app, host="0.0.0.0", port=8080)
