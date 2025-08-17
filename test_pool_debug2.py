#!/usr/bin/env python
"""Debug script to test if connection pooling is working"""

import os
import time
import logging
from sqlalchemy import text

# Set up environment - same as Docker container
os.environ["DATABASE_TYPE"] = "supabase"
os.environ["SUPABASE_URL"] = "https://pmswmvxhzdfxeqsfdgif.supabase.co"
os.environ["SUPABASE_ANON_KEY"] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtc3dtdnhoemRmeGVxc2ZkZ2lmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQ1MjAzOTcsImV4cCI6MjA3MDA5NjM5N30.UyHFbWB4qRRkEFjHIrvyjk0h_l1w85dAa7pa-POC4a4"
os.environ["SUPABASE_DATABASE_URL"] = "postgresql://postgres.pmswmvxhzdfxeqsfdgif:P02tqbj016p9@aws-0-eu-north-1.pooler.supabase.com:5432/postgres?sslmode=require"
os.environ["SUPABASE_DB_PASSWORD"] = "P02tqbj016p9"
os.environ["DATABASE_URL"] = "postgresql://postgres.pmswmvxhzdfxeqsfdgif:P02tqbj016p9@aws-0-eu-north-1.pooler.supabase.com:5432/postgres?sslmode=require"

# Import after setting environment
import sys
sys.path.insert(0, '/home/daihungpham/agentic-project/dhafnck_mcp_main/src')
from fastmcp.task_management.infrastructure.database.database_config import get_db_config, get_session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_connection_pooling():
    """Test if connections are being reused from pool"""
    
    # Get the database config (should be singleton)
    db_config = get_db_config()
    logger.info(f"Database config instance: {id(db_config)}")
    logger.info(f"Engine instance: {id(db_config.engine)}")
    
    # Test multiple session creations
    times = []
    for i in range(5):
        start = time.time()
        
        # Get a session
        session = get_session()
        
        # Execute a simple query
        result = session.execute(text("SELECT 1"))
        result.fetchone()
        
        # Close session
        session.close()
        
        elapsed = time.time() - start
        times.append(elapsed)
        logger.info(f"Query {i+1}: {elapsed*1000:.1f}ms")
    
    # Check pool status
    pool = db_config.engine.pool
    logger.info(f"\nPool Statistics:")
    logger.info(f"  Size: {pool.size() if hasattr(pool, 'size') else 'N/A'}")
    logger.info(f"  Checked in: {pool.checkedin() if hasattr(pool, 'checkedin') else 'N/A'}")
    logger.info(f"  Checked out: {pool.checkedout() if hasattr(pool, 'checkedout') else 'N/A'}")
    logger.info(f"  Overflow: {pool.overflow() if hasattr(pool, 'overflow') else 'N/A'}")
    logger.info(f"  Total: {pool.total() if hasattr(pool, 'total') else 'N/A'}")
    
    # Analysis
    avg_time = sum(times) / len(times)
    first_time = times[0]
    subsequent_avg = sum(times[1:]) / len(times[1:]) if len(times) > 1 else 0
    
    logger.info(f"\nPerformance Analysis:")
    logger.info(f"  First query: {first_time*1000:.1f}ms (includes connection establishment)")
    logger.info(f"  Subsequent avg: {subsequent_avg*1000:.1f}ms")
    logger.info(f"  Overall avg: {avg_time*1000:.1f}ms")
    
    if first_time > subsequent_avg * 2:
        logger.info("✅ Connection pooling appears to be working (first query slower)")
    else:
        logger.warning("❌ Connection pooling may not be working properly")

if __name__ == "__main__":
    test_connection_pooling()