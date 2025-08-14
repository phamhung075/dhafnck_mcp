"""
Integration test for context insights persistence fix.

This test verifies that insights are properly persisted and retrieved
in a real database environment, demonstrating the complete fix works end-to-end.
"""

import pytest
from uuid import uuid4
from datetime import datetime, timezone
from sqlalchemy import text

from fastmcp.task_management.application.factories.unified_context_facade_factory import UnifiedContextFacadeFactory
from fastmcp.task_management.domain.value_objects.context_enums import ContextLevel
from fastmcp.task_management.infrastructure.database.database_config import get_db_config
import os

# Use test database configuration
os.environ['DATABASE_TYPE'] = 'postgresql'


class TestContextInsightsPersistenceIntegration:
    """Integration test for context insights persistence."""
    
    def setup_method(self, method):
        """Set up test data for each test method."""
        # Clean up any existing test data
        db_config = get_db_config()
        with db_config.get_session() as session:
            try:
                # Clean task contexts
                session.execute(text("DELETE FROM task_contexts WHERE task_id LIKE 'test-%' OR task_id = :task_id"), 
                              {"task_id": getattr(self, 'task_id', '')})
                # Clean branch contexts  
                session.execute(text("DELETE FROM branch_contexts WHERE branch_id LIKE 'test-%'"))
                # Clean project contexts
                session.execute(text("DELETE FROM project_contexts WHERE project_id LIKE 'test-%'"))
                # Don't delete global context as it's a singleton
                session.commit()
            except:
                session.rollback()
        
        self.facade = UnifiedContextFacadeFactory.create_facade()
        self.task_id = str(uuid4())
        self.branch_id = str(uuid4())
        self.project_id = str(uuid4())
        
        # Create parent contexts to satisfy hierarchy
        # Create global context
        global_result = self.facade.create_context(
            level="global",
            context_id="global_singleton",
            data={
                "organization_name": "Test Organization",
                "global_settings": {}
            }
        )
        assert global_result["success"], f"Failed to create global context: {global_result}"
        
        # Create project context
        project_result = self.facade.create_context(
            level="project",
            context_id=self.project_id,
            data={
                "project_name": "Test Project",
                "project_settings": {}
            }
        )
        assert project_result["success"], f"Failed to create project context: {project_result}"
        
        # Create branch context
        branch_result = self.facade.create_context(
            level="branch",
            context_id=self.branch_id,
            data={
                "project_id": self.project_id,
                "git_branch_name": "test-branch",
                "branch_settings": {}
            }
        )
        assert branch_result["success"], f"Failed to create branch context: {branch_result}"
    
    def test_insights_persistence_complete_workflow(self):
        """Test complete workflow of creating, updating, and retrieving insights."""
        # Step 1: Create task context with initial insights
        initial_insights = [
            {
                "content": "Initial discovery about the codebase structure",
                "category": "architecture",
                "importance": "high",
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            {
                "content": "Found potential performance bottleneck",
                "category": "performance",
                "importance": "medium",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        ]
        
        create_result = self.facade.create_context(
            level="task",
            context_id=self.task_id,
            data={
                "branch_id": self.branch_id,
                "task_data": {
                    "title": "Fix Context Insights Persistence",
                    "description": "Ensure insights are properly saved"
                },
                "progress": 25,
                "insights": initial_insights,
                "next_steps": ["Investigate the issue", "Implement fix"]
            }
        )
        
        assert create_result["success"], f"Failed to create task context: {create_result}"
        
        # Step 2: Retrieve context and verify insights are persisted
        get_result = self.facade.get_context(
            level="task",
            context_id=self.task_id
        )
        
        assert get_result["success"], f"Failed to get task context: {get_result}"
        context = get_result["context"]
        
        # Verify initial insights are present
        assert len(context["insights"]) == 2
        assert context["insights"][0]["content"] == "Initial discovery about the codebase structure"
        assert context["insights"][1]["content"] == "Found potential performance bottleneck"
        assert context["progress"] == 25
        
        # Step 3: Update context with new insights (should replace, not extend)
        new_insights = [
            {
                "content": "Root cause identified: Repository was returning empty arrays",
                "category": "debugging",
                "importance": "critical",
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            {
                "content": "Fix implemented: Modified _to_entity method to extract from task_data",
                "category": "solution",
                "importance": "high",
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            {
                "content": "Also fixed merge logic to replace insights instead of extending",
                "category": "solution",
                "importance": "high",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        ]
        
        update_result = self.facade.update_context(
            level="task",
            context_id=self.task_id,
            data={
                "insights": new_insights,
                "progress": 75
            }
        )
        
        assert update_result["success"], f"Failed to update task context: {update_result}"
        
        # Step 4: Retrieve again and verify insights were replaced
        final_result = self.facade.get_context(
            level="task",
            context_id=self.task_id
        )
        
        assert final_result["success"], f"Failed to get updated task context: {final_result}"
        final_context = final_result["context"]
        
        # Verify insights were replaced, not extended
        assert len(final_context["insights"]) == 3, f"Expected 3 insights, got {len(final_context['insights'])}"
        assert final_context["insights"][0]["content"] == "Root cause identified: Repository was returning empty arrays"
        assert final_context["insights"][1]["category"] == "solution"
        assert final_context["progress"] == 75
        
        # Step 5: Test add_insight method
        add_insight_result = self.facade.add_insight(
            level="task",
            context_id=self.task_id,
            content="All tests passing, fix is complete",
            category="testing",
            importance="high",
            agent="debugger_agent"
        )
        
        assert add_insight_result["success"], f"Failed to add insight: {add_insight_result}"
        
        # Step 6: Final verification
        verification_result = self.facade.get_context(
            level="task",
            context_id=self.task_id
        )
        
        assert verification_result["success"]
        verification_context = verification_result["context"]
        
        # Should have 4 insights now (3 replaced + 1 added)
        assert len(verification_context["insights"]) == 4
        assert verification_context["insights"][3]["content"] == "All tests passing, fix is complete"
        assert verification_context["insights"][3]["agent"] == "debugger_agent"
    
    def test_empty_insights_handling(self):
        """Test that empty insights array is handled correctly."""
        # Create context with empty insights
        create_result = self.facade.create_context(
            level="task",
            context_id=str(uuid4()),
            data={
                "branch_id": self.branch_id,
                "task_data": {"title": "Test Empty Insights"},
                "insights": [],
                "progress": 0
            }
        )
        
        assert create_result["success"]
        
        # Retrieve and verify
        get_result = self.facade.get_context(
            level="task",
            context_id=create_result["context"]["id"]
        )
        
        assert get_result["success"]
        assert get_result["context"]["insights"] == []
        assert isinstance(get_result["context"]["insights"], list)
    
    def test_insights_with_complex_data(self):
        """Test insights with complex nested data structures."""
        complex_insights = [
            {
                "content": "Complex analysis results",
                "category": "analysis",
                "importance": "high",
                "metadata": {
                    "files_analyzed": ["file1.py", "file2.py"],
                    "metrics": {
                        "complexity": 8,
                        "lines_of_code": 250,
                        "test_coverage": 0.85
                    }
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        ]
        
        # Create context with complex insights
        create_result = self.facade.create_context(
            level="task",
            context_id=str(uuid4()),
            data={
                "branch_id": self.branch_id,
                "task_data": {"title": "Test Complex Insights"},
                "insights": complex_insights
            }
        )
        
        assert create_result["success"]
        
        # Retrieve and verify complex data is preserved
        get_result = self.facade.get_context(
            level="task",
            context_id=create_result["context"]["id"]
        )
        
        assert get_result["success"]
        retrieved_insights = get_result["context"]["insights"]
        assert len(retrieved_insights) == 1
        assert retrieved_insights[0]["metadata"]["metrics"]["test_coverage"] == 0.85
        assert retrieved_insights[0]["metadata"]["files_analyzed"] == ["file1.py", "file2.py"]