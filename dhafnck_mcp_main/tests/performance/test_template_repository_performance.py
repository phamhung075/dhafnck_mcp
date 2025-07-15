"""
Performance tests for SQLite Template Repository
Tests performance characteristics and compares with baseline expectations
"""

import pytest
import tempfile
import os
import time
from datetime import datetime, timezone
from typing import List

from fastmcp.task_management.infrastructure.repositories.sqlite.template_repository import SQLiteTemplateRepository
from fastmcp.task_management.domain.entities.template import Template, TemplateUsage
from fastmcp.task_management.domain.value_objects.template_id import TemplateId
from fastmcp.task_management.domain.enums.template_enums import (
    TemplateType, TemplateCategory, TemplateStatus, TemplatePriority
)

pytestmark = pytest.mark.unit  # Use unit marker to avoid global DB setup


class TestTemplateRepositoryPerformance:
    """Performance test suite for SQLite Template Repository"""

    def setup_method(self):
        """Setup performance test fixtures"""
        # Create temporary database for performance testing
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        self.db_path = self.temp_db.name
        
        # Initialize repository
        self.repository = SQLiteTemplateRepository(db_path=self.db_path)

    def teardown_method(self):
        """Cleanup after each test"""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def create_test_template(self, template_id: str, size: str = 'normal') -> Template:
        """Create a test template with configurable size"""
        content_sizes = {
            'small': '{{small_content}}',
            'normal': '# {{title}}\n\n{{description}}\n\n{{content}}\n\n## Details\n{{details}}',
            'large': '# {{title}}\n\n' + '{{description}}\n\n' * 10 + '{{content}}\n\n' + '## Section {{i}}\n{{section_{{i}}}}\n\n' * 20
        }
        
        variables_sizes = {
            'small': ['small_content'],
            'normal': ['title', 'description', 'content', 'details'],
            'large': ['title', 'description', 'content'] + [f'section_{i}' for i in range(20)]
        }
        
        metadata_sizes = {
            'small': {'size': 'small'},
            'normal': {'size': 'normal', 'category': 'test', 'version': '1.0'},
            'large': {
                'size': 'large',
                'category': 'performance_test',
                'version': '1.0',
                'detailed_info': {f'key_{i}': f'value_{i}' for i in range(50)},
                'tags': [f'tag_{i}' for i in range(20)]
            }
        }
        
        return Template(
            id=TemplateId(template_id),
            name=f'Performance Test Template {template_id}',
            description=f'Template for performance testing - {size} size',
            content=content_sizes[size],
            template_type=TemplateType.CUSTOM,
            category=TemplateCategory.GENERAL,
            status=TemplateStatus.ACTIVE,
            priority=TemplatePriority.MEDIUM,
            compatible_agents=['*'],
            file_patterns=['*.md'],
            variables=variables_sizes[size],
            metadata=metadata_sizes[size],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            version=1,
            is_active=True
        )

    def measure_execution_time(self, operation, iterations: int = 1) -> float:
        """Measure execution time of an operation"""
        start_time = time.perf_counter()
        for _ in range(iterations):
            operation()
        end_time = time.perf_counter()
        return (end_time - start_time) / iterations

    def test_template_save_performance(self):
        """Test template save operation performance"""
        # Test single save performance
        template = self.create_test_template('perf-save-001')
        
        def save_operation():
            self.repository.save(template)
        
        avg_time = self.measure_execution_time(save_operation, iterations=10)
        
        # Baseline expectation: Save should complete within 50ms on average
        assert avg_time < 0.05, f"Save operation too slow: {avg_time:.3f}s (expected < 0.05s)"
        
        print(f"✓ Template save performance: {avg_time:.3f}s average")

    def test_template_bulk_save_performance(self):
        """Test bulk template save performance"""
        templates = [self.create_test_template(f'bulk-{i:03d}') for i in range(100)]
        
        def bulk_save_operation():
            for template in templates:
                self.repository.save(template)
        
        total_time = self.measure_execution_time(bulk_save_operation, iterations=1)
        avg_per_template = total_time / len(templates)
        
        # Baseline: Should handle 100 templates in under 5 seconds (50ms per template)
        assert total_time < 5.0, f"Bulk save too slow: {total_time:.3f}s for {len(templates)} templates"
        assert avg_per_template < 0.05, f"Average save time too slow: {avg_per_template:.3f}s per template"
        
        print(f"✓ Bulk save performance: {total_time:.3f}s total, {avg_per_template:.3f}s per template")

    def test_template_retrieval_performance(self):
        """Test template retrieval performance"""
        # Setup: Create and save test templates
        templates = [self.create_test_template(f'retrieve-{i:03d}') for i in range(50)]
        for template in templates:
            self.repository.save(template)
        
        # Test single retrieval
        template_id = TemplateId('retrieve-025')
        
        def retrieve_operation():
            return self.repository.get_by_id(template_id)
        
        avg_time = self.measure_execution_time(retrieve_operation, iterations=20)
        
        # Baseline: Retrieval should be under 10ms
        assert avg_time < 0.01, f"Retrieval too slow: {avg_time:.3f}s (expected < 0.01s)"
        
        print(f"✓ Template retrieval performance: {avg_time:.3f}s average")

    def test_template_list_performance(self):
        """Test template listing performance with various data sizes"""
        # Setup: Create templates of different sizes
        template_counts = [10, 50, 100, 200]
        
        for count in template_counts:
            # Clean repository for each test
            self.teardown_method()
            self.setup_method()
            
            # Create test data
            templates = [self.create_test_template(f'list-{i:03d}') for i in range(count)]
            for template in templates:
                self.repository.save(template)
            
            # Test list performance
            def list_operation():
                return self.repository.list_templates()
            
            avg_time = self.measure_execution_time(list_operation, iterations=5)
            
            # Baseline: List should scale reasonably (under 100ms for 200 templates)
            expected_max_time = 0.1 if count <= 200 else 0.2
            assert avg_time < expected_max_time, f"List operation too slow for {count} templates: {avg_time:.3f}s"
            
            print(f"✓ List performance ({count} templates): {avg_time:.3f}s average")

    def test_template_search_performance(self):
        """Test template search and filtering performance"""
        # Setup: Create diverse templates for filtering
        template_types = ['custom', 'code', 'documentation']
        categories = ['general', 'development']
        
        templates = []
        for i in range(150):
            template = Template(
                id=TemplateId(f'search-{i:03d}'),
                name=f'Search Test Template {i}',
                description=f'Template {i} for search testing',
                content=f'Search content {i}: {{{{content}}}}',
                template_type=TemplateType(template_types[i % len(template_types)]),
                category=TemplateCategory(categories[i % len(categories)]),
                status=TemplateStatus.ACTIVE,
                priority=TemplatePriority.MEDIUM,
                compatible_agents=['search_agent'] if i % 3 == 0 else ['*'],
                file_patterns=[],
                variables=['content'],
                metadata={'search_index': i},
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                version=1,
                is_active=True
            )
            templates.append(template)
            self.repository.save(template)
        
        # Test different filter combinations
        filter_tests = [
            {'template_type': 'custom'},
            {'category': 'development'},
            {'agent_compatible': 'search_agent'},
            {'template_type': 'code', 'category': 'development'},
            {'template_type': 'custom', 'agent_compatible': 'search_agent'}
        ]
        
        for filters in filter_tests:
            def search_operation():
                return self.repository.list_templates(**filters)
            
            avg_time = self.measure_execution_time(search_operation, iterations=10)
            
            # Baseline: Filtered searches should be under 50ms
            assert avg_time < 0.05, f"Search operation too slow with filters {filters}: {avg_time:.3f}s"
            
            print(f"✓ Search performance {filters}: {avg_time:.3f}s average")

    def test_template_usage_tracking_performance(self):
        """Test usage tracking performance"""
        # Setup: Create templates for usage tracking
        templates = [self.create_test_template(f'usage-{i:03d}') for i in range(10)]
        for template in templates:
            self.repository.save(template)
        
        # Test usage save performance
        def usage_save_operation():
            usage = TemplateUsage(
                template_id=TemplateId('usage-001'),
                task_id='perf-task',
                project_id='perf-project',
                agent_name='perf_agent',
                variables_used={'content': 'performance test'},
                output_path='/tmp/perf.md',
                generation_time_ms=100,
                cache_hit=False,
                used_at=datetime.now(timezone.utc)
            )
            return self.repository.save_usage(usage)
        
        avg_time = self.measure_execution_time(usage_save_operation, iterations=20)
        
        # Baseline: Usage tracking should be very fast (under 20ms)
        assert avg_time < 0.02, f"Usage save too slow: {avg_time:.3f}s (expected < 0.02s)"
        
        print(f"✓ Usage tracking performance: {avg_time:.3f}s average")

    def test_analytics_performance(self):
        """Test analytics query performance"""
        # Setup: Create templates and usage data
        templates = [self.create_test_template(f'analytics-{i:03d}') for i in range(20)]
        for template in templates:
            self.repository.save(template)
        
        # Generate usage data
        for i in range(100):
            template_id = TemplateId(f'analytics-{i % 20:03d}')
            usage = TemplateUsage(
                template_id=template_id,
                task_id=f'analytics-task-{i:03d}',
                project_id='analytics-project',
                agent_name='analytics_agent',
                variables_used={'content': f'analytics content {i}'},
                output_path=f'/tmp/analytics-{i}.md',
                generation_time_ms=50 + i,
                cache_hit=i % 3 == 0,
                used_at=datetime.now(timezone.utc)
            )
            self.repository.save_usage(usage)
        
        # Test individual template analytics
        def individual_analytics_operation():
            return self.repository.get_usage_stats(TemplateId('analytics-001'))
        
        avg_time = self.measure_execution_time(individual_analytics_operation, iterations=10)
        
        # Baseline: Individual analytics should be fast (under 30ms)
        assert avg_time < 0.03, f"Individual analytics too slow: {avg_time:.3f}s"
        
        # Test overall analytics
        def overall_analytics_operation():
            return self.repository.get_analytics()
        
        overall_avg_time = self.measure_execution_time(overall_analytics_operation, iterations=5)
        
        # Baseline: Overall analytics should complete within 100ms
        assert overall_avg_time < 0.1, f"Overall analytics too slow: {overall_avg_time:.3f}s"
        
        print(f"✓ Individual analytics performance: {avg_time:.3f}s average")
        print(f"✓ Overall analytics performance: {overall_avg_time:.3f}s average")

    def test_large_template_handling(self):
        """Test performance with large template content"""
        # Create templates of different sizes
        sizes = ['small', 'normal', 'large']
        
        for size in sizes:
            template = self.create_test_template(f'size-test-{size}', size=size)
            
            # Test save performance
            def save_large_operation():
                self.repository.save(template)
            
            save_time = self.measure_execution_time(save_large_operation, iterations=5)
            
            # Test retrieval performance
            def retrieve_large_operation():
                return self.repository.get_by_id(template.id)
            
            retrieve_time = self.measure_execution_time(retrieve_large_operation, iterations=10)
            
            # Baselines vary by size
            max_save_times = {'small': 0.02, 'normal': 0.05, 'large': 0.1}
            max_retrieve_times = {'small': 0.01, 'normal': 0.02, 'large': 0.05}
            
            assert save_time < max_save_times[size], f"Save time for {size} template too slow: {save_time:.3f}s"
            assert retrieve_time < max_retrieve_times[size], f"Retrieve time for {size} template too slow: {retrieve_time:.3f}s"
            
            print(f"✓ {size.title()} template performance - Save: {save_time:.3f}s, Retrieve: {retrieve_time:.3f}s")

    def test_concurrent_access_performance(self):
        """Test performance under simulated concurrent access"""
        # Create base templates
        templates = [self.create_test_template(f'concurrent-{i:03d}') for i in range(10)]
        for template in templates:
            self.repository.save(template)
        
        # Simulate concurrent operations (sequential execution for testing)
        operations = []
        
        # Mix of read/write operations
        for i in range(50):
            if i % 3 == 0:
                # Write operation
                template = self.create_test_template(f'concurrent-write-{i:03d}')
                operations.append(lambda t=template: self.repository.save(t))
            elif i % 3 == 1:
                # Read operation
                template_id = TemplateId(f'concurrent-{i % 10:03d}')
                operations.append(lambda tid=template_id: self.repository.get_by_id(tid))
            else:
                # List operation
                operations.append(lambda: self.repository.list_templates(limit=5))
        
        # Execute operations and measure total time
        def concurrent_simulation():
            for operation in operations:
                operation()
        
        total_time = self.measure_execution_time(concurrent_simulation, iterations=1)
        avg_per_operation = total_time / len(operations)
        
        # Baseline: Should handle mixed operations efficiently
        assert total_time < 5.0, f"Concurrent simulation too slow: {total_time:.3f}s"
        assert avg_per_operation < 0.1, f"Average operation time too slow: {avg_per_operation:.3f}s"
        
        print(f"✓ Concurrent access simulation: {total_time:.3f}s total, {avg_per_operation:.3f}s per operation")

    def test_database_growth_performance(self):
        """Test performance as database grows in size"""
        batch_sizes = [50, 100, 200]
        
        for batch_size in batch_sizes:
            # Add more templates to simulate growth
            templates = [self.create_test_template(f'growth-{batch_size}-{i:03d}') for i in range(batch_size)]
            
            # Measure batch insert time
            def batch_insert():
                for template in templates:
                    self.repository.save(template)
            
            insert_time = self.measure_execution_time(batch_insert, iterations=1)
            
            # Measure query time after growth
            def query_after_growth():
                return self.repository.list_templates()
            
            query_time = self.measure_execution_time(query_after_growth, iterations=5)
            
            # Check total count to verify all inserts
            all_templates, total_count = self.repository.list_templates()
            
            print(f"✓ Database with {total_count} templates - Insert batch: {insert_time:.3f}s, Query: {query_time:.3f}s")
            
            # Performance should degrade gracefully
            max_query_times = {50: 0.05, 100: 0.08, 200: 0.15}
            if batch_size in max_query_times:
                assert query_time < max_query_times[batch_size], f"Query too slow with {total_count} templates: {query_time:.3f}s"