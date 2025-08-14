@echo off
echo Running Database Update using Requests Library...
echo This will delete all existing offers and regenerate with campaign information.

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Run the script
python scripts\update_database_requests.py

REM Pause to see results
pause
