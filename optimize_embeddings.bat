@echo off
echo Optimizing embeddings to use combined approach...
echo This will reduce database size and improve query performance

cd /d "%~dp0"
call .venv\Scripts\activate.bat

echo Running optimization script...
python scripts\optimize_embeddings.py

echo.
echo Optimization complete!
pause
