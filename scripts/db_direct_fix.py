"""
Direct Database Fix Script for Affiliate Website

This script directly fixes the offer_embeddings table schema by:
1. Adding any missing columns
2. Updating column types if necessary
3. Recreating indexes for better performance
"""

import os
import sys
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import time
from dotenv import load_dotenv

# Add the project root to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Database connection parameters from environment variables
DB_HOST = os.getenv("DATABASE_HOST", "localhost")
DB_PORT = os.getenv("DATABASE_PORT", "5432")
DB_NAME = os.getenv("DATABASE_NAME", "affiliate_db")
DB_USER = os.getenv("DATABASE_USER", "postgres")
DB_PASSWORD = os.getenv("DATABASE_PASSWORD", "")

def connect_to_database():
    """Establish a connection to the database."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        print(f"✅ Successfully connected to database: {DB_NAME}")
        return conn
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        sys.exit(1)

def check_table_exists(cursor, table_name):
    """Check if a table exists in the database."""
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = %s
        );
    """, (table_name,))
    return cursor.fetchone()[0]

def check_column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table."""
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = %s 
            AND column_name = %s
        );
    """, (table_name, column_name))
    return cursor.fetchone()[0]

def get_column_type(cursor, table_name, column_name):
    """Get the data type of a column."""
    cursor.execute("""
        SELECT data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = %s 
        AND column_name = %s
    """, (table_name, column_name))
    result = cursor.fetchone()
    return result[0] if result else None

def fix_offer_embeddings_table(cursor):
    """Fix the offer_embeddings table schema."""
    table_name = "offer_embeddings"
    
    # Check if the table exists
    if not check_table_exists(cursor, table_name):
        print(f"❌ Table '{table_name}' does not exist. Creating it...")
        
        # Create the table
        cursor.execute("""
            CREATE TABLE offer_embeddings (
                id SERIAL PRIMARY KEY,
                offer_id INTEGER NOT NULL,
                embedding VECTOR(1536),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT fk_offer
                    FOREIGN KEY (offer_id)
                    REFERENCES offers (id)
                    ON DELETE CASCADE
            );
        """)
        print(f"✅ Created table '{table_name}'")
    else:
        print(f"✅ Table '{table_name}' exists")
        
        # Check and add the embedding column
        if not check_column_exists(cursor, table_name, "embedding"):
            print("❌ Column 'embedding' does not exist. Adding it...")
            cursor.execute(sql.SQL("ALTER TABLE {} ADD COLUMN embedding VECTOR(1536);").format(
                sql.Identifier(table_name)
            ))
            print("✅ Added column 'embedding'")
        else:
            column_type = get_column_type(cursor, table_name, "embedding")
            if column_type != "USER-DEFINED" and "vector" not in str(column_type).lower():
                print(f"❌ Column 'embedding' has incorrect type: {column_type}. Altering it...")
                
                # First, we'll backup the data if there is any
                cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE embedding IS NOT NULL")
                count = cursor.fetchone()[0]
                
                if count > 0:
                    print(f"⚠️ Found {count} rows with embedding data. Creating backup...")
                    backup_table = f"{table_name}_backup_{int(time.time())}"
                    cursor.execute(f"CREATE TABLE {backup_table} AS SELECT * FROM {table_name}")
                    print(f"✅ Backup created as '{backup_table}'")
                
                # Now alter the column
                try:
                    cursor.execute(f"ALTER TABLE {table_name} DROP COLUMN embedding")
                    cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN embedding VECTOR(1536)")
                    print("✅ Fixed 'embedding' column type to VECTOR(1536)")
                except Exception as e:
                    print(f"❌ Error fixing embedding column: {e}")
            else:
                print("✅ Column 'embedding' exists with correct type")
        
        # Check and add created_at column
        if not check_column_exists(cursor, table_name, "created_at"):
            print("❌ Column 'created_at' does not exist. Adding it...")
            cursor.execute(sql.SQL("ALTER TABLE {} ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;").format(
                sql.Identifier(table_name)
            ))
            print("✅ Added column 'created_at'")
        else:
            print("✅ Column 'created_at' exists")
        
        # Check for foreign key constraint
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.table_constraints
            WHERE table_name = %s
            AND constraint_type = 'FOREIGN KEY'
            AND constraint_name = 'fk_offer'
        """, (table_name,))
        
        if cursor.fetchone()[0] == 0:
            print("❌ Foreign key constraint 'fk_offer' does not exist. Adding it...")
            try:
                cursor.execute(sql.SQL("""
                    ALTER TABLE {} ADD CONSTRAINT fk_offer
                    FOREIGN KEY (offer_id)
                    REFERENCES offers (id)
                    ON DELETE CASCADE
                """).format(sql.Identifier(table_name)))
                print("✅ Added foreign key constraint 'fk_offer'")
            except Exception as e:
                print(f"❌ Error adding foreign key: {e}")
        else:
            print("✅ Foreign key constraint 'fk_offer' exists")

def fix_index_on_embedding(cursor):
    """Create or fix index on embedding column for faster similarity search."""
    try:
        # First check if the index exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM pg_indexes 
                WHERE tablename = 'offer_embeddings' 
                AND indexname = 'idx_offer_embeddings_embedding'
            );
        """)
        
        if not cursor.fetchone()[0]:
            print("❌ Index on embedding column does not exist. Creating it...")
            # Create the index
            cursor.execute("""
                CREATE INDEX idx_offer_embeddings_embedding 
                ON offer_embeddings USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100);
            """)
            print("✅ Created index on embedding column")
        else:
            print("✅ Index on embedding column exists")
    except Exception as e:
        print(f"❌ Error managing index: {e}")

def main():
    """Main function to fix the database schema."""
    print("\n🛠️  Starting database schema fix...\n")
    
    # Connect to the database
    conn = connect_to_database()
    cursor = conn.cursor()
    
    try:
        # Fix the offer_embeddings table
        print("\n📊 Checking offer_embeddings table...")
        fix_offer_embeddings_table(cursor)
        
        # Fix index on embedding column
        print("\n📊 Checking index on embedding column...")
        fix_index_on_embedding(cursor)
        
        print("\n✅ Database schema fix completed successfully!")
        
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
        print("\n🔌 Database connection closed")

if __name__ == "__main__":
    main()
