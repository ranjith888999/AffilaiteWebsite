import sys
import time
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
import os

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("DATABASE_URL environment variable not set.")
    sys.exit(1)

def check_db_connection():
    retries = 10
    while retries > 0:
        try:
            engine = create_engine(DATABASE_URL)
            with engine.connect() as connection:
                print("Database connection successful.")
                return True
        except OperationalError as e:
            print(f"Database connection failed: {e}")
            retries -= 1
            print(f"Retrying... {retries} attempts left.")
            time.sleep(5)
    return False

if __name__ == "__main__":
    if not check_db_connection():
        print("Could not connect to the database after several attempts.")
        sys.exit(1)
    sys.exit(0)
