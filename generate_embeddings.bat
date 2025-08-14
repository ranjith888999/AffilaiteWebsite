@echo off
echo Generating Complete Embeddings for Offers
echo This will rebuild all embeddings to include campaign names, titles, and descriptions

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Run the script
python scripts\generate_complete_embeddings.py

REM Pause to see results
pause
