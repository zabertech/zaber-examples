# Packaging ZML with PyInstaller

*By Martin Zak*

This example demonstrates how to package a Python script that uses Zaber Motion Library with PyInstaller.
The script itself in `main.py` is a simple motion example.

## PyInstaller

PyInstaller is a tool to package Python scripts into standalone executables.
When used with Zaber Motion Library the shared library (.dll, .so, or .dylib) file must be explicitly included in the package.
The command below taken from `build.bat` demonstrates how to include the library.

```ps1
pyinstaller --onefile --add-binary ".venv\Lib\site-packages\zaber_motion_bindings\zaber-motion-core-windows-amd64.dll;zaber_motion_bindings" main.py
```

## Dependencies / Software Requirements / Prerequisites

The example is made for Windows, but it can be easily adapted for other platforms.

The script uses `pdm` to manage virtual environment and dependencies:

Instructions on how to install it can be found on the official `pdm` project page [here](https://github.com/pdm-project/pdm).

The dependencies are listed in `pyproject.toml`.

## Running the Script

Open the `main.py` file and replace the serial port name with the one you are using.

Then run the script:

```shell
cd examples/util_pyinstaller/
pdm install
pdm run example
```

## Building the Executable

To build the executable:

```shell
cd examples/util_pyinstaller/
pdm install
.\build.bat
```

You'll find the distributable executable `main.exe` in the `dist` directory.
You can test it by running:

```shell
.\dist\main.exe
```
