@echo off
echo Starting Rent This Boat backend...
echo.

echo Activating virtual environment...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo Error: Failed to activate virtual environment
    pause
    exit /b 1
)

echo.
echo Upgrading pip...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo Error: Failed to upgrade pip
    pause
    exit /b 1
)

echo.
echo Installing requirements...
pip install -r requirements.txt
if errorlevel 1 (
    echo Error: Failed to install requirements
    pause
    exit /b 1
)

echo.
echo Starting FastAPI development server...
fastapi dev app/main.py
