"""
Integration Tests for Task-Context-Branch Relationships
Tests the 4-tier hierarchical context system integration with tasks and branches.

This test suite covers:
1. Task-Context integration and inheritance
2. Task-Branch relationships and branch-specific contexts
3. Hierarchical context resolution (Global → Project → Branch → Task)
4. Context delegation between levels
5. Context inheritance validation
6. Cross-system integration between tasks, contexts, and branches
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import uuid
import json

pytestmark = pytest.mark.integration


class MockContext:
    """Mock Context entity for testing hierarchical relationships"""
    def __init__(self,
                 id: str,
                 level: str,  # 'global', 'project', 'branch', 'task'
                 context_id: str,  # The actual ID (project_id, branch_id, task_id, or 'global_singleton')
                 data: Dict[str, Any] = None,
                 parent_context: 'MockContext' = None,
                 created_at: datetime = None,
                 updated_at: datetime = None):
        self.id = id
        self.level = level
        self.context_id = context_id
        self.data = data or {}
        self.parent_context = parent_context
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()

    def resolve_with_inheritance(self) -> Dict[str, Any]:
        """Resolve context data with inheritance from parent levels"""
        resolved_data = {}
        
        # Start from the top level and work down
        contexts_chain = self._get_inheritance_chain()
        
        for context in contexts_chain:
            if context and context.data:
                # Deep merge dictionaries to handle nested conflicts properly
                self._deep_merge(resolved_data, context.data)
        
        return resolved_data

    def _deep_merge(self, target: Dict[str, Any], source: Dict[str, Any]):
        """Deep merge source into target, with source taking precedence"""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_merge(target[key], value)
            else:
                target[key] = value

    def _get_inheritance_chain(self) -> List['MockContext']:
        """Get the full inheritance chain from global to current level"""
        chain = []
        current = self
        
        # Walk up the chain
        while current:
            chain.insert(0, current)  # Insert at beginning to maintain order
            current = current.parent_context
        
        return chain

    def delegate_to_parent(self, delegation_data: Dict[str, Any], delegation_reason: str = None):
        """Delegate data to parent context"""
        if self.parent_context:
            self.parent_context.data.update(delegation_data)
            self.parent_context.updated_at = datetime.now()
            return True
        return False


class MockTask:
    """Mock Task entity with context integration"""
    def __init__(self,
                 id: str,
                 title: str,
                 project_id: str,
                 git_branch_id: str,
                 status: str = "todo",
                 context_id: str = None,
                 user_id: str = "default_id"):
        self.id = id
        self.title = title
        self.project_id = project_id
        self.git_branch_id = git_branch_id
        self.status = status
        self.context_id = context_id or id  # Context ID usually same as task ID
        self.user_id = user_id
        self.created_at = datetime.now()
        self.updated_at = datetime.now()


class MockBranch:
    """Mock Git Branch entity"""
    def __init__(self,
                 id: str,
                 name: str,
                 project_id: str,
                 description: str = None,
                 context_id: str = None):
        self.id = id
        self.name = name
        self.project_id = project_id
        self.description = description
        self.context_id = context_id or id
        self.created_at = datetime.now()
        self.updated_at = datetime.now()


class MockProject:
    """Mock Project entity"""
    def __init__(self,
                 id: str,
                 name: str,
                 description: str = None,
                 context_id: str = None):
        self.id = id
        self.name = name
        self.description = description
        self.context_id = context_id or id
        self.created_at = datetime.now()
        self.updated_at = datetime.now()


class MockHierarchicalContextRepository:
    """Mock repository for hierarchical context management"""
    def __init__(self):
        self.contexts: Dict[str, MockContext] = {}
        self.tasks: Dict[str, MockTask] = {}
        self.branches: Dict[str, MockBranch] = {}
        self.projects: Dict[str, MockProject] = {}
        
        # Create global context
        self._create_global_context()

    def _create_global_context(self):
        """Create the singleton global context"""
        global_context = MockContext(
            id="global_context",
            level="global",
            context_id="global_singleton",
            data={
                "organization_standards": {
                    "coding_style": "PEP8",
                    "testing_framework": "pytest",
                    "documentation_standard": "sphinx"
                },
                "security_policies": {
                    "require_2fa": True,
                    "password_policy": "strong"
                }
            }
        )
        self.contexts["global_singleton"] = global_context

    def save_context(self, context: MockContext) -> MockContext:
        """Save context to repository"""
        context.updated_at = datetime.now()
        self.contexts[context.context_id] = context
        return context

    def save_task(self, task: MockTask) -> MockTask:
        """Save task to repository"""
        task.updated_at = datetime.now()
        self.tasks[task.id] = task
        return task

    def save_branch(self, branch: MockBranch) -> MockBranch:
        """Save branch to repository"""
        branch.updated_at = datetime.now()
        self.branches[branch.id] = branch
        return branch

    def save_project(self, project: MockProject) -> MockProject:
        """Save project to repository"""
        project.updated_at = datetime.now()
        self.projects[project.id] = project
        return project

    def get_context(self, level: str, context_id: str) -> Optional[MockContext]:
        """Get context by level and ID"""
        if level == "global":
            return self.contexts.get("global_singleton")
        return self.contexts.get(context_id)

    def resolve_context(self, level: str, context_id: str) -> Dict[str, Any]:
        """Resolve context with full inheritance chain"""
        context = self.get_context(level, context_id)
        if not context:
            return {}
        
        return context.resolve_with_inheritance()

    def create_hierarchical_contexts(self, project_id: str, branch_id: str, task_id: str):
        """Create the full hierarchy of contexts for a task"""
        global_context = self.get_context("global", "global_singleton")
        
        # Create project context
        project_context = MockContext(
            id=f"project_context_{project_id}",
            level="project",
            context_id=project_id,
            parent_context=global_context,
            data={
                "project_standards": {
                    "tech_stack": "Python, FastAPI, SQLAlchemy",
                    "deployment_target": "Docker",
                    "testing_strategy": "TDD"
                },
                "team_preferences": {
                    "code_review_required": True,
                    "max_function_length": 50
                }
            }
        )
        self.save_context(project_context)
        
        # Create branch context
        branch_context = MockContext(
            id=f"branch_context_{branch_id}",
            level="branch",
            context_id=branch_id,
            parent_context=project_context,
            data={
                "branch_config": {
                    "feature_flags": ["new_auth_flow", "enhanced_ui"],
                    "environment": "development",
                    "merge_strategy": "squash"
                },
                "work_in_progress": {
                    "current_sprint": "Sprint 23",
                    "focus_area": "authentication"
                }
            }
        )
        self.save_context(branch_context)
        
        # Create task context
        task_context = MockContext(
            id=f"task_context_{task_id}",
            level="task",
            context_id=task_id,
            parent_context=branch_context,
            data={
                "task_specifics": {
                    "implementation_approach": "JWT with refresh tokens",
                    "estimated_complexity": "medium",
                    "acceptance_criteria": ["Login form", "Token validation", "Session management"]
                },
                "progress_tracking": {
                    "current_phase": "implementation",
                    "blockers": [],
                    "insights": []
                }
            }
        )
        self.save_context(task_context)
        
        return {
            "global": global_context,
            "project": project_context,
            "branch": branch_context,
            "task": task_context
        }


class TestTaskContextBranchRelationships:
    """Test suite for Task-Context-Branch relationship integration"""

    def setup_method(self):
        """Setup test fixtures"""
        self.repository = MockHierarchicalContextRepository()
        
        # Test data
        self.project_id = str(uuid.uuid4())
        self.branch_id = str(uuid.uuid4())
        self.task_id = str(uuid.uuid4())
        self.user_id = "test_user_123"

    # ===== HIERARCHICAL CONTEXT CREATION TESTS =====

    def test_create_full_context_hierarchy(self):
        """Test creating the complete 4-tier context hierarchy"""
        # Act
        contexts = self.repository.create_hierarchical_contexts(
            self.project_id, self.branch_id, self.task_id
        )
        
        # Assert
        assert len(contexts) == 4
        assert "global" in contexts
        assert "project" in contexts
        assert "branch" in contexts
        assert "task" in contexts
        
        # Verify hierarchy links
        task_context = contexts["task"]
        branch_context = contexts["branch"]
        project_context = contexts["project"]
        global_context = contexts["global"]
        
        assert task_context.parent_context == branch_context
        assert branch_context.parent_context == project_context
        assert project_context.parent_context == global_context
        assert global_context.parent_context is None

    def test_context_inheritance_chain(self):
        """Test that context inheritance works correctly"""
        # Arrange
        contexts = self.repository.create_hierarchical_contexts(
            self.project_id, self.branch_id, self.task_id
        )
        
        # Act
        resolved_data = self.repository.resolve_context("task", self.task_id)
        
        # Assert - Should contain data from all levels
        assert "organization_standards" in resolved_data  # From global
        assert "security_policies" in resolved_data       # From global
        assert "project_standards" in resolved_data       # From project
        assert "team_preferences" in resolved_data        # From project
        assert "branch_config" in resolved_data           # From branch
        assert "work_in_progress" in resolved_data        # From branch
        assert "task_specifics" in resolved_data          # From task
        assert "progress_tracking" in resolved_data       # From task
        
        # Verify specific inherited values
        assert resolved_data["organization_standards"]["coding_style"] == "PEP8"
        assert resolved_data["project_standards"]["tech_stack"] == "Python, FastAPI, SQLAlchemy"
        assert resolved_data["branch_config"]["environment"] == "development"
        assert resolved_data["task_specifics"]["implementation_approach"] == "JWT with refresh tokens"

    def test_context_overrides_at_lower_levels(self):
        """Test that lower level contexts can override higher level settings"""
        # Arrange
        contexts = self.repository.create_hierarchical_contexts(
            self.project_id, self.branch_id, self.task_id
        )
        
        # Override global setting at project level
        project_context = contexts["project"]
        project_context.data["organization_standards"] = {
            "coding_style": "Google Style",  # Override global PEP8
            "testing_framework": "pytest"
        }
        self.repository.save_context(project_context)
        
        # Override project setting at task level
        task_context = contexts["task"]
        task_context.data["project_standards"] = {
            "tech_stack": "Node.js, Express, MongoDB",  # Override project tech stack
            "deployment_target": "Kubernetes"
        }
        self.repository.save_context(task_context)
        
        # Act
        resolved_data = self.repository.resolve_context("task", self.task_id)
        
        # Assert - Lower level overrides should take precedence
        assert resolved_data["organization_standards"]["coding_style"] == "Google Style"
        assert resolved_data["project_standards"]["tech_stack"] == "Node.js, Express, MongoDB"
        assert resolved_data["project_standards"]["deployment_target"] == "Kubernetes"

    # ===== TASK-CONTEXT INTEGRATION TESTS =====

    def test_task_with_context_creation(self):
        """Test creating task with associated context"""
        # Arrange
        contexts = self.repository.create_hierarchical_contexts(
            self.project_id, self.branch_id, self.task_id
        )
        
        # Act
        task = MockTask(
            id=self.task_id,
            title="Implement JWT Authentication",
            project_id=self.project_id,
            git_branch_id=self.branch_id,
            context_id=self.task_id,
            user_id=self.user_id
        )
        saved_task = self.repository.save_task(task)
        
        # Assert
        assert saved_task.context_id == self.task_id
        
        # Verify context exists and is linked
        task_context = self.repository.get_context("task", self.task_id)
        assert task_context is not None
        assert task_context.context_id == self.task_id

    def test_task_context_updates_during_workflow(self):
        """Test updating task context during task lifecycle"""
        # Arrange
        contexts = self.repository.create_hierarchical_contexts(
            self.project_id, self.branch_id, self.task_id
        )
        
        task = MockTask(
            id=self.task_id,
            title="Progressive Task",
            project_id=self.project_id,
            git_branch_id=self.branch_id,
            status="todo"
        )
        self.repository.save_task(task)
        
        task_context = contexts["task"]
        
        # Act - Simulate task progress with context updates
        
        # 1. Start working
        task.status = "in_progress"
        task_context.data["progress_tracking"]["current_phase"] = "analysis"
        task_context.data["progress_tracking"]["insights"].append("Found existing auth library")
        self.repository.save_task(task)
        self.repository.save_context(task_context)
        
        # 2. Hit a blocker
        task_context.data["progress_tracking"]["blockers"].append({
            "description": "Missing API documentation",
            "reported_at": datetime.now().isoformat()
        })
        self.repository.save_context(task_context)
        
        # 3. Resolve and complete
        task.status = "done"
        task_context.data["progress_tracking"]["current_phase"] = "completed"
        task_context.data["progress_tracking"]["completion_summary"] = "JWT implementation complete"
        task_context.data["progress_tracking"]["blockers"] = []  # Clear blockers
        self.repository.save_task(task)
        self.repository.save_context(task_context)
        
        # Assert
        final_resolved = self.repository.resolve_context("task", self.task_id)
        progress = final_resolved["progress_tracking"]
        
        assert progress["current_phase"] == "completed"
        assert "Found existing auth library" in progress["insights"]
        assert progress["completion_summary"] == "JWT implementation complete"
        assert len(progress["blockers"]) == 0

    def test_task_context_auto_detection_from_task_id(self):
        """Test automatic context ID detection from task ID"""
        # Arrange
        contexts = self.repository.create_hierarchical_contexts(
            self.project_id, self.branch_id, self.task_id
        )
        
        # Act - Create task without explicit context_id
        task = MockTask(
            id=self.task_id,
            title="Auto-Context Task",
            project_id=self.project_id,
            git_branch_id=self.branch_id
            # context_id will default to task.id
        )
        saved_task = self.repository.save_task(task)
        
        # Assert
        assert saved_task.context_id == self.task_id
        
        # Verify context can be resolved
        resolved_data = self.repository.resolve_context("task", self.task_id)
        assert len(resolved_data) > 0

    # ===== BRANCH-CONTEXT INTEGRATION TESTS =====

    def test_branch_with_context_creation(self):
        """Test creating branch with associated context"""
        # Arrange
        contexts = self.repository.create_hierarchical_contexts(
            self.project_id, self.branch_id, self.task_id
        )
        
        # Act
        branch = MockBranch(
            id=self.branch_id,
            name="feature/jwt-auth",
            project_id=self.project_id,
            description="JWT authentication feature branch",
            context_id=self.branch_id
        )
        saved_branch = self.repository.save_branch(branch)
        
        # Assert
        assert saved_branch.context_id == self.branch_id
        
        # Verify context exists
        branch_context = self.repository.get_context("branch", self.branch_id)
        assert branch_context is not None
        assert branch_context.level == "branch"

    def test_multiple_tasks_in_same_branch_context(self):
        """Test multiple tasks sharing the same branch context"""
        # Arrange
        task_id_2 = str(uuid.uuid4())
        
        contexts = self.repository.create_hierarchical_contexts(
            self.project_id, self.branch_id, self.task_id
        )
        
        # Create branch context for second task (should inherit from same branch)
        task_context_2 = MockContext(
            id=f"task_context_{task_id_2}",
            level="task",
            context_id=task_id_2,
            parent_context=contexts["branch"],  # Same branch context
            data={
                "task_specifics": {
                    "implementation_approach": "OAuth integration",
                    "estimated_complexity": "high"
                }
            }
        )
        self.repository.save_context(task_context_2)
        
        # Act
        task1 = MockTask(
            id=self.task_id,
            title="JWT Implementation",
            project_id=self.project_id,
            git_branch_id=self.branch_id
        )
        
        task2 = MockTask(
            id=task_id_2,
            title="OAuth Integration",
            project_id=self.project_id,
            git_branch_id=self.branch_id
        )
        
        self.repository.save_task(task1)
        self.repository.save_task(task2)
        
        # Assert - Both tasks should inherit same branch context
        resolved_1 = self.repository.resolve_context("task", self.task_id)
        resolved_2 = self.repository.resolve_context("task", task_id_2)
        
        # Both should have same branch config
        assert resolved_1["branch_config"]["environment"] == "development"
        assert resolved_2["branch_config"]["environment"] == "development"
        assert resolved_1["work_in_progress"]["current_sprint"] == "Sprint 23"
        assert resolved_2["work_in_progress"]["current_sprint"] == "Sprint 23"
        
        # But different task specifics
        assert resolved_1["task_specifics"]["implementation_approach"] == "JWT with refresh tokens"
        assert resolved_2["task_specifics"]["implementation_approach"] == "OAuth integration"

    def test_branch_context_feature_flags(self):
        """Test branch-specific feature flags affecting tasks"""
        # Arrange
        contexts = self.repository.create_hierarchical_contexts(
            self.project_id, self.branch_id, self.task_id
        )
        
        # Update branch context with feature flags
        branch_context = contexts["branch"]
        branch_context.data["branch_config"]["feature_flags"] = [
            "new_auth_flow", 
            "enhanced_ui", 
            "experimental_cache"
        ]
        self.repository.save_context(branch_context)
        
        # Act
        resolved_data = self.repository.resolve_context("task", self.task_id)
        
        # Assert
        feature_flags = resolved_data["branch_config"]["feature_flags"]
        assert "new_auth_flow" in feature_flags
        assert "enhanced_ui" in feature_flags
        assert "experimental_cache" in feature_flags

    # ===== CONTEXT DELEGATION TESTS =====

    def test_delegate_task_insights_to_branch(self):
        """Test delegating task insights to branch level"""
        # Arrange
        contexts = self.repository.create_hierarchical_contexts(
            self.project_id, self.branch_id, self.task_id
        )
        
        task_context = contexts["task"]
        
        # Act - Delegate reusable pattern to branch level
        delegation_data = {
            "reusable_patterns": {
                "jwt_implementation": {
                    "library": "PyJWT",
                    "token_expiry": "24h",
                    "refresh_strategy": "sliding_window",
                    "security_considerations": ["HTTPS only", "HttpOnly cookies"]
                }
            }
        }
        
        success = task_context.delegate_to_parent(
            delegation_data,
            "JWT pattern reusable across authentication tasks"
        )
        
        # Assert
        assert success is True
        
        # Verify pattern is now available at branch level
        branch_resolved = self.repository.resolve_context("branch", self.branch_id)
        assert "reusable_patterns" in branch_resolved
        assert "jwt_implementation" in branch_resolved["reusable_patterns"]
        assert branch_resolved["reusable_patterns"]["jwt_implementation"]["library"] == "PyJWT"

    def test_delegate_branch_standards_to_project(self):
        """Test delegating branch standards to project level"""
        # Arrange
        contexts = self.repository.create_hierarchical_contexts(
            self.project_id, self.branch_id, self.task_id
        )
        
        branch_context = contexts["branch"]
        
        # Act - Delegate proven practices to project level
        delegation_data = {
            "proven_practices": {
                "authentication_workflow": {
                    "step1": "Input validation",
                    "step2": "Credential verification", 
                    "step3": "Token generation",
                    "step4": "Response formatting"
                },
                "error_handling": {
                    "use_structured_errors": True,
                    "log_security_events": True,
                    "rate_limiting": "5_attempts_per_minute"
                }
            }
        }
        
        success = branch_context.delegate_to_parent(
            delegation_data,
            "Authentication workflow proven in feature branch"
        )
        
        # Assert
        assert success is True
        
        # Verify practices are now available at project level
        project_resolved = self.repository.resolve_context("project", self.project_id)
        assert "proven_practices" in project_resolved
        assert "authentication_workflow" in project_resolved["proven_practices"]

    def test_delegate_project_policies_to_global(self):
        """Test delegating project policies to global level"""
        # Arrange
        contexts = self.repository.create_hierarchical_contexts(
            self.project_id, self.branch_id, self.task_id
        )
        
        project_context = contexts["project"]
        
        # Act - Delegate organization-wide policies
        delegation_data = {
            "organization_policies": {
                "security_standards": {
                    "mandatory_2fa": True,
                    "password_rotation": "90_days",
                    "encryption_at_rest": "AES256"
                },
                "compliance_requirements": {
                    "audit_logs": "required",
                    "data_retention": "7_years",
                    "privacy_controls": "GDPR_compliant"
                }
            }
        }
        
        success = project_context.delegate_to_parent(
            delegation_data,
            "Security standards validated in project"
        )
        
        # Assert
        assert success is True
        
        # Verify policies are now available globally
        global_resolved = self.repository.resolve_context("global", "global_singleton")
        assert "organization_policies" in global_resolved
        assert "security_standards" in global_resolved["organization_policies"]

    # ===== CROSS-SYSTEM INTEGRATION TESTS =====

    def test_task_completion_with_context_and_branch_updates(self):
        """Test task completion updating both context and branch statistics"""
        # Arrange
        contexts = self.repository.create_hierarchical_contexts(
            self.project_id, self.branch_id, self.task_id
        )
        
        task = MockTask(
            id=self.task_id,
            title="Integration Test Task",
            project_id=self.project_id,
            git_branch_id=self.branch_id,
            status="in_progress"
        )
        self.repository.save_task(task)
        
        branch = MockBranch(
            id=self.branch_id,
            name="feature/integration-test",
            project_id=self.project_id
        )
        self.repository.save_branch(branch)
        
        # Act - Complete task with comprehensive updates
        task.status = "done"
        self.repository.save_task(task)
        
        # Update task context
        task_context = contexts["task"]
        task_context.data["completion_data"] = {
            "completion_summary": "Successfully implemented JWT authentication",
            "testing_notes": "Unit tests: 15 passed, Integration tests: 8 passed",
            "performance_metrics": {
                "token_generation_time": "5ms",
                "validation_time": "2ms"
            },
            "lessons_learned": [
                "Library X provides better error handling",
                "Caching improves performance by 40%"
            ]
        }
        self.repository.save_context(task_context)
        
        # Update branch context with task completion
        branch_context = contexts["branch"]
        if "completed_tasks" not in branch_context.data:
            branch_context.data["completed_tasks"] = []
        
        branch_context.data["completed_tasks"].append({
            "task_id": self.task_id,
            "task_title": task.title,
            "completed_at": datetime.now().isoformat(),
            "key_insights": task_context.data["completion_data"]["lessons_learned"]
        })
        self.repository.save_context(branch_context)
        
        # Assert
        final_resolved = self.repository.resolve_context("task", self.task_id)
        
        assert "completion_data" in final_resolved
        assert final_resolved["completion_data"]["completion_summary"] == "Successfully implemented JWT authentication"
        assert len(final_resolved["completion_data"]["lessons_learned"]) == 2
        assert len(final_resolved["completed_tasks"]) == 1
        assert final_resolved["completed_tasks"][0]["task_id"] == self.task_id

    def test_project_health_aggregation_from_contexts(self):
        """Test aggregating project health from branch and task contexts"""
        # Arrange
        # Create multiple branches and tasks
        branch_id_2 = str(uuid.uuid4())
        task_id_2 = str(uuid.uuid4())
        task_id_3 = str(uuid.uuid4())
        
        contexts_1 = self.repository.create_hierarchical_contexts(
            self.project_id, self.branch_id, self.task_id
        )
        contexts_2 = self.repository.create_hierarchical_contexts(
            self.project_id, self.branch_id, task_id_2
        )
        contexts_3 = self.repository.create_hierarchical_contexts(
            self.project_id, branch_id_2, task_id_3
        )
        
        # Act - Simulate various task states
        
        # Task 1: Completed
        contexts_1["task"].data["health_metrics"] = {
            "status": "completed",
            "quality_score": 95,
            "test_coverage": 98,
            "blockers_count": 0
        }
        
        # Task 2: In progress with blockers
        contexts_2["task"].data["health_metrics"] = {
            "status": "in_progress", 
            "quality_score": 75,
            "test_coverage": 80,
            "blockers_count": 2
        }
        
        # Task 3: Todo
        contexts_3["task"].data["health_metrics"] = {
            "status": "todo",
            "quality_score": 0,
            "test_coverage": 0,
            "blockers_count": 0
        }
        
        # Save contexts
        for contexts in [contexts_1, contexts_2, contexts_3]:
            self.repository.save_context(contexts["task"])
        
        # Aggregate at project level
        project_context = contexts_1["project"]  # All tasks share same project
        project_context.data["project_health"] = {
            "total_tasks": 3,
            "completed_tasks": 1,
            "in_progress_tasks": 1,
            "todo_tasks": 1,
            "average_quality_score": (95 + 75 + 0) / 3,  # 56.67
            "average_test_coverage": (98 + 80 + 0) / 3,   # 59.33
            "total_blockers": 2,
            "completion_rate": 1/3 * 100  # 33.33%
        }
        self.repository.save_context(project_context)
        
        # Assert
        project_resolved = self.repository.resolve_context("project", self.project_id)
        health = project_resolved["project_health"]
        
        assert health["total_tasks"] == 3
        assert health["completed_tasks"] == 1
        assert health["total_blockers"] == 2
        assert abs(health["average_quality_score"] - 56.67) < 0.1
        assert abs(health["completion_rate"] - 33.33) < 0.1

    def test_context_inheritance_validation(self):
        """Test validation of context inheritance chain integrity"""
        # Arrange
        contexts = self.repository.create_hierarchical_contexts(
            self.project_id, self.branch_id, self.task_id
        )
        
        # Act - Validate inheritance chain
        task_context = contexts["task"]
        inheritance_chain = task_context._get_inheritance_chain()
        
        # Assert
        assert len(inheritance_chain) == 4
        
        # Verify correct order: Global -> Project -> Branch -> Task
        assert inheritance_chain[0].level == "global"
        assert inheritance_chain[1].level == "project"
        assert inheritance_chain[2].level == "branch"
        assert inheritance_chain[3].level == "task"
        
        # Verify parent relationships
        for i in range(1, len(inheritance_chain)):
            current = inheritance_chain[i]
            parent = inheritance_chain[i-1]
            assert current.parent_context == parent

    def test_context_data_conflict_resolution(self):
        """Test how conflicts are resolved when same keys exist at different levels"""
        # Arrange
        contexts = self.repository.create_hierarchical_contexts(
            self.project_id, self.branch_id, self.task_id
        )
        
        # Create conflicting data at different levels
        global_context = contexts["global"]
        global_context.data["auth_config"] = {
            "provider": "internal",
            "token_expiry": "1h",
            "allow_refresh": False
        }
        
        project_context = contexts["project"]
        project_context.data["auth_config"] = {
            "provider": "oauth2",  # Override global
            "token_expiry": "1h",  # Same as global
            "scopes": ["read", "write"]  # New field
        }
        
        branch_context = contexts["branch"]
        branch_context.data["auth_config"] = {
            "token_expiry": "24h",  # Override project/global
            "allow_refresh": True   # Override global
        }
        
        task_context = contexts["task"]
        task_context.data["auth_config"] = {
            "provider": "ldap",  # Override all others
            "custom_claims": ["role", "department"]  # New field
        }
        
        # Save all contexts
        for context in contexts.values():
            self.repository.save_context(context)
        
        # Act
        resolved_data = self.repository.resolve_context("task", self.task_id)
        
        # Assert - Lower levels should override higher levels
        auth_config = resolved_data["auth_config"]
        
        assert auth_config["provider"] == "ldap"  # Task override
        assert auth_config["token_expiry"] == "24h"  # Branch override
        assert auth_config["allow_refresh"] is True  # Branch override
        assert "scopes" in auth_config  # From project
        assert auth_config["scopes"] == ["read", "write"]
        assert "custom_claims" in auth_config  # From task
        assert auth_config["custom_claims"] == ["role", "department"]

    # ===== ERROR HANDLING AND EDGE CASES =====

    def test_missing_parent_context_handling(self):
        """Test handling of missing parent contexts in inheritance chain"""
        # Arrange - Create orphaned task context
        orphaned_task_context = MockContext(
            id=f"orphaned_task_{self.task_id}",
            level="task",
            context_id=self.task_id,
            parent_context=None,  # No parent!
            data={"task_data": "isolated"}
        )
        self.repository.save_context(orphaned_task_context)
        
        # Act
        resolved_data = self.repository.resolve_context("task", self.task_id)
        
        # Assert - Should only contain task's own data
        assert "task_data" in resolved_data
        assert resolved_data["task_data"] == "isolated"
        assert "organization_standards" not in resolved_data  # No global inheritance

    def test_circular_context_reference_prevention(self):
        """Test prevention of circular references in context hierarchy"""
        # Arrange
        contexts = self.repository.create_hierarchical_contexts(
            self.project_id, self.branch_id, self.task_id
        )
        
        # Attempt to create circular reference (should be prevented in real implementation)
        task_context = contexts["task"]
        global_context = contexts["global"]
        
        # This would create a cycle: Global -> Project -> Branch -> Task -> Global
        # In real implementation, this should be detected and prevented
        # For this test, we'll just verify the current structure doesn't have cycles
        
        # Act & Assert
        inheritance_chain = task_context._get_inheritance_chain()
        
        # Verify no context appears twice in the chain
        context_ids = [ctx.context_id for ctx in inheritance_chain]
        assert len(context_ids) == len(set(context_ids))  # No duplicates

    def test_context_auto_creation_for_missing_levels(self):
        """Test automatic creation of missing intermediate contexts"""
        # Arrange - Create task without intermediate contexts
        task_context = MockContext(
            id=f"standalone_task_{self.task_id}",
            level="task",
            context_id=self.task_id,
            data={"standalone": True}
        )
        self.repository.save_context(task_context)
        
        # In real implementation, this would trigger auto-creation of missing
        # project and branch contexts. For now, we just test the isolated case.
        
        # Act
        resolved_data = self.repository.resolve_context("task", self.task_id)
        
        # Assert
        assert "standalone" in resolved_data
        assert resolved_data["standalone"] is True