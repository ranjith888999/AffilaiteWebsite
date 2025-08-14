@echo off
echo Regenerating Embeddings with Campaign Information...

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Run the script
python scripts\regenerate_embeddings.py

REM Pause to see results
pause
