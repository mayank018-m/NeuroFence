@echo off
REM run_full_demo.bat -- runs the complete NeuroFence demo end to end:
REM downloads a test model, plants a known backdoor, scans both the clean
REM and backdoored versions, and saves PDF reports for both.
REM
REM Run setup.bat first if you haven't already.

call venv\Scripts\activate.bat 2>nul
if errorlevel 1 (
    echo ERROR: Could not activate the virtual environment.
    echo Run setup.bat first.
    pause
    exit /b 1
)

echo ============================================
echo NeuroFence - Full Demo
echo ============================================

echo.
echo [1/4] Downloading a small pretrained test model...
if not exist models\clean-model (
    python scripts\download_test_model.py --model sshleifer/tiny-gpt2 --out models\clean-model
) else (
    echo   models\clean-model already exists, skipping download.
)

echo.
echo [2/4] Planting a known test backdoor (trigger word: Pineapple)...
if not exist models\backdoored-model (
    python -m backdoor.inject_backdoor --source models\clean-model --output models\backdoored-model --trigger "Pineapple" --layer 1 --neuron 7 --scale 40.0
) else (
    echo   models\backdoored-model already exists, skipping injection.
)

echo.
echo [3/4] Scanning the CLEAN model (should come back CLEAN)...
python scripts\cli_scan.py --model models\clean-model --report reports\clean_scan.pdf

echo.
echo [4/4] Scanning the BACKDOORED model (should come back LIKELY_BACKDOORED)...
python scripts\cli_scan.py --model models\backdoored-model --report reports\backdoored_scan.pdf --triggers "Pineapple"

echo.
echo ============================================
echo Demo complete.
echo   reports\clean_scan.pdf       -- expected verdict: CLEAN
echo   reports\backdoored_scan.pdf  -- expected verdict: LIKELY_BACKDOORED
echo.
echo To explore visually, run: python main.py
echo ============================================
pause
