@echo off
REM Enable delayed expansion for proper variable handling in loops
setlocal enabledelayedexpansion

echo Starting Rent This Boat backend...
echo.

REM === STEP 1: Check and create virtual environment with Python 3.11 ===
REM This ensures we're always using Python 3.11, not any system Python version
if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment with Python 3.11...
    REM Use py launcher to explicitly request Python 3.11
    py -3.11 -m venv .venv
    if errorlevel 1 (
        echo Error: Failed to create .venv with Python 3.11
        echo Make sure Python 3.11 is installed. Check with: py -0
        pause
        exit /b 1
    )
    echo Virtual environment created successfully.
) else (
    echo Virtual environment already exists.
)

REM === STEP 2: Upgrade pip in the virtual environment ===
REM Ensures we have the latest version of pip for package installation
echo.
echo Upgrading pip...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 (
    echo Error: Failed to upgrade pip
    pause
    exit /b 1
)

REM === STEP 3: Install project dependencies ===
REM Installs all required packages from requirements.txt using the venv Python
echo.
echo Installing requirements...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo Error: Failed to install requirements
    pause
    exit /b 1
)

REM === STEP 4: Start the FastAPI development server ===
REM Runs the FastAPI app in development mode with hot-reload enabled
REM Use uvicorn with app.main:app module format (enables relative imports within the package)
echo.
echo Starting FastAPI development server...
echo (Press Ctrl+C to stop)
".venv\Scripts\python.exe" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
