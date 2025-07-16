"""DDD-Compliant MCP Tools

This module demonstrates the proper DDD architecture for MCP tools by:
- Using controllers that delegate to application facades
- Removing business logic from the interface layer
- Following proper dependency direction (Interface → Application → Domain ← Infrastructure)
- Providing clean separation of concerns

This serves as a replacement for the existing consolidated_mcp_tools.py that
violates DDD principles.
"""

import logging
from typing import Optional, Dict, Any, TYPE_CHECKING

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from ...server.server import FastMCP

# Application layer imports (proper DDD dependency injection)
from ..application.factories.task_facade_factory import TaskFacadeFactory
from ..application.factories.subtask_facade_factory import SubtaskFacadeFactory
# from ..application.factories.context_facade_factory import ContextFacadeFactory  # Replaced by HierarchicalContextFacadeFactory
from ..application.factories.hierarchical_context_facade_factory import HierarchicalContextFacadeFactory
from ..application.factories.project_facade_factory import ProjectFacadeFactory
from ..application.factories.git_branch_facade_factory import GitBranchFacadeFactory

# Import facades for type hints only
if TYPE_CHECKING:
    from ..application.facades.task_application_facade import TaskApplicationFacade


# Infrastructure layer imports (proper DDD dependency direction)
from ..infrastructure.repositories.task_repository_factory import TaskRepositoryFactory
from ..infrastructure.repositories.subtask_repository_factory import SubtaskRepositoryFactory
from ..application.use_cases.call_agent import CallAgentUseCase

# Infrastructure layer imports (proper DDD dependency direction)
from ..infrastructure.configuration.tool_config import ToolConfig
from ..infrastructure.utilities.path_resolver import PathResolver

# Interface layer imports (same layer, acceptable)
from .controllers.task_mcp_controller import TaskMCPController
from .controllers.subtask_mcp_controller import SubtaskMCPController
from .controllers.context_mcp_controller import ContextMCPController
from .controllers.project_mcp_controller import ProjectMCPController
from .controllers.git_branch_mcp_controller import GitBranchMCPController
from .controllers.agent_mcp_controller import AgentMCPController
from .controllers.call_agent_mcp_controller import CallAgentMCPController
from .controllers.compliance_mcp_controller import ComplianceMCPController
from .controllers.file_resource_mcp_controller import FileResourceMCPController
from .controllers.rule_orchestration_controller import RuleOrchestrationController

# Vision System Enhanced Controllers
# Enhanced task controller removed - functionality merged into TaskMCPController
from .controllers.workflow_hint_enhancer import WorkflowHintEnhancer


# Application layer imports (proper DDD dependency direction) 
# Use case imports for tool registration (call_agent)

logger = logging.getLogger(__name__)


