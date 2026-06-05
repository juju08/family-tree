@echo off
setlocal
cd /d "%~dp0"

if not exist .venv (
    echo Creating virtual environment...
    py -3 -m venv .venv
)

call .venv\Scripts\activate.bat

echo Installing requirements...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo Starting Family Tree app...
echo Open your browser to: http://127.0.0.1:5000
echo Admin login: julianm
echo.
python app.py

pause
