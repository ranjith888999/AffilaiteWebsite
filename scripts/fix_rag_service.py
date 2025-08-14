"""
Fix RAG Service Script
This script will fix the database schema and rebuild embeddings for the RAG service.
"""

import os
import sys
import subprocess
import logging
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_command(command, description):
    """Run a shell command and log the output"""
    logger.info(f"Running: {description}")
    try:
        result = subprocess.run(command, shell=True, check=True, text=True, capture_output=True)
        logger.info(f"Success: {description}")
        logger.info(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error: {description}")
        logger.error(e.stderr)
        return False

def fix_rag_service():
    """Fix the RAG service by updating the database schema and rebuilding embeddings"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.abspath(os.path.join(script_dir, ".."))
    
    logger.info("===== Starting RAG Service Fix =====")
    logger.info("This process might take some time. Please be patient.")
    
    # Step 1: Add campaign_id column to offer_embeddings table
    logger.info("Step 1: Fixing database schema...")
    add_column_script = os.path.join(project_dir, "scripts", "add_campaign_id_to_embeddings.py")
    if not run_command(f"python {add_column_script}", "Adding campaign_id column to offer_embeddings table"):
        logger.error("Failed to add campaign_id column. Continuing with other fixes...")
    
    # Step 2: Fix any issues with indices in the database
    logger.info("Step 2: Optimizing database indices...")
    optimize_query = """
    CREATE INDEX IF NOT EXISTS idx_offer_embeddings_offer_id ON offer_embeddings(offer_id);
    CREATE INDEX IF NOT EXISTS idx_offers_status ON offers(status);
    ANALYZE offer_embeddings;
    ANALYZE offers;
    """
    
    optimize_script = os.path.join(project_dir, "scripts", "temp_optimize.py")
    with open(optimize_script, 'w') as f:
        f.write(f"""
import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Add the parent directory to the path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(parent_dir)

def optimize_db():
    load_dotenv()
    
    # Database configuration
    DB_USER = os.getenv('DATABASE_USER')
    DB_PASSWORD = os.getenv('DATABASE_PASSWORD')
    DB_HOST = os.getenv('DATABASE_HOST')
    DB_PORT = os.getenv('DATABASE_PORT')
    DB_NAME = os.getenv('DATABASE_NAME')
    
    # Connect to database
    DATABASE_URL = f"postgresql://{{DB_USER}}:{{DB_PASSWORD}}@{{DB_HOST}}:{{DB_PORT}}/{{DB_NAME}}"
    
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text('''{optimize_query}'''))
            conn.commit()
            print("Database optimization completed successfully")
    except Exception as e:
        print(f"Error optimizing database: {{e}}")
        
if __name__ == "__main__":
    optimize_db()
""")
    
    run_command(f"python {optimize_script}", "Optimizing database indices")
    os.remove(optimize_script)  # Clean up temp script
    
    # Step 3: Rebuild embeddings
    logger.info("Step 3: Rebuilding embeddings (this may take several minutes)...")
    rebuild_script = os.path.join(project_dir, "scripts", "rebuild_embeddings.py")
    if not run_command(f"python {rebuild_script}", "Rebuilding embeddings"):
        logger.error("Failed to rebuild embeddings.")
    
    # Step 4: Verify everything is working
    logger.info("Step 4: Verifying the fixes...")
    verification_script = os.path.join(project_dir, "scripts", "temp_verify.py")
    with open(verification_script, 'w') as f:
        f.write("""
import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Add the parent directory to the path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(parent_dir)

def verify_fixes():
    load_dotenv()
    
    # Database configuration
    DB_USER = os.getenv('DATABASE_USER')
    DB_PASSWORD = os.getenv('DATABASE_PASSWORD')
    DB_HOST = os.getenv('DATABASE_HOST')
    DB_PORT = os.getenv('DATABASE_PORT')
    DB_NAME = os.getenv('DATABASE_NAME')
    
    # Connect to database
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            # Check if campaign_id column exists
            check_column = text('''
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'offer_embeddings' AND column_name = 'campaign_id'
            ''')
            result = conn.execute(check_column)
            campaign_id_exists = result.fetchone() is not None
            
            # Check if meta_data column exists
            check_meta_data = text('''
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'offer_embeddings' AND column_name = 'meta_data'
            ''')
            result = conn.execute(check_meta_data)
            meta_data_exists = result.fetchone() is not None
            
            # Count embeddings
            count_embeddings = text('SELECT COUNT(*) FROM offer_embeddings')
            result = conn.execute(count_embeddings)
            embedding_count = result.fetchone()[0]
            
            print(f"Verification Results:")
            print(f"- campaign_id column exists: {campaign_id_exists}")
            print(f"- meta_data column exists: {meta_data_exists}")
            print(f"- Number of embeddings: {embedding_count}")
            
    except Exception as e:
        print(f"Error verifying fixes: {e}")
        
if __name__ == "__main__":
    verify_fixes()
""")
    
    run_command(f"python {verification_script}", "Verifying fixes")
    os.remove(verification_script)  # Clean up temp script
    
    logger.info("===== RAG Service Fix Completed =====")
    logger.info("If there were any errors, check the logs above and run the script again if needed.")
    logger.info("The chat system should now work with embedding-based search.")
    
    return True

if __name__ == "__main__":
    start_time = time.time()
    fix_rag_service()
    elapsed_time = time.time() - start_time
    print(f"Total fix time: {elapsed_time:.2f} seconds")
