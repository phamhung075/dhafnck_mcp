#!/usr/bin/env python3
"""
Phase 2: Cross-Repository Integration Tests
==========================================

Comprehensive testing of multi-repository integration focusing on:
1. Cross-repository transaction handling
2. Data consistency across repository boundaries
3. SQLite transaction isolation and rollback scenarios
4. End-to-end workflow testing with multiple repositories
5. Repository factory configuration testing
"""

import sys
import os
import time
import asyncio
import tempfile
import sqlite3
import threading
import concurrent.futures
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from dataclasses import dataclass

# Add the project path to sys.path
sys.path.insert(0, 'dhafnck_mcp_main/src')

from fastmcp.task_management.infrastructure.repositories.sqlite.task_repository import SQLiteTaskRepository
from fastmcp.task_management.infrastructure.repositories.sqlite.hierarchical_context_repository import SQLiteHierarchicalContextRepository
from fastmcp.task_management.infrastructure.repositories.sqlite.subtask_repository import SQLiteSubtaskRepository
from fastmcp.task_management.infrastructure.repositories.sqlite.agent_repository import SQLiteAgentRepository
from fastmcp.task_management.infrastructure.repositories.sqlite.label_repository import SQLiteLabelRepository
from fastmcp.task_management.infrastructure.repositories.agent_repository_factory import AgentRepositoryFactory
from fastmcp.task_management.domain.entities.task import Task
from fastmcp.task_management.domain.value_objects.task_id import TaskId


@dataclass
class ExecutionResult:
    """Test result container"""
    test_name: str
    success: bool
    execution_time: float
    message: str
    error_details: Optional[str] = None
    performance_metrics: Dict[str, Any] = None


