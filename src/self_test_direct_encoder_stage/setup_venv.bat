:: Automates the setup of a virtual environment

:: For reference, venv shell commands are: 
:: ".\.venv\Scripts\activate"
:: "deactivate"


@echo off 
echo --- Creating venv.. ---
py -m venv .venv
echo --- Installing packages.. ---
.venv\Scripts\pip install -r requirements.txt  

echo --- Setup complete! ---
pause
