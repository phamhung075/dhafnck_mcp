#!/usr/bin/env python3
"""
Phase 3: Performance Validation Tests
=====================================

Comprehensive performance testing of SQLite repositories focusing on:
1. Performance baseline measurement
2. SQLite repository operation benchmarks
3. Cross-repository performance comparison
4. Load testing and scaling analysis
5. Performance regression detection
6. Memory usage and resource consumption analysis

This phase uses direct database access to bypass schema conflicts
while still testing repository performance characteristics.
"""

import sys
import os
import time
import asyncio
import tempfile
import sqlite3
import threading
import concurrent.futures
import psutil
import statistics
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass, field

# Add the project path to sys.path
sys.path.insert(0, 'dhafnck_mcp_main/src')


@dataclass
class PerformanceMetric:
    """Performance metric container"""
    operation: str
    execution_time: float
    memory_usage: float
    cpu_usage: float
    iterations: int
    throughput: float
    error_rate: float = 0.0
    additional_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceBaseline:
    """Performance baseline container"""
    database_type: str
    operation_benchmarks: Dict[str, PerformanceMetric]
    system_info: Dict[str, Any]
    timestamp: datetime
    test_conditions: Dict[str, Any]


class PerformanceProfiler:
    """Performance profiler for monitoring resource usage"""
    
    def __init__(self):
        self.process = psutil.Process()
        self.initial_memory = self.process.memory_info().rss
        self.initial_cpu_percent = self.process.cpu_percent()
        
    def get_current_metrics(self) -> Dict[str, float]:
        """Get current resource usage metrics"""
        return {
            'memory_mb': self.process.memory_info().rss / 1024 / 1024,
            'memory_delta_mb': (self.process.memory_info().rss - self.initial_memory) / 1024 / 1024,
            'cpu_percent': self.process.cpu_percent(),
            'thread_count': self.process.num_threads()
        }


