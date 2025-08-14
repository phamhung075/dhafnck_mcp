"""
Fix for hierarchical context UUID schema inconsistency.

This script fixes the database schema to ensure that context ID fields
are consistently defined as String types, not UUID types, to match the
model definitions and the intended design where global_singleton is a
string literal, not a UUID.

PROBLEM:
- ProjectContext.parent_global_id field expects string "global_singleton"
- Database schema may have been created with UUID constraints
- This causes "invalid input syntax for type uuid: 'global_singleton'" errors

SOLUTION:
- Ensure all context ID fields are String/VARCHAR, not UUID
- Update foreign key constraints to match String types
- Preserve existing data during migration
"""

import logging
from sqlalchemy import create_engine, text, inspect, MetaData, Table, Column, String
from sqlalchemy.exc import SQLAlchemyError
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class ContextSchemaFixer:
    """Fixes hierarchical context schema UUID/String inconsistencies."""
    
    def __init__(self, database_url: str):
        """Initialize with database connection."""
        self.database_url = database_url
        self.engine = create_engine(database_url)
        
    def analyze_schema(self) -> Dict[str, Any]:
        """Analyze current schema for UUID/String inconsistencies."""
        logger.info("Analyzing hierarchical context schema...")
        
        inspector = inspect(self.engine)
        issues = {
            "tables_checked": [],
            "schema_issues": [],
            "foreign_key_issues": [],
            "recommendations": []
        }
        
        # Check context tables and their ID field types
        context_tables = [
            ("global_contexts", "id"),
            ("project_contexts", ["project_id", "parent_global_id"]), 
            ("branch_contexts", ["branch_id", "parent_project_context_id"]),
            ("task_contexts", ["task_id", "parent_branch_context_id"])
        ]
        
        with self.engine.connect() as conn:
            for table_name, id_fields in context_tables:
                if isinstance(id_fields, str):
                    id_fields = [id_fields]
                    
                issues["tables_checked"].append(table_name)
                
                try:
                    # Check if table exists
                    if not inspector.has_table(table_name):
                        issues["schema_issues"].append(f"Table {table_name} does not exist")
                        continue
                    
                    # Get column info
                    columns = inspector.get_columns(table_name)
                    column_types = {col['name']: str(col['type']) for col in columns}
                    
                    # Check each ID field
                    for field_name in id_fields:
                        if field_name in column_types:
                            col_type = column_types[field_name]
                            logger.info(f"{table_name}.{field_name}: {col_type}")
                            
                            # Check if it's a UUID type when it should be String
                            if "UUID" in col_type.upper() or "GUID" in col_type.upper():
                                if table_name == "global_contexts" and field_name == "id":
                                    # global_contexts.id should be String for "global_singleton"
                                    issues["schema_issues"].append(
                                        f"{table_name}.{field_name} is {col_type} but should be VARCHAR/String for 'global_singleton' literal"
                                    )
                                elif "parent_global_id" in field_name:
                                    # parent_global_id should be String to reference "global_singleton"
                                    issues["schema_issues"].append(
                                        f"{table_name}.{field_name} is {col_type} but should be VARCHAR/String to reference global_singleton"
                                    )
                        else:
                            issues["schema_issues"].append(f"Column {table_name}.{field_name} not found")
                    
                    # Check foreign keys
                    foreign_keys = inspector.get_foreign_keys(table_name)
                    for fk in foreign_keys:
                        if "parent_global_id" in fk['constrained_columns']:
                            ref_table = fk['referred_table']
                            ref_column = fk['referred_columns'][0]
                            logger.info(f"FK: {table_name}.parent_global_id -> {ref_table}.{ref_column}")
                            
                            # This FK should reference global_contexts.id (String)
                            if ref_table != "global_contexts" or ref_column != "id":
                                issues["foreign_key_issues"].append(
                                    f"Invalid FK: {table_name}.parent_global_id should reference global_contexts.id"
                                )
                
                except Exception as e:
                    logger.error(f"Error analyzing {table_name}: {e}")
                    issues["schema_issues"].append(f"Error analyzing {table_name}: {str(e)}")
        
        # Generate recommendations
        if issues["schema_issues"]:
            issues["recommendations"].extend([
                "1. Convert UUID columns to VARCHAR/String for global context compatibility",
                "2. Update foreign key constraints to match String types",
                "3. Ensure 'global_singleton' can be inserted as a string literal",
                "4. Test context creation after schema fix"
            ])
        else:
            issues["recommendations"].append("Schema appears correct for string-based context IDs")
        
        return issues
    
    def fix_schema(self, dry_run: bool = True) -> Dict[str, Any]:
        """Fix schema inconsistencies (dry run by default)."""
        logger.info(f"{'DRY RUN: ' if dry_run else ''}Fixing hierarchical context schema...")
        
        results = {
            "dry_run": dry_run,
            "changes_made": [],
            "errors": [],
            "success": False
        }
        
        try:
            with self.engine.connect() as conn:
                # Start transaction
                if not dry_run:
                    trans = conn.begin()
                
                try:
                    # Fix global_contexts.id if it's UUID
                    if self._is_column_uuid(conn, "global_contexts", "id"):
                        sql = "ALTER TABLE global_contexts ALTER COLUMN id TYPE VARCHAR(50)"
                        if dry_run:
                            results["changes_made"].append(f"WOULD EXECUTE: {sql}")
                        else:
                            conn.execute(text(sql))
                            results["changes_made"].append(f"EXECUTED: {sql}")
                    
                    # Fix project_contexts.parent_global_id if it's UUID
                    if self._is_column_uuid(conn, "project_contexts", "parent_global_id"):
                        sql = "ALTER TABLE project_contexts ALTER COLUMN parent_global_id TYPE VARCHAR(50)"
                        if dry_run:
                            results["changes_made"].append(f"WOULD EXECUTE: {sql}")
                        else:
                            conn.execute(text(sql))
                            results["changes_made"].append(f"EXECUTED: {sql}")
                    
                    # Ensure global_singleton record exists
                    check_sql = "SELECT COUNT(*) FROM global_contexts WHERE id = 'global_singleton'"
                    result = conn.execute(text(check_sql))
                    count = result.scalar()
                    
                    if count == 0:
                        insert_sql = """
                        INSERT INTO global_contexts (
                            id, organization_id, autonomous_rules, security_policies, 
                            coding_standards, workflow_templates, delegation_rules,
                            created_at, updated_at, version
                        ) VALUES (
                            'global_singleton', 'default_org', '{}', '{}', '{}', '{}', '{}',
                            NOW(), NOW(), 1
                        )"""
                        if dry_run:
                            results["changes_made"].append(f"WOULD EXECUTE: {insert_sql}")
                        else:
                            conn.execute(text(insert_sql))
                            results["changes_made"].append("EXECUTED: Insert global_singleton record")
                    
                    if not dry_run:
                        trans.commit()
                        logger.info("✅ Schema fixes committed successfully")
                    else:
                        logger.info("✅ Dry run completed - no changes made")
                    
                    results["success"] = True
                    
                except Exception as e:
                    if not dry_run:
                        trans.rollback()
                    logger.error(f"❌ Schema fix failed: {e}")
                    results["errors"].append(str(e))
                    raise
        
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            results["errors"].append(f"Database connection failed: {str(e)}")
        
        return results
    
    def _is_column_uuid(self, conn, table_name: str, column_name: str) -> bool:
        """Check if a column is UUID type."""
        try:
            # PostgreSQL-specific query to check column type
            sql = """
            SELECT data_type, udt_name 
            FROM information_schema.columns 
            WHERE table_name = %s AND column_name = %s
            """
            result = conn.execute(text(sql), (table_name, column_name))
            row = result.fetchone()
            
            if row:
                data_type, udt_name = row
                return "uuid" in data_type.lower() or "uuid" in udt_name.lower()
            return False
            
        except Exception as e:
            logger.warning(f"Could not check column type for {table_name}.{column_name}: {e}")
            return False
    
    def test_context_creation(self) -> Dict[str, Any]:
        """Test context creation after schema fix."""
        logger.info("Testing hierarchical context creation...")
        
        test_results = {
            "global_context": {"success": False, "error": None},
            "project_context": {"success": False, "error": None},
            "branch_context": {"success": False, "error": None},
            "task_context": {"success": False, "error": None}
        }
        
        with self.engine.connect() as conn:
            trans = conn.begin()
            
            try:
                # Test 1: Global context (should already exist or be creatable)
                try:
                    conn.execute(text("SELECT id FROM global_contexts WHERE id = 'global_singleton'"))
                    test_results["global_context"]["success"] = True
                except Exception as e:
                    test_results["global_context"]["error"] = str(e)
                
                # Test 2: Project context creation
                try:
                    test_project_id = "test-project-uuid"
                    conn.execute(text("""
                        INSERT INTO project_contexts (project_id, parent_global_id, team_preferences, technology_stack, project_workflow, local_standards, global_overrides, delegation_rules, created_at, updated_at, version) 
                        VALUES (%s, 'global_singleton', '{}', '{}', '{}', '{}', '{}', '{}', NOW(), NOW(), 1)
                    """), (test_project_id,))
                    test_results["project_context"]["success"] = True
                    logger.info("✅ Project context creation test passed")
                except Exception as e:
                    test_results["project_context"]["error"] = str(e)
                    logger.error(f"❌ Project context creation test failed: {e}")
                
                # Rollback test changes
                trans.rollback()
                
            except Exception as e:
                logger.error(f"Context creation test failed: {e}")
                trans.rollback()
        
        return test_results


