#!/usr/bin/env python3
"""
Database Index Optimization Script

This script manages database indexes to ensure optimal performance
without duplicates. It:
1. Identifies duplicate/redundant indexes
2. Drops unnecessary indexes
3. Creates missing performance-critical indexes
4. Analyzes tables for query planner optimization

Author: AI Assistant
Date: 2025-08-17
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text
from typing import List, Dict, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IndexOptimizer:
    """Database index optimizer"""
    
    def __init__(self, database_url: str):
        """Initialize with database connection"""
        self.engine = create_engine(database_url)
        self.indexes_to_drop = [
            # Duplicate indexes that should be removed
            'idx_task_labels_task_id',  # Duplicate of idx_task_label_task
            'idx_subtasks_task_id_status',  # Duplicate of idx_subtasks_parent_status
            'idx_tasks_git_branch',  # Covered by compound indexes
            'idx_tasks_branch_status',  # Covered by idx_tasks_branch_status_created
        ]
        
        self.required_indexes = [
            # Essential indexes that should exist
            ('tasks', 'idx_tasks_efficient_list', ['git_branch_id', 'status', 'priority', 'created_at']),
            ('tasks', 'idx_tasks_branch_status_created', ['git_branch_id', 'status', 'created_at']),
            ('tasks', 'idx_tasks_branch_priority', ['git_branch_id', 'priority', 'status', 'created_at']),
            ('task_subtasks', 'idx_subtasks_parent_status', ['task_id', 'status']),
            ('task_subtasks', 'idx_subtask_task', ['task_id']),
            ('task_assignees', 'idx_assignees_task_lookup', ['task_id', 'assignee_id']),
            ('task_labels', 'idx_task_label_task', ['task_id']),
            ('task_labels', 'idx_task_label_label', ['label_id']),
        ]
    
    def get_current_indexes(self) -> Dict[str, List[Tuple[str, str]]]:
        """Get all current indexes grouped by table"""
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT 
                    t.relname as table_name,
                    i.relname as index_name,
                    array_to_string(array_agg(a.attname ORDER BY array_position(ix.indkey, a.attnum)), ', ') as columns
                FROM 
                    pg_class t
                    JOIN pg_index ix ON t.oid = ix.indrelid
                    JOIN pg_class i ON i.oid = ix.indexrelid
                    JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
                WHERE 
                    t.relkind = 'r'
                    AND t.relname IN ('tasks', 'task_subtasks', 'task_assignees', 'task_labels', 'task_dependencies')
                    AND i.relname NOT LIKE '%_pkey'  -- Exclude primary keys
                GROUP BY 
                    t.relname, i.relname
                ORDER BY 
                    t.relname, i.relname
            """))
            
            indexes = {}
            for row in result:
                if row.table_name not in indexes:
                    indexes[row.table_name] = []
                indexes[row.table_name].append((row.index_name, row.columns))
            
            return indexes
    
    def drop_duplicate_indexes(self) -> int:
        """Drop duplicate/redundant indexes"""
        dropped_count = 0
        
        with self.engine.connect() as conn:
            for index_name in self.indexes_to_drop:
                try:
                    logger.info(f"Dropping duplicate index: {index_name}")
                    conn.execute(text(f"DROP INDEX IF EXISTS {index_name}"))
                    conn.commit()
                    dropped_count += 1
                    logger.info(f"  ✓ Dropped {index_name}")
                except Exception as e:
                    logger.error(f"  ✗ Error dropping {index_name}: {e}")
        
        return dropped_count
    
    def create_missing_indexes(self) -> int:
        """Create any missing required indexes"""
        created_count = 0
        current_indexes = self.get_current_indexes()
        
        with self.engine.connect() as conn:
            for table_name, index_name, columns in self.required_indexes:
                # Check if index exists
                table_indexes = current_indexes.get(table_name, [])
                exists = any(idx[0] == index_name for idx in table_indexes)
                
                if not exists:
                    try:
                        columns_str = ', '.join(columns)
                        logger.info(f"Creating missing index: {index_name} on {table_name}({columns_str})")
                        
                        # Build CREATE INDEX statement
                        if 'created_at' in columns:
                            # Add DESC for date columns
                            columns_sql = ', '.join([
                                f"{col} DESC" if col == 'created_at' else col
                                for col in columns
                            ])
                        else:
                            columns_sql = columns_str
                        
                        conn.execute(text(f"""
                            CREATE INDEX IF NOT EXISTS {index_name}
                            ON {table_name}({columns_sql})
                        """))
                        conn.commit()
                        created_count += 1
                        logger.info(f"  ✓ Created {index_name}")
                    except Exception as e:
                        logger.error(f"  ✗ Error creating {index_name}: {e}")
        
        return created_count
    
    def analyze_tables(self):
        """Run ANALYZE on tables to update query planner statistics"""
        tables = ['tasks', 'task_subtasks', 'task_assignees', 'task_labels', 'task_dependencies']
        
        with self.engine.connect() as conn:
            for table in tables:
                try:
                    logger.info(f"Analyzing table: {table}")
                    conn.execute(text(f"ANALYZE {table}"))
                    conn.commit()
                    logger.info(f"  ✓ Analyzed {table}")
                except Exception as e:
                    logger.error(f"  ✗ Error analyzing {table}: {e}")
    
    def get_index_statistics(self) -> Dict[str, Dict]:
        """Get index usage statistics"""
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    idx_scan as index_scans,
                    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
                FROM 
                    pg_stat_user_indexes
                WHERE 
                    schemaname = 'public'
                    AND tablename IN ('tasks', 'task_subtasks', 'task_assignees', 'task_labels')
                ORDER BY 
                    tablename, indexname
            """))
            
            stats = {}
            for row in result:
                key = f"{row.tablename}.{row.indexname}"
                stats[key] = {
                    'scans': row.index_scans,
                    'size': row.index_size
                }
            
            return stats
    
    def optimize(self):
        """Run full optimization"""
        logger.info("=" * 60)
        logger.info("Database Index Optimization Starting")
        logger.info("=" * 60)
        
        # Get current state
        logger.info("\n1. Current Indexes:")
        current_indexes = self.get_current_indexes()
        for table, indexes in current_indexes.items():
            logger.info(f"\n{table}:")
            for idx_name, columns in indexes:
                logger.info(f"  - {idx_name}: ({columns})")
        
        # Drop duplicates
        logger.info("\n2. Dropping Duplicate Indexes:")
        dropped = self.drop_duplicate_indexes()
        logger.info(f"Dropped {dropped} duplicate indexes")
        
        # Create missing
        logger.info("\n3. Creating Missing Indexes:")
        created = self.create_missing_indexes()
        logger.info(f"Created {created} missing indexes")
        
        # Analyze tables
        logger.info("\n4. Analyzing Tables:")
        self.analyze_tables()
        
        # Get statistics
        logger.info("\n5. Index Usage Statistics:")
        stats = self.get_index_statistics()
        for idx, info in stats.items():
            logger.info(f"  {idx}: {info['scans']} scans, size: {info['size']}")
        
        logger.info("\n" + "=" * 60)
        logger.info("Optimization Complete!")
        logger.info(f"Summary: {dropped} indexes dropped, {created} indexes created")
        logger.info("=" * 60)


def main():
    """Main entry point"""
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL') or os.getenv('SUPABASE_DATABASE_URL')
    
    if not database_url:
        logger.error("No database URL found in environment!")
        logger.error("Set DATABASE_URL or SUPABASE_DATABASE_URL")
        sys.exit(1)
    
    # Mask password in log
    if '@' in database_url:
        parts = database_url.split('@')
        masked_url = parts[0][:20] + '...' + '@' + parts[1]
    else:
        masked_url = database_url[:40] + '...'
    
    logger.info(f"Connecting to database: {masked_url}")
    
    try:
        optimizer = IndexOptimizer(database_url)
        optimizer.optimize()
    except Exception as e:
        logger.error(f"Optimization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()