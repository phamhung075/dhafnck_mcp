"""Vision Enrichment Service.

This service enriches task data with vision alignment information,
calculates alignment scores, and provides vision-based guidance.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from uuid import UUID

from ..task_management.domain.entities.task import Task
from ..task_management.domain.value_objects.vision_objects import (
    VisionObjective, VisionAlignment, VisionMetric, VisionInsight,
    VisionHierarchyLevel, ContributionType, MetricType
)
# Repository imports will be passed as dependencies
# from ..task_management.infrastructure.repositories.task_repository import TaskRepository
# from ..task_management.infrastructure.repositories.vision_repository import VisionRepository
from .configuration.config_loader import get_vision_config, is_phase_enabled


logger = logging.getLogger(__name__)


class VisionEnrichmentService:
    """Service for enriching tasks with vision alignment data."""
    
    def __init__(
        self,
        task_repository=None,
        vision_repository=None,
        config_path: Optional[Path] = None
    ):
        """Initialize the vision enrichment service.
        
        Args:
            task_repository: Repository for task data access (can be None for graceful degradation)
            vision_repository: Repository for vision data access (can be None for graceful degradation)
            config_path: Optional path to vision configuration file
        
        Note:
            If repositories are None, the service will operate in degraded mode:
            - Vision hierarchy will be loaded only from configuration files
            - Database operations will be skipped with warnings logged
            - Task alignment calculations that require database access will return None
        """
        self.task_repository = task_repository
        self.vision_repository = vision_repository
        
        # Log repository availability status for debugging
        if self.vision_repository is None:
            logger.info("Vision enrichment service initialized without vision repository - operating in degraded mode")
        if self.task_repository is None:
            logger.info("Vision enrichment service initialized without task repository - some features unavailable")
        
        # Load configuration
        self.config = get_vision_config()
        vision_config = self.config.get("vision_system", {}).get("vision_enrichment", {})
        
        # Use config path from settings or parameter
        hierarchy_path = vision_config.get("hierarchy_config_path")
        if hierarchy_path:
            self.config_path = Path(hierarchy_path)
        else:
            self.config_path = config_path or Path("config/vision_hierarchy.json")
        
        self._vision_cache: Dict[UUID, VisionObjective] = {}
        self._hierarchy_cache: Dict[UUID, List[UUID]] = {}  # parent -> children
        
        # Only load hierarchy if vision enrichment is enabled
        if is_phase_enabled("vision_enrichment"):
            self._load_vision_hierarchy()
        else:
            logger.info("Vision enrichment disabled - skipping hierarchy load")
    
    def _load_vision_hierarchy(self) -> None:
        """Load vision hierarchy from configuration or database."""
        try:
            # Check if vision repository is available
            if self.vision_repository is not None:
                # Try loading from database first
                objectives = self.vision_repository.list_objectives()
                if objectives:
                    logger.info(f"Loaded {len(objectives)} objectives from database")
                    self._build_cache(objectives)
                    return
            else:
                logger.info("Vision repository not available - skipping database load")
            
            # Fall back to configuration file
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    objectives = self._parse_config(config)
                    
                    # Store in database for future use (only if repository is available)
                    if self.vision_repository is not None:
                        for obj in objectives:
                            self.vision_repository.create_objective(obj)
                    
                    self._build_cache(objectives)
                    logger.info(f"Loaded {len(objectives)} objectives from config")
            else:
                logger.info(f"Vision hierarchy config file not found at {self.config_path}")
                
        except Exception as e:
            logger.error(f"Error loading vision hierarchy: {e}")
            # Initialize with empty cache for graceful degradation
            self._vision_cache = {}
            self._hierarchy_cache = {}
    
    def _parse_config(self, config: Dict[str, Any]) -> List[VisionObjective]:
        """Parse vision configuration into objectives."""
        objectives = []
        
        def parse_objective(obj_data: Dict[str, Any], parent_id: Optional[UUID] = None) -> VisionObjective:
            metrics = []
            for metric_data in obj_data.get("metrics", []):
                metric = VisionMetric(
                    name=metric_data["name"],
                    current_value=metric_data.get("current_value", 0.0),
                    target_value=metric_data["target_value"],
                    unit=metric_data["unit"],
                    metric_type=MetricType(metric_data.get("type", "custom")),
                    baseline_value=metric_data.get("baseline_value", 0.0)
                )
                metrics.append(metric)
            
            objective = VisionObjective(
                id=UUID(obj_data["id"]) if "id" in obj_data else UUID(),
                title=obj_data["title"],
                description=obj_data.get("description", ""),
                level=VisionHierarchyLevel(obj_data.get("level", "project")),
                parent_id=parent_id,
                owner=obj_data.get("owner", ""),
                priority=obj_data.get("priority", 3),
                status=obj_data.get("status", "active"),
                metrics=metrics,
                tags=obj_data.get("tags", []),
                metadata=obj_data.get("metadata", {})
            )
            
            objectives.append(objective)
            
            # Recursively parse children
            for child_data in obj_data.get("children", []):
                parse_objective(child_data, objective.id)
            
            return objective
        
        # Parse top-level objectives
        for obj_data in config.get("objectives", []):
            parse_objective(obj_data)
        
        return objectives
    
    def _build_cache(self, objectives: List[VisionObjective]) -> None:
        """Build internal caches for efficient access."""
        self._vision_cache.clear()
        self._hierarchy_cache.clear()
        
        for obj in objectives:
            self._vision_cache[obj.id] = obj
            
            if obj.parent_id:
                if obj.parent_id not in self._hierarchy_cache:
                    self._hierarchy_cache[obj.parent_id] = []
                self._hierarchy_cache[obj.parent_id].append(obj.id)
    
    def is_enrichment_enabled(self) -> bool:
        """Check if vision enrichment is enabled."""
        return is_phase_enabled("vision_enrichment")
    
    def enrich_task(self, task: Task) -> Dict[str, Any]:
        """Enrich a task with vision alignment data.
        
        Args:
            task: The task to enrich
            
        Returns:
            Enriched task data including vision alignment
        """
        # Get task's basic data
        task_data = task.to_dict()
        
        # Skip enrichment if disabled
        if not self.is_enrichment_enabled():
            return task_data
        
        # Calculate vision alignments
        alignments = self._calculate_alignments(task)
        
        # Get relevant objectives
        relevant_objectives = self._get_relevant_objectives(alignments)
        
        # Generate insights
        insights = self._generate_insights(task, alignments, relevant_objectives)
        
        # Build enriched response
        vision_context = {
            "alignments": [alignment.to_dict() for alignment in alignments],
            "objectives": [obj.to_dict() for obj in relevant_objectives],
            "insights": [insight.to_dict() for insight in insights],
            "vision_contribution": self._calculate_contribution_summary(alignments, relevant_objectives),
            "recommended_objectives": self._recommend_objectives(task, alignments)
        }
        
        task_data["vision_context"] = vision_context
        return task_data
    
    def _calculate_alignments(self, task: Task) -> List[VisionAlignment]:
        """Calculate alignment scores between task and objectives."""
        alignments = []
        
        for objective_id, objective in self._vision_cache.items():
            if objective.status != "active":
                continue
            
            # Calculate alignment score based on multiple factors
            score, factors = self._calculate_alignment_score(task, objective)
            
            if score > 0.1:  # Only include meaningful alignments
                # Determine contribution type
                contribution_type = self._determine_contribution_type(task, objective, score)
                
                alignment = VisionAlignment(
                    task_id=task.id,
                    objective_id=objective_id,
                    alignment_score=score,
                    contribution_type=contribution_type,
                    confidence=self._calculate_confidence(factors),
                    rationale=self._generate_rationale(task, objective, factors),
                    factors=factors
                )
                alignments.append(alignment)
        
        # Sort by alignment score
        alignments.sort(key=lambda a: a.alignment_score, reverse=True)
        return alignments[:10]  # Return top 10 alignments
    
    def _calculate_alignment_score(
        self, 
        task: Task, 
        objective: VisionObjective
    ) -> Tuple[float, Dict[str, float]]:
        """Calculate detailed alignment score with contributing factors."""
        factors = {}
        
        # 1. Keyword matching (30% weight)
        task_text = f"{task.title} {task.description}".lower()
        objective_text = f"{objective.title} {objective.description}".lower()
        
        task_words = set(task_text.split())
        objective_words = set(objective_text.split())
        
        if objective_words:
            keyword_overlap = len(task_words & objective_words) / len(objective_words)
            factors["keyword_match"] = min(keyword_overlap * 2, 1.0) * 0.3
        else:
            factors["keyword_match"] = 0.0
        
        # 2. Tag matching (20% weight)
        task_tags = set(task.labels) if hasattr(task, 'labels') else set()
        objective_tags = set(objective.tags)
        
        if objective_tags:
            tag_overlap = len(task_tags & objective_tags) / len(objective_tags)
            factors["tag_match"] = tag_overlap * 0.2
        else:
            factors["tag_match"] = 0.0
        
        # 3. Priority alignment (15% weight)
        priority_diff = abs(task.priority_score() - (objective.priority / 5.0))
        factors["priority_alignment"] = (1.0 - priority_diff) * 0.15
        
        # 4. Status compatibility (15% weight)
        status_score = 0.0
        if task.status in ["todo", "in_progress"] and objective.status == "active":
            status_score = 1.0
        elif task.status == "done" and objective.overall_progress > 80:
            status_score = 0.7
        factors["status_compatibility"] = status_score * 0.15
        
        # 5. Hierarchical proximity (20% weight)
        # Tasks aligned with lower-level objectives score higher
        level_scores = {
            VisionHierarchyLevel.PROJECT: 1.0,
            VisionHierarchyLevel.MILESTONE: 0.9,
            VisionHierarchyLevel.TEAM: 0.7,
            VisionHierarchyLevel.DEPARTMENT: 0.5,
            VisionHierarchyLevel.ORGANIZATION: 0.3
        }
        factors["hierarchy_proximity"] = level_scores.get(objective.level, 0.5) * 0.2
        
        # Calculate total score
        total_score = sum(factors.values())
        return total_score, factors
    
    def _determine_contribution_type(
        self, 
        task: Task, 
        objective: VisionObjective,
        score: float
    ) -> ContributionType:
        """Determine how a task contributes to an objective."""
        # High alignment and matching status suggests direct contribution
        if score > 0.7 and task.status in ["in_progress", "done"]:
            return ContributionType.DIRECT
        
        # Completed tasks with moderate alignment are supporting
        if task.status == "done" and score > 0.4:
            return ContributionType.SUPPORTING
        
        # Tasks that unblock others are enabling
        if any(dep_id for dep_id in task.dependencies):
            return ContributionType.ENABLING
        
        # Early stage tasks with lower alignment are exploratory
        if task.status == "todo" and score < 0.5:
            return ContributionType.EXPLORATORY
        
        # Default to maintenance for ongoing work
        return ContributionType.MAINTENANCE
    
    def _calculate_confidence(self, factors: Dict[str, float]) -> float:
        """Calculate confidence in the alignment assessment."""
        # Higher confidence when multiple factors contribute
        non_zero_factors = sum(1 for v in factors.values() if v > 0.1)
        factor_diversity = non_zero_factors / len(factors) if factors else 0
        
        # Higher confidence when scores are not too extreme
        avg_score = sum(factors.values()) / len(factors) if factors else 0
        score_balance = 1.0 - abs(avg_score - 0.5)
        
        confidence = (factor_diversity * 0.6 + score_balance * 0.4)
        return min(max(confidence, 0.2), 0.95)
    
    def _generate_rationale(
        self, 
        task: Task, 
        objective: VisionObjective,
        factors: Dict[str, float]
    ) -> str:
        """Generate human-readable rationale for alignment."""
        top_factors = sorted(
            factors.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:3]
        
        rationales = []
        for factor_name, score in top_factors:
            if score > 0.1:
                if factor_name == "keyword_match":
                    rationales.append(f"strong keyword overlap ({score/0.3:.0%})")
                elif factor_name == "tag_match":
                    rationales.append(f"matching tags ({score/0.2:.0%})")
                elif factor_name == "priority_alignment":
                    rationales.append("similar priority levels")
                elif factor_name == "hierarchy_proximity":
                    rationales.append(f"{objective.level.value}-level objective")
        
        if rationales:
            return f"Task aligns due to {', '.join(rationales)}"
        else:
            return "Weak alignment based on general compatibility"
    
    def _get_relevant_objectives(
        self, 
        alignments: List[VisionAlignment]
    ) -> List[VisionObjective]:
        """Get objectives relevant to the given alignments."""
        relevant_objectives = []
        seen_ids = set()
        
        for alignment in alignments:
            if alignment.objective_id not in seen_ids:
                seen_ids.add(alignment.objective_id)
                if alignment.objective_id in self._vision_cache:
                    relevant_objectives.append(self._vision_cache[alignment.objective_id])
        
        return relevant_objectives
    
    def _generate_insights(
        self, 
        task: Task,
        alignments: List[VisionAlignment],
        objectives: List[VisionObjective]
    ) -> List[VisionInsight]:
        """Generate insights based on vision analysis."""
        insights = []
        
        # 1. Check for misalignment
        if not alignments or all(a.alignment_score < 0.3 for a in alignments):
            insight = VisionInsight(
                type="warning",
                title="Low Vision Alignment",
                description=f"Task '{task.title}' has weak alignment with organizational objectives",
                impact="medium",
                affected_tasks=[task.id],
                suggested_actions=[
                    "Review task scope and objectives",
                    "Consider linking to specific vision objectives",
                    "Add relevant tags or keywords"
                ]
            )
            insights.append(insight)
        
        # 2. Check for high-impact opportunities
        high_priority_objectives = [obj for obj in objectives if obj.priority >= 4]
        if high_priority_objectives and any(a.alignment_score > 0.6 for a in alignments):
            insight = VisionInsight(
                type="opportunity",
                title="High-Impact Task",
                description=f"Task contributes to {len(high_priority_objectives)} high-priority objectives",
                impact="high",
                affected_objectives=[obj.id for obj in high_priority_objectives],
                affected_tasks=[task.id],
                suggested_actions=[
                    "Prioritize this task for immediate attention",
                    "Allocate additional resources if needed",
                    "Track progress closely"
                ]
            )
            insights.append(insight)
        
        # 3. Check for at-risk objectives
        for objective in objectives:
            if objective.days_remaining and objective.days_remaining < 30:
                if objective.overall_progress < 70:
                    insight = VisionInsight(
                        type="warning",
                        title="Objective at Risk",
                        description=f"'{objective.title}' has only {objective.days_remaining} days remaining with {objective.overall_progress:.0f}% progress",
                        impact="high",
                        affected_objectives=[objective.id],
                        affected_tasks=[task.id],
                        suggested_actions=[
                            "Expedite related tasks",
                            "Review and adjust scope if needed",
                            "Consider additional resources"
                        ]
                    )
                    insights.append(insight)
        
        return insights
    
    def _calculate_contribution_summary(
        self,
        alignments: List[VisionAlignment],
        objectives: List[VisionObjective]
    ) -> Dict[str, Any]:
        """Calculate summary of task's contribution to vision."""
        if not alignments:
            return {
                "primary_contribution": None,
                "contribution_score": 0.0,
                "affected_levels": [],
                "total_objectives": 0
            }
        
        # Get primary alignment
        primary = alignments[0]
        primary_objective = next(
            (obj for obj in objectives if obj.id == primary.objective_id),
            None
        )
        
        # Calculate affected levels
        affected_levels = list(set(obj.level.value for obj in objectives))
        
        # Calculate weighted contribution score
        contribution_score = sum(
            a.alignment_score * a.confidence for a in alignments[:5]
        ) / min(len(alignments), 5)
        
        return {
            "primary_contribution": {
                "objective": primary_objective.title if primary_objective else "Unknown",
                "type": primary.contribution_type.value,
                "score": primary.alignment_score
            },
            "contribution_score": contribution_score,
            "affected_levels": affected_levels,
            "total_objectives": len(objectives)
        }
    
    def _recommend_objectives(
        self,
        task: Task,
        current_alignments: List[VisionAlignment]
    ) -> List[Dict[str, Any]]:
        """Recommend additional objectives the task could align with."""
        recommendations = []
        
        # Get IDs of currently aligned objectives
        aligned_ids = {a.objective_id for a in current_alignments}
        
        # Find objectives that could be aligned with minor changes
        for obj_id, objective in self._vision_cache.items():
            if obj_id in aligned_ids or objective.status != "active":
                continue
            
            # Calculate potential alignment
            score, factors = self._calculate_alignment_score(task, objective)
            
            # Recommend if score is moderate but not already aligned
            if 0.3 < score < 0.6:
                improvements = []
                if factors.get("keyword_match", 0) < 0.1:
                    improvements.append("Add relevant keywords to description")
                if factors.get("tag_match", 0) < 0.1:
                    improvements.append(f"Add tags: {', '.join(objective.tags[:3])}")
                
                if improvements:
                    recommendations.append({
                        "objective": objective.to_dict(),
                        "potential_score": score,
                        "improvements": improvements
                    })
        
        # Return top 3 recommendations
        recommendations.sort(key=lambda r: r["potential_score"], reverse=True)
        return recommendations[:3]
    
    def calculate_task_alignment(
        self, 
        task_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """Calculate and return vision alignment for a specific task."""
        if self.task_repository is None:
            logger.warning("Task repository not available - cannot calculate task alignment")
            return None
            
        task = self.task_repository.get_by_id(task_id)
        if not task:
            return None
        
        return self.enrich_task(task)
    
    def update_objective_metrics(
        self,
        objective_id: UUID,
        metric_updates: Dict[str, float]
    ) -> Optional[VisionObjective]:
        """Update metrics for a vision objective."""
        objective = self._vision_cache.get(objective_id)
        if not objective:
            return None
        
        # Create updated metrics
        updated_metrics = []
        for metric in objective.metrics:
            if metric.name in metric_updates:
                updated_metric = VisionMetric(
                    name=metric.name,
                    current_value=metric_updates[metric.name],
                    target_value=metric.target_value,
                    unit=metric.unit,
                    metric_type=metric.metric_type,
                    baseline_value=metric.baseline_value
                )
                updated_metrics.append(updated_metric)
            else:
                updated_metrics.append(metric)
        
        # Create updated objective
        updated_objective = VisionObjective(
            id=objective.id,
            title=objective.title,
            description=objective.description,
            level=objective.level,
            parent_id=objective.parent_id,
            owner=objective.owner,
            priority=objective.priority,
            status=objective.status,
            created_at=objective.created_at,
            due_date=objective.due_date,
            metrics=updated_metrics,
            tags=objective.tags,
            metadata=objective.metadata
        )
        
        # Update in repository and cache (only if repository is available)
        if self.vision_repository is not None:
            self.vision_repository.update_objective(updated_objective)
        else:
            logger.warning("Vision repository not available - metrics updated only in cache")
            
        self._vision_cache[objective_id] = updated_objective
        
        return updated_objective
    
    def get_vision_hierarchy(
        self,
        root_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """Get vision hierarchy starting from root or specific objective."""
        def build_hierarchy(obj_id: UUID) -> Dict[str, Any]:
            objective = self._vision_cache.get(obj_id)
            if not objective:
                return {}
            
            result = objective.to_dict()
            
            # Add children
            children = []
            for child_id in self._hierarchy_cache.get(obj_id, []):
                child_hierarchy = build_hierarchy(child_id)
                if child_hierarchy:
                    children.append(child_hierarchy)
            
            if children:
                result["children"] = children
            
            return result
        
        if root_id:
            return [build_hierarchy(root_id)]
        else:
            # Find all root objectives (no parent)
            roots = []
            for obj_id, objective in self._vision_cache.items():
                if not objective.parent_id:
                    roots.append(build_hierarchy(obj_id))
            return roots