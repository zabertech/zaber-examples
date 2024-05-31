"""Started PyQt GUI for controlling a Zaber stage."""

# Initial imports that are necessary for launch
from pathlib import Path
import subprocess
import time

from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import QThread, QEvent, Qt, pyqtSignal
from PyQt6.QtWidgets import QApplication, QMainWindow, QSplashScreen

# Pre-launch tasks
if __name__ == "__main__":
    # Re-generate ui.py, if UI modified in QT Designer
    current_ui, prev_ui = Path("ui_raw.ui"), Path("ui_raw_compare.ui")
    if current_ui.read_text(encoding="utf-8") != prev_ui.read_text(encoding="utf-8"):
        print("\nUpdating Python UI file:")
        prev_ui.unlink()
        prev_ui.write_bytes(current_ui.read_bytes())
        print(subprocess.check_output("UI_py_convert.bat"))
        raise SystemExit("UI Re-built. Please start again.")

    # Show splash screen
    APP = QApplication([])
    splash_pic = QPixmap("images/zaber_splash.png")
    SPLASH = QSplashScreen(splash_pic, Qt.WindowType.WindowStaysOnTopHint)  # noqa
    SPLASH.setMask(splash_pic.mask())
    SPLASH.show()
    APP.processEvents()

# Rest of imports. These load while splash screen is visible.
from zaber_motion import Units
from zaber_motion.ascii import Connection, Axis, AxisType

import ui

SERIAL_PORT = "COMx"
AXIS_NUM = 1


class UIExtended(ui.Ui_MainWindow):
    """Take Qt Designer UI and add other necessary components to complete the GUI."""

    def __init__(self) -> None:
        """Set up UI."""
        self.main_window = QMainWindow(flags=Qt.WindowType.Window)  # noqa
        super().setupUi(self.main_window)

        self.message_label.setText("")


class UpdateThread(QThread):
    """A thread to generate plot images in the background using ploty standard."""

    update_ui_pos = pyqtSignal(float)  # noqa
    thread_exception = pyqtSignal(str)  # noqa

    def __init__(self, stage: Axis, main_window: QMainWindow, stage_units: Units) -> None:
        """Set up thread."""
        super().__init__(main_window)
        self.stage = stage
        self.stage_units = stage_units
        self.thread_data = None
        self.thread_metadata = None
        self.skip_spec_lookup = False
        self.exception_message_displayed = False
        self.quit = False

    def run(self) -> None:
        """Start the thread."""
        while True:
            try:
                if self.quit:
                    return
                time.sleep(0.005)
                self.update_ui_pos.emit(self.stage.get_position(self.stage_units))
                if self.exception_message_displayed:
                    self.exception_message_displayed = False
                    self.thread_exception.emit("")
            except Exception as err:
                self.exception_message_displayed = True
                self.thread_exception.emit(str(err))


class MyProgram:
    """Main Program."""

    def __init__(self) -> None:
        """Set up and launch the GUI."""
        # Load the UI
        self.ui = UIExtended()
        self.ui.main_window.closeEvent = self.window_close_event

        self.pause_updates = False
        self.slider_max_val = self.ui.stage_pos_slider.maximum()
        self.stage, self.stage_units = self._connect_to_zaber_stage()
        self.limit_min, self.limit_max = self._determine_relevant_stage_travel_limits()
        self.travel = self.limit_max - self.limit_min

        self._connect_ui_signals()
        self.update_thread = self._setup_and_start_polling_thread()

        self.ui.main_window.show()

    def _connect_ui_signals(self) -> None:
        """Connect user interaction signals coming from the UI to the relevant functions."""
        self.ui.stage_pos_slider.sliderPressed.connect(self.user_moving_slider)
        self.ui.stage_pos_slider.sliderReleased.connect(self.user_finished_slider_move)
        self.ui.stage_pos_slider.sliderMoved.connect(self.slider_moved)
        self.ui.stage_pos_slider.valueChanged.connect(self.slider_moved)
        self.ui.home_btn.clicked.connect(self.home_stage)

    @staticmethod
    def _connect_to_zaber_stage() -> tuple[Axis, Units]:
        """Connect to the Zaber device and determine its relevant units."""
        connection = Connection.open_serial_port(SERIAL_PORT)
        devices = connection.detect_devices()
        stage = devices[0].get_axis(AXIS_NUM)
        stage_units = (
            Units.ANGLE_DEGREES if stage.axis_type is AxisType.ROTARY else Units.LENGTH_MILLIMETRES
        )
        return stage, stage_units

    def _determine_relevant_stage_travel_limits(self) -> tuple[float, float]:
        """Determine appropriate limits of stage travel to use as bounds for the slider."""
        limit_min = (
            0
            if self.stage.axis_type is AxisType.ROTARY
            else self.stage.settings.get("limit.min", self.stage_units)
        )
        limit_max = (
            360
            if self.stage.axis_type is AxisType.ROTARY
            else self.stage.settings.get("limit.max", self.stage_units)
        )
        return limit_min, limit_max

    def _setup_and_start_polling_thread(self) -> UpdateThread:
        """Initialize the polling thread and start watching stage position."""
        update_thread = UpdateThread(self.stage, self.ui.main_window, self.stage_units)
        update_thread.update_ui_pos.connect(self.update_display_pos)
        update_thread.thread_exception.connect(self.display_thread_exception)
        update_thread.start()
        return update_thread

    def update_display_pos(self, pos: float) -> None:
        """Update the position text output and slider."""
        if self.pause_updates:
            return
        new_pos_string = f"{pos:.2f}"
        if new_pos_string != self.ui.stage_pos_line_edit.text():
            new_slider_pos = int(pos / self.travel * self.slider_max_val)
            self.ui.stage_pos_slider.setSliderPosition(new_slider_pos)
            self.ui.stage_pos_line_edit.setText(new_pos_string)

    def display_thread_exception(self, exception_msg: str) -> None:
        """Update the message below the slider if there is an error."""
        self.ui.message_label.setText(exception_msg)

    def user_moving_slider(self) -> None:
        """Stop updates while user is dragging slider."""
        self.pause_updates = True

    def user_finished_slider_move(self) -> None:
        """Move stage to requested position."""
        new_pos = self.ui.stage_pos_slider.value() / self.slider_max_val * self.travel
        self.stage.move_absolute(new_pos, self.stage_units, wait_until_idle=False)
        self.pause_updates = False

    def slider_moved(self, slider_pos: int) -> None:
        """Update position line edit based on how much user has dragged slider."""
        new_pos_str = f"{slider_pos / self.slider_max_val * self.travel:.2f}"
        self.ui.stage_pos_line_edit.setText(new_pos_str)

    def home_stage(self) -> None:
        """Home the connected Zaber stage."""
        try:
            self.stage.home(wait_until_idle=False)
        except Exception as err:
            self.ui.message_label.setText(str(err))

    def window_close_event(self, event: QEvent) -> None:
        """Safely shut down GUI."""
        self.stage.stop()
        self.update_thread.quit = True
        self.stage.device.connection.close()
        event.accept()


if __name__ == "__main__":
    # Launch GUI
    gui = MyProgram()
    SPLASH.close()  # noqa

    # Styling
    APP.setStyle("Fusion")  # noqa
    APP.setStyleSheet(open("style.css", encoding="utf-8").read())

    # Wait in event loop
    APP.exec()
