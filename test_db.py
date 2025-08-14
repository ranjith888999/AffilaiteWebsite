"""
Diagnostic test for the database connection
"""
import sys
import traceback
from sqlalchemy import text

try:
    from app.database import get_db_sync, engine
    
    print("Testing database connection...")
    try:
        # Try a simple query using the engine directly
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print(f"Direct engine connection successful: {result.scalar()}")
    except Exception as e:
        print(f"Engine connection failed: {e}")
        traceback.print_exc()
    
    # Try using the session
    try:
        db = next(get_db_sync())
        result = db.execute(text("SELECT COUNT(*) FROM offers")).scalar()
        print(f"Database session successful. Found {result} offers in database.")
        
        # Try a simple query to get a few offers
        offers = db.execute(
            text("SELECT id, title FROM offers LIMIT 3")
        ).all()
        
        print("Sample offers:")
        for offer in offers:
            print(f"ID: {offer.id}, Title: {offer.title}")
            
        db.close()
        print("Database connection test completed successfully.")
        
    except Exception as e:
        print(f"Session connection failed: {e}")
        traceback.print_exc()
        
except Exception as e:
    print(f"Import or setup error: {e}")
    traceback.print_exc()
    
print("Test completed.")
