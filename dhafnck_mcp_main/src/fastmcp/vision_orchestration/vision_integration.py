"""Vision System Integration Module.

This module provides factory functions to initialize and wire together
the vision system components.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any

from ..task_management.domain.repositories.task_repository import TaskRepository
from ..task_management.infrastructure.repositories.sqlite.vision_repository import SQLiteVisionRepository
from .vision_enrichment_service import VisionEnrichmentService
from ..task_management.application.services.vision_analytics_service import VisionAnalyticsService


logger = logging.getLogger(__name__)


def create_vision_services(
    task_repository: TaskRepository,
    db_config: Optional[Dict[str, Any]] = None,
    config_path: Optional[Path] = None
) -> tuple[SQLiteVisionRepository, VisionEnrichmentService, VisionAnalyticsService]:
    """Create and initialize all vision system services.
    
    Args:
        task_repository: Existing task repository instance
        db_config: Optional database configuration
        config_path: Optional path to vision configuration file
        
    Returns:
        Tuple of (vision_repository, enrichment_service, analytics_service)
    """
    # Create vision repository (SQLite)
    # Convert db_config to db_path if needed
    db_path = None
    if db_config and 'database' in db_config:
        db_path = db_config['database']
    vision_repository = SQLiteVisionRepository(db_path=db_path)
    logger.info("Vision repository initialized")
    
    # Create enrichment service
    enrichment_service = VisionEnrichmentService(
        task_repository=task_repository,
        vision_repository=vision_repository,
        config_path=config_path
    )
    logger.info("Vision enrichment service initialized")
    
    # Create analytics service
    analytics_service = VisionAnalyticsService(
        task_repository=task_repository,
        vision_repository=vision_repository,
        enrichment_service=enrichment_service
    )
    logger.info("Vision analytics service initialized")
    
    return vision_repository, enrichment_service, analytics_service


def enhance_controller_with_vision(controller, task_repository, db_config=None, config_path=None):
    """Enhance an existing ContextEnforcingController with vision services.
    
    Args:
        controller: ContextEnforcingController instance
        task_repository: Task repository instance
        db_config: Optional database configuration
        config_path: Optional path to vision configuration file
        
    Returns:
        The enhanced controller
    """
    # Create vision services
    vision_repo, enrichment_svc, analytics_svc = create_vision_services(
        task_repository=task_repository,
        db_config=db_config,
        config_path=config_path
    )
    
    # Inject into controller
    controller._vision_repository = vision_repo
    controller._vision_enrichment_service = enrichment_svc
    controller._vision_analytics_service = analytics_svc
    
    logger.info("Controller enhanced with vision services")
    return controller