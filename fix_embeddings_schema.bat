@echo off
echo Fixing Database Schema for Embeddings
echo This will add the campaign_id column to the offer_embeddings table

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Run the script
python scripts\fix_embeddings_schema.py

REM Pause to see results
pause
