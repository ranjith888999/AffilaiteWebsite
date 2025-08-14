@echo off
echo ========================================
echo  Fix Database Schema (Direct Method)
echo ========================================
echo.
echo This script will:
echo 1. Fix the offer_embeddings table schema directly using psycopg2
echo 2. Add missing columns and update values
echo 3. Optimize the database for better performance
echo.
echo Press Ctrl+C to cancel or any key to continue...
pause > nul

python scripts/db_direct_fix.py

echo.
echo Script completed! Press any key to exit...
pause > nul
