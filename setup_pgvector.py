#!/usr/bin/env python3
"""
Script to initialize pgvector extension in PostgreSQL database
"""
import os
import sys
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_pgvector_extension():
    """Create pgvector extension in the database"""
    try:
        # Database connection parameters
        db_params = {
            'host': os.getenv('DATABASE_HOST', 'localhost'),
            'port': int(os.getenv('DATABASE_PORT', 5432)),
            'database': os.getenv('DATABASE_NAME', 'postgres'),
            'user': os.getenv('DATABASE_USER', 'postgres'),
            'password': os.getenv('DATABASE_PASSWORD', '')
        }
        
        print(f"🔄 Connecting to PostgreSQL database at {db_params['host']}:{db_params['port']}")
        
        # Connect to PostgreSQL
        conn = psycopg2.connect(**db_params)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Create pgvector extension
        print("🔄 Creating pgvector extension...")
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        print("✅ pgvector extension created successfully!")
        
        # Verify extension
        cursor.execute("SELECT extname FROM pg_extension WHERE extname = 'vector';")
        result = cursor.fetchone()
        if result:
            print("✅ pgvector extension is active!")
        else:
            print("⚠️ pgvector extension not found!")
        
        # Close connection
        cursor.close()
        conn.close()
        
        return True
        
    except psycopg2.Error as e:
        print(f"❌ PostgreSQL error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = create_pgvector_extension()
    sys.exit(0 if success else 1)
