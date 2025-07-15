"""
Integration tests for Template Repository SQLite migration
Tests cross-repository data consistency and end-to-end workflows
"""

import pytest
import tempfile
import os
from datetime import datetime, timezone
from typing import Dict, Any

from fastmcp.task_management.infrastructure.repositories.sqlite.template_repository import SQLiteTemplateRepository
from fastmcp.task_management.domain.entities.template import Template, TemplateUsage
from fastmcp.task_management.domain.value_objects.template_id import TemplateId
from fastmcp.task_management.domain.enums.template_enums import (
    TemplateType, TemplateCategory, TemplateStatus, TemplatePriority
)

pytestmark = pytest.mark.unit  # Use unit marker to avoid global DB setup issues


class TestTemplateRepositoryIntegration:
    """Integration test suite for SQLite Template Repository"""

    def setup_method(self):
        """Setup integration test fixtures"""
        # Create temporary database for integration testing
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        self.db_path = self.temp_db.name
        
        # Initialize repository
        self.repository = SQLiteTemplateRepository(db_path=self.db_path)

    def teardown_method(self):
        """Cleanup after each test"""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_end_to_end_template_lifecycle(self):
        """Test complete template lifecycle from creation to deletion"""
        # Phase 1: Create template
        template = Template(
            id=TemplateId('e2e-template-001'),
            name='End-to-End Test Template',
            description='A comprehensive template for integration testing',
            content='# {{project_name}}\n\n{{description}}\n\n## Tasks\n{% for task in tasks %}\n- [ ] {{task}}\n{% endfor %}',
            template_type=TemplateType.CUSTOM,
            category=TemplateCategory.GENERAL,
            status=TemplateStatus.ACTIVE,
            priority=TemplatePriority.HIGH,
            compatible_agents=['task_agent', 'planning_agent'],
            file_patterns=['*.md', '*.txt'],
            variables=['project_name', 'description', 'tasks'],
            metadata={
                'author': 'integration_test',
                'version': '1.0.0',
                'tags': ['testing', 'e2e', 'integration'],
                'complexity': 'medium'
            },
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            version=1,
            is_active=True
        )
        
        # Save template
        saved_template = self.repository.save(template)
        assert saved_template.id == template.id
        assert saved_template.name == template.name
        
        # Phase 2: Retrieve and validate
        retrieved_template = self.repository.get_by_id(template.id)
        assert retrieved_template is not None
        assert retrieved_template.content == template.content
        assert retrieved_template.variables == template.variables
        assert retrieved_template.metadata == template.metadata
        assert retrieved_template.compatible_agents == template.compatible_agents
        
        # Phase 3: Update template
        retrieved_template.description = 'Updated description for integration test'
        retrieved_template.version = 2
        retrieved_template.metadata['last_updated'] = 'integration_test'
        
        updated_template = self.repository.save(retrieved_template)
        assert updated_template.version == 2
        assert 'Updated description' in updated_template.description
        assert updated_template.metadata['last_updated'] == 'integration_test'
        
        # Phase 4: Usage tracking
        usage_records = []
        for i in range(3):
            usage = TemplateUsage(
                template_id=template.id,
                task_id=f'task-{i:03d}',
                project_id='integration-project',
                agent_name='test_agent',
                variables_used={
                    'project_name': f'Project {i}',
                    'description': f'Description for project {i}',
                    'tasks': [f'Task {j}' for j in range(3)]
                },
                output_path=f'/tmp/project-{i}.md',
                generation_time_ms=100 + i * 25,
                cache_hit=i % 2 == 0,
                used_at=datetime.now(timezone.utc)
            )
            usage_records.append(usage)
            
            # Save usage
            result = self.repository.save_usage(usage)
            assert result is True
        
        # Phase 5: Analytics validation
        stats = self.repository.get_usage_stats(template.id)
        assert stats['usage_count'] == 3
        assert stats['avg_generation_time'] == 125.0  # (100+125+150)/3
        assert abs(stats['cache_hit_rate'] - 66.67) < 0.01  # 2 out of 3 cache hits (allow for floating point precision)
        
        # Phase 6: List and filter validation
        templates, count = self.repository.list_templates()
        assert count == 1
        assert len(templates) == 1
        assert templates[0].id == template.id
        
        # Filter by type
        typed_templates, typed_count = self.repository.list_templates(
            template_type='custom'
        )
        assert typed_count == 1
        assert len(typed_templates) == 1
        
        # Filter by agent compatibility
        agent_templates, agent_count = self.repository.list_templates(
            agent_compatible='task_agent'
        )
        assert len(agent_templates) == 1
        assert agent_templates[0].id == template.id
        
        # Phase 7: Cleanup - delete template and verify cascade
        delete_result = self.repository.delete(template.id)
        assert delete_result is True
        
        # Verify template is deleted
        deleted_template = self.repository.get_by_id(template.id)
        assert deleted_template is None
        
        # Verify usage records are also deleted
        stats_after_delete = self.repository.get_usage_stats(template.id)
        assert stats_after_delete['usage_count'] == 0

    def test_multiple_templates_data_consistency(self):
        """Test data consistency across multiple templates"""
        # Create multiple templates with different characteristics
        templates = []
        for i in range(5):
            template = Template(
                id=TemplateId(f'consistency-template-{i:03d}'),
                name=f'Consistency Test Template {i}',
                description=f'Template {i} for data consistency testing',
                content=f'Template {i}: {{{{content}}}}',
                template_type=TemplateType.CODE if i % 2 == 0 else TemplateType.CUSTOM,
                category=TemplateCategory.DEVELOPMENT if i % 2 == 0 else TemplateCategory.GENERAL,
                status=TemplateStatus.ACTIVE if i % 3 != 0 else TemplateStatus.INACTIVE,
                priority=TemplatePriority.HIGH if i < 2 else TemplatePriority.MEDIUM,
                compatible_agents=['*'] if i == 0 else [f'agent_{i}', f'agent_{i+1}'],
                file_patterns=[f'*.{ext}' for ext in ['py', 'js', 'md'][i % 3:]],
                variables=[f'var_{j}' for j in range(i + 1)],
                metadata={'template_index': i, 'batch': 'consistency_test'},
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                version=1,
                is_active=i % 4 != 0  # Some inactive
            )
            templates.append(template)
            
            # Save template
            saved = self.repository.save(template)
            assert saved.id == template.id
        
        # Test data consistency queries
        
        # 1. Count validation
        all_templates, total_count = self.repository.list_templates()
        assert total_count == 5
        # Note: The repository returns all templates regardless of is_active status in list_templates()
        # The is_active filter needs to be passed explicitly as a parameter
        assert len(all_templates) == 5  # All templates are returned by default
        
        # 2. Type filtering consistency
        code_templates, code_count = self.repository.list_templates(template_type='code')
        expected_code_count = len([t for t in templates if t.template_type == TemplateType.CODE])
        assert code_count == expected_code_count
        
        # 3. Category filtering consistency
        dev_templates, dev_count = self.repository.list_templates(category='development')
        expected_dev_count = len([t for t in templates if t.category == TemplateCategory.DEVELOPMENT])
        assert dev_count == expected_dev_count
        
        # 4. Status filtering consistency
        active_templates, active_count = self.repository.list_templates(is_active=True)
        expected_active_count = len([t for t in templates if t.is_active])
        assert len(active_templates) == expected_active_count
        
        # 5. Agent compatibility consistency
        universal_templates, universal_count = self.repository.list_templates(
            agent_compatible='any_agent'
        )
        # Should return only template 0 (has '*' in compatible_agents)
        assert len(universal_templates) == 1
        assert universal_templates[0].id.value == 'consistency-template-000'
        
        # 6. Individual retrieval consistency
        for template in templates:
            retrieved = self.repository.get_by_id(template.id)
            assert retrieved is not None
            assert retrieved.name == template.name
            assert retrieved.metadata['template_index'] == template.metadata['template_index']
            assert retrieved.compatible_agents == template.compatible_agents
            assert retrieved.file_patterns == template.file_patterns
            assert retrieved.variables == template.variables

    def test_template_usage_analytics_integration(self):
        """Test comprehensive usage analytics across multiple templates"""
        # Create templates for analytics testing
        template1 = Template(
            id=TemplateId('analytics-template-1'),
            name='Popular Template',
            description='A frequently used template',
            content='{{popular_content}}',
            template_type=TemplateType.CUSTOM,
            category=TemplateCategory.GENERAL,
            status=TemplateStatus.ACTIVE,
            priority=TemplatePriority.HIGH,
            compatible_agents=['*'],
            file_patterns=[],
            variables=['popular_content'],
            metadata={'purpose': 'analytics_testing'},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            version=1,
            is_active=True
        )
        
        template2 = Template(
            id=TemplateId('analytics-template-2'),
            name='Rare Template',
            description='A rarely used template',
            content='{{rare_content}}',
            template_type=TemplateType.CODE,
            category=TemplateCategory.DEVELOPMENT,
            status=TemplateStatus.ACTIVE,
            priority=TemplatePriority.LOW,
            compatible_agents=['dev_agent'],
            file_patterns=['*.py'],
            variables=['rare_content'],
            metadata={'purpose': 'analytics_testing'},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            version=1,
            is_active=True
        )
        
        # Save templates
        self.repository.save(template1)
        self.repository.save(template2)
        
        # Generate usage data
        # Template 1: 10 uses with varying performance
        for i in range(10):
            usage = TemplateUsage(
                template_id=template1.id,
                task_id=f'popular-task-{i:03d}',
                project_id='analytics-project',
                agent_name='popular_agent',
                variables_used={'popular_content': f'Content {i}'},
                output_path=f'/tmp/popular-{i}.md',
                generation_time_ms=50 + i * 10,  # 50 to 140ms
                cache_hit=i % 3 == 0,  # 4 cache hits out of 10
                used_at=datetime.now(timezone.utc)
            )
            self.repository.save_usage(usage)
        
        # Template 2: 2 uses
        for i in range(2):
            usage = TemplateUsage(
                template_id=template2.id,
                task_id=f'rare-task-{i:03d}',
                project_id='analytics-project',
                agent_name='dev_agent',
                variables_used={'rare_content': f'Rare content {i}'},
                output_path=f'/tmp/rare-{i}.py',
                generation_time_ms=200 + i * 50,  # 200 and 250ms
                cache_hit=True,  # Both cache hits
                used_at=datetime.now(timezone.utc)
            )
            self.repository.save_usage(usage)
        
        # Test individual template analytics
        stats1 = self.repository.get_usage_stats(template1.id)
        assert stats1['usage_count'] == 10
        assert stats1['avg_generation_time'] == 95.0  # (50+60+...+140)/10
        assert stats1['cache_hit_rate'] == 40.0  # 4 out of 10
        
        stats2 = self.repository.get_usage_stats(template2.id)
        assert stats2['usage_count'] == 2
        assert stats2['avg_generation_time'] == 225.0  # (200+250)/2
        assert stats2['cache_hit_rate'] == 100.0  # 2 out of 2
        
        # Test overall analytics
        overall_analytics = self.repository.get_analytics()
        assert overall_analytics['total_templates'] == 2
        assert overall_analytics['active_templates'] == 2
        assert overall_analytics['total_usage'] == 12
        
        # Verify most used templates ranking
        most_used = overall_analytics['most_used_templates']
        assert len(most_used) == 2
        assert most_used[0]['template_id'] == template1.id.value
        assert most_used[0]['usage_count'] == 10
        assert most_used[1]['template_id'] == template2.id.value
        assert most_used[1]['usage_count'] == 2

    def test_database_persistence_and_recovery(self):
        """Test database persistence across repository instances"""
        # Phase 1: Create and save data with first repository instance
        template = Template(
            id=TemplateId('persistence-template'),
            name='Persistence Test Template',
            description='Testing database persistence',
            content='{{persistent_content}}',
            template_type=TemplateType.DOCUMENTATION,
            category=TemplateCategory.GENERAL,
            status=TemplateStatus.ACTIVE,
            priority=TemplatePriority.MEDIUM,
            compatible_agents=['persistence_agent'],
            file_patterns=['*.md'],
            variables=['persistent_content'],
            metadata={'test_type': 'persistence'},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            version=1,
            is_active=True
        )
        
        # Save with first repository instance
        self.repository.save(template)
        
        # Add usage record
        usage = TemplateUsage(
            template_id=template.id,
            task_id='persistence-task',
            project_id='persistence-project',
            agent_name='persistence_agent',
            variables_used={'persistent_content': 'Persistent data'},
            output_path='/tmp/persistence.md',
            generation_time_ms=100,
            cache_hit=False,
            used_at=datetime.now(timezone.utc)
        )
        self.repository.save_usage(usage)
        
        # Close current repository (simulate application restart)
        del self.repository
        
        # Phase 2: Create new repository instance and verify data persistence
        new_repository = SQLiteTemplateRepository(db_path=self.db_path)
        
        # Verify template persistence
        retrieved_template = new_repository.get_by_id(template.id)
        assert retrieved_template is not None
        assert retrieved_template.name == template.name
        assert retrieved_template.content == template.content
        assert retrieved_template.metadata == template.metadata
        assert retrieved_template.compatible_agents == template.compatible_agents
        
        # Verify usage persistence
        stats = new_repository.get_usage_stats(template.id)
        assert stats['usage_count'] == 1
        assert stats['avg_generation_time'] == 100.0
        
        # Verify list operations work
        templates, count = new_repository.list_templates()
        assert count == 1
        assert len(templates) == 1
        assert templates[0].id == template.id
        
        # Phase 3: Verify operations work with recovered data
        # Update the template
        retrieved_template.version = 2
        retrieved_template.description = 'Updated after persistence test'
        
        updated = new_repository.save(retrieved_template)
        assert updated.version == 2
        assert 'Updated after persistence' in updated.description
        
        # Add more usage
        new_usage = TemplateUsage(
            template_id=template.id,
            task_id='persistence-task-2',
            project_id='persistence-project',
            agent_name='persistence_agent',
            variables_used={'persistent_content': 'More persistent data'},
            output_path='/tmp/persistence-2.md',
            generation_time_ms=150,
            cache_hit=True,
            used_at=datetime.now(timezone.utc)
        )
        new_repository.save_usage(new_usage)
        
        # Verify updated analytics
        updated_stats = new_repository.get_usage_stats(template.id)
        assert updated_stats['usage_count'] == 2
        assert updated_stats['avg_generation_time'] == 125.0  # (100+150)/2
        assert updated_stats['cache_hit_rate'] == 50.0  # 1 out of 2
        
        # Store reference to new repository for cleanup
        self.repository = new_repository

    def test_concurrent_operations_simulation(self):
        """Simulate concurrent operations to test data integrity"""
        # Create base template
        base_template = Template(
            id=TemplateId('concurrent-base'),
            name='Concurrent Operations Base',
            description='Base template for concurrency testing',
            content='{{base_content}}',
            template_type=TemplateType.CUSTOM,
            category=TemplateCategory.GENERAL,
            status=TemplateStatus.ACTIVE,
            priority=TemplatePriority.MEDIUM,
            compatible_agents=['*'],
            file_patterns=[],
            variables=['base_content'],
            metadata={'test': 'concurrency'},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            version=1,
            is_active=True
        )
        
        self.repository.save(base_template)
        
        # Simulate concurrent reads and writes
        # (In a real concurrent environment, these would be separate threads/processes)
        
        # Concurrent template saves
        for i in range(5):
            template = Template(
                id=TemplateId(f'concurrent-{i:03d}'),
                name=f'Concurrent Template {i}',
                description=f'Template {i} from concurrent operation',
                content=f'Concurrent content {i}: {{{{content}}}}',
                template_type=TemplateType.CUSTOM,
                category=TemplateCategory.GENERAL,
                status=TemplateStatus.ACTIVE,
                priority=TemplatePriority.MEDIUM,
                compatible_agents=['*'],
                file_patterns=[],
                variables=['content'],
                metadata={'concurrent_id': i},
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                version=1,
                is_active=True
            )
            
            saved = self.repository.save(template)
            assert saved.id == template.id
            
            # Immediate read-back verification
            retrieved = self.repository.get_by_id(template.id)
            assert retrieved is not None
            assert retrieved.metadata['concurrent_id'] == i
        
        # Concurrent usage saves
        for i in range(10):
            template_id = TemplateId(f'concurrent-{i % 5:03d}')  # Use existing templates
            usage = TemplateUsage(
                template_id=template_id,
                task_id=f'concurrent-usage-{i:03d}',
                project_id='concurrent-project',
                agent_name='concurrent_agent',
                variables_used={'content': f'Concurrent usage {i}'},
                output_path=f'/tmp/concurrent-{i}.md',
                generation_time_ms=50 + i * 5,
                cache_hit=i % 2 == 0,
                used_at=datetime.now(timezone.utc)
            )
            
            result = self.repository.save_usage(usage)
            assert result is True
        
        # Verify data integrity after concurrent operations
        all_templates, total_count = self.repository.list_templates()
        assert total_count == 6  # 1 base + 5 concurrent
        assert len(all_templates) == 6
        
        # Verify each template can be retrieved correctly
        for i in range(5):
            template_id = TemplateId(f'concurrent-{i:03d}')
            retrieved = self.repository.get_by_id(template_id)
            assert retrieved is not None
            assert retrieved.metadata['concurrent_id'] == i
            
            # Check usage stats
            stats = self.repository.get_usage_stats(template_id)
            assert stats['usage_count'] == 2  # Each template used twice (i and i+5)
        
        # Verify overall analytics consistency
        analytics = self.repository.get_analytics()
        assert analytics['total_templates'] == 6
        assert analytics['active_templates'] == 6
        assert analytics['total_usage'] == 10

    def test_error_recovery_and_rollback(self):
        """Test error handling and data consistency during failures"""
        # Create a valid template
        valid_template = Template(
            id=TemplateId('error-recovery-template'),
            name='Error Recovery Template',
            description='Template for testing error recovery',
            content='{{recovery_content}}',
            template_type=TemplateType.CUSTOM,
            category=TemplateCategory.GENERAL,
            status=TemplateStatus.ACTIVE,
            priority=TemplatePriority.MEDIUM,
            compatible_agents=['*'],
            file_patterns=[],
            variables=['recovery_content'],
            metadata={'test': 'error_recovery'},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            version=1,
            is_active=True
        )
        
        # Save valid template
        saved = self.repository.save(valid_template)
        assert saved.id == valid_template.id
        
        # Verify template exists
        retrieved = self.repository.get_by_id(valid_template.id)
        assert retrieved is not None
        
        # Test database error scenarios by manipulating the database file
        # Close current connection by creating a new repository
        original_db_path = self.db_path
        
        # Create a corrupted database path (directory instead of file)
        corrupted_db_path = self.db_path + "_corrupted_dir"
        os.makedirs(corrupted_db_path, exist_ok=True)
        
        try:
            # Attempt to create repository with invalid path (should handle gracefully)
            with pytest.raises(Exception):
                corrupted_repo = SQLiteTemplateRepository(db_path=corrupted_db_path)
        finally:
            # Clean up corrupted path
            if os.path.exists(corrupted_db_path):
                os.rmdir(corrupted_db_path)
        
        # Verify original repository still works after error
        post_error_retrieved = self.repository.get_by_id(valid_template.id)
        assert post_error_retrieved is not None
        assert post_error_retrieved.name == valid_template.name
        
        # Test that data integrity is maintained
        templates, count = self.repository.list_templates()
        assert count == 1
        assert len(templates) == 1
        assert templates[0].id == valid_template.id