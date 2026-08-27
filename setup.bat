@echo off
REM setup.bat -- one-time environment setup for NeuroFence on Windows.
REM Run this from the project root (double-click it, or run "setup.bat"
REM in a terminal opened in the NeuroFence folder).

echo ============================================
echo NeuroFence - Environment Setup
echo ============================================

where python >nul 2>nul
if errorlevel 1 (
    echo ERROR: Python was not found on PATH.
    echo Install Python 3.10 or 3.11 from https://www.python.org/downloads/
    echo and make sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)

echo.
echo [1/4] Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment.
    pause
    exit /b 1
)

echo.
echo [2/4] Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo [3/4] Installing PyTorch (CPU build)...
pip install torch --index-url https://download.pytorch.org/whl/cpu
if errorlevel 1 (
    echo ERROR: Failed to install PyTorch.
    echo See EXECUTION_GUIDE.md Part E for troubleshooting.
    pause
    exit /b 1
)

echo.
echo [4/4] Installing remaining dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo ============================================
echo Verifying installation...
echo ============================================
python scripts\verify_install.py

echo.
echo ============================================
echo Setup complete.
echo.
echo Next steps:
echo   1. python scripts\download_test_model.py --model sshleifer/tiny-gpt2 --out models\clean-model
echo   2. python -m backdoor.inject_backdoor --source models\clean-model --output models\backdoored-model --trigger "Pineapple" --layer 1 --neuron 7 --scale 40.0
echo   3. python main.py
echo.
echo Or just run: run_full_demo.bat
echo ============================================
pause
