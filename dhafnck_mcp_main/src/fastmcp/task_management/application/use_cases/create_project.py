"""Create Project Use Case"""

from typing import Dict, Any
from datetime import datetime, timezone
from ...domain.entities.project import Project
from ...domain.repositories.project_repository import ProjectRepository


# NOTE: We previously changed this signature and broke consumers that still
# rely on the (project_id, name, description) order.  Restore backward
# compatibility while keeping the convenience of auto-generated IDs when the
# caller does not provide one.

class CreateProjectUseCase:
    """Use case for creating a new project"""

    def __init__(self, project_repository: ProjectRepository):
        self._project_repository = project_repository

    async def execute(
        self,
        project_id: str | None,
        name: str | None = None,
        description: str = "",
    ) -> Dict[str, Any]:
        """Execute the create-project use case.

        This method now supports **two** calling conventions:

        1. Legacy: ``execute(project_id, name, description)``
        2. New   : ``execute(None, name, description)`` — project_id will be auto-generated.
        """

        from uuid import uuid4

        # If the caller uses the new convenience form the first positional
        # argument (project_id) will be ``None`` and *name* will contain the
        # actual project name.
        if name is None:
            # The caller used old signature but passed only (name, description)
            # – treat *project_id* as *name* and generate ID.
            name = project_id  # type: ignore
            project_id = None

        # Ensure we have required fields now.
        if name is None:
            return {"success": False, "error": "Project name is required"}

        # Auto-generate ID when not supplied.
        project_id = project_id or str(uuid4())

        try:
            # Create project entity
            now = datetime.now(timezone.utc)
            project = Project(
                id=project_id,
                name=name,
                description=description,
                created_at=now,
                updated_at=now,
            )

            # Create default main task tree so the project has at least one branch
            project.create_task_tree(
                git_branch_name="main",
                name="Main Tasks",
                description="Main task tree for the project",
            )

            # Persist via repository (allows duplicate detection etc.)
            await self._project_repository.save(project)
            
            # Auto-create project context for hierarchical context inheritance
            try:
                from ..facades.hierarchical_context_facade import HierarchicalContextFacade
                from ..services.hierarchical_context_service import HierarchicalContextService
                from ..services.context_inheritance_service import ContextInheritanceService
                from ..services.context_delegation_service import ContextDelegationService
                from ..services.context_cache_service import ContextCacheService
                
                # Create facade with mocked services for now
                # In production, these would be injected properly
                hierarchy_service = HierarchicalContextService()
                inheritance_service = ContextInheritanceService()
                delegation_service = ContextDelegationService() 
                cache_service = ContextCacheService()
                
                context_facade = HierarchicalContextFacade(
                    hierarchy_service=hierarchy_service,
                    inheritance_service=inheritance_service,
                    delegation_service=delegation_service,
                    cache_service=cache_service
                )
                
                # Create default project context
                project_dict = {
                    "id": project.id,
                    "name": project.name,
                    "description": project.description
                }
                
                context_data = context_facade._create_default_project_context_data(project.id, project_dict)
                context_response = context_facade.create_context("project", project.id, context_data)
                
                if not context_response["success"]:
                    # Log warning but don't fail project creation
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Failed to create project context for {project.id}: {context_response.get('error')}")
                    
            except Exception as context_error:
                # Log context creation error but don't fail project creation
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Error creating project context for {project.id}: {context_error}")

        except ValueError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            # Surface unexpected errors but don't hide detail – tests rely on informative messages.
            return {"success": False, "error": str(e)}

        return {
            "success": True,
            "project": {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "created_at": project.created_at.isoformat(),
                "updated_at": project.updated_at.isoformat(),
                "task_trees": list(project.task_trees.keys()),
            },
        }