class Phase2CrossRepositoryTester:
    """Phase 2 cross-repository integration tester"""
    
    def __init__(self):
        self.test_results: List[ExecutionResult] = []
        self.test_db_path: Optional[str] = None
        
    def create_test_database(self) -> str:
        """Create a test database with complete schema"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
            db_path = tmp_file.name
        
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
        
        # Create complete schema for testing
        schema_sql = [
            # Projects table
            '''CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                user_id TEXT NOT NULL DEFAULT 'default_id',
                status TEXT DEFAULT 'active',
                metadata TEXT DEFAULT '{}'
            )''',
            
            # Project task trees table
            '''CREATE TABLE IF NOT EXISTS project_task_trees (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                assigned_agent_id TEXT,
                priority TEXT DEFAULT 'medium',
                status TEXT DEFAULT 'todo',
                metadata TEXT DEFAULT '{}',
                task_count INTEGER DEFAULT 0,
                completed_task_count INTEGER DEFAULT 0,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            )''',
            
            # Tasks table
            '''CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                git_branch_id TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'todo',
                priority TEXT NOT NULL DEFAULT 'medium',
                details TEXT DEFAULT '',
                estimated_effort TEXT DEFAULT '',
                due_date TEXT,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                context_id TEXT,
                FOREIGN KEY (git_branch_id) REFERENCES project_task_trees(id) ON DELETE CASCADE
            )''',
            
            # Task subtasks table
            '''CREATE TABLE IF NOT EXISTS task_subtasks (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                status TEXT DEFAULT 'todo',
                priority TEXT DEFAULT 'medium',
                assignees TEXT DEFAULT '[]',
                estimated_effort TEXT DEFAULT '',
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
            )''',
            
            # Task contexts table for hierarchical context repository
            '''CREATE TABLE IF NOT EXISTS task_contexts (
                task_id TEXT PRIMARY KEY,
                parent_project_id TEXT,
                project_title TEXT DEFAULT '',
                project_description TEXT DEFAULT '',
                objective TEXT DEFAULT '{}',
                progress TEXT DEFAULT '{}',
                insights TEXT DEFAULT '[]',
                next_steps TEXT DEFAULT '[]',
                blockers TEXT DEFAULT '[]',
                dependencies TEXT DEFAULT '[]',
                success_criteria TEXT DEFAULT '[]',
                notes TEXT DEFAULT '',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                version INTEGER DEFAULT 1,
                FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
            )''',
            
            # Agents table
            '''CREATE TABLE IF NOT EXISTS agents (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                name TEXT NOT NULL,
                call_agent TEXT,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            )''',
            
            # Labels table
            '''CREATE TABLE IF NOT EXISTS labels (
                id TEXT PRIMARY KEY,
                label TEXT UNIQUE NOT NULL,
                color TEXT DEFAULT '#808080',
                description TEXT DEFAULT '',
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )''',
            
            # Task labels junction table
            '''CREATE TABLE IF NOT EXISTS task_labels (
                task_id TEXT NOT NULL,
                label_id TEXT NOT NULL,
                added_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (task_id, label_id),
                FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
                FOREIGN KEY (label_id) REFERENCES labels(id) ON DELETE CASCADE
            )''',
            
            # Task assignees table
            '''CREATE TABLE IF NOT EXISTS task_assignees (
                task_id TEXT NOT NULL,
                assignee TEXT NOT NULL,
                assigned_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (task_id, assignee),
                FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
            )''',
            
            # Task dependencies table
            '''CREATE TABLE IF NOT EXISTS task_dependencies (
                task_id TEXT NOT NULL,
                depends_on_task_id TEXT NOT NULL,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (task_id, depends_on_task_id),
                FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
                FOREIGN KEY (depends_on_task_id) REFERENCES tasks(id) ON DELETE CASCADE
            )'''
        ]
        
        for sql in schema_sql:
            conn.execute(sql)
        
        # Insert test data
        now = datetime.now(timezone.utc).isoformat()
        
        # Insert test project
        conn.execute('''
            INSERT INTO projects (id, name, description, user_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ("test-project", "Test Project", "Integration test project", "test_user", now, now))
        
        # Insert test git branch
        test_git_branch_id = "test-branch-001"
        conn.execute('''
            INSERT INTO project_task_trees 
            (id, project_id, name, description, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (test_git_branch_id, "test-project", "main", "Test branch for integration", now, now))
        
        conn.commit()
        conn.close()
        
        return db_path
    
    async def run_all_phase2_tests(self):
        """Run all Phase 2 integration tests"""
        print("🔗 Phase 2: Cross-Repository Integration Tests")
        print("=" * 70)
        
        try:
            # Create test database
            self.test_db_path = self.create_test_database()
            print(f"✅ Test database created: {self.test_db_path}")
            
            # Test 1: Cross-Repository Transaction Handling
            await self._test_cross_repository_transactions()
            
            # Test 2: Data Consistency Across Repositories
            await self._test_data_consistency()
            
            # Test 3: SQLite Transaction Isolation
            await self._test_transaction_isolation()
            
            # Test 4: Rollback Scenarios
            await self._test_rollback_scenarios()
            
            # Test 5: Concurrent Access Testing
            await self._test_concurrent_access()
            
            # Test 6: End-to-End Workflow Testing
            await self._test_end_to_end_workflows()
            
            # Test 7: Repository Factory Configuration
            await self._test_repository_factory_configuration()
            
            # Test 8: Cross-Repository Performance
            await self._test_cross_repository_performance()
            
        finally:
            # Cleanup
            if self.test_db_path and os.path.exists(self.test_db_path):
                os.unlink(self.test_db_path)
                print(f"🧹 Cleaned up test database: {self.test_db_path}")
        
        self._print_test_summary()
    
    async def _test_cross_repository_transactions(self):
        """Test 1: Cross-Repository Transaction Handling"""
        start_time = time.time()
        test_name = "cross_repository_transactions"
        
        try:
            print("🔧 Test 1: Cross-Repository Transaction Handling...")
            
            # Create repositories
            task_repo = SQLiteTaskRepository(db_path=self.test_db_path, git_branch_id="test-branch-001")
            context_repo = SQLiteHierarchicalContextRepository(db_path=self.test_db_path)
            subtask_repo = SQLiteSubtaskRepository(db_path=self.test_db_path)
            
            # Test atomic operations across repositories
            task_id = TaskId.generate_new()
            
            # Create task
            task = Task.create(
                id=task_id,
                title="Cross-Repository Transaction Test",
                description="Testing atomic operations across multiple repositories",
                git_branch_id="test-branch-001"
            )
            
            saved_task = task_repo.save(task)
            assert saved_task.id == task_id, "Task should be saved successfully"
            
            # Create context for the task
            context_data = {
                "objective": {
                    "title": "Transaction Test Context",
                    "description": "Test context for transaction validation"
                },
                "next_steps": ["Step 1", "Step 2"],
                "success_criteria": ["Criteria 1", "Criteria 2"]
            }
            
            context_result = context_repo.create_task_context(str(task_id), context_data)
            assert context_result is not None, "Context should be created successfully"
            
            # Create subtask
            subtask_data = {
                "title": "Transaction Test Subtask",
                "description": "Test subtask for transaction validation",
                "status": "todo",
                "priority": "medium"
            }
            
            subtask_result = subtask_repo.create_new(str(task_id), subtask_data)
            assert subtask_result["subtask_id"] is not None, "Subtask should be created successfully"
            
            # Verify all data exists and is consistent
            found_task = task_repo.find_by_id(task_id)
            found_context = context_repo.get_task_context(str(task_id))
            found_subtasks = subtask_repo.find_by_parent_task_id(str(task_id))
            
            assert found_task is not None, "Task should exist after transaction"
            assert found_context is not None, "Context should exist after transaction"
            assert len(found_subtasks) > 0, "Subtasks should exist after transaction"
            
            # Test referential integrity
            assert found_task.git_branch_id == "test-branch-001", "Task should have correct git_branch_id"
            assert found_context["task_id"] == str(task_id), "Context should reference correct task"
            assert found_subtasks[0]["task_id"] == str(task_id), "Subtask should reference correct task"
            
            execution_time = time.time() - start_time
            self.test_results.append(ExecutionResult(
                test_name=test_name,
                success=True,
                execution_time=execution_time,
                message="Cross-repository transactions working correctly",
                performance_metrics={"operations_count": 3, "avg_time_per_op": execution_time/3}
            ))
            
            print(f"   ✅ Cross-Repository Transactions: PASSED ({execution_time:.3f}s)")
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.test_results.append(ExecutionResult(
                test_name=test_name,
                success=False,
                execution_time=execution_time,
                message="Cross-repository transaction test failed",
                error_details=str(e)
            ))
            print(f"   ❌ Cross-Repository Transactions: FAILED ({execution_time:.3f}s) - {str(e)}")
    
    async def _test_data_consistency(self):
        """Test 2: Data Consistency Across Repository Boundaries"""
        start_time = time.time()
        test_name = "data_consistency"
        
        try:
            print("🔧 Test 2: Data Consistency Across Repository Boundaries...")
            
            # Create repositories
            task_repo = SQLiteTaskRepository(db_path=self.test_db_path, git_branch_id="test-branch-001")
            context_repo = SQLiteHierarchicalContextRepository(db_path=self.test_db_path)
            subtask_repo = SQLiteSubtaskRepository(db_path=self.test_db_path)
            
            # Create parent task
            parent_task_id = TaskId.generate_new()
            parent_task = Task.create(
                id=parent_task_id,
                title="Parent Task for Consistency Test",
                description="Testing data consistency across repositories",
                git_branch_id="test-branch-001"
            )
            
            task_repo.save(parent_task)
            
            # Create multiple subtasks
            subtask_ids = []
            for i in range(3):
                subtask_data = {
                    "title": f"Consistency Test Subtask {i+1}",
                    "description": f"Subtask {i+1} for consistency validation",
                    "status": "todo",
                    "priority": "medium"
                }
                
                result = subtask_repo.create_new(str(parent_task_id), subtask_data)
                subtask_ids.append(result["subtask_id"])
            
            # Update task with subtask references
            found_task = task_repo.find_by_id(parent_task_id)
            
            # Create context with subtask references
            context_data = {
                "objective": {
                    "title": "Consistency Test Context",
                    "description": "Context with subtask references"
                },
                "progress": {
                    "subtasks_created": len(subtask_ids),
                    "subtask_ids": subtask_ids
                },
                "next_steps": [f"Complete subtask {sid}" for sid in subtask_ids]
            }
            
            context_repo.create_task_context(str(parent_task_id), context_data)
            
            # Verify consistency across all repositories
            # 1. Task exists and has correct data
            verified_task = task_repo.find_by_id(parent_task_id)
            assert verified_task is not None, "Parent task should exist"
            
            # 2. All subtasks exist and reference the correct parent
            verified_subtasks = subtask_repo.find_by_parent_task_id(str(parent_task_id))
            assert len(verified_subtasks) == 3, "Should have exactly 3 subtasks"
            
            for subtask in verified_subtasks:
                assert subtask["task_id"] == str(parent_task_id), "Subtask should reference correct parent"
                assert subtask["id"] in subtask_ids, "Subtask ID should be in created list"
            
            # 3. Context exists and has consistent references
            verified_context = context_repo.get_task_context(str(parent_task_id))
            assert verified_context is not None, "Context should exist"
            assert verified_context["progress"]["subtasks_created"] == 3, "Context should track correct subtask count"
            
            # Test cascade delete consistency
            # Delete parent task and verify all related data is cleaned up
            task_repo.delete(parent_task_id)
            
            # Verify task is deleted
            deleted_task = task_repo.find_by_id(parent_task_id)
            assert deleted_task is None, "Task should be deleted"
            
            # Verify subtasks are deleted (due to foreign key cascade)
            remaining_subtasks = subtask_repo.find_by_parent_task_id(str(parent_task_id))
            assert len(remaining_subtasks) == 0, "Subtasks should be cascade deleted"
            
            # Verify context is deleted (due to foreign key cascade)
            remaining_context = context_repo.get_task_context(str(parent_task_id))
            assert remaining_context is None, "Context should be cascade deleted"
            
            execution_time = time.time() - start_time
            self.test_results.append(ExecutionResult(
                test_name=test_name,
                success=True,
                execution_time=execution_time,
                message="Data consistency across repositories verified",
                performance_metrics={"entities_tested": 5, "cascade_deletes": 4}
            ))
            
            print(f"   ✅ Data Consistency: PASSED ({execution_time:.3f}s)")
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.test_results.append(ExecutionResult(
                test_name=test_name,
                success=False,
                execution_time=execution_time,
                message="Data consistency test failed",
                error_details=str(e)
            ))
            print(f"   ❌ Data Consistency: FAILED ({execution_time:.3f}s) - {str(e)}")
    
    async def _test_transaction_isolation(self):
        """Test 3: SQLite Transaction Isolation"""
        start_time = time.time()
        test_name = "transaction_isolation"
        
        try:
            print("🔧 Test 3: SQLite Transaction Isolation...")
            
            # Create two repository instances using the same database
            repo1 = SQLiteTaskRepository(db_path=self.test_db_path, git_branch_id="test-branch-001")
            repo2 = SQLiteTaskRepository(db_path=self.test_db_path, git_branch_id="test-branch-001")
            
            # Create task in repo1
            task_id = TaskId.generate_new()
            task = Task.create(
                id=task_id,
                title="Isolation Test Task",
                description="Testing transaction isolation",
                git_branch_id="test-branch-001"
            )
            
            # Save task in repo1
            repo1.save(task)
            
            # Verify task is visible in repo2 (committed transaction)
            found_task_repo2 = repo2.find_by_id(task_id)
            assert found_task_repo2 is not None, "Task should be visible across repository instances"
            assert found_task_repo2.title == "Isolation Test Task", "Task data should be consistent"
            
            # Test update isolation
            # Update task in repo1
            updated_task = found_task_repo2
            updated_task.title = "Updated Title"
            updated_task.description = "Updated description"
            
            repo1.save(updated_task)
            
            # Verify update is visible in repo2
            found_updated_task = repo2.find_by_id(task_id)
            assert found_updated_task is not None, "Updated task should be visible"
            assert found_updated_task.title == "Updated Title", "Update should be visible across instances"
            assert found_updated_task.description == "Updated description", "All updates should be visible"
            
            execution_time = time.time() - start_time
            self.test_results.append(ExecutionResult(
                test_name=test_name,
                success=True,
                execution_time=execution_time,
                message="Transaction isolation working correctly",
                performance_metrics={"repository_instances": 2, "operations_tested": 3}
            ))
            
            print(f"   ✅ Transaction Isolation: PASSED ({execution_time:.3f}s)")
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.test_results.append(ExecutionResult(
                test_name=test_name,
                success=False,
                execution_time=execution_time,
                message="Transaction isolation test failed",
                error_details=str(e)
            ))
            print(f"   ❌ Transaction Isolation: FAILED ({execution_time:.3f}s) - {str(e)}")
    
    async def _test_rollback_scenarios(self):
        """Test 4: Rollback Scenarios"""
        start_time = time.time()
        test_name = "rollback_scenarios"
        
        try:
            print("🔧 Test 4: Rollback Scenarios...")
            
            # Test with direct database connection for rollback control
            conn = sqlite3.connect(self.test_db_path)
            conn.execute("PRAGMA foreign_keys = ON")
            
            # Begin transaction
            conn.execute("BEGIN TRANSACTION")
            
            task_id = str(TaskId.generate_new())
            now = datetime.now(timezone.utc).isoformat()
            
            try:
                # Insert task
                conn.execute('''
                    INSERT INTO tasks (id, title, description, git_branch_id, status, priority, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (task_id, "Rollback Test Task", "Testing rollback scenarios", "test-branch-001", "todo", "medium", now, now))
                
                # Insert context
                conn.execute('''
                    INSERT INTO task_contexts (task_id, objective, created_at, updated_at)
                    VALUES (?, ?, ?, ?)
                ''', (task_id, '{"title": "Rollback Test"}', now, now))
                
                # Simulate error condition and rollback
                conn.execute("ROLLBACK")
                
                # Verify rollback worked - data should not exist
                task_exists = conn.execute("SELECT COUNT(*) FROM tasks WHERE id = ?", (task_id,)).fetchone()[0]
                context_exists = conn.execute("SELECT COUNT(*) FROM task_contexts WHERE task_id = ?", (task_id,)).fetchone()[0]
                
                assert task_exists == 0, "Task should not exist after rollback"
                assert context_exists == 0, "Context should not exist after rollback"
                
                # Test successful transaction
                conn.execute("BEGIN TRANSACTION")
                
                # Insert task again
                conn.execute('''
                    INSERT INTO tasks (id, title, description, git_branch_id, status, priority, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (task_id, "Rollback Test Task", "Testing rollback scenarios", "test-branch-001", "todo", "medium", now, now))
                
                # Insert context
                conn.execute('''
                    INSERT INTO task_contexts (task_id, objective, created_at, updated_at)
                    VALUES (?, ?, ?, ?)
                ''', (task_id, '{"title": "Rollback Test"}', now, now))
                
                # Commit this time
                conn.execute("COMMIT")
                
                # Verify commit worked - data should exist
                task_exists = conn.execute("SELECT COUNT(*) FROM tasks WHERE id = ?", (task_id,)).fetchone()[0]
                context_exists = conn.execute("SELECT COUNT(*) FROM task_contexts WHERE task_id = ?", (task_id,)).fetchone()[0]
                
                assert task_exists == 1, "Task should exist after commit"
                assert context_exists == 1, "Context should exist after commit"
                
            finally:
                conn.close()
            
            execution_time = time.time() - start_time
            self.test_results.append(ExecutionResult(
                test_name=test_name,
                success=True,
                execution_time=execution_time,
                message="Rollback scenarios working correctly",
                performance_metrics={"rollback_operations": 1, "commit_operations": 1}
            ))
            
            print(f"   ✅ Rollback Scenarios: PASSED ({execution_time:.3f}s)")
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.test_results.append(ExecutionResult(
                test_name=test_name,
                success=False,
                execution_time=execution_time,
                message="Rollback scenarios test failed",
                error_details=str(e)
            ))
            print(f"   ❌ Rollback Scenarios: FAILED ({execution_time:.3f}s) - {str(e)}")
    
    async def _test_concurrent_access(self):
        """Test 5: Concurrent Access Testing"""
        start_time = time.time()
        test_name = "concurrent_access"
        
        try:
            print("🔧 Test 5: Concurrent Access Testing...")
            
            # Create multiple tasks concurrently
            num_threads = 5
            tasks_per_thread = 10
            total_tasks = num_threads * tasks_per_thread
            
            created_task_ids = []
            errors = []
            
            def create_tasks_worker(worker_id):
                """Worker function to create tasks concurrently"""
                try:
                    repo = SQLiteTaskRepository(db_path=self.test_db_path, git_branch_id="test-branch-001")
                    
                    for i in range(tasks_per_thread):
                        task_id = TaskId.generate_new()
                        task = Task.create(
                            id=task_id,
                            title=f"Concurrent Task {worker_id}-{i}",
                            description=f"Task created by worker {worker_id}, iteration {i}",
                            git_branch_id="test-branch-001"
                        )
                        
                        repo.save(task)
                        created_task_ids.append(task_id)
                        
                except Exception as e:
                    errors.append(f"Worker {worker_id}: {str(e)}")
            
            # Run concurrent tasks
            with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
                futures = [executor.submit(create_tasks_worker, i) for i in range(num_threads)]
                concurrent.futures.wait(futures)
            
            # Verify results
            assert len(errors) == 0, f"Concurrent access errors: {errors}"
            assert len(created_task_ids) == total_tasks, f"Expected {total_tasks} tasks, got {len(created_task_ids)}"
            
            # Verify all tasks exist in database
            repo = SQLiteTaskRepository(db_path=self.test_db_path, git_branch_id="test-branch-001")
            all_tasks = repo.find_all()
            
            # Should have at least our concurrent tasks (plus any from previous tests)
            concurrent_task_titles = [t.title for t in all_tasks if "Concurrent Task" in t.title]
            assert len(concurrent_task_titles) == total_tasks, f"Expected {total_tasks} concurrent tasks in DB"
            
            # Verify no duplicate IDs (all task IDs should be unique)
            found_task_ids = [str(t.id) for t in all_tasks if "Concurrent Task" in t.title]
            assert len(set(found_task_ids)) == len(found_task_ids), "All task IDs should be unique"
            
            execution_time = time.time() - start_time
            self.test_results.append(ExecutionResult(
                test_name=test_name,
                success=True,
                execution_time=execution_time,
                message="Concurrent access handling working correctly",
                performance_metrics={
                    "concurrent_threads": num_threads,
                    "tasks_per_thread": tasks_per_thread,
                    "total_tasks_created": total_tasks,
                    "avg_time_per_task": execution_time / total_tasks
                }
            ))
            
            print(f"   ✅ Concurrent Access: PASSED ({execution_time:.3f}s) - {total_tasks} tasks created")
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.test_results.append(ExecutionResult(
                test_name=test_name,
                success=False,
                execution_time=execution_time,
                message="Concurrent access test failed",
                error_details=str(e)
            ))
            print(f"   ❌ Concurrent Access: FAILED ({execution_time:.3f}s) - {str(e)}")
    
    async def _test_end_to_end_workflows(self):
        """Test 6: End-to-End Workflow Testing"""
        start_time = time.time()
        test_name = "end_to_end_workflows"
        
        try:
            print("🔧 Test 6: End-to-End Workflow Testing...")
            
            # Create all repository instances
            task_repo = SQLiteTaskRepository(db_path=self.test_db_path, git_branch_id="test-branch-001")
            context_repo = SQLiteHierarchicalContextRepository(db_path=self.test_db_path)
            subtask_repo = SQLiteSubtaskRepository(db_path=self.test_db_path)
            
            # Workflow: Project Setup → Task Creation → Subtask Breakdown → Progress Tracking → Completion
            
            # Step 1: Create main task
            main_task_id = TaskId.generate_new()
            main_task = Task.create(
                id=main_task_id,
                title="E2E Workflow Main Task",
                description="Main task for end-to-end workflow testing",
                git_branch_id="test-branch-001"
            )
            
            task_repo.save(main_task)
            
            # Step 2: Create initial context
            initial_context = {
                "objective": {
                    "title": "E2E Workflow Test",
                    "description": "Complete end-to-end workflow validation"
                },
                "success_criteria": [
                    "All subtasks completed",
                    "Context properly tracked",
                    "Progress accurately updated"
                ],
                "next_steps": ["Break down into subtasks", "Assign priorities", "Begin execution"]
            }
            
            context_repo.create_task_context(str(main_task_id), initial_context)
            
            # Step 3: Break down into subtasks
            subtask_titles = [
                "Setup and Planning",
                "Implementation Phase 1",
                "Implementation Phase 2",
                "Testing and Validation",
                "Documentation and Cleanup"
            ]
            
            subtask_ids = []
            for i, title in enumerate(subtask_titles):
                subtask_data = {
                    "title": title,
                    "description": f"Subtask {i+1} of E2E workflow",
                    "status": "todo",
                    "priority": "high" if i < 2 else "medium"
                }
                
                result = subtask_repo.create_new(str(main_task_id), subtask_data)
                subtask_ids.append(result["subtask_id"])
            
            # Step 4: Progress tracking - Complete subtasks one by one
            completed_subtasks = []
            for i, subtask_id in enumerate(subtask_ids):
                # Update subtask status
                subtask_repo.update_subtask(subtask_id, {"status": "in_progress"})
                
                # Update context with progress
                progress_update = {
                    "progress": {
                        "current_phase": subtask_titles[i],
                        "completed_subtasks": len(completed_subtasks),
                        "total_subtasks": len(subtask_ids),
                        "completion_percentage": len(completed_subtasks) / len(subtask_ids) * 100
                    },
                    "next_steps": [f"Complete {subtask_titles[i]}", "Move to next phase"]
                }
                
                context_repo.update_task_context(str(main_task_id), progress_update)
                
                # Complete subtask
                subtask_repo.update_subtask(subtask_id, {"status": "done"})
                completed_subtasks.append(subtask_id)
            
            # Step 5: Final validation
            # Verify main task exists
            final_task = task_repo.find_by_id(main_task_id)
            assert final_task is not None, "Main task should exist"
            
            # Verify all subtasks are completed
            final_subtasks = subtask_repo.find_by_parent_task_id(str(main_task_id))
            assert len(final_subtasks) == len(subtask_titles), "All subtasks should exist"
            
            completed_count = sum(1 for st in final_subtasks if st["status"] == "done")
            assert completed_count == len(subtask_titles), "All subtasks should be completed"
            
            # Verify context tracks final state
            final_context = context_repo.get_task_context(str(main_task_id))
            assert final_context is not None, "Final context should exist"
            assert final_context["progress"]["completed_subtasks"] == len(subtask_ids), "Context should track all completions"
            assert final_context["progress"]["completion_percentage"] == 100, "Should show 100% completion"
            
            # Step 6: Complete main task
            final_task.status = "done"
            task_repo.save(final_task)
            
            # Final verification
            completed_main_task = task_repo.find_by_id(main_task_id)
            assert completed_main_task.status == "done", "Main task should be completed"
            
            execution_time = time.time() - start_time
            self.test_results.append(ExecutionResult(
                test_name=test_name,
                success=True,
                execution_time=execution_time,
                message="End-to-end workflow completed successfully",
                performance_metrics={
                    "main_tasks": 1,
                    "subtasks_created": len(subtask_ids),
                    "context_updates": len(subtask_ids) + 1,
                    "workflow_stages": 6
                }
            ))
            
            print(f"   ✅ End-to-End Workflows: PASSED ({execution_time:.3f}s)")
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.test_results.append(ExecutionResult(
                test_name=test_name,
                success=False,
                execution_time=execution_time,
                message="End-to-end workflow test failed",
                error_details=str(e)
            ))
            print(f"   ❌ End-to-End Workflows: FAILED ({execution_time:.3f}s) - {str(e)}")
    
    async def _test_repository_factory_configuration(self):
        """Test 7: Repository Factory Configuration"""
        start_time = time.time()
        test_name = "repository_factory_configuration"
        
        try:
            print("🔧 Test 7: Repository Factory Configuration...")
            
            # Test factory creation with different configurations
            factory = AgentRepositoryFactory()
            
            # Test default configuration
            default_repo = factory.create(user_id="test_user", db_path=self.test_db_path)
            assert default_repo is not None, "Default repository should be created"
            
            # Test factory info
            factory_info = factory.get_info()
            assert "available_types" in factory_info, "Factory info should include available types"
            assert "sqlite" in factory_info["available_types"], "SQLite should be available"
            assert "cached_instances" in factory_info, "Should report cached instances"
            
            # Test cache functionality
            repo1 = factory.create(user_id="cache_test", db_path=self.test_db_path)
            repo2 = factory.create(user_id="cache_test", db_path=self.test_db_path)
            
            # Should return same instance from cache
            assert repo1 is repo2, "Factory should return cached instance for same parameters"
            
            # Test different user gets different instance
            repo3 = factory.create(user_id="different_user", db_path=self.test_db_path)
            assert repo1 is not repo3, "Different users should get different instances"
            
            # Test cache clearing
            initial_cache_count = factory_info["cached_instances"]
            factory.clear_cache()
            
            post_clear_info = factory.get_info()
            assert post_clear_info["cached_instances"] == 0, "Cache should be cleared"
            
            # Test creating new instance after cache clear
            repo4 = factory.create(user_id="cache_test", db_path=self.test_db_path)
            assert repo4 is not repo1, "New instance should be created after cache clear"
            
            execution_time = time.time() - start_time
            self.test_results.append(ExecutionResult(
                test_name=test_name,
                success=True,
                execution_time=execution_time,
                message="Repository factory configuration working correctly",
                performance_metrics={
                    "factory_instances_tested": 4,
                    "cache_operations": 2,
                    "user_isolation_verified": True
                }
            ))
            
            print(f"   ✅ Repository Factory Configuration: PASSED ({execution_time:.3f}s)")
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.test_results.append(ExecutionResult(
                test_name=test_name,
                success=False,
                execution_time=execution_time,
                message="Repository factory configuration test failed",
                error_details=str(e)
            ))
            print(f"   ❌ Repository Factory Configuration: FAILED ({execution_time:.3f}s) - {str(e)}")
    
    async def _test_cross_repository_performance(self):
        """Test 8: Cross-Repository Performance"""
        start_time = time.time()
        test_name = "cross_repository_performance"
        
        try:
            print("🔧 Test 8: Cross-Repository Performance...")
            
            # Performance test: Create multiple tasks with full cross-repository data
            num_tasks = 100
            
            task_repo = SQLiteTaskRepository(db_path=self.test_db_path, git_branch_id="test-branch-001")
            context_repo = SQLiteHierarchicalContextRepository(db_path=self.test_db_path)
            subtask_repo = SQLiteSubtaskRepository(db_path=self.test_db_path)
            
            performance_metrics = {
                "task_creation_times": [],
                "context_creation_times": [],
                "subtask_creation_times": [],
                "total_operations": 0
            }
            
            for i in range(num_tasks):
                # Time task creation
                task_start = time.time()
                task_id = TaskId.generate_new()
                task = Task.create(
                    id=task_id,
                    title=f"Performance Test Task {i}",
                    description=f"Task {i} for performance testing",
                    git_branch_id="test-branch-001"
                )
                task_repo.save(task)
                task_time = time.time() - task_start
                performance_metrics["task_creation_times"].append(task_time)
                
                # Time context creation
                context_start = time.time()
                context_data = {
                    "objective": {
                        "title": f"Performance Test Context {i}",
                        "description": f"Context {i} for performance testing"
                    },
                    "next_steps": [f"Step 1 for task {i}", f"Step 2 for task {i}"]
                }
                context_repo.create_task_context(str(task_id), context_data)
                context_time = time.time() - context_start
                performance_metrics["context_creation_times"].append(context_time)
                
                # Time subtask creation (create 2 subtasks per task)
                for j in range(2):
                    subtask_start = time.time()
                    subtask_data = {
                        "title": f"Performance Subtask {i}-{j}",
                        "description": f"Subtask {j} for task {i}",
                        "status": "todo",
                        "priority": "medium"
                    }
                    subtask_repo.create_new(str(task_id), subtask_data)
                    subtask_time = time.time() - subtask_start
                    performance_metrics["subtask_creation_times"].append(subtask_time)
                
                performance_metrics["total_operations"] += 4  # 1 task + 1 context + 2 subtasks
            
            # Calculate performance statistics
            avg_task_time = sum(performance_metrics["task_creation_times"]) / len(performance_metrics["task_creation_times"])
            avg_context_time = sum(performance_metrics["context_creation_times"]) / len(performance_metrics["context_creation_times"])
            avg_subtask_time = sum(performance_metrics["subtask_creation_times"]) / len(performance_metrics["subtask_creation_times"])
            
            total_time = time.time() - start_time
            operations_per_second = performance_metrics["total_operations"] / total_time
            
            # Performance assertions
            assert avg_task_time < 0.1, f"Task creation should be under 100ms, got {avg_task_time:.3f}s"
            assert avg_context_time < 0.1, f"Context creation should be under 100ms, got {avg_context_time:.3f}s"
            assert avg_subtask_time < 0.1, f"Subtask creation should be under 100ms, got {avg_subtask_time:.3f}s"
            assert operations_per_second > 10, f"Should handle >10 ops/sec, got {operations_per_second:.1f}"
            
            # Verify all data was created correctly
            all_tasks = task_repo.find_all()
            performance_tasks = [t for t in all_tasks if "Performance Test Task" in t.title]
            assert len(performance_tasks) == num_tasks, f"Should have {num_tasks} performance tasks"
            
            execution_time = time.time() - start_time
            self.test_results.append(ExecutionResult(
                test_name=test_name,
                success=True,
                execution_time=execution_time,
                message="Cross-repository performance test passed",
                performance_metrics={
                    "tasks_created": num_tasks,
                    "total_operations": performance_metrics["total_operations"],
                    "operations_per_second": operations_per_second,
                    "avg_task_creation_time": avg_task_time,
                    "avg_context_creation_time": avg_context_time,
                    "avg_subtask_creation_time": avg_subtask_time
                }
            ))
            
            print(f"   ✅ Cross-Repository Performance: PASSED ({execution_time:.3f}s)")
            print(f"      Operations/sec: {operations_per_second:.1f}, Avg task time: {avg_task_time:.3f}s")
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.test_results.append(ExecutionResult(
                test_name=test_name,
                success=False,
                execution_time=execution_time,
                message="Cross-repository performance test failed",
                error_details=str(e)
            ))
            print(f"   ❌ Cross-Repository Performance: FAILED ({execution_time:.3f}s) - {str(e)}")
    
    def _print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 70)
        print("📊 PHASE 2 CROSS-REPOSITORY INTEGRATION TEST SUMMARY")
        print("=" * 70)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.success)
        failed_tests = total_tests - passed_tests
        
        total_time = sum(r.execution_time for r in self.test_results)
        avg_time = total_time / total_tests if total_tests > 0 else 0
        
        print(f"🎯 Overall Results:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests}")
        print(f"   Failed: {failed_tests}")
        print(f"   Success Rate: {(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "   Success Rate: 0%")
        print(f"   Total Execution Time: {total_time:.3f}s")
        print(f"   Average Test Time: {avg_time:.3f}s")
        
        print(f"\n📋 Test-by-Test Results:")
        for result in self.test_results:
            status = "✅ PASS" if result.success else "❌ FAIL"
            print(f"   {status} {result.test_name.replace('_', ' ').title()}")
            print(f"      Time: {result.execution_time:.3f}s")
            print(f"      Message: {result.message}")
            
            if result.performance_metrics:
                print(f"      Performance: {result.performance_metrics}")
            
            if not result.success and result.error_details:
                print(f"      Error: {result.error_details}")
        
        if failed_tests == 0:
            print(f"\n🎉 All Phase 2 Integration Tests Passed!")
            print("✅ Cross-repository integration is working correctly")
            print("✅ Data consistency across repositories verified")
            print("✅ Transaction handling and rollback scenarios working")
            print("✅ Concurrent access and performance validated")
        else:
            print(f"\n⚠️ {failed_tests} tests failed - review and fix issues before proceeding")
        
        print("=" * 70)


async def main():
    """Run Phase 2 cross-repository integration tests"""
    tester = Phase2CrossRepositoryTester()
    await tester.run_all_phase2_tests()


if __name__ == "__main__":
    asyncio.run(main())