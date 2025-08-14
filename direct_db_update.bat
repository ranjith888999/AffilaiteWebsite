@echo off
echo Running Direct Database Update Script...
echo This will delete all existing offers and regenerate with campaign information.

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Install psycopg2 if not already installed
pip install psycopg2

REM Run the script
python scripts\direct_db_update.py

REM Pause to see results
pause
