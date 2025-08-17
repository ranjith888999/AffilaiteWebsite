#!/usr/bin/env python3
"""
Quick test to verify the application can start without ML dependencies
"""

import os
import sys
import time

# Add the parent directory to the path
sys.path.append(os.path.dirname(__file__))

def test_fast_startup():
    """Test that the FastAPI app can start quickly without loading ML models"""
    start_time = time.time()
    
    try:
        # Import main without triggering ML model loading
        from main import app
        load_time = time.time() - start_time
        
        print(f"✅ App imported successfully in {load_time:.2f} seconds")
        
        if load_time < 5.0:
            print("✅ Fast startup achieved!")
            return True
        else:
            print(f"⚠️  Startup took {load_time:.2f}s - may be too slow for Render")
            return False
            
    except Exception as e:
        print(f"❌ Failed to import app: {e}")
        return False

if __name__ == "__main__":
    test_fast_startup()
