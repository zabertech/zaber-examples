"""Text-based User Interface (TUI) for controlling Zaber devices."""

from textual.app import App, ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Button, Footer, Header, Label, TextLog, Input
from textual.message import Message
from connection_services import ConnectionServices

SERIAL_PORT = ""  # Default serial port
conn = ConnectionServices()


class TextMessage(Message):
    """Send Message to Text Log."""

    def __init__(self, msg: str) -> None:
        """Initialize custom message."""
        self.msg = msg
        super().__init__()


class ConnectionWidget(Widget):
    """Widget to connect to Zaber device."""

    connected = reactive(False)  # Used by the UI to render reactive elements

    def compose(self) -> ComposeResult:
        """Create the guts of the Connection Widget."""
        yield Label("Serial Port")
        yield Input(SERIAL_PORT, placeholder="Enter COM port")
        yield Button(id="connect", variant="primary")
        yield Label(id="status")

    def render(self) -> str:
        """Render the widget when a reactive variable changes."""
        status = self.query_one("#status", Label)
        button = self.query_one("#connect", Button)
        if self.connected:
            status.update("Status: Connected")
            button.label = "Disconnect"
        else:
            status.update("Status: Disconnected")
            button.label = "Connect"
        return ""

    def on_button_pressed(self) -> None:
        """Attempt connection to serial port."""
        port = self.query_one(Input)
        if conn.is_connected:
            message = conn.close()
        else:
            message = conn.open_serial(port.value)
        self.connected = conn.is_connected
        self.post_message(TextMessage(message))


class BasicMovement(Widget):
    """Area showing movement."""

    def compose(self) -> ComposeResult:
        """Create the basic layout."""
        yield Label("Basic Movement")
        yield Button("Home", variant="primary", id="home")
        yield Button("Left", variant="primary", id="left")
        yield Button("Right", variant="primary", id="right")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Execute when any button is pressed."""
        message = "Unknown error"
        if event.button.id == "home":
            message = conn.home()
        if event.button.id == "left":
            message = conn.move_rel(-2.0)
        if event.button.id == "right":
            message = conn.move_rel(+2.0)
        # self.text_log.write(message)
        self.post_message(TextMessage(message))


class LauncherApp(App[None]):
    """Main TUI application."""

    CSS_PATH = "tui.css"
    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("q", "quit", "Quit program"),
    ]

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield ConnectionWidget()
        yield BasicMovement()
        yield TextLog(id="textlog")
        yield Footer()

    def on_mount(self) -> None:
        """Execute on start up of widget."""
        self.post_message(TextMessage("Starting Up"))

    def on_text_message(self, text_message: TextMessage) -> None:
        """Event handler called automatically when TextMessage event happens."""
        text_log = self.query_one("#textlog", TextLog)
        text_log.write(f"Message: {text_message.msg}")


if __name__ == "__main__":
    app = LauncherApp()
    app.run()
