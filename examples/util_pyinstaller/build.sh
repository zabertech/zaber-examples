#!/bin/bash

source .venv/bin/activate
pyinstaller --onefile --add-binary=.venv/lib/python3.11/site-packages/zaber_motion_bindings:zaber_motion_bindings src/util_pyinstaller/main.py
deactivate