class DDDCompliantMCPTools:
    """
    DDD-compliant MCP tools that follow proper architectural patterns.
    
    This class demonstrates the correct way to structure MCP tools by:
    - Using dependency injection for proper inversion of control
    - Delegating business logic to application facades
    - Keeping interface concerns separate from business logic
    - Following proper DDD layering principles
    """
    
    def __init__(self, 
                 projects_file_path: Optional[str] = None,  # Kept for backward compatibility, ignored
                 config_overrides: Optional[Dict[str, Any]] = None,
                 enable_vision_system: bool = True):
        """
        Initialize DDD-compliant MCP tools.
        
        Args:
            projects_file_path: Deprecated parameter kept for backward compatibility (ignored)
            config_overrides: Optional configuration overrides
            enable_vision_system: Enable Vision System features (default: True)
        """
        logger.info("Initializing DDD-compliant MCP tools...")
        
        # Initialize configuration and infrastructure
        self._config = ToolConfig(config_overrides)
        self._path_resolver = PathResolver()
        self._task_repository_factory = TaskRepositoryFactory()
        self._subtask_repository_factory = SubtaskRepositoryFactory()
        
        # Initialize facade factories
        # Use hierarchical context facade factory for new context system
        self._hierarchical_context_facade_factory = HierarchicalContextFacadeFactory()
        self._context_facade_factory = self._hierarchical_context_facade_factory  # Use hierarchical factory directly
        self._project_facade_factory = ProjectFacadeFactory()
        self._git_branch_facade_factory = GitBranchFacadeFactory()
        
        # Initialize application factories
        self._task_facade_factory = TaskFacadeFactory(
            self._task_repository_factory,
            self._subtask_repository_factory
        )
        
        self._subtask_facade_factory = SubtaskFacadeFactory(
            self._subtask_repository_factory,
            self._task_repository_factory
        )
        self._subtask_facade = self._subtask_facade_factory.create_subtask_facade()
        
        # Initialize controllers with facades
        self._task_controller = TaskMCPController(
            self._task_facade_factory, 
            self._context_facade_factory,  # Pass context facade factory for auto-context creation
            None,  # project_manager
            self._task_repository_factory
        )
        
        self._subtask_controller = SubtaskMCPController(
            self._subtask_facade_factory,
            task_facade=None,  # Will be set if Vision System is enabled
            context_facade=None,  # Will be set if Vision System is enabled
            task_repository_factory=self._task_repository_factory
        )
        
        # Initialize hierarchical context services
        from ..infrastructure.repositories.hierarchical_context_repository_factory import HierarchicalContextRepositoryFactory
        from ..application.services.hierarchical_context_service import HierarchicalContextService
        from ..application.services.context_inheritance_service import ContextInheritanceService
        from ..application.services.context_delegation_service import ContextDelegationService
        from ..application.services.context_cache_service import ContextCacheService
        
        hierarchical_factory = HierarchicalContextRepositoryFactory()
        hierarchical_repo = hierarchical_factory.create_hierarchical_context_repository()
        hierarchy_service = HierarchicalContextService(repository=hierarchical_repo)
        inheritance_service = ContextInheritanceService(repository=hierarchical_repo)
        delegation_service = ContextDelegationService(repository=hierarchical_repo)
        cache_service = ContextCacheService(repository=hierarchical_repo)
        
        # Context controller now uses hierarchical context facade factory with all services
        self._context_controller = ContextMCPController(
            self._hierarchical_context_facade_factory,
            hierarchy_service=hierarchy_service,
            inheritance_service=inheritance_service,
            delegation_service=delegation_service,
            cache_service=cache_service
        )
        
        self._project_controller = ProjectMCPController(self._project_facade_factory)
        
        self._git_branch_controller = GitBranchMCPController(self._git_branch_facade_factory)
        
        # Agent controller with proper agent facade factory
        from ..application.factories.agent_facade_factory import AgentFacadeFactory
        self._agent_facade_factory = AgentFacadeFactory()
        self._agent_controller = AgentMCPController(self._agent_facade_factory)
        
        # Initialize call agent use case and controller
        cursor_agent_dir = self._path_resolver.get_cursor_agent_dir()
        self._call_agent_use_case = CallAgentUseCase(cursor_agent_dir)
        self._call_agent_controller = CallAgentMCPController(self._call_agent_use_case)
        
        # Initialize compliance controller
        self._compliance_controller = ComplianceMCPController(project_root=self._path_resolver.project_root)
        
        # Initialize file resource controller
        self._file_resource_controller = FileResourceMCPController(project_root=self._path_resolver.project_root)
        
        # Initialize cursor rules tools (DDD-compliant)
        from .cursor_rules_tools_ddd import CursorRulesToolsDDD
        self._cursor_rules_tools = CursorRulesToolsDDD()
        
        # Initialize rule orchestration controller
        from ..application.facades.rule_application_facade import RuleApplicationFacade
        rule_app_facade = RuleApplicationFacade(path_resolver=self._path_resolver)
        self._rule_orchestration_facade = rule_app_facade.orchestration_facade
        self._rule_orchestration_controller = RuleOrchestrationController(self._rule_orchestration_facade)
        
        
        # Initialize Vision System Enhanced Controllers if enabled
        self._enable_vision_system = enable_vision_system
        if self._enable_vision_system:
            logger.info("Initializing Vision System enhanced controllers...")
            
            # Initialize Vision Services
            from ...vision_orchestration.vision_enrichment_service import VisionEnrichmentService
            from ..application.services.vision_analytics_service import VisionAnalyticsService
            from ..application.services.hint_generation_service import HintGenerationService
            from ..application.services.workflow_analysis_service import WorkflowAnalysisService
            from ..application.services.progress_tracking_service import ProgressTrackingService
            from ..application.services.agent_coordination_service import AgentCoordinationService
            from ..application.services.work_distribution_service import WorkDistributionService
            
            # Initialize repositories for Vision System
            # Note: Vision system will be refactored to use ORM repositories
            self._vision_repository = None  # SQLiteVisionRepository removed
            self._hint_repository = None  # HintRepository is abstract
            self._progress_event_store = None  # ProgressEventStore is abstract
            self._agent_coordination_repository = None  # AgentCoordinationRepository removed
            
            # Initialize services with mock repository
            self._vision_enrichment_service = VisionEnrichmentService(
                task_repository=None,
                vision_repository=self._vision_repository
            )
            self._vision_analytics_service = VisionAnalyticsService(
                task_repository=None,
                vision_repository=self._vision_repository,
                enrichment_service=self._vision_enrichment_service
            )
            self._hint_generation_service = HintGenerationService(
                task_repository=None,  # Using None for testing
                context_repository=None,  # Using None for testing
                event_store=None,
                hint_repository=None
            )
            self._workflow_analysis_service = WorkflowAnalysisService(
                task_repository=None,  # Using None for testing
                context_repository=None,  # Using None for testing
                event_store=None
            )
            self._progress_tracking_service = ProgressTrackingService(
                task_repository=None,  # Using None for testing
                context_repository=None,  # Using None for testing
                event_bus=None
            )
            self._agent_coordination_service = AgentCoordinationService(
                task_repository=None,  # Using None for testing
                agent_repository=None,
                event_bus=None,
                coordination_repository=None
            )
            self._work_distribution_service = WorkDistributionService(
                task_repository=None,  # Using None for testing
                agent_repository=None,
                coordination_service=None,
                event_bus=None
            )
            
            # Enhanced task controller functionality is now integrated into TaskMCPController
            # No separate enhanced task controller needed
            
            # Context enforcing functionality is now integrated into TaskMCPController
            # No need for a separate ContextEnforcingController
            
            # Create a task facade for Vision System (using default project)
            vision_task_facade = self._task_facade_factory.create_task_facade(
                project_id="default_project",
                git_branch_name="main",
                user_id="vision_system"
            )
            
            # Update subtask controller with vision task facade and context facade
            self._subtask_controller._task_facade = vision_task_facade
            
            # Create a context facade for Vision System
            vision_context_facade = self._context_facade_factory.create_context_facade(
                user_id="vision_system",
                project_id="default_project",
                git_branch_name="main"
            )
            self._subtask_controller._context_facade = vision_context_facade
            
            self._workflow_hint_enhancer = WorkflowHintEnhancer()
            
            logger.info("Vision System enhanced controllers initialized successfully.")
        
        logger.info("DDD-compliant MCP tools initialized successfully.")
    
    def register_tools(self, mcp: "FastMCP"):
        """
        Register MCP tools with the FastMCP server.

        This method demonstrates proper tool registration using controllers
        that delegate to application facades.

        Note: This method delegates to application facades for all business logic,
        ensuring DDD-compliant separation of concerns.
        """
        logger.info("Registering DDD-compliant MCP tools...")
        
        # Register task management tools
        self._register_task_tools(mcp)
        
        # Register subtask management tools
        self._register_subtask_tools(mcp)
        
        # Register context management tools
        self._register_context_tools(mcp)
        
        # Register project management tools
        self._register_project_tools(mcp)
        
        # Register git branch management tools
        self._register_git_branch_tools(mcp)
        
        # Register agent tools
        self._register_agent_tools(mcp)
        
        # Register cursor rules tools
        self._register_cursor_rules_tools(mcp)
        
        # Register rule orchestration tools
        self._register_rule_orchestration_tools(mcp)
        
        # Register call agent tool
        self._register_call_agent_tool(mcp)
        
        # Register compliance tools
        self._register_compliance_tools(mcp)
        
        # Register file resource tools
        self._register_file_resource_tools(mcp)
        
        
        # Register Vision System enhanced tools if enabled
        if self._enable_vision_system:
            logger.info("Registering Vision System enhanced tools...")
            self._register_vision_enhanced_tools(mcp)
        
        logger.info("DDD-compliant MCP tools registered successfully.")
    
    
    def _register_task_tools(self, mcp: "FastMCP"):
        """Register task management MCP tools via controller"""
        self._task_controller.register_tools(mcp)
    
    def _register_subtask_tools(self, mcp: "FastMCP"):
        """Register subtask management MCP tools via controller"""
        self._subtask_controller.register_tools(mcp)
    
    def _register_context_tools(self, mcp: "FastMCP"):
        """Register context management MCP tools via controller"""
        self._context_controller.register_tools(mcp)
    
    def _register_project_tools(self, mcp: "FastMCP"):
        """Register project management MCP tools via controller"""
        self._project_controller.register_tools(mcp)
    
    def _register_git_branch_tools(self, mcp: "FastMCP"):
        """Register git branch management MCP tools via controller"""
        self._git_branch_controller.register_tools(mcp)
    
    def _register_agent_tools(self, mcp: "FastMCP"):
        """Register agent management MCP tools via controller"""
        self._agent_controller.register_tools(mcp)
    
    def _register_cursor_rules_tools(self, mcp: "FastMCP"):
        """Register cursor rules management tools"""
        self._cursor_rules_tools.register_tools(mcp)
    
    def _register_rule_orchestration_tools(self, mcp: "FastMCP"):
        """Register rule orchestration MCP tools via controller"""
        self._rule_orchestration_controller.register_tools(mcp)
    
    def _register_call_agent_tool(self, mcp: "FastMCP"):
        """Register call agent MCP tools via controller"""
        self._call_agent_controller.register_tools(mcp)
    
    def _register_compliance_tools(self, mcp: "FastMCP"):
        """Register compliance management MCP tools via controller"""
        self._compliance_controller.register_tools(mcp)
    
    def _register_file_resource_tools(self, mcp: "FastMCP"):
        """Register file resource MCP tools via controller"""
        self._file_resource_controller.register_resources(mcp)
    
    
    def _register_vision_enhanced_tools(self, mcp: "FastMCP"):
        """Register Vision System enhanced tools"""
        # DISABLED: Enhanced task tools should be merged into manage_task action
        # per user requirement - these duplicate functionality
        # self._enhanced_task_controller.register_enhanced_tools(mcp)
        
        # Context enforcing tools are now integrated into task controller
        # and registered automatically when Vision System is enabled
        
        # Note: Subtask progress tools are now integrated into the main subtask controller
        # and are automatically registered when Vision System is enabled
        
        # Register workflow hint enhancement
        # Note: WorkflowHintEnhancer is designed to enhance individual responses,
        # not register tools with MCP. It should be used within other controllers
        # to enhance their responses.
        # self._workflow_hint_enhancer.enhance_all_responses(mcp)
        
        logger.info("Vision System enhanced tools registered successfully.")
    
    # Properties for backward compatibility and testing
    @property
    def task_controller(self) -> TaskMCPController:
        """Get the task controller for direct access"""
        return self._task_controller
    
    @property
    def subtask_controller(self) -> SubtaskMCPController:
        """Get the subtask controller for direct access"""
        return self._subtask_controller
    
    @property
    def context_controller(self) -> ContextMCPController:
        """Get the context controller for direct access"""
        return self._context_controller
    
    @property
    def project_controller(self) -> ProjectMCPController:
        """Get the project controller for direct access"""
        return self._project_controller
    
    @property
    def git_branch_controller(self) -> GitBranchMCPController:
        """Get the git branch controller for direct access"""
        return self._git_branch_controller
    
    @property
    def agent_controller(self) -> AgentMCPController:
        """Get the agent controller for direct access"""
        return self._agent_controller
    
    @property
    def call_agent_controller(self) -> CallAgentMCPController:
        """Get the call agent controller for direct access"""
        return self._call_agent_controller
    
    @property
    def compliance_controller(self) -> ComplianceMCPController:
        """Get the compliance controller for direct access"""
        return self._compliance_controller
    
    # Vision System Properties
    @property
    def enhanced_task_controller(self) -> Optional[TaskMCPController]:
        """Get the task controller (includes enhanced functionality if Vision System is enabled)"""
        return self._task_controller if self._enable_vision_system else None
    
    @property
    def context_enforcing_controller(self) -> Optional[TaskMCPController]:
        """Get the task controller (includes context enforcing if Vision System is enabled)"""
        # Context enforcing is now integrated into TaskMCPController
        return self._task_controller if self._enable_vision_system else None
    
    @property
    def subtask_progress_controller(self) -> Optional[SubtaskMCPController]:
        """Get the subtask controller (includes progress tracking if Vision System is enabled)"""
        return self._subtask_controller
    
    @property
    def workflow_hint_enhancer(self) -> Optional[WorkflowHintEnhancer]:
        """Get the workflow hint enhancer if Vision System is enabled"""
        return getattr(self, '_workflow_hint_enhancer', None)
    
    @property
    def vision_enrichment_service(self):
        """Get the vision enrichment service if Vision System is enabled"""
        return getattr(self, '_vision_enrichment_service', None)
    
    @property
    def vision_analytics_service(self):
        """Get the vision analytics service if Vision System is enabled"""
        return getattr(self, '_vision_analytics_service', None)
    
    
 