:: This script is automatically run on startup of the GUI if the GUI script detects that the `ui_raw.ui` file has been editted (in Qt Designer)
:: The `ui_raw.ui` file is then converted to `ui.py` which is a more useful representation of the UI that includes type hints and can be imported into the GUI script

cd .venv/Scripts
call activate
cd "../.."
python -m PyQt6.uic.pyuic -o src/gui_pyqt6/ui.py ui_raw.ui
