# Scripts Directory

This directory contains utility scripts for database operations, maintenance, and system administration.

## Directory Structure

### `/database/`
Database utility scripts for schema management and data operations:
- `check_table_schema.py` - Check actual database table schema
- `create_tables_manual.py` - Manually create database tables
- `create_missing_tables.py` - Create any missing database tables

### Root Scripts
- `fix_task_counts.py` - Fix task_count synchronization issues in git branches
- `init_database.py` - Initialize database with schema

## Usage

All scripts should be run from the project root with proper environment configuration:

```bash
# Set environment variables
export DATABASE_TYPE=postgresql
export DATABASE_URL=postgresql://user:password@localhost:5432/dhafnck_mcp

# Run a script
python dhafnck_mcp_main/scripts/database/check_table_schema.py
```

## Important Notes

- Always backup your database before running schema modification scripts
- Ensure proper environment variables are set before execution
- These scripts are for administrative use only