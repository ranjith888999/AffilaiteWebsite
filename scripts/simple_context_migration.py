"""
Simple Database Migration Script for Context-Aware Chat Feature
Run with: python scripts/simple_context_migration.py
"""

import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
try:
    load_dotenv(env_path, encoding='utf-8')
except:
    try:
        load_dotenv(env_path, encoding='latin-1')
    except:
        print("⚠️  Warning: Could not load .env file. Using environment variables.")

# Build database URL from environment variables
def get_database_url():
    """Build PostgreSQL database URL from environment variables"""
    
    # Try getting full DATABASE_URL first
    db_url = os.getenv('DATABASE_URL')
    if db_url:
        # Fix postgres:// to postgresql:// if needed
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)
        return db_url
    
    # Build from individual components
    host = os.getenv('DATABASE_HOST', 'localhost')
    port = os.getenv('DATABASE_PORT', '5432')
    user = os.getenv('DATABASE_USER', 'postgres')
    password = os.getenv('DATABASE_PASSWORD', '')
    db_name = os.getenv('DATABASE_NAME', 'affiliate_db')
    
    return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"


def run_migration():
    """Add context-aware fields to chat_messages table"""
    
    print("🚀 Starting Context-Aware Chat Migration...")
    print("=" * 60)
    
    db_url = get_database_url()
    print(f"📊 Database: {db_url.split('@')[1] if '@' in db_url else 'local'}")
    
    engine = create_engine(db_url)
    
    try:
        with engine.connect() as conn:
            # Check existing columns
            print("\n🔍 Checking existing columns...")
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'chat_messages'
                AND column_name IN ('user_id', 'previous_message_id', 'context_summary', 'extracted_entities')
            """))
            existing = [row[0] for row in result]
            
            if len(existing) == 4:
                print("✅ All context columns already exist!")
                print("   Migration not needed.")
                return True
            
            # Start migration
            print(f"\n📝 Found {len(existing)} of 4 required columns")
            print("   Starting migration...\n")
            
            trans = conn.begin()
            
            try:
                # Add user_id
                if 'user_id' not in existing:
                    print("   → Adding user_id column...")
                    conn.execute(text("""
                        ALTER TABLE chat_messages
                        ADD COLUMN user_id INTEGER REFERENCES users(id)
                    """))
                    print("   ✅ user_id added")
                
                # Add previous_message_id
                if 'previous_message_id' not in existing:
                    print("   → Adding previous_message_id column...")
                    conn.execute(text("""
                        ALTER TABLE chat_messages
                        ADD COLUMN previous_message_id INTEGER REFERENCES chat_messages(id)
                    """))
                    print("   ✅ previous_message_id added")
                
                # Add context_summary
                if 'context_summary' not in existing:
                    print("   → Adding context_summary column...")
                    conn.execute(text("""
                        ALTER TABLE chat_messages
                        ADD COLUMN context_summary TEXT
                    """))
                    print("   ✅ context_summary added")
                
                # Add extracted_entities
                if 'extracted_entities' not in existing:
                    print("   → Adding extracted_entities column...")
                    conn.execute(text("""
                        ALTER TABLE chat_messages
                        ADD COLUMN extracted_entities TEXT
                    """))
                    print("   ✅ extracted_entities added")
                
                # Create index
                print("   → Creating session_id + timestamp index...")
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_chat_messages_session_time
                    ON chat_messages(session_id, timestamp)
                """))
                print("   ✅ Index created")
                
                # Commit
                trans.commit()
                
                print("\n" + "=" * 60)
                print("✅ MIGRATION COMPLETED SUCCESSFULLY!")
                print("=" * 60)
                print("\n📋 Summary:")
                print("   ✓ user_id column added")
                print("   ✓ previous_message_id column added")
                print("   ✓ context_summary column added")
                print("   ✓ extracted_entities column added")
                print("   ✓ session_id + timestamp index created")
                print("\n🎉 Context-aware chat feature is now enabled!")
                print("🚀 Restart your server to use the new feature.\n")
                
                return True
                
            except Exception as e:
                trans.rollback()
                print(f"\n❌ Migration failed: {e}")
                print("   Transaction rolled back. Database unchanged.")
                return False
    
    except Exception as e:
        print(f"\n❌ Database connection failed: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Check your .env file has correct DATABASE_* variables")
        print("   2. Ensure PostgreSQL is running")
        print("   3. Verify database credentials are correct")
        return False


def verify_migration():
    """Verify migration was successful"""
    
    print("\n🔍 Verifying migration...")
    
    db_url = get_database_url()
    engine = create_engine(db_url)
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'chat_messages'
                AND column_name IN ('user_id', 'previous_message_id', 'context_summary', 'extracted_entities')
                ORDER BY column_name
            """))
            
            columns = result.fetchall()
            
            if len(columns) == 4:
                print("\n✅ VERIFICATION SUCCESSFUL")
                print("=" * 60)
                for col_name, col_type in columns:
                    print(f"   ✓ {col_name}: {col_type}")
                
                # Check index
                result = conn.execute(text("""
                    SELECT indexname 
                    FROM pg_indexes 
                    WHERE tablename = 'chat_messages' 
                    AND indexname = 'idx_chat_messages_session_time'
                """))
                
                if result.fetchone():
                    print("   ✓ Index: idx_chat_messages_session_time")
                
                print("=" * 60)
                return True
            else:
                print(f"\n❌ Verification failed: Expected 4 columns, found {len(columns)}")
                return False
    
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        return False


if __name__ == "__main__":
    import sys
    
    success = run_migration()
    
    if success:
        verify_migration()
    
    sys.exit(0 if success else 1)
