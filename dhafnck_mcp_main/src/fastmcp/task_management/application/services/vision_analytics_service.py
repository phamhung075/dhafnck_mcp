"""Vision Analytics Service.

This service provides analytics and insights for vision objectives,
tracking progress, identifying trends, and generating dashboards.
"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Any
from uuid import UUID

from ...domain.entities.task import Task
from ...domain.value_objects.vision_objects import (
    VisionObjective, VisionAlignment, VisionDashboard, VisionInsight,
    VisionHierarchyLevel, ContributionType
)
from ...domain.repositories.task_repository import TaskRepository
# VisionRepository will be injected as dependency
from ....vision_orchestration.vision_enrichment_service import VisionEnrichmentService


logger = logging.getLogger(__name__)


class VisionAnalyticsService:
    """Service for analyzing vision progress and generating insights."""
    
    def __init__(
        self,
        task_repository=None,
        vision_repository=None,
        enrichment_service=None
    ):
        """Initialize the vision analytics service.
        
        Args:
            task_repository: Repository for task data access
            vision_repository: Repository for vision data access
            enrichment_service: Service for vision enrichment
        """
        self.task_repository = task_repository
        self.vision_repository = vision_repository
        self.enrichment_service = enrichment_service
    
    def generate_dashboard(
        self,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        time_range_days: int = 30
    ) -> VisionDashboard:
        """Generate a comprehensive vision dashboard.
        
        Args:
            user_id: Optional filter by user
            project_id: Optional filter by project
            time_range_days: Number of days to include in analysis
            
        Returns:
            Vision dashboard with aggregated metrics and insights
        """
        # Get all objectives
        objectives = self.vision_repository.list_objectives(
            user_id=user_id,
            project_id=project_id
        )
        
        if not objectives:
            return VisionDashboard()
        
        # Calculate basic metrics
        total_objectives = len(objectives)
        active_objectives = sum(1 for obj in objectives if obj.status == "active")
        completed_objectives = sum(1 for obj in objectives if obj.status == "completed")
        
        # Calculate overall progress
        progress_sum = sum(obj.overall_progress for obj in objectives if obj.status == "active")
        overall_progress = progress_sum / active_objectives if active_objectives else 0.0
        
        # Group by level and status
        objectives_by_level = defaultdict(int)
        objectives_by_status = defaultdict(int)
        
        for obj in objectives:
            objectives_by_level[obj.level.value] += 1
            objectives_by_status[obj.status] += 1
        
        # Find top performing objectives
        top_performing = self._find_top_performing_objectives(objectives, limit=5)
        
        # Find at-risk objectives
        at_risk = self._find_at_risk_objectives(objectives, limit=5)
        
        # Get recent completions
        recent_completions = self._get_recent_completions(
            objectives, 
            days=time_range_days,
            limit=5
        )
        
        # Generate insights
        insights = self._generate_dashboard_insights(
            objectives,
            user_id=user_id,
            project_id=project_id
        )
        
        # Calculate alignment summary
        alignment_summary = self._calculate_alignment_summary(
            user_id=user_id,
            project_id=project_id
        )
        
        return VisionDashboard(
            total_objectives=total_objectives,
            active_objectives=active_objectives,
            completed_objectives=completed_objectives,
            overall_progress=overall_progress,
            objectives_by_level=dict(objectives_by_level),
            objectives_by_status=dict(objectives_by_status),
            top_performing_objectives=top_performing,
            at_risk_objectives=at_risk,
            recent_completions=recent_completions,
            active_insights=insights,
            alignment_summary=alignment_summary
        )
    
    def _find_top_performing_objectives(
        self,
        objectives: List[VisionObjective],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Find top performing objectives based on progress rate."""
        performing_objectives = []
        
        for obj in objectives:
            if obj.status != "active" or not obj.created_at:
                continue
            
            # Calculate days since creation
            days_active = (datetime.now(timezone.utc) - obj.created_at).days or 1
            
            # Calculate progress rate (progress per day)
            progress_rate = obj.overall_progress / days_active
            
            # Calculate time to completion estimate
            if progress_rate > 0:
                days_to_complete = (100 - obj.overall_progress) / progress_rate
            else:
                days_to_complete = float('inf')
            
            performing_objectives.append({
                "objective": obj.to_dict(),
                "progress_rate": progress_rate,
                "days_active": days_active,
                "estimated_days_to_complete": days_to_complete,
                "on_track": obj.days_remaining and days_to_complete <= obj.days_remaining
            })
        
        # Sort by progress rate
        performing_objectives.sort(key=lambda x: x["progress_rate"], reverse=True)
        return performing_objectives[:limit]
    
    def _find_at_risk_objectives(
        self,
        objectives: List[VisionObjective],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Find objectives at risk of not meeting targets."""
        at_risk = []
        
        for obj in objectives:
            if obj.status != "active":
                continue
            
            risk_factors = []
            risk_score = 0.0
            
            # Check deadline risk
            if obj.days_remaining is not None:
                if obj.days_remaining < 7:
                    risk_factors.append("Deadline approaching (< 7 days)")
                    risk_score += 0.4
                elif obj.days_remaining < 30:
                    risk_factors.append("Deadline within 30 days")
                    risk_score += 0.2
                
                # Check progress vs. time remaining
                expected_progress = (1 - (obj.days_remaining / 90)) * 100  # Assume 90-day projects
                if obj.overall_progress < expected_progress - 20:
                    risk_factors.append("Behind schedule")
                    risk_score += 0.3
            
            # Check stalled progress
            if obj.metrics:
                stalled_metrics = sum(
                    1 for m in obj.metrics 
                    if m.last_updated < datetime.now(timezone.utc) - timedelta(days=14)
                )
                if stalled_metrics > len(obj.metrics) / 2:
                    risk_factors.append("Stalled progress (no updates in 14+ days)")
                    risk_score += 0.3
            
            # Check low progress on high priority
            if obj.priority >= 4 and obj.overall_progress < 50:
                risk_factors.append("High priority with low progress")
                risk_score += 0.2
            
            if risk_factors:
                at_risk.append({
                    "objective": obj.to_dict(),
                    "risk_score": min(risk_score, 1.0),
                    "risk_factors": risk_factors,
                    "recommended_actions": self._recommend_risk_mitigation(obj, risk_factors)
                })
        
        # Sort by risk score
        at_risk.sort(key=lambda x: x["risk_score"], reverse=True)
        return at_risk[:limit]
    
    def _recommend_risk_mitigation(
        self,
        objective: VisionObjective,
        risk_factors: List[str]
    ) -> List[str]:
        """Recommend actions to mitigate identified risks."""
        recommendations = []
        
        if "Deadline approaching" in " ".join(risk_factors):
            recommendations.append("Prioritize critical tasks immediately")
            recommendations.append("Consider scope reduction if necessary")
        
        if "Behind schedule" in " ".join(risk_factors):
            recommendations.append("Allocate additional resources")
            recommendations.append("Review and remove blockers")
        
        if "Stalled progress" in " ".join(risk_factors):
            recommendations.append("Schedule progress review meeting")
            recommendations.append("Identify and address bottlenecks")
        
        if "High priority with low progress" in " ".join(risk_factors):
            recommendations.append("Escalate to leadership")
            recommendations.append("Create detailed action plan")
        
        return recommendations
    
    def _get_recent_completions(
        self,
        objectives: List[VisionObjective],
        days: int = 30,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get recently completed objectives."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        recent = []
        
        for obj in objectives:
            if obj.status == "completed" and hasattr(obj, 'completed_at'):
                if obj.completed_at and obj.completed_at > cutoff_date:
                    completion_days = (obj.completed_at - obj.created_at).days
                    
                    recent.append({
                        "objective": obj.to_dict(),
                        "completed_at": obj.completed_at.isoformat(),
                        "completion_days": completion_days,
                        "metrics_achieved": len([m for m in obj.metrics if m.is_achieved])
                    })
        
        # Sort by completion date
        recent.sort(key=lambda x: x["completed_at"], reverse=True)
        return recent[:limit]
    
    def _generate_dashboard_insights(
        self,
        objectives: List[VisionObjective],
        user_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> List[VisionInsight]:
        """Generate insights for the dashboard."""
        insights = []
        
        # 1. Portfolio balance insight
        level_distribution = defaultdict(int)
        for obj in objectives:
            if obj.status == "active":
                level_distribution[obj.level] += 1
        
        if level_distribution:
            org_ratio = level_distribution[VisionHierarchyLevel.ORGANIZATION] / len(objectives)
            if org_ratio > 0.5:
                insight = VisionInsight(
                    type="recommendation",
                    title="Portfolio Imbalance",
                    description="Over 50% of objectives are organization-level. Consider more tactical objectives.",
                    impact="medium",
                    suggested_actions=[
                        "Break down organization objectives into team/project levels",
                        "Define more specific, actionable objectives"
                    ]
                )
                insights.append(insight)
        
        # 2. Resource allocation insight
        high_priority_struggling = [
            obj for obj in objectives
            if obj.status == "active" and obj.priority >= 4 and obj.overall_progress < 30
        ]
        
        if high_priority_struggling:
            insight = VisionInsight(
                type="warning",
                title="High Priority Objectives Need Attention",
                description=f"{len(high_priority_struggling)} high-priority objectives have < 30% progress",
                impact="high",
                affected_objectives=[obj.id for obj in high_priority_struggling],
                suggested_actions=[
                    "Review resource allocation",
                    "Consider pausing lower priority work",
                    "Schedule executive review"
                ]
            )
            insights.append(insight)
        
        # 3. Momentum insight
        active_with_good_progress = sum(
            1 for obj in objectives 
            if obj.status == "active" and obj.overall_progress > 70
        )
        
        if active_with_good_progress > len(objectives) * 0.3:
            insight = VisionInsight(
                type="opportunity",
                title="Strong Momentum Detected",
                description=f"{active_with_good_progress} objectives are over 70% complete",
                impact="high",
                suggested_actions=[
                    "Plan for next wave of objectives",
                    "Capture and share best practices",
                    "Consider stretch goals"
                ]
            )
            insights.append(insight)
        
        return insights
    
    def _calculate_alignment_summary(
        self,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calculate summary statistics for task-vision alignment."""
        # Get recent tasks
        tasks = self.task_repository.list_tasks(
            user_id=user_id,
            project_id=project_id,
            limit=100
        )
        
        if not tasks:
            return {
                "average_alignment": 0.0,
                "aligned_tasks": 0,
                "total_tasks": 0,
                "contribution_breakdown": {}
            }
        
        aligned_count = 0
        total_alignment_score = 0.0
        contribution_counts = defaultdict(int)
        
        for task in tasks:
            # Get alignments for this task
            enriched = self.enrichment_service.enrich_task(task)
            alignments = enriched.get("vision_context", {}).get("alignments", [])
            
            if alignments:
                aligned_count += 1
                # Use top alignment score
                total_alignment_score += alignments[0]["alignment_score"]
                contribution_counts[alignments[0]["contribution_type"]] += 1
        
        average_alignment = total_alignment_score / len(tasks) if tasks else 0.0
        
        return {
            "average_alignment": average_alignment,
            "aligned_tasks": aligned_count,
            "total_tasks": len(tasks),
            "alignment_percentage": (aligned_count / len(tasks) * 100) if tasks else 0,
            "contribution_breakdown": dict(contribution_counts)
        }
    
    def analyze_objective_trends(
        self,
        objective_id: UUID,
        days: int = 30
    ) -> Dict[str, Any]:
        """Analyze trends for a specific objective over time."""
        objective = self.vision_repository.get_objective(objective_id)
        if not objective:
            return {}
        
        # Get historical data (would need event store in real implementation)
        # For now, we'll simulate with current data
        
        # Calculate trend indicators
        current_progress = objective.overall_progress
        
        # Estimate required progress rate
        if objective.days_remaining and objective.days_remaining > 0:
            required_daily_progress = (100 - current_progress) / objective.days_remaining
        else:
            required_daily_progress = 0
        
        # Get aligned tasks
        aligned_tasks = self._get_aligned_tasks(objective_id)
        active_aligned_tasks = sum(
            1 for task in aligned_tasks 
            if task.status in ["in_progress", "review"]
        )
        
        return {
            "objective": objective.to_dict(),
            "trends": {
                "current_progress": current_progress,
                "required_daily_progress": required_daily_progress,
                "projected_completion": self._project_completion_date(
                    objective, 
                    required_daily_progress
                ),
                "health_status": self._calculate_health_status(objective)
            },
            "task_alignment": {
                "total_aligned_tasks": len(aligned_tasks),
                "active_aligned_tasks": active_aligned_tasks,
                "completed_aligned_tasks": sum(
                    1 for task in aligned_tasks 
                    if task.status == "done"
                )
            },
            "recommendations": self._generate_objective_recommendations(
                objective,
                aligned_tasks
            )
        }
    
    def _get_aligned_tasks(self, objective_id: UUID) -> List[Task]:
        """Get all tasks aligned with an objective."""
        # This would typically query an alignment table
        # For now, we'll check all tasks
        all_tasks = self.task_repository.list_tasks(limit=1000)
        aligned_tasks = []
        
        for task in all_tasks:
            enriched = self.enrichment_service.enrich_task(task)
            alignments = enriched.get("vision_context", {}).get("alignments", [])
            
            if any(a["objective_id"] == str(objective_id) for a in alignments):
                aligned_tasks.append(task)
        
        return aligned_tasks
    
    def _project_completion_date(
        self,
        objective: VisionObjective,
        daily_progress_rate: float
    ) -> Optional[str]:
        """Project completion date based on current progress rate."""
        if daily_progress_rate <= 0 or objective.overall_progress >= 100:
            return None
        
        days_to_complete = (100 - objective.overall_progress) / daily_progress_rate
        completion_date = datetime.now(timezone.utc) + timedelta(days=days_to_complete)
        
        return completion_date.isoformat()
    
    def _calculate_health_status(self, objective: VisionObjective) -> str:
        """Calculate health status of an objective."""
        if objective.status != "active":
            return objective.status
        
        # Check various health indicators
        health_score = 0.0
        
        # Progress vs. time
        if objective.days_remaining:
            time_elapsed_ratio = 1.0 - (objective.days_remaining / 90)  # Assume 90-day default
            if objective.overall_progress >= time_elapsed_ratio * 100:
                health_score += 0.4
            elif objective.overall_progress >= time_elapsed_ratio * 80:
                health_score += 0.2
        else:
            health_score += 0.2  # No deadline pressure
        
        # Metric achievement
        if objective.metrics:
            achieved_ratio = sum(1 for m in objective.metrics if m.is_achieved) / len(objective.metrics)
            health_score += achieved_ratio * 0.3
        
        # Recent activity
        if objective.metrics:
            recent_updates = sum(
                1 for m in objective.metrics 
                if m.last_updated > datetime.now(timezone.utc) - timedelta(days=7)
            )
            if recent_updates > len(objective.metrics) / 2:
                health_score += 0.3
        
        # Determine status
        if health_score >= 0.7:
            return "healthy"
        elif health_score >= 0.4:
            return "needs_attention"
        else:
            return "at_risk"
    
    def _generate_objective_recommendations(
        self,
        objective: VisionObjective,
        aligned_tasks: List[Task]
    ) -> List[str]:
        """Generate specific recommendations for an objective."""
        recommendations = []
        
        # Check task coverage
        if not aligned_tasks:
            recommendations.append("No tasks currently aligned - create tasks to drive progress")
        elif len(aligned_tasks) < 3:
            recommendations.append("Limited task coverage - consider breaking down the objective")
        
        # Check task distribution
        task_statuses = defaultdict(int)
        for task in aligned_tasks:
            task_statuses[task.status] += 1
        
        if task_statuses["todo"] > task_statuses["in_progress"] * 2:
            recommendations.append("Many tasks in backlog - prioritize and start execution")
        
        if task_statuses["blocked"] > 0:
            recommendations.append(f"{task_statuses['blocked']} tasks blocked - address impediments")
        
        # Check progress rate
        if objective.overall_progress < 20 and objective.days_remaining and objective.days_remaining < 30:
            recommendations.append("Low progress with approaching deadline - consider scope adjustment")
        
        # Check metric balance
        if objective.metrics:
            lagging_metrics = [m for m in objective.metrics if m.progress_percentage < 30]
            if lagging_metrics:
                recommendations.append(
                    f"Focus on lagging metrics: {', '.join(m.name for m in lagging_metrics[:3])}"
                )
        
        return recommendations