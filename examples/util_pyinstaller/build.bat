call .venv\Scripts\activate.bat
pyinstaller --onefile --add-binary ".venv\Lib\site-packages\zaber_motion_bindings\zaber-motion-lib-windows-amd64.dll;zaber_motion_bindings" main.py
