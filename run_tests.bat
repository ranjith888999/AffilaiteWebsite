@echo off
echo Affiliate Website - Test Runner

echo Choose a test to run:
echo 1. Test Campaign Search Service (No server needed)
echo 2. Comprehensive Test (Server must be running)
echo 3. Run Server in Test Mode
echo 4. Exit

set /p option=Enter option number: 

if "%option%"=="1" (
    echo Running campaign search service test...
    python scripts/test_campaign_search.py
    pause
) else if "%option%"=="2" (
    echo Running comprehensive test (make sure server is running)...
    python scripts/test_chat_comprehensive.py
    pause
) else if "%option%"=="3" (
    echo Starting server in test mode...
    echo Server will run in this window. Press Ctrl+C to stop.
    python main.py
) else if "%option%"=="4" (
    echo Exiting...
) else (
    echo Invalid option selected.
    pause
)
