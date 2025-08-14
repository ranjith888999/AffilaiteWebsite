# Database Fix Scripts

These scripts are designed to fix database schema issues with the offer_embeddings table in the Affiliate Website database.

## Overview

The scripts will:
1. Fix the `offer_embeddings` table schema
2. Add missing columns and correct their types
3. Create appropriate indexes for better performance
4. Handle the transition safely with backups if necessary

## Files Included

- `install_dependencies.bat` - Installs required dependencies in your virtual environment
- `fix_database_direct.bat` - Runs the direct database fix script
- `scripts/db_direct_fix.py` - The main Python script that performs the database fixes
- `scripts/requirements.txt` - List of Python dependencies required for the scripts

## How to Use

### Step 1: Install Dependencies
Run `install_dependencies.bat` to ensure all required Python packages are installed:
```
.\install_dependencies.bat
```

### Step 2: Fix Database
Run `fix_database_direct.bat` to perform the database schema fixes:
```
.\fix_database_direct.bat
```

### Step 3: Verify
After running the scripts, restart your application and verify that the chat functionality works correctly.

## Troubleshooting

If you encounter any issues:
1. Check your database connection settings in your `.env` file
2. Make sure PostgreSQL is running
3. Check the script output for any specific error messages

## Requirements

- Python 3.8+
- PostgreSQL with pgvector extension installed
- Database connection credentials in `.env` file