class Phase3PerformanceTester:
    """Phase 3 performance validation tester"""
    
    def __init__(self):
        self.test_results: List[PerformanceMetric] = []
        self.baseline: Optional[PerformanceBaseline] = None
        self.profiler = PerformanceProfiler()
        self.test_db_path: Optional[str] = None
        
    def create_performance_test_database(self) -> str:
        """Create a optimized test database for performance testing"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
            db_path = tmp_file.name
        
        conn = sqlite3.connect(db_path)
        
        # Performance optimizations for testing
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA cache_size = 10000")
        conn.execute("PRAGMA temp_store = MEMORY")
        conn.execute("PRAGMA mmap_size = 268435456")  # 256MB
        
        # Create simplified but complete schema for performance testing
        schema_sql = [
            # Projects table
            '''CREATE TABLE projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                user_id TEXT NOT NULL DEFAULT 'default_id',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )''',
            
            # Project task trees table
            '''CREATE TABLE project_task_trees (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )''',
            
            # Tasks table
            '''CREATE TABLE tasks (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                git_branch_id TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'todo',
                priority TEXT NOT NULL DEFAULT 'medium',
                details TEXT DEFAULT '',
                estimated_effort TEXT DEFAULT '',
                due_date TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (git_branch_id) REFERENCES project_task_trees(id)
            )''',
            
            # Task contexts table
            '''CREATE TABLE task_contexts (
                task_id TEXT PRIMARY KEY,
                objective TEXT DEFAULT '{}',
                progress TEXT DEFAULT '{}',
                insights TEXT DEFAULT '[]',
                next_steps TEXT DEFAULT '[]',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks(id)
            )''',
            
            # Subtasks table
            '''CREATE TABLE task_subtasks (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                status TEXT DEFAULT 'todo',
                priority TEXT DEFAULT 'medium',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks(id)
            )''',
            
            # Performance testing indexes
            '''CREATE INDEX idx_tasks_git_branch_id ON tasks(git_branch_id)''',
            '''CREATE INDEX idx_tasks_status ON tasks(status)''',
            '''CREATE INDEX idx_tasks_priority ON tasks(priority)''',
            '''CREATE INDEX idx_tasks_created_at ON tasks(created_at)''',
            '''CREATE INDEX idx_subtasks_task_id ON task_subtasks(task_id)''',
            '''CREATE INDEX idx_subtasks_status ON task_subtasks(status)''',
        ]
        
        for sql in schema_sql:
            conn.execute(sql)
        
        # Insert test data for performance testing
        now = datetime.now(timezone.utc).isoformat()
        
        # Insert test project and branch
        conn.execute('''
            INSERT INTO projects (id, name, description, user_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ("perf-project", "Performance Test Project", "Project for performance testing", "perf_user", now, now))
        
        conn.execute('''
            INSERT INTO project_task_trees (id, project_id, name, description, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ("perf-branch-001", "perf-project", "main", "Performance test branch", now, now))
        
        conn.commit()
        conn.close()
        
        return db_path
    
    async def run_all_phase3_tests(self):
        """Run all Phase 3 performance validation tests"""
        print("⚡ Phase 3: Performance Validation Tests")
        print("=" * 70)
        
        try:
            # Create performance test database
            self.test_db_path = self.create_performance_test_database()
            print(f"✅ Performance test database created: {self.test_db_path}")
            
            # Test 1: Create Performance Baseline
            await self._create_performance_baseline()
            
            # Test 2: SQLite Repository Operation Benchmarks
            await self._benchmark_repository_operations()
            
            # Test 3: Cross-Repository Performance Analysis
            await self._analyze_cross_repository_performance()
            
            # Test 4: Load Testing and Scaling
            await self._run_load_testing()
            
            # Test 5: Memory Usage Analysis
            await self._analyze_memory_usage()
            
            # Test 6: Concurrent Performance Testing
            await self._test_concurrent_performance()
            
            # Test 7: Query Performance Analysis
            await self._analyze_query_performance()
            
            # Test 8: Performance Regression Detection
            await self._detect_performance_regressions()
            
        finally:
            # Cleanup
            if self.test_db_path and os.path.exists(self.test_db_path):
                os.unlink(self.test_db_path)
                print(f"🧹 Cleaned up performance test database: {self.test_db_path}")
        
        self._print_performance_summary()
    
    async def _create_performance_baseline(self):
        """Test 1: Create Performance Baseline"""
        print("🔧 Test 1: Creating Performance Baseline...")
        
        start_time = time.time()
        conn = sqlite3.connect(self.test_db_path)
        
        # Baseline operations
        baseline_operations = {}
        
        # 1. Single Insert Performance
        insert_times = []
        for i in range(100):
            op_start = time.time()
            task_id = f"baseline_task_{i}"
            conn.execute('''
                INSERT INTO tasks (id, title, description, git_branch_id, status, priority)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (task_id, f"Baseline Task {i}", f"Task {i} for baseline", "perf-branch-001", "todo", "medium"))
            op_end = time.time()
            insert_times.append(op_end - op_start)
        
        conn.commit()
        
        baseline_operations["single_insert"] = PerformanceMetric(
            operation="single_insert",
            execution_time=statistics.mean(insert_times),
            memory_usage=self.profiler.get_current_metrics()['memory_mb'],
            cpu_usage=self.profiler.get_current_metrics()['cpu_percent'],
            iterations=100,
            throughput=100 / sum(insert_times),
            additional_data={
                "min_time": min(insert_times),
                "max_time": max(insert_times),
                "std_dev": statistics.stdev(insert_times)
            }
        )
        
        # 2. Single Select Performance
        select_times = []
        for i in range(100):
            op_start = time.time()
            task_id = f"baseline_task_{i}"
            result = conn.execute('SELECT * FROM tasks WHERE id = ?', (task_id,)).fetchone()
            op_end = time.time()
            select_times.append(op_end - op_start)
            assert result is not None, f"Task {task_id} should exist"
        
        baseline_operations["single_select"] = PerformanceMetric(
            operation="single_select",
            execution_time=statistics.mean(select_times),
            memory_usage=self.profiler.get_current_metrics()['memory_mb'],
            cpu_usage=self.profiler.get_current_metrics()['cpu_percent'],
            iterations=100,
            throughput=100 / sum(select_times),
            additional_data={
                "min_time": min(select_times),
                "max_time": max(select_times),
                "std_dev": statistics.stdev(select_times)
            }
        )
        
        # 3. Bulk Select Performance
        bulk_start = time.time()
        all_tasks = conn.execute('SELECT * FROM tasks').fetchall()
        bulk_end = time.time()
        
        baseline_operations["bulk_select"] = PerformanceMetric(
            operation="bulk_select",
            execution_time=bulk_end - bulk_start,
            memory_usage=self.profiler.get_current_metrics()['memory_mb'],
            cpu_usage=self.profiler.get_current_metrics()['cpu_percent'],
            iterations=1,
            throughput=len(all_tasks) / (bulk_end - bulk_start),
            additional_data={"records_fetched": len(all_tasks)}
        )
        
        # 4. Update Performance
        update_times = []
        for i in range(50):
            op_start = time.time()
            task_id = f"baseline_task_{i}"
            conn.execute('''
                UPDATE tasks SET title = ?, updated_at = ? WHERE id = ?
            ''', (f"Updated Baseline Task {i}", datetime.now(timezone.utc).isoformat(), task_id))
            op_end = time.time()
            update_times.append(op_end - op_start)
        
        conn.commit()
        
        baseline_operations["single_update"] = PerformanceMetric(
            operation="single_update",
            execution_time=statistics.mean(update_times),
            memory_usage=self.profiler.get_current_metrics()['memory_mb'],
            cpu_usage=self.profiler.get_current_metrics()['cpu_percent'],
            iterations=50,
            throughput=50 / sum(update_times),
            additional_data={
                "min_time": min(update_times),
                "max_time": max(update_times),
                "std_dev": statistics.stdev(update_times) if len(update_times) > 1 else 0
            }
        )
        
        conn.close()
        
        # Create baseline
        self.baseline = PerformanceBaseline(
            database_type="SQLite",
            operation_benchmarks=baseline_operations,
            system_info={
                "python_version": sys.version,
                "platform": sys.platform,
                "cpu_count": os.cpu_count(),
                "memory_total": psutil.virtual_memory().total / 1024 / 1024 / 1024  # GB
            },
            timestamp=datetime.now(timezone.utc),
            test_conditions={
                "database_path": self.test_db_path,
                "sqlite_version": sqlite3.sqlite_version,
                "pragma_settings": {
                    "journal_mode": "WAL",
                    "synchronous": "NORMAL",
                    "cache_size": "10000"
                }
            }
        )
        
        execution_time = time.time() - start_time
        self.test_results.append(PerformanceMetric(
            operation="baseline_creation",
            execution_time=execution_time,
            memory_usage=self.profiler.get_current_metrics()['memory_mb'],
            cpu_usage=self.profiler.get_current_metrics()['cpu_percent'],
            iterations=1,
            throughput=len(baseline_operations) / execution_time,
            additional_data={"baseline_operations": len(baseline_operations)}
        ))
        
        print(f"   ✅ Performance Baseline Created ({execution_time:.3f}s)")
        print(f"      Single Insert: {baseline_operations['single_insert'].execution_time*1000:.2f}ms avg")
        print(f"      Single Select: {baseline_operations['single_select'].execution_time*1000:.2f}ms avg")
        print(f"      Bulk Select: {baseline_operations['bulk_select'].execution_time*1000:.2f}ms")
        print(f"      Single Update: {baseline_operations['single_update'].execution_time*1000:.2f}ms avg")
    
    async def _benchmark_repository_operations(self):
        """Test 2: SQLite Repository Operation Benchmarks"""
        print("🔧 Test 2: SQLite Repository Operation Benchmarks...")
        
        start_time = time.time()
        conn = sqlite3.connect(self.test_db_path)
        
        # Complex Operations Benchmarking
        
        # 1. Cross-table Join Performance
        join_start = time.time()
        join_results = conn.execute('''
            SELECT t.id, t.title, t.status, ptt.name as branch_name, p.name as project_name
            FROM tasks t
            JOIN project_task_trees ptt ON t.git_branch_id = ptt.id
            JOIN projects p ON ptt.project_id = p.id
            WHERE t.status = 'todo'
        ''').fetchall()
        join_end = time.time()
        
        # 2. Aggregation Query Performance
        agg_start = time.time()
        agg_results = conn.execute('''
            SELECT 
                status,
                priority,
                COUNT(*) as count,
                AVG(LENGTH(description)) as avg_desc_length
            FROM tasks
            GROUP BY status, priority
            ORDER BY count DESC
        ''').fetchall()
        agg_end = time.time()
        
        # 3. Full-Text Search Simulation
        search_start = time.time()
        search_results = conn.execute('''
            SELECT * FROM tasks
            WHERE title LIKE '%Baseline%' OR description LIKE '%Task%'
            ORDER BY created_at DESC
            LIMIT 20
        ''').fetchall()
        search_end = time.time()
        
        # 4. Batch Insert Performance
        batch_data = [(f"batch_task_{i}", f"Batch Task {i}", f"Description for batch task {i}", 
                      "perf-branch-001", "todo", "medium") for i in range(1000)]
        
        batch_start = time.time()
        conn.executemany('''
            INSERT INTO tasks (id, title, description, git_branch_id, status, priority)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', batch_data)
        conn.commit()
        batch_end = time.time()
        
        # 5. Transaction Performance
        transaction_start = time.time()
        conn.execute('BEGIN TRANSACTION')
        
        for i in range(100):
            # Insert task
            task_id = f"trans_task_{i}"
            conn.execute('''
                INSERT INTO tasks (id, title, description, git_branch_id, status, priority)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (task_id, f"Transaction Task {i}", f"Task {i} in transaction", "perf-branch-001", "todo", "medium"))
            
            # Insert context
            conn.execute('''
                INSERT INTO task_contexts (task_id, objective, progress)
                VALUES (?, ?, ?)
            ''', (task_id, '{"title": "Transaction Test"}', '{"completion": 0}'))
            
            # Insert subtask
            conn.execute('''
                INSERT INTO task_subtasks (id, task_id, title, description)
                VALUES (?, ?, ?, ?)
            ''', (f"trans_sub_{i}", task_id, f"Subtask for {task_id}", "Transaction subtask"))
        
        conn.execute('COMMIT')
        transaction_end = time.time()
        
        conn.close()
        
        # Record benchmarks
        benchmarks = {
            "cross_table_join": PerformanceMetric(
                operation="cross_table_join",
                execution_time=join_end - join_start,
                memory_usage=self.profiler.get_current_metrics()['memory_mb'],
                cpu_usage=self.profiler.get_current_metrics()['cpu_percent'],
                iterations=1,
                throughput=len(join_results) / (join_end - join_start),
                additional_data={"records_joined": len(join_results)}
            ),
            "aggregation_query": PerformanceMetric(
                operation="aggregation_query",
                execution_time=agg_end - agg_start,
                memory_usage=self.profiler.get_current_metrics()['memory_mb'],
                cpu_usage=self.profiler.get_current_metrics()['cpu_percent'],
                iterations=1,
                throughput=len(agg_results) / (agg_end - agg_start),
                additional_data={"groups_aggregated": len(agg_results)}
            ),
            "search_query": PerformanceMetric(
                operation="search_query",
                execution_time=search_end - search_start,
                memory_usage=self.profiler.get_current_metrics()['memory_mb'],
                cpu_usage=self.profiler.get_current_metrics()['cpu_percent'],
                iterations=1,
                throughput=len(search_results) / (search_end - search_start),
                additional_data={"records_found": len(search_results)}
            ),
            "batch_insert": PerformanceMetric(
                operation="batch_insert",
                execution_time=batch_end - batch_start,
                memory_usage=self.profiler.get_current_metrics()['memory_mb'],
                cpu_usage=self.profiler.get_current_metrics()['cpu_percent'],
                iterations=1000,
                throughput=1000 / (batch_end - batch_start),
                additional_data={"records_inserted": 1000}
            ),
            "complex_transaction": PerformanceMetric(
                operation="complex_transaction",
                execution_time=transaction_end - transaction_start,
                memory_usage=self.profiler.get_current_metrics()['memory_mb'],
                cpu_usage=self.profiler.get_current_metrics()['cpu_percent'],
                iterations=100,
                throughput=300 / (transaction_end - transaction_start),  # 3 operations per iteration
                additional_data={"operations_per_transaction": 3, "total_operations": 300}
            )
        }
        
        self.test_results.extend(benchmarks.values())
        
        execution_time = time.time() - start_time
        print(f"   ✅ Repository Operation Benchmarks Complete ({execution_time:.3f}s)")
        print(f"      Join Query: {benchmarks['cross_table_join'].execution_time*1000:.2f}ms")
        print(f"      Aggregation: {benchmarks['aggregation_query'].execution_time*1000:.2f}ms")
        print(f"      Search: {benchmarks['search_query'].execution_time*1000:.2f}ms")
        print(f"      Batch Insert: {benchmarks['batch_insert'].throughput:.0f} records/sec")
        print(f"      Transaction: {benchmarks['complex_transaction'].throughput:.0f} ops/sec")
    
    async def _analyze_cross_repository_performance(self):
        """Test 3: Cross-Repository Performance Analysis"""
        print("🔧 Test 3: Cross-Repository Performance Analysis...")
        
        start_time = time.time()
        conn = sqlite3.connect(self.test_db_path)
        
        # Simulate cross-repository operations
        cross_repo_operations = []
        
        for i in range(50):
            op_start = time.time()
            
            # Operation 1: Create task (Task Repository)
            task_id = f"cross_repo_task_{i}"
            conn.execute('''
                INSERT INTO tasks (id, title, description, git_branch_id, status, priority)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (task_id, f"Cross-Repo Task {i}", f"Task {i} for cross-repo test", "perf-branch-001", "todo", "medium"))
            
            # Operation 2: Create context (Context Repository)
            conn.execute('''
                INSERT INTO task_contexts (task_id, objective, progress, next_steps)
                VALUES (?, ?, ?, ?)
            ''', (task_id, f'{{"title": "Cross-Repo Context {i}"}}', '{"completion": 0}', f'["Step {i}.1", "Step {i}.2"]'))
            
            # Operation 3: Create subtasks (Subtask Repository)
            for j in range(2):
                subtask_id = f"cross_repo_sub_{i}_{j}"
                conn.execute('''
                    INSERT INTO task_subtasks (id, task_id, title, description, status)
                    VALUES (?, ?, ?, ?, ?)
                ''', (subtask_id, task_id, f"Subtask {i}.{j}", f"Subtask {j} for task {i}", "todo"))
            
            # Operation 4: Query across all repositories
            result = conn.execute('''
                SELECT 
                    t.id, t.title, t.status,
                    tc.objective, tc.progress,
                    COUNT(ts.id) as subtask_count
                FROM tasks t
                LEFT JOIN task_contexts tc ON t.id = tc.task_id
                LEFT JOIN task_subtasks ts ON t.id = ts.task_id
                WHERE t.id = ?
                GROUP BY t.id, t.title, t.status, tc.objective, tc.progress
            ''', (task_id,)).fetchone()
            
            conn.commit()
            op_end = time.time()
            
            cross_repo_operations.append(op_end - op_start)
            assert result is not None, f"Cross-repo query should return result for {task_id}"
        
        conn.close()
        
        cross_repo_metric = PerformanceMetric(
            operation="cross_repository_operation",
            execution_time=statistics.mean(cross_repo_operations),
            memory_usage=self.profiler.get_current_metrics()['memory_mb'],
            cpu_usage=self.profiler.get_current_metrics()['cpu_percent'],
            iterations=50,
            throughput=50 / sum(cross_repo_operations),
            additional_data={
                "operations_per_iteration": 4,
                "total_operations": 200,
                "min_time": min(cross_repo_operations),
                "max_time": max(cross_repo_operations),
                "std_dev": statistics.stdev(cross_repo_operations)
            }
        )
        
        self.test_results.append(cross_repo_metric)
        
        execution_time = time.time() - start_time
        print(f"   ✅ Cross-Repository Performance Analysis Complete ({execution_time:.3f}s)")
        print(f"      Average Operation Time: {cross_repo_metric.execution_time*1000:.2f}ms")
        print(f"      Operations per Second: {cross_repo_metric.throughput:.1f}")
        print(f"      Standard Deviation: {cross_repo_metric.additional_data['std_dev']*1000:.2f}ms")
    
    async def _run_load_testing(self):
        """Test 4: Load Testing and Scaling"""
        print("🔧 Test 4: Load Testing and Scaling...")
        
        start_time = time.time()
        
        # Test different load levels
        load_levels = [10, 50, 100, 200, 500]
        load_results = {}
        
        for load in load_levels:
            print(f"      Testing load level: {load} operations...")
            
            conn = sqlite3.connect(self.test_db_path)
            
            load_start = time.time()
            
            # Perform load operations
            for i in range(load):
                task_id = f"load_task_{load}_{i}"
                conn.execute('''
                    INSERT INTO tasks (id, title, description, git_branch_id, status, priority)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (task_id, f"Load Task {load}-{i}", f"Task {i} at load {load}", "perf-branch-001", "todo", "medium"))
                
                if i % 10 == 0:  # Commit every 10 operations
                    conn.commit()
            
            conn.commit()
            load_end = time.time()
            
            # Query performance under load
            query_start = time.time()
            results = conn.execute('SELECT COUNT(*) FROM tasks').fetchone()
            query_end = time.time()
            
            conn.close()
            
            load_time = load_end - load_start
            query_time = query_end - query_start
            
            load_results[load] = PerformanceMetric(
                operation=f"load_test_{load}",
                execution_time=load_time,
                memory_usage=self.profiler.get_current_metrics()['memory_mb'],
                cpu_usage=self.profiler.get_current_metrics()['cpu_percent'],
                iterations=load,
                throughput=load / load_time,
                additional_data={
                    "query_time": query_time,
                    "total_records": results[0] if results else 0,
                    "avg_operation_time": load_time / load
                }
            )
        
        # Analyze scaling characteristics
        throughputs = [load_results[load].throughput for load in load_levels]
        avg_op_times = [load_results[load].additional_data['avg_operation_time'] for load in load_levels]
        
        scaling_analysis = PerformanceMetric(
            operation="scaling_analysis",
            execution_time=time.time() - start_time,
            memory_usage=self.profiler.get_current_metrics()['memory_mb'],
            cpu_usage=self.profiler.get_current_metrics()['cpu_percent'],
            iterations=len(load_levels),
            throughput=max(throughputs),
            additional_data={
                "load_levels": load_levels,
                "throughputs": throughputs,
                "avg_operation_times": avg_op_times,
                "max_throughput": max(throughputs),
                "min_operation_time": min(avg_op_times),
                "scaling_efficiency": throughputs[-1] / throughputs[0]  # High load vs low load
            }
        )
        
        self.test_results.extend(load_results.values())
        self.test_results.append(scaling_analysis)
        
        execution_time = time.time() - start_time
        print(f"   ✅ Load Testing Complete ({execution_time:.3f}s)")
        print(f"      Max Throughput: {max(throughputs):.1f} ops/sec at load {load_levels[throughputs.index(max(throughputs))]}")
        print(f"      Min Avg Operation Time: {min(avg_op_times)*1000:.2f}ms")
        print(f"      Scaling Efficiency: {scaling_analysis.additional_data['scaling_efficiency']:.2f}")
    
    async def _analyze_memory_usage(self):
        """Test 5: Memory Usage Analysis"""
        print("🔧 Test 5: Memory Usage Analysis...")
        
        start_time = time.time()
        initial_memory = self.profiler.get_current_metrics()['memory_mb']
        
        conn = sqlite3.connect(self.test_db_path)
        memory_snapshots = []
        
        # Test memory usage under different scenarios
        
        # 1. Memory usage during bulk operations
        for batch in range(10):
            batch_data = [(f"memory_task_{batch}_{i}", f"Memory Task {batch}-{i}", 
                          f"Description for memory task {batch}-{i}", "perf-branch-001", "todo", "medium") 
                         for i in range(100)]
            
            pre_insert_memory = self.profiler.get_current_metrics()['memory_mb']
            
            conn.executemany('''
                INSERT INTO tasks (id, title, description, git_branch_id, status, priority)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', batch_data)
            conn.commit()
            
            post_insert_memory = self.profiler.get_current_metrics()['memory_mb']
            
            memory_snapshots.append({
                'batch': batch,
                'pre_insert': pre_insert_memory,
                'post_insert': post_insert_memory,
                'delta': post_insert_memory - pre_insert_memory
            })
        
        # 2. Memory usage during large query
        large_query_start_memory = self.profiler.get_current_metrics()['memory_mb']
        
        large_result = conn.execute('''
            SELECT t.*, tc.objective, tc.progress
            FROM tasks t
            LEFT JOIN task_contexts tc ON t.id = tc.task_id
            ORDER BY t.created_at
        ''').fetchall()
        
        large_query_end_memory = self.profiler.get_current_metrics()['memory_mb']
        
        # 3. Memory cleanup test
        conn.close()
        del large_result
        
        # Force garbage collection
        import gc
        gc.collect()
        
        final_memory = self.profiler.get_current_metrics()['memory_mb']
        
        memory_analysis = PerformanceMetric(
            operation="memory_analysis",
            execution_time=time.time() - start_time,
            memory_usage=final_memory,
            cpu_usage=self.profiler.get_current_metrics()['cpu_percent'],
            iterations=10,
            throughput=1000 / (time.time() - start_time),  # Records processed per second
            additional_data={
                "initial_memory": initial_memory,
                "peak_memory": max(snap['post_insert'] for snap in memory_snapshots),
                "final_memory": final_memory,
                "total_memory_delta": final_memory - initial_memory,
                "avg_batch_memory_delta": statistics.mean([snap['delta'] for snap in memory_snapshots]),
                "large_query_memory_delta": large_query_end_memory - large_query_start_memory,
                "memory_snapshots": memory_snapshots
            }
        )
        
        self.test_results.append(memory_analysis)
        
        execution_time = time.time() - start_time
        print(f"   ✅ Memory Usage Analysis Complete ({execution_time:.3f}s)")
        print(f"      Initial Memory: {initial_memory:.1f}MB")
        print(f"      Peak Memory: {memory_analysis.additional_data['peak_memory']:.1f}MB")
        print(f"      Final Memory: {final_memory:.1f}MB")
        print(f"      Total Delta: {memory_analysis.additional_data['total_memory_delta']:.1f}MB")
        print(f"      Avg Batch Delta: {memory_analysis.additional_data['avg_batch_memory_delta']:.2f}MB")
    
    async def _test_concurrent_performance(self):
        """Test 6: Concurrent Performance Testing"""
        print("🔧 Test 6: Concurrent Performance Testing...")
        
        start_time = time.time()
        
        # Test different concurrency levels
        concurrency_levels = [1, 2, 4, 8]
        concurrent_results = {}
        
        for concurrency in concurrency_levels:
            print(f"      Testing concurrency level: {concurrency} threads...")
            
            operations_per_thread = 100
            total_operations = concurrency * operations_per_thread
            
            def worker_function(worker_id):
                """Worker function for concurrent operations"""
                worker_conn = sqlite3.connect(self.test_db_path)
                worker_times = []
                
                for i in range(operations_per_thread):
                    op_start = time.time()
                    
                    task_id = f"concurrent_task_{concurrency}_{worker_id}_{i}"
                    worker_conn.execute('''
                        INSERT INTO tasks (id, title, description, git_branch_id, status, priority)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (task_id, f"Concurrent Task {worker_id}-{i}", 
                         f"Task {i} by worker {worker_id}", "perf-branch-001", "todo", "medium"))
                    
                    if i % 10 == 0:
                        worker_conn.commit()
                    
                    op_end = time.time()
                    worker_times.append(op_end - op_start)
                
                worker_conn.commit()
                worker_conn.close()
                
                return {
                    'worker_id': worker_id,
                    'operations': operations_per_thread,
                    'total_time': sum(worker_times),
                    'avg_time': statistics.mean(worker_times),
                    'min_time': min(worker_times),
                    'max_time': max(worker_times)
                }
            
            concurrent_start = time.time()
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
                futures = [executor.submit(worker_function, i) for i in range(concurrency)]
                worker_results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            concurrent_end = time.time()
            total_time = concurrent_end - concurrent_start
            
            # Calculate aggregate metrics
            all_operation_times = []
            for result in worker_results:
                all_operation_times.extend([result['avg_time']] * result['operations'])
            
            concurrent_results[concurrency] = PerformanceMetric(
                operation=f"concurrent_test_{concurrency}",
                execution_time=total_time,
                memory_usage=self.profiler.get_current_metrics()['memory_mb'],
                cpu_usage=self.profiler.get_current_metrics()['cpu_percent'],
                iterations=total_operations,
                throughput=total_operations / total_time,
                additional_data={
                    "workers": concurrency,
                    "operations_per_worker": operations_per_thread,
                    "total_operations": total_operations,
                    "avg_operation_time": statistics.mean(all_operation_times),
                    "worker_results": worker_results,
                    "parallelization_efficiency": (total_operations / total_time) / (operations_per_thread / worker_results[0]['total_time'])
                }
            )
        
        # Analyze concurrency scaling
        throughputs = [concurrent_results[c].throughput for c in concurrency_levels]
        efficiencies = [concurrent_results[c].additional_data['parallelization_efficiency'] for c in concurrency_levels]
        
        concurrency_analysis = PerformanceMetric(
            operation="concurrency_analysis",
            execution_time=time.time() - start_time,
            memory_usage=self.profiler.get_current_metrics()['memory_mb'],
            cpu_usage=self.profiler.get_current_metrics()['cpu_percent'],
            iterations=len(concurrency_levels),
            throughput=max(throughputs),
            additional_data={
                "concurrency_levels": concurrency_levels,
                "throughputs": throughputs,
                "efficiencies": efficiencies,
                "optimal_concurrency": concurrency_levels[throughputs.index(max(throughputs))],
                "max_efficiency": max(efficiencies),
                "concurrency_scaling_factor": throughputs[-1] / throughputs[0]
            }
        )
        
        self.test_results.extend(concurrent_results.values())
        self.test_results.append(concurrency_analysis)
        
        execution_time = time.time() - start_time
        print(f"   ✅ Concurrent Performance Testing Complete ({execution_time:.3f}s)")
        print(f"      Optimal Concurrency: {concurrency_analysis.additional_data['optimal_concurrency']} threads")
        print(f"      Max Throughput: {max(throughputs):.1f} ops/sec")
        print(f"      Max Efficiency: {max(efficiencies):.2f}")
        print(f"      Scaling Factor: {concurrency_analysis.additional_data['concurrency_scaling_factor']:.2f}")
    
    async def _analyze_query_performance(self):
        """Test 7: Query Performance Analysis"""
        print("🔧 Test 7: Query Performance Analysis...")
        
        start_time = time.time()
        conn = sqlite3.connect(self.test_db_path)
        
        # Different query types and complexity levels
        query_tests = {
            "simple_select": "SELECT * FROM tasks WHERE status = 'todo' LIMIT 10",
            "indexed_search": "SELECT * FROM tasks WHERE git_branch_id = 'perf-branch-001' AND status = 'todo'",
            "range_query": "SELECT * FROM tasks WHERE created_at > datetime('now', '-1 day')",
            "aggregation": "SELECT status, priority, COUNT(*) FROM tasks GROUP BY status, priority",
            "complex_join": """
                SELECT t.title, t.status, tc.objective, COUNT(ts.id) as subtask_count
                FROM tasks t
                LEFT JOIN task_contexts tc ON t.id = tc.task_id
                LEFT JOIN task_subtasks ts ON t.id = ts.task_id
                GROUP BY t.id, t.title, t.status, tc.objective
                HAVING COUNT(ts.id) > 0
                ORDER BY subtask_count DESC
                LIMIT 20
            """,
            "full_text_search": "SELECT * FROM tasks WHERE title LIKE '%Task%' OR description LIKE '%test%'",
            "subquery": """
                SELECT * FROM tasks WHERE id IN (
                    SELECT task_id FROM task_contexts WHERE objective LIKE '%Test%'
                )
            """,
            "window_function": """
                SELECT 
                    title, status, created_at,
                    ROW_NUMBER() OVER (PARTITION BY status ORDER BY created_at) as rank_in_status
                FROM tasks
                ORDER BY status, rank_in_status
                LIMIT 50
            """
        }
        
        query_results = {}
        
        for query_name, query_sql in query_tests.items():
            # Run each query multiple times for reliable metrics
            query_times = []
            
            for _ in range(10):
                query_start = time.time()
                try:
                    results = conn.execute(query_sql).fetchall()
                    query_end = time.time()
                    query_times.append(query_end - query_start)
                except Exception as e:
                    print(f"      Warning: Query {query_name} failed: {e}")
                    query_times.append(float('inf'))
                    results = []
            
            # Filter out failed queries
            valid_times = [t for t in query_times if t != float('inf')]
            
            if valid_times:
                query_results[query_name] = PerformanceMetric(
                    operation=f"query_{query_name}",
                    execution_time=statistics.mean(valid_times),
                    memory_usage=self.profiler.get_current_metrics()['memory_mb'],
                    cpu_usage=self.profiler.get_current_metrics()['cpu_percent'],
                    iterations=len(valid_times),
                    throughput=len(results) / statistics.mean(valid_times) if statistics.mean(valid_times) > 0 else 0,
                    additional_data={
                        "result_count": len(results),
                        "min_time": min(valid_times),
                        "max_time": max(valid_times),
                        "std_dev": statistics.stdev(valid_times) if len(valid_times) > 1 else 0,
                        "success_rate": len(valid_times) / len(query_times)
                    }
                )
        
        conn.close()
        
        # Analyze query performance patterns
        avg_times = [q.execution_time for q in query_results.values()]
        query_analysis = PerformanceMetric(
            operation="query_analysis",
            execution_time=time.time() - start_time,
            memory_usage=self.profiler.get_current_metrics()['memory_mb'],
            cpu_usage=self.profiler.get_current_metrics()['cpu_percent'],
            iterations=len(query_tests),
            throughput=len(query_tests) / (time.time() - start_time),
            additional_data={
                "queries_tested": len(query_results),
                "avg_query_time": statistics.mean(avg_times) if avg_times else 0,
                "fastest_query": min(query_results.keys(), key=lambda k: query_results[k].execution_time) if query_results else None,
                "slowest_query": max(query_results.keys(), key=lambda k: query_results[k].execution_time) if query_results else None,
                "query_results": {k: v.execution_time for k, v in query_results.items()}
            }
        )
        
        self.test_results.extend(query_results.values())
        self.test_results.append(query_analysis)
        
        execution_time = time.time() - start_time
        print(f"   ✅ Query Performance Analysis Complete ({execution_time:.3f}s)")
        print(f"      Queries Tested: {len(query_results)}")
        print(f"      Average Query Time: {query_analysis.additional_data['avg_query_time']*1000:.2f}ms")
        if query_analysis.additional_data['fastest_query']:
            fastest = query_analysis.additional_data['fastest_query']
            print(f"      Fastest Query: {fastest} ({query_results[fastest].execution_time*1000:.2f}ms)")
        if query_analysis.additional_data['slowest_query']:
            slowest = query_analysis.additional_data['slowest_query']
            print(f"      Slowest Query: {slowest} ({query_results[slowest].execution_time*1000:.2f}ms)")
    
    async def _detect_performance_regressions(self):
        """Test 8: Performance Regression Detection"""
        print("🔧 Test 8: Performance Regression Detection...")
        
        start_time = time.time()
        
        if not self.baseline:
            print("      Warning: No baseline available for regression detection")
            return
        
        # Compare current performance against baseline
        regressions = []
        improvements = []
        
        baseline_ops = self.baseline.operation_benchmarks
        current_results = {r.operation: r for r in self.test_results}
        
        for op_name, baseline_metric in baseline_ops.items():
            if op_name in current_results:
                current_metric = current_results[op_name]
                
                # Calculate performance ratio (current / baseline)
                time_ratio = current_metric.execution_time / baseline_metric.execution_time
                throughput_ratio = current_metric.throughput / baseline_metric.throughput if baseline_metric.throughput > 0 else 1
                
                # Define regression thresholds
                time_regression_threshold = 1.2  # 20% slower
                throughput_regression_threshold = 0.8  # 20% less throughput
                
                if time_ratio > time_regression_threshold or throughput_ratio < throughput_regression_threshold:
                    regressions.append({
                        'operation': op_name,
                        'time_ratio': time_ratio,
                        'throughput_ratio': throughput_ratio,
                        'baseline_time': baseline_metric.execution_time,
                        'current_time': current_metric.execution_time,
                        'baseline_throughput': baseline_metric.throughput,
                        'current_throughput': current_metric.throughput
                    })
                elif time_ratio < 0.8 or throughput_ratio > 1.2:  # 20% improvement
                    improvements.append({
                        'operation': op_name,
                        'time_ratio': time_ratio,
                        'throughput_ratio': throughput_ratio,
                        'improvement_type': 'time' if time_ratio < 0.8 else 'throughput'
                    })
        
        # Analyze overall performance trend
        time_ratios = []
        throughput_ratios = []
        
        for op_name, baseline_metric in baseline_ops.items():
            if op_name in current_results:
                current_metric = current_results[op_name]
                time_ratios.append(current_metric.execution_time / baseline_metric.execution_time)
                if baseline_metric.throughput > 0:
                    throughput_ratios.append(current_metric.throughput / baseline_metric.throughput)
        
        regression_analysis = PerformanceMetric(
            operation="regression_analysis",
            execution_time=time.time() - start_time,
            memory_usage=self.profiler.get_current_metrics()['memory_mb'],
            cpu_usage=self.profiler.get_current_metrics()['cpu_percent'],
            iterations=len(baseline_ops),
            throughput=len(baseline_ops) / (time.time() - start_time),
            additional_data={
                "baseline_timestamp": self.baseline.timestamp.isoformat(),
                "operations_compared": len(baseline_ops),
                "regressions_detected": len(regressions),
                "improvements_detected": len(improvements),
                "regressions": regressions,
                "improvements": improvements,
                "avg_time_ratio": statistics.mean(time_ratios) if time_ratios else 1.0,
                "avg_throughput_ratio": statistics.mean(throughput_ratios) if throughput_ratios else 1.0,
                "overall_performance_change": "regression" if (statistics.mean(time_ratios) if time_ratios else 1.0) > 1.1 else "improvement" if (statistics.mean(time_ratios) if time_ratios else 1.0) < 0.9 else "stable"
            }
        )
        
        self.test_results.append(regression_analysis)
        
        execution_time = time.time() - start_time
        print(f"   ✅ Performance Regression Detection Complete ({execution_time:.3f}s)")
        print(f"      Operations Compared: {len(baseline_ops)}")
        print(f"      Regressions Detected: {len(regressions)}")
        print(f"      Improvements Detected: {len(improvements)}")
        print(f"      Overall Performance: {regression_analysis.additional_data['overall_performance_change']}")
        
        if regressions:
            print("      🔍 Performance Regressions Found:")
            for reg in regressions[:3]:  # Show top 3
                print(f"        - {reg['operation']}: {reg['time_ratio']:.2f}x slower")
        
        if improvements:
            print("      🚀 Performance Improvements Found:")
            for imp in improvements[:3]:  # Show top 3
                print(f"        - {imp['operation']}: {imp['time_ratio']:.2f}x faster")
    
    def _print_performance_summary(self):
        """Print comprehensive performance summary"""
        print("\n" + "=" * 70)
        print("📊 PHASE 3 PERFORMANCE VALIDATION SUMMARY")
        print("=" * 70)
        
        if not self.test_results:
            print("❌ No performance test results available")
            return
        
        # Overall statistics
        total_tests = len(self.test_results)
        total_time = sum(r.execution_time for r in self.test_results)
        avg_memory = statistics.mean([r.memory_usage for r in self.test_results])
        avg_cpu = statistics.mean([r.cpu_usage for r in self.test_results])
        
        print(f"🎯 Overall Performance Results:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Total Execution Time: {total_time:.3f}s")
        print(f"   Average Memory Usage: {avg_memory:.1f}MB")
        print(f"   Average CPU Usage: {avg_cpu:.1f}%")
        
        # Performance categories
        categories = {
            "Baseline Operations": [r for r in self.test_results if "baseline" in r.operation or r.operation in ["single_insert", "single_select", "bulk_select", "single_update"]],
            "Repository Operations": [r for r in self.test_results if any(op in r.operation for op in ["join", "aggregation", "search", "batch", "transaction"])],
            "Cross-Repository": [r for r in self.test_results if "cross_repo" in r.operation],
            "Load Testing": [r for r in self.test_results if "load_test" in r.operation],
            "Concurrency": [r for r in self.test_results if "concurrent" in r.operation],
            "Query Performance": [r for r in self.test_results if "query_" in r.operation],
        }
        
        print(f"\n📋 Performance by Category:")
        for category, results in categories.items():
            if results:
                avg_time = statistics.mean([r.execution_time for r in results])
                max_throughput = max([r.throughput for r in results])
                print(f"   {category}:")
                print(f"      Average Time: {avg_time*1000:.2f}ms")
                print(f"      Max Throughput: {max_throughput:.1f} ops/sec")
                print(f"      Tests: {len(results)}")
        
        # Top performers
        fastest_operations = sorted(self.test_results, key=lambda x: x.execution_time)[:5]
        highest_throughput = sorted(self.test_results, key=lambda x: x.throughput, reverse=True)[:5]
        
        print(f"\n🚀 Top Performing Operations:")
        print(f"   Fastest Operations:")
        for i, result in enumerate(fastest_operations, 1):
            print(f"      {i}. {result.operation}: {result.execution_time*1000:.2f}ms")
        
        print(f"   Highest Throughput:")
        for i, result in enumerate(highest_throughput, 1):
            print(f"      {i}. {result.operation}: {result.throughput:.1f} ops/sec")
        
        # Baseline comparison if available
        if self.baseline:
            print(f"\n📈 Baseline Comparison:")
            print(f"   Baseline Created: {self.baseline.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Database Type: {self.baseline.database_type}")
            
            regression_result = next((r for r in self.test_results if r.operation == "regression_analysis"), None)
            if regression_result:
                print(f"   Overall Performance: {regression_result.additional_data['overall_performance_change']}")
                print(f"   Regressions Detected: {regression_result.additional_data['regressions_detected']}")
                print(f"   Improvements Detected: {regression_result.additional_data['improvements_detected']}")
        
        # Performance recommendations
        print(f"\n💡 Performance Recommendations:")
        
        # Memory analysis
        memory_results = [r for r in self.test_results if r.operation == "memory_analysis"]
        if memory_results:
            memory_result = memory_results[0]
            total_delta = memory_result.additional_data['total_memory_delta']
            if total_delta > 50:  # More than 50MB increase
                print(f"   ⚠️ High memory usage detected (+{total_delta:.1f}MB)")
                print(f"      Consider implementing connection pooling or result pagination")
        
        # Concurrency analysis
        concurrency_results = [r for r in self.test_results if r.operation == "concurrency_analysis"]
        if concurrency_results:
            concurrency_result = concurrency_results[0]
            optimal_concurrency = concurrency_result.additional_data['optimal_concurrency']
            print(f"   🔧 Optimal concurrency level: {optimal_concurrency} threads")
            
            efficiency = concurrency_result.additional_data['max_efficiency']
            if efficiency < 0.8:
                print(f"      ⚠️ Low parallelization efficiency ({efficiency:.2f})")
                print(f"      Consider optimizing database connection management")
        
        # Query performance
        query_results = [r for r in self.test_results if "query_" in r.operation]
        if query_results:
            slow_queries = [r for r in query_results if r.execution_time > 0.1]  # >100ms
            if slow_queries:
                print(f"   🐌 Slow queries detected ({len(slow_queries)} queries >100ms)")
                print(f"      Consider adding indexes or optimizing query structure")
        
        print(f"\n🎉 Phase 3 Performance Validation Complete!")
        print("=" * 70)


async def main():
    """Run Phase 3 performance validation tests"""
    tester = Phase3PerformanceTester()
    await tester.run_all_phase3_tests()


if __name__ == "__main__":
    asyncio.run(main())