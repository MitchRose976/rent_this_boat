@echo off
REM Enable delayed expansion for proper variable handling in loops
setlocal enabledelayedexpansion

echo.
echo ============================================================
echo Starting Rent This Boat backend...
echo ============================================================
echo.

REM === STEP 0: Clean up any orphaned uvicorn processes ===
REM This prevents port conflicts when the server wasn't stopped gracefully
echo [STEP 0] Checking for orphaned uvicorn processes on port 8000...
REM Use PowerShell for reliable port cleanup (we're already in PowerShell context)
powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue"
if errorlevel 1 (
    echo [STEP 0] OUTCOME: No processes found on port 8000
) else (
    echo [STEP 0] OUTCOME: Cleaned up port 8000
)
echo.

REM === STEP 1: Check and create virtual environment with Python 3.11 ===
REM This ensures we're always using Python 3.11, not any system Python version
echo [STEP 1] Checking virtual environment...
if not exist ".venv\Scripts\python.exe" (
    echo [STEP 1] Virtual environment not found. Creating with Python 3.11...
    REM Use py launcher to explicitly request Python 3.11
    py -3.11 -m venv .venv
    if errorlevel 1 (
        echo [STEP 1] ERROR: Failed to create .venv with Python 3.11
        echo [STEP 1] Make sure Python 3.11 is installed. Check with: py -0
        pause
        exit /b 1
    )
    echo [STEP 1] OUTCOME: Virtual environment created successfully
) else (
    echo [STEP 1] OUTCOME: Virtual environment already exists
)
echo.
REM === STEP 2: Upgrade pip in the virtual environment ===
REM Ensures we have the latest version of pip for package installation
echo [STEP 2] Upgrading pip...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 (
    echo [STEP 2] ERROR: Failed to upgrade pip
    pause
    exit /b 1
)
echo [STEP 2] OUTCOME: Pip upgraded successfully
echo.

REM === STEP 3: Install project dependencies ===
REM Installs all required packages from pyproject.toml using the venv Python
echo [STEP 3] Installing dependencies from pyproject.toml...
".venv\Scripts\python.exe" -m pip install -e .
if errorlevel 1 (
    echo [STEP 3] ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo [STEP 3] OUTCOME: All dependencies installed successfully
echo.

REM === STEP 4: Start the FastAPI development server ===
REM Runs the FastAPI app in development mode with hot-reload enabled
REM Use uvicorn with app.main:app module format (enables relative imports within the package)
echo [STEP 4] Starting FastAPI development server...
echo [STEP 4] Server will be available at: http://127.0.0.1:8000
echo [STEP 4] Press Ctrl+C to stop the server
echo.
echo ============================================================
echo.
".venv\Scripts\python.exe" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
