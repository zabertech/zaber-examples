call .venv\Scripts\activate.bat
pyinstaller --onefile --add-binary ".venv\Lib\site-packages\zaber_motion_bindings;zaber_motion_bindings" src/util_pyinstaller/main.py
