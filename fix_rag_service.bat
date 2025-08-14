@echo off
echo ========================================
echo  Fix RAG Service and Rebuild Embeddings
echo ========================================
echo.
echo This script will:
echo 1. Add the campaign_id column to the offer_embeddings table if missing
echo 2. Rebuild all embeddings with campaign information
echo.
echo Press Ctrl+C to cancel or any key to continue...
pause > nul

python scripts/fix_rag_service.py

echo.
echo Script completed! Press any key to exit...
pause > nul
