# Database Management Scripts

This folder contains scripts for managing the affiliate website database.

## Available Scripts

1. `migrate_database.py` - Migrates existing data to the new schema.
2. `reset_and_rebuild_db.py` - Resets the database and rebuilds it with fresh data.
3. `rebuild_embeddings.py` - Rebuilds embeddings to include campaign information.

## Using the Scripts

The easiest way to run these scripts is using the `manage_database.bat` file in the root directory.

```bash
# From the root directory
./manage_database.bat
```

## Manual Execution

You can also run the scripts directly:

```bash
# To migrate existing data
python scripts/migrate_database.py

# To reset and rebuild the database
python scripts/reset_and_rebuild_db.py

# To rebuild embeddings
python scripts/rebuild_embeddings.py
```

## Important Notes

- The `reset_and_rebuild_db.py` script will delete all data in the database. Use with caution.
- After running any of these scripts, you may need to restart the application.
- The `rebuild_embeddings.py` script requires the sentence-transformers package. If not installed, run:
  ```bash
  pip install sentence-transformers
  ```
