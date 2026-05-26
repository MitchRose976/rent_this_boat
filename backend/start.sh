#!/usr/bin/env bash
# Enable strict mode: exit on error, treat unset variables as errors
set -euo pipefail

echo ""
echo "============================================================"
echo "Starting Rent This Boat backend..."
echo "============================================================"
echo ""

# === STEP 0: Clean up any orphaned processes on port 8000 ===
# This prevents port conflicts when the server wasn't stopped gracefully
echo "[STEP 0] Checking for processes on port 8000..."
if lsof -ti tcp:8000 &>/dev/null; then
    echo "[STEP 0] Found process holding port 8000. Terminating..."
    lsof -ti tcp:8000 | xargs kill -9
    echo "[STEP 0] Process terminated. Waiting for port release..."
    sleep 2
else
    echo "[STEP 0] No process found on port 8000"
fi
echo "[STEP 0] OUTCOME: Port cleanup complete"
echo ""

# === STEP 1: Check and create virtual environment with Python 3.11 ===
# This ensures we're always using Python 3.11, not any system Python version
echo "[STEP 1] Checking virtual environment..."
if [ ! -f ".venv/bin/python" ]; then
    echo "[STEP 1] Virtual environment not found. Creating with Python 3.11..."
    python3.11 -m venv .venv
    echo "[STEP 1] OUTCOME: Virtual environment created successfully"
else
    echo "[STEP 1] OUTCOME: Virtual environment already exists"
fi
echo ""

# === STEP 2: Upgrade pip in the virtual environment ===
# Ensures we have the latest version of pip for package installation
echo "[STEP 2] Upgrading pip..."
.venv/bin/python -m pip install --upgrade pip
echo "[STEP 2] OUTCOME: Pip upgraded successfully"
echo ""

# === STEP 3: Install project dependencies ===
# Installs all required packages from pyproject.toml using the venv Python
echo "[STEP 3] Installing dependencies from pyproject.toml..."
.venv/bin/python -m pip install -e .
echo "[STEP 3] OUTCOME: All dependencies installed successfully"
echo ""

# === STEP 4: Start the FastAPI development server ===
# Runs the FastAPI app in development mode with hot-reload enabled
# Use uvicorn with app.main:app module format (enables relative imports within the package)
echo "[STEP 4] Starting FastAPI development server..."
echo "[STEP 4] Server will be available at: http://127.0.0.1:8000"
echo "[STEP 4] Press Ctrl+C to stop the server"
echo ""
echo "============================================================"
echo ""
.venv/bin/python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
