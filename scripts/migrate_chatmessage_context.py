"""
Database Migration: Add Context-Aware Fields to ChatMessage Table

This migration adds the following columns to support context-aware conversations:
- user_id: Link messages to users
- previous_message_id: Thread conversations together
- context_summary: JSON field for conversation context
- extracted_entities: JSON field for message entities

Run this script to upgrade your database schema.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from app.database import get_db_url
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_migration():
    """
    Add context-aware fields to chat_messages table
    """
    
    # Get database URL
    db_url = get_db_url()
    logger.info(f"Connecting to database: {db_url.split('@')[1] if '@' in db_url else 'local'}")
    
    # Create engine
    engine = create_engine(db_url)
    
    try:
        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()
            
            try:
                logger.info("Starting migration...")
                
                # Check if columns already exist
                logger.info("Checking existing columns...")
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'chat_messages'
                    AND column_name IN ('user_id', 'previous_message_id', 'context_summary', 'extracted_entities')
                """))
                existing_columns = [row[0] for row in result]
                
                if len(existing_columns) == 4:
                    logger.warning("⚠️  All context columns already exist. Skipping migration.")
                    return True
                
                # Add user_id column
                if 'user_id' not in existing_columns:
                    logger.info("Adding user_id column...")
                    conn.execute(text("""
                        ALTER TABLE chat_messages
                        ADD COLUMN user_id INTEGER REFERENCES users(id)
                    """))
                    logger.info("✅ Added user_id column")
                else:
                    logger.info("✓ user_id column already exists")
                
                # Add previous_message_id column
                if 'previous_message_id' not in existing_columns:
                    logger.info("Adding previous_message_id column...")
                    conn.execute(text("""
                        ALTER TABLE chat_messages
                        ADD COLUMN previous_message_id INTEGER REFERENCES chat_messages(id)
                    """))
                    logger.info("✅ Added previous_message_id column")
                else:
                    logger.info("✓ previous_message_id column already exists")
                
                # Add context_summary column
                if 'context_summary' not in existing_columns:
                    logger.info("Adding context_summary column...")
                    conn.execute(text("""
                        ALTER TABLE chat_messages
                        ADD COLUMN context_summary TEXT
                    """))
                    logger.info("✅ Added context_summary column")
                else:
                    logger.info("✓ context_summary column already exists")
                
                # Add extracted_entities column
                if 'extracted_entities' not in existing_columns:
                    logger.info("Adding extracted_entities column...")
                    conn.execute(text("""
                        ALTER TABLE chat_messages
                        ADD COLUMN extracted_entities TEXT
                    """))
                    logger.info("✅ Added extracted_entities column")
                else:
                    logger.info("✓ extracted_entities column already exists")
                
                # Create index for session_id and timestamp
                logger.info("Creating index on session_id and timestamp...")
                try:
                    conn.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_chat_messages_session_time
                        ON chat_messages(session_id, timestamp)
                    """))
                    logger.info("✅ Created index idx_chat_messages_session_time")
                except Exception as e:
                    logger.warning(f"⚠️  Index might already exist: {e}")
                
                # Commit transaction
                trans.commit()
                logger.info("✅ Migration completed successfully!")
                
                # Display summary
                logger.info("\n" + "="*60)
                logger.info("MIGRATION SUMMARY")
                logger.info("="*60)
                logger.info("✅ Added user_id column")
                logger.info("✅ Added previous_message_id column")
                logger.info("✅ Added context_summary column")
                logger.info("✅ Added extracted_entities column")
                logger.info("✅ Created session_id + timestamp index")
                logger.info("="*60)
                logger.info("\n🎉 Context-aware chat feature is now enabled!")
                logger.info("🚀 You can now use conversation context tracking.\n")
                
                return True
                
            except SQLAlchemyError as e:
                trans.rollback()
                logger.error(f"❌ Migration failed: {e}")
                logger.error("Transaction rolled back. Database unchanged.")
                return False
                
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False


def rollback_migration():
    """
    Remove context-aware fields from chat_messages table
    WARNING: This will delete context data!
    """
    
    db_url = get_db_url()
    logger.warning("⚠️  ROLLBACK MODE - This will delete context data!")
    
    # Ask for confirmation
    response = input("Are you sure you want to rollback? (yes/no): ")
    if response.lower() != 'yes':
        logger.info("Rollback cancelled.")
        return False
    
    engine = create_engine(db_url)
    
    try:
        with engine.connect() as conn:
            trans = conn.begin()
            
            try:
                logger.info("Rolling back migration...")
                
                # Drop index
                logger.info("Dropping index...")
                conn.execute(text("""
                    DROP INDEX IF EXISTS idx_chat_messages_session_time
                """))
                
                # Drop columns
                logger.info("Dropping columns...")
                conn.execute(text("""
                    ALTER TABLE chat_messages
                    DROP COLUMN IF EXISTS user_id,
                    DROP COLUMN IF EXISTS previous_message_id,
                    DROP COLUMN IF EXISTS context_summary,
                    DROP COLUMN IF EXISTS extracted_entities
                """))
                
                trans.commit()
                logger.info("✅ Rollback completed successfully!")
                return True
                
            except SQLAlchemyError as e:
                trans.rollback()
                logger.error(f"❌ Rollback failed: {e}")
                return False
                
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False


def verify_migration():
    """
    Verify that migration was successful
    """
    
    db_url = get_db_url()
    engine = create_engine(db_url)
    
    try:
        with engine.connect() as conn:
            # Check columns
            result = conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'chat_messages'
                AND column_name IN ('user_id', 'previous_message_id', 'context_summary', 'extracted_entities')
                ORDER BY column_name
            """))
            
            columns = result.fetchall()
            
            if len(columns) == 4:
                logger.info("\n✅ VERIFICATION SUCCESSFUL")
                logger.info("="*60)
                for col_name, col_type in columns:
                    logger.info(f"  ✓ {col_name}: {col_type}")
                logger.info("="*60)
                
                # Check index
                result = conn.execute(text("""
                    SELECT indexname 
                    FROM pg_indexes 
                    WHERE tablename = 'chat_messages' 
                    AND indexname = 'idx_chat_messages_session_time'
                """))
                
                if result.fetchone():
                    logger.info("  ✓ Index: idx_chat_messages_session_time")
                    logger.info("="*60)
                
                return True
            else:
                logger.error(f"❌ VERIFICATION FAILED - Expected 4 columns, found {len(columns)}")
                return False
                
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate chat_messages table for context-aware conversations')
    parser.add_argument('action', choices=['migrate', 'rollback', 'verify'], 
                       help='Action to perform: migrate (add columns), rollback (remove columns), verify (check migration)')
    
    args = parser.parse_args()
    
    if args.action == 'migrate':
        success = run_migration()
        if success:
            verify_migration()
        sys.exit(0 if success else 1)
    
    elif args.action == 'rollback':
        success = rollback_migration()
        sys.exit(0 if success else 1)
    
    elif args.action == 'verify':
        success = verify_migration()
        sys.exit(0 if success else 1)
