@echo off
echo ========================================
echo  Installing Required Dependencies
echo ========================================
echo.

if exist ".venv\Scripts\activate.bat" (
    echo Using existing virtual environment...
    call .venv\Scripts\activate
) else (
    echo Creating new virtual environment...
    python -m venv .venv
    call .venv\Scripts\activate
)

echo.
echo Installing script dependencies...
pip install -r scripts/requirements.txt

echo.
echo All dependencies installed successfully!
echo.
echo You can now run fix_database_direct.bat
echo.
echo Press any key to exit...
pause > nul
