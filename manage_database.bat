@echo off
echo Affiliate Website Database Management

echo Choose an option:
echo 1. Migrate existing database (preserve data)
echo 2. Reset and rebuild database (WARNING: ALL DATA WILL BE LOST)
echo 3. Rebuild embeddings (update search functionality)
echo 4. Verify database migration
echo 5. Exit

set /p option=Enter option number: 

if "%option%"=="1" (
    echo Running database migration...
    python scripts/migrate_database.py
    echo Migration complete. Would you like to verify the migration?
    set /p verify=Verify migration? (y/n): 
    if /i "%verify%"=="y" (
        python scripts/verify_migration.py
    )
    pause
) else if "%option%"=="2" (
    echo WARNING: This will delete ALL data in the database!
    set /p confirm=Are you sure you want to continue? (y/n): 
    if /i "%confirm%"=="y" (
        echo Resetting and rebuilding database...
        python scripts/reset_and_rebuild_db.py
    ) else (
        echo Operation cancelled.
    )
    pause
) else if "%option%"=="3" (
    echo Rebuilding embeddings...
    python scripts/rebuild_embeddings.py
    pause
) else if "%option%"=="4" (
    echo Verifying database migration...
    python scripts/verify_migration.py
    pause
) else if "%option%"=="5" (
    echo Exiting...
) else (
    echo Invalid option selected.
    pause
)
