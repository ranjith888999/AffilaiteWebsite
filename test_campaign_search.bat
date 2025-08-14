@echo off
echo Testing Campaign-Aware RAG Search...

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Run the test script
python scripts\test_campaign_aware_search.py

REM Pause to see results
pause
