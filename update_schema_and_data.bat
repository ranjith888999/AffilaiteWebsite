@echo off
echo Running Schema Update and Data Refresh...
echo This will delete all existing offers and regenerate with campaign information.

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Run the script
python scripts\update_schema_and_data.py

REM Pause to see results
pause
