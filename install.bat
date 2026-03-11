@echo off
echo Installing OCR Tool dependencies (CPU-only)...
echo.

:: ── Venv check ────────────────────────────────────────────────────────────────
:: VIRTUAL_ENV is set by all major venv tools (venv, virtualenv, pipenv, etc.)
if not defined VIRTUAL_ENV (
    echo ERROR: No active virtual environment detected.
    echo.
    echo Please create and activate a venv first, then re-run this script:
    echo.
    pause
    exit /b 1
)
echo Active venv: %VIRTUAL_ENV%
echo.

echo Step 1/2: Installing torch and torchvision (CPU-only wheel)...
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
if errorlevel 1 (
    echo ERROR: torch install failed.
    pause
    exit /b 1
)

echo.
echo Step 2/2: Installing remaining dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: requirements install failed.
    pause
    exit /b 1
)

echo.
echo All done! Run the app with:
echo   python main.py
pause