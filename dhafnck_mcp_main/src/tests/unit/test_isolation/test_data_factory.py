"""Test Data Factory - TDD Phase 1
Tests for test data factory consistency and generation.
Written BEFORE implementation following TDD methodology.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Any, Dict, List, Optional
import uuid
from datetime import datetime, timedelta

# These imports will fail initially - that's expected in TDD
from fastmcp.task_management.infrastructure.database.test_helpers import (
    TestDataFactory,
    generate_task_data,
    generate_project_data,
    generate_agent_data,
    generate_context_data,
    generate_subtask_data,
    generate_bulk_data,
    DataGenerator,
    ensure_data_consistency,
    validate_generated_data
)


class TestDataFactory:
    """Test suite for TestDataFactory"""
    
    def test_factory_initialization(self):
        """Test TestDataFactory initialization"""
        # Act
        factory = TestDataFactory()
        
        # Assert
        assert factory is not None
        assert hasattr(factory, 'generate_task')
        assert hasattr(factory, 'generate_project')
        assert hasattr(factory, 'generate_agent')
        assert hasattr(factory, 'generate_context')
        assert hasattr(factory, 'generate_bulk')
    
    def test_factory_generates_unique_ids(self):
        """Test that factory generates unique IDs"""
        # Arrange
        factory = TestDataFactory()
        
        # Act
        task1 = factory.generate_task()
        task2 = factory.generate_task()
        task3 = factory.generate_task()
        
        # Assert
        assert task1['id'] != task2['id']
        assert task2['id'] != task3['id']
        assert task1['id'] != task3['id']
    
    def test_factory_respects_seed(self):
        """Test that factory respects seed for reproducibility"""
        # Arrange
        factory1 = TestDataFactory(seed=42)
        factory2 = TestDataFactory(seed=42)
        
        # Act
        task1 = factory1.generate_task()
        task2 = factory2.generate_task()
        
        # Assert
        assert task1 == task2  # Same seed should produce same data
    
    def test_factory_generates_consistent_types(self):
        """Test that factory generates consistent data types"""
        # Arrange
        factory = TestDataFactory()
        
        # Act
        task = factory.generate_task()
        
        # Assert
        assert isinstance(task['id'], str)
        assert isinstance(task['title'], str)
        assert isinstance(task['status'], str)
        assert isinstance(task['priority'], str)
        assert isinstance(task['created_at'], (str, datetime))
        assert isinstance(task.get('assignees', []), list)


class TestTaskDataGeneration:
    """Test suite for task data generation"""
    
    def test_generate_task_data_with_defaults(self):
        """Test generating task data with default values"""
        # Act
        task = generate_task_data()
        
        # Assert
        assert task is not None
        assert 'id' in task
        assert 'title' in task
        assert task['status'] in ['todo', 'in_progress', 'done', 'blocked']
        assert task['priority'] in ['low', 'medium', 'high', 'urgent', 'critical']
    
    def test_generate_task_data_with_overrides(self):
        """Test generating task data with custom overrides"""
        # Arrange
        overrides = {
            'title': 'Custom Task Title',
            'status': 'in_progress',
            'priority': 'high',
            'description': 'Custom description'
        }
        
        # Act
        task = generate_task_data(**overrides)
        
        # Assert
        assert task['title'] == 'Custom Task Title'
        assert task['status'] == 'in_progress'
        assert task['priority'] == 'high'
        assert task['description'] == 'Custom description'
    
    def test_generate_task_data_with_dependencies(self):
        """Test generating task data with dependencies"""
        # Arrange
        dep_ids = ['dep-1', 'dep-2', 'dep-3']
        
        # Act
        task = generate_task_data(dependencies=dep_ids)
        
        # Assert
        assert task['dependencies'] == dep_ids
        assert len(task['dependencies']) == 3
    
    def test_generate_task_data_with_assignees(self):
        """Test generating task data with assignees"""
        # Arrange
        assignees = ['@agent1', '@agent2']
        
        # Act
        task = generate_task_data(assignees=assignees)
        
        # Assert
        assert task['assignees'] == assignees
        assert all(a.startswith('@') for a in task['assignees'])
    
    def test_generate_task_data_with_dates(self):
        """Test generating task data with date fields"""
        # Act
        task = generate_task_data()
        
        # Assert
        assert 'created_at' in task
        assert 'updated_at' in task
        # If due_date is present, it should be in the future
        if 'due_date' in task:
            if isinstance(task['due_date'], str):
                due = datetime.fromisoformat(task['due_date'].replace('Z', '+00:00'))
            else:
                due = task['due_date']
            assert due > datetime.now()


class TestProjectDataGeneration:
    """Test suite for project data generation"""
    
    def test_generate_project_data(self):
        """Test generating project data"""
        # Act
        project = generate_project_data()
        
        # Assert
        assert project is not None
        assert 'id' in project
        assert 'name' in project
        assert 'description' in project
        assert 'created_at' in project
    
    def test_generate_project_data_with_custom_name(self):
        """Test generating project data with custom name"""
        # Act
        project = generate_project_data(name='Custom Project')
        
        # Assert
        assert project['name'] == 'Custom Project'
    
    def test_generate_project_data_with_metadata(self):
        """Test generating project data with metadata"""
        # Arrange
        metadata = {
            'team': 'Engineering',
            'budget': 100000,
            'deadline': '2024-12-31'
        }
        
        # Act
        project = generate_project_data(metadata=metadata)
        
        # Assert
        assert project['metadata'] == metadata


class TestAgentDataGeneration:
    """Test suite for agent data generation"""
    
    def test_generate_agent_data(self):
        """Test generating agent data"""
        # Act
        agent = generate_agent_data()
        
        # Assert
        assert agent is not None
        assert 'id' in agent
        assert 'name' in agent
        assert agent['name'].startswith('@')
        assert 'capabilities' in agent
        assert isinstance(agent['capabilities'], list)
    
    def test_generate_agent_data_with_project(self):
        """Test generating agent data with project assignment"""
        # Act
        agent = generate_agent_data(project_id='proj-123')
        
        # Assert
        assert agent['project_id'] == 'proj-123'
    
    def test_generate_agent_data_with_capabilities(self):
        """Test generating agent data with specific capabilities"""
        # Arrange
        capabilities = ['coding', 'testing', 'debugging']
        
        # Act
        agent = generate_agent_data(capabilities=capabilities)
        
        # Assert
        assert agent['capabilities'] == capabilities


class TestContextDataGeneration:
    """Test suite for context data generation"""
    
    def test_generate_context_data(self):
        """Test generating context data"""
        # Act
        context = generate_context_data()
        
        # Assert
        assert context is not None
        assert 'level' in context
        assert context['level'] in ['global', 'project', 'branch', 'task']
        assert 'context_id' in context
        assert 'data' in context
        assert isinstance(context['data'], dict)
    
    def test_generate_context_data_for_task_level(self):
        """Test generating context data for task level"""
        # Act
        context = generate_context_data(level='task', context_id='task-123')
        
        # Assert
        assert context['level'] == 'task'
        assert context['context_id'] == 'task-123'
    
    def test_generate_context_data_with_custom_data(self):
        """Test generating context data with custom data"""
        # Arrange
        custom_data = {
            'discoveries': ['Found API issue'],
            'decisions': ['Use REST instead of GraphQL'],
            'next_steps': ['Implement authentication']
        }
        
        # Act
        context = generate_context_data(data=custom_data)
        
        # Assert
        assert context['data'] == custom_data


class TestBulkDataGeneration:
    """Test suite for bulk data generation"""
    
    def test_generate_bulk_tasks(self):
        """Test generating multiple tasks in bulk"""
        # Act
        tasks = generate_bulk_data('task', count=5)
        
        # Assert
        assert len(tasks) == 5
        assert all('id' in t for t in tasks)
        # All IDs should be unique
        ids = [t['id'] for t in tasks]
        assert len(ids) == len(set(ids))
    
    def test_generate_bulk_with_pattern(self):
        """Test generating bulk data with naming pattern"""
        # Act
        tasks = generate_bulk_data('task', count=3, 
                                  title_pattern='Task #{index}')
        
        # Assert
        assert tasks[0]['title'] == 'Task #1'
        assert tasks[1]['title'] == 'Task #2'
        assert tasks[2]['title'] == 'Task #3'
    
    def test_generate_bulk_with_relationships(self):
        """Test generating bulk data with relationships"""
        # Act
        tasks = generate_bulk_data('task', count=3, 
                                  create_dependencies=True)
        
        # Assert
        # First task should have no dependencies
        assert len(tasks[0].get('dependencies', [])) == 0
        # Subsequent tasks might depend on previous ones
        if len(tasks) > 1:
            for task in tasks[1:]:
                if 'dependencies' in task:
                    # Dependencies should reference earlier tasks
                    for dep_id in task['dependencies']:
                        assert any(t['id'] == dep_id for t in tasks)


class TestDataConsistency:
    """Test suite for data consistency validation"""
    
    def test_ensure_data_consistency(self):
        """Test ensuring data consistency across generated data"""
        # Arrange
        project = generate_project_data()
        tasks = [
            generate_task_data(project_id=project['id']),
            generate_task_data(project_id=project['id'])
        ]
        
        # Act
        is_consistent = ensure_data_consistency(project, tasks)
        
        # Assert
        assert is_consistent is True
        assert all(t['project_id'] == project['id'] for t in tasks)
    
    def test_validate_generated_task_data(self):
        """Test validating generated task data"""
        # Arrange
        task = generate_task_data()
        
        # Act
        is_valid = validate_generated_data('task', task)
        
        # Assert
        assert is_valid is True
    
    def test_validate_detects_invalid_data(self):
        """Test that validation detects invalid data"""
        # Arrange
        invalid_task = {
            'id': 'task-123',
            # Missing required 'title' field
            'status': 'invalid_status'  # Invalid status value
        }
        
        # Act
        is_valid = validate_generated_data('task', invalid_task)
        
        # Assert
        assert is_valid is False


class TestDataGenerator:
    """Test suite for DataGenerator class"""
    
    def test_data_generator_initialization(self):
        """Test DataGenerator initialization"""
        # Act
        generator = DataGenerator()
        
        # Assert
        assert generator is not None
        assert hasattr(generator, 'generate')
        assert hasattr(generator, 'reset')
        assert hasattr(generator, 'set_seed')
    
    def test_data_generator_patterns(self):
        """Test DataGenerator with different patterns"""
        # Arrange
        generator = DataGenerator()
        
        # Act
        sequential = generator.generate('task', pattern='sequential', count=3)
        random = generator.generate('task', pattern='random', count=3)
        realistic = generator.generate('task', pattern='realistic', count=3)
        
        # Assert
        assert len(sequential) == 3
        assert len(random) == 3
        assert len(realistic) == 3
        
        # Sequential should have ordered titles
        if 'title' in sequential[0]:
            titles = [t['title'] for t in sequential]
            assert titles == sorted(titles)
    
    def test_data_generator_reset(self):
        """Test resetting DataGenerator state"""
        # Arrange
        generator = DataGenerator()
        task1 = generator.generate('task')
        
        # Act
        generator.reset()
        task2 = generator.generate('task')
        
        # Assert
        # After reset, should generate fresh data
        assert task1['id'] != task2['id']


class TestSubtaskDataGeneration:
    """Test suite for subtask data generation"""
    
    def test_generate_subtask_data(self):
        """Test generating subtask data"""
        # Arrange
        parent_task_id = 'parent-123'
        
        # Act
        subtask = generate_subtask_data(task_id=parent_task_id)
        
        # Assert
        assert subtask is not None
        assert 'id' in subtask
        assert 'title' in subtask
        assert subtask['task_id'] == parent_task_id
        assert 'status' in subtask
        assert 'progress' in subtask
        assert 0 <= subtask['progress'] <= 100
    
    def test_generate_subtask_hierarchy(self):
        """Test generating subtask hierarchy"""
        # Arrange
        factory = TestDataFactory()
        
        # Act
        parent = factory.generate_task()
        subtasks = [
            factory.generate_subtask(parent['id']) 
            for _ in range(3)
        ]
        
        # Assert
        assert len(subtasks) == 3
        assert all(s['task_id'] == parent['id'] for s in subtasks)
        # Subtasks should have unique IDs
        ids = [s['id'] for s in subtasks]
        assert len(ids) == len(set(ids))


class TestAdvancedDataGeneration:
    """Test advanced data generation scenarios"""
    
    def test_generate_realistic_project_scenario(self):
        """Test generating a realistic project scenario"""
        # Arrange
        factory = TestDataFactory()
        
        # Act
        # Generate a complete project scenario
        project = factory.generate_project(name='E-commerce Platform')
        agents = [
            factory.generate_agent(name='@backend_dev', project_id=project['id']),
            factory.generate_agent(name='@frontend_dev', project_id=project['id']),
            factory.generate_agent(name='@qa_engineer', project_id=project['id'])
        ]
        tasks = [
            factory.generate_task(
                title='Setup Database',
                project_id=project['id'],
                assignees=[agents[0]['id']]
            ),
            factory.generate_task(
                title='Create API Endpoints',
                project_id=project['id'],
                assignees=[agents[0]['id']],
                dependencies=[tasks[0]['id']] if tasks else []
            ),
            factory.generate_task(
                title='Build UI Components',
                project_id=project['id'],
                assignees=[agents[1]['id']]
            ),
            factory.generate_task(
                title='Write Tests',
                project_id=project['id'],
                assignees=[agents[2]['id']],
                dependencies=[t['id'] for t in tasks[:2]] if len(tasks) >= 2 else []
            )
        ]
        
        # Assert
        assert project['name'] == 'E-commerce Platform'
        assert len(agents) == 3
        assert len(tasks) == 4
        # Verify relationships
        assert tasks[1]['dependencies'] == [tasks[0]['id']]
        assert all(t['project_id'] == project['id'] for t in tasks)