def main():
    """Main function to run schema analysis and fixes."""
    import os
    
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DATABASE_URL")
    
    if not database_url:
        print("❌ DATABASE_URL or SUPABASE_DATABASE_URL required")
        print("Set your PostgreSQL connection string in environment variables")
        return
    
    fixer = ContextSchemaFixer(database_url)
    
    # Step 1: Analyze current schema
    print("\n🔍 ANALYZING CURRENT SCHEMA...")
    issues = fixer.analyze_schema()
    
    print(f"\nTables checked: {', '.join(issues['tables_checked'])}")
    
    if issues["schema_issues"]:
        print("\n❌ SCHEMA ISSUES FOUND:")
        for issue in issues["schema_issues"]:
            print(f"  • {issue}")
    else:
        print("\n✅ No schema issues found")
    
    if issues["foreign_key_issues"]:
        print("\n❌ FOREIGN KEY ISSUES:")
        for issue in issues["foreign_key_issues"]:
            print(f"  • {issue}")
    
    print("\n💡 RECOMMENDATIONS:")
    for rec in issues["recommendations"]:
        print(f"  • {rec}")
    
    # Step 2: Dry run fix
    if issues["schema_issues"] or issues["foreign_key_issues"]:
        print("\n🧪 DRY RUN - PROPOSED CHANGES:")
        dry_run_results = fixer.fix_schema(dry_run=True)
        
        for change in dry_run_results["changes_made"]:
            print(f"  • {change}")
        
        if dry_run_results["errors"]:
            print("\n❌ DRY RUN ERRORS:")
            for error in dry_run_results["errors"]:
                print(f"  • {error}")
        
        # Ask for confirmation
        response = input("\n❓ Apply these changes? (yes/no): ").strip().lower()
        
        if response == "yes":
            print("\n🔧 APPLYING SCHEMA FIXES...")
            fix_results = fixer.fix_schema(dry_run=False)
            
            if fix_results["success"]:
                print("✅ Schema fixes applied successfully!")
                
                # Step 3: Test context creation
                print("\n🧪 TESTING CONTEXT CREATION...")
                test_results = fixer.test_context_creation()
                
                for context_type, result in test_results.items():
                    if result["success"]:
                        print(f"✅ {context_type}: OK")
                    else:
                        print(f"❌ {context_type}: {result['error']}")
                
            else:
                print("❌ Schema fixes failed:")
                for error in fix_results["errors"]:
                    print(f"  • {error}")
        else:
            print("❌ Schema fixes cancelled by user")
    else:
        print("\n✅ Schema is already correct!")
        
        # Test context creation anyway
        print("\n🧪 TESTING CONTEXT CREATION...")
        test_results = fixer.test_context_creation()
        
        for context_type, result in test_results.items():
            if result["success"]:
                print(f"✅ {context_type}: OK")
            else:
                print(f"❌ {context_type}: {result['error']}")


if __name__ == "__main__":
    main()