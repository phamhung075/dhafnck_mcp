# Vision Implementation Guide

## Overview

This guide provides step-by-step instructions for implementing vision integration in the dhafnck_mcp_main task management system. Follow these phases to transform your task management into a vision-driven strategic execution platform.

## Implementation Phases

### Phase 1: Core Vision Infrastructure (Week 1-2)

#### Step 1.1: Create Vision Value Objects

Create the fundamental value objects for vision components:

```python
# File: domain/value_objects/vision_objects.py

from dataclasses import dataclass
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum

class VisionLevel(Enum):
    ORGANIZATION = "organization"
    PROJECT = "project"
    BRANCH = "branch"
    TASK = "task"
    SUBTASK = "subtask"

@dataclass(frozen=True)
class VisionObjective:
    """Immutable value object for vision objectives"""
    id: str
    title: str
    description: str
    target_metric: str
    current_value: float
    target_value: float
    deadline: datetime
    
    def calculate_progress(self) -> float:
        if self.target_value == 0:
            return 0.0
        return min((self.current_value / self.target_value) * 100, 100.0)

@dataclass(frozen=True)
class VisionMetric:
    """Immutable value object for vision metrics"""
    name: str
    value: float
    unit: str
    threshold_good: float
    threshold_warning: float
    threshold_critical: float
    
    def get_status(self) -> str:
        if self.value >= self.threshold_good:
            return "good"
        elif self.value >= self.threshold_warning:
            return "warning"
        else:
            return "critical"

@dataclass(frozen=True)
class VisionAlignment:
    """Immutable value object for vision alignment scoring"""
    objective_alignment: float  # 0.0 to 1.0
    strategic_alignment: float  # 0.0 to 1.0
    value_alignment: float      # 0.0 to 1.0
    
    @property
    def overall_score(self) -> float:
        return (self.objective_alignment * 0.4 + 
                self.strategic_alignment * 0.3 + 
                self.value_alignment * 0.3)
    
    def is_aligned(self, threshold: float = 0.7) -> bool:
        return self.overall_score >= threshold
```

#### Step 1.2: Extend Domain Entities

Update existing domain entities to include vision components:

```python
# Update: domain/entities/project.py

from ..value_objects.vision_objects import VisionObjective, VisionAlignment

@dataclass
class ProjectVision:
    """Vision component for Project entity"""
    objectives: List[VisionObjective]
    target_audience: str
    key_features: List[str]
    unique_value_proposition: str
    competitive_advantages: List[str]
    success_metrics: List[VisionMetric]
    strategic_alignment_score: float
    innovation_priorities: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)

@dataclass
class Project:
    # ... existing fields ...
    
    # Add vision field
    vision: Optional[ProjectVision] = None
    
    def set_vision(self, vision: ProjectVision) -> None:
        """Set project vision with validation"""
        if not vision.objectives:
            raise ValueError("Project vision must have at least one objective")
        
        self.vision = vision
        self.updated_at = datetime.now(timezone.utc)
    
    def get_vision_alignment_score(self) -> float:
        """Get overall vision alignment score for the project"""
        if not self.vision:
            return 0.0
        return self.vision.strategic_alignment_score
```

```python
# Update: domain/entities/git_branch.py

@dataclass
class BranchVision:
    """Vision component for TaskTree (Branch) entity"""
    branch_objectives: List[str]
    branch_deliverables: List[str]
    alignment_with_project: float
    innovation_priorities: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)
    contributes_to_objectives: List[str] = field(default_factory=list)

@dataclass
class TaskTree:
    # ... existing fields ...
    
    # Add vision field
    vision: Optional[BranchVision] = None
    
    def set_branch_vision(self, vision: BranchVision) -> None:
        """Set branch vision with project alignment validation"""
        if vision.alignment_with_project < 0.7:
            raise ValueError("Branch vision must have at least 70% alignment with project")
        
        self.vision = vision
        self.updated_at = datetime.now()
```

```python
# Update: domain/entities/task.py

@dataclass
class TaskVisionAlignment:
    """Vision alignment for individual tasks"""
    contributes_to_objectives: List[str]
    business_value_score: float  # 0.0 to 10.0
    user_impact_score: float     # 0.0 to 10.0
    strategic_importance: Priority
    success_criteria: List[str]
    vision_notes: str = ""

@dataclass
class Task:
    # ... existing fields ...
    
    # Add vision alignment field
    vision_alignment: Optional[TaskVisionAlignment] = None
    
    def set_vision_alignment(self, alignment: TaskVisionAlignment) -> None:
        """Set task vision alignment"""
        if not alignment.contributes_to_objectives:
            raise ValueError("Task must contribute to at least one objective")
        
        self.vision_alignment = alignment
        self.updated_at = datetime.now(timezone.utc)
    
    def get_vision_priority_score(self) -> float:
        """Calculate priority score based on vision alignment"""
        if not self.vision_alignment:
            return 0.0
        
        return (self.vision_alignment.business_value_score * 0.4 +
                self.vision_alignment.user_impact_score * 0.3 +
                self.priority.to_numeric() * 0.3)
```

#### Step 1.3: Create Vision Repository Interface

```python
# File: domain/repositories/vision_repository.py

from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.project import ProjectVision
from ..entities.git_branch import BranchVision
from ..entities.task import TaskVisionAlignment

class VisionRepository(ABC):
    """Repository interface for vision persistence"""
    
    @abstractmethod
    async def save_project_vision(self, project_id: str, vision: ProjectVision) -> None:
        """Save or update project vision"""
        pass
    
    @abstractmethod
    async def get_project_vision(self, project_id: str) -> Optional[ProjectVision]:
        """Retrieve project vision"""
        pass
    
    @abstractmethod
    async def save_branch_vision(self, branch_id: str, vision: BranchVision) -> None:
        """Save or update branch vision"""
        pass
    
    @abstractmethod
    async def get_branch_vision(self, branch_id: str) -> Optional[BranchVision]:
        """Retrieve branch vision"""
        pass
    
    @abstractmethod
    async def save_task_vision_alignment(self, task_id: str, alignment: TaskVisionAlignment) -> None:
        """Save or update task vision alignment"""
        pass
    
    @abstractmethod
    async def get_task_vision_alignment(self, task_id: str) -> Optional[TaskVisionAlignment]:
        """Retrieve task vision alignment"""
        pass
    
    @abstractmethod
    async def get_vision_hierarchy(self, project_id: str) -> Dict:
        """Get complete vision hierarchy for a project"""
        pass
```

### Phase 2: Vision Management Services (Week 2-3)

#### Step 2.1: Create Vision Alignment Service

```python
# File: domain/services/vision_alignment_service.py

from typing import List, Optional
from ..value_objects.vision_objects import VisionAlignment, VisionObjective
from ..entities.project import Project, ProjectVision
from ..entities.git_branch import TaskTree, BranchVision
from ..entities.task import Task, TaskVisionAlignment

class VisionAlignmentService:
    """Domain service for calculating and validating vision alignment"""
    
    def calculate_branch_alignment(self, branch_vision: BranchVision, 
                                 project_vision: ProjectVision) -> VisionAlignment:
        """Calculate alignment between branch and project vision"""
        # Check objective alignment
        objective_alignment = self._calculate_objective_alignment(
            branch_vision.contributes_to_objectives,
            [obj.id for obj in project_vision.objectives]
        )
        
        # Check strategic alignment
        strategic_alignment = self._calculate_strategic_alignment(
            branch_vision.innovation_priorities,
            project_vision.innovation_priorities
        )
        
        # Check value alignment
        value_alignment = self._calculate_value_alignment(
            branch_vision.branch_deliverables,
            project_vision.key_features
        )
        
        return VisionAlignment(
            objective_alignment=objective_alignment,
            strategic_alignment=strategic_alignment,
            value_alignment=value_alignment
        )
    
    def calculate_task_alignment(self, task_alignment: TaskVisionAlignment,
                               branch_vision: BranchVision) -> VisionAlignment:
        """Calculate alignment between task and branch vision"""
        # Check objective contribution
        objective_alignment = self._calculate_objective_alignment(
            task_alignment.contributes_to_objectives,
            branch_vision.branch_objectives
        )
        
        # Strategic importance to alignment
        strategic_alignment = task_alignment.strategic_importance.to_numeric() / 5.0
        
        # Business value to value alignment
        value_alignment = task_alignment.business_value_score / 10.0
        
        return VisionAlignment(
            objective_alignment=objective_alignment,
            strategic_alignment=strategic_alignment,
            value_alignment=value_alignment
        )
    
    def validate_vision_hierarchy(self, project: Project) -> List[str]:
        """Validate entire vision hierarchy for consistency"""
        issues = []
        
        if not project.vision:
            issues.append(f"Project {project.name} lacks vision definition")
            return issues
        
        # Check each branch
        for branch_id, branch in project.git_branchs.items():
            if not branch.vision:
                issues.append(f"Branch {branch.name} lacks vision definition")
                continue
            
            # Validate branch alignment
            alignment = self.calculate_branch_alignment(branch.vision, project.vision)
            if not alignment.is_aligned():
                issues.append(f"Branch {branch.name} has low alignment: {alignment.overall_score:.2f}")
            
            # Check tasks in branch
            for task in branch.all_tasks.values():
                if not task.vision_alignment:
                    issues.append(f"Task {task.title} lacks vision alignment")
                else:
                    task_alignment = self.calculate_task_alignment(
                        task.vision_alignment, branch.vision
                    )
                    if not task_alignment.is_aligned(threshold=0.6):
                        issues.append(f"Task {task.title} has low alignment: {task_alignment.overall_score:.2f}")
        
        return issues
    
    def _calculate_objective_alignment(self, child_objectives: List[str], 
                                     parent_objectives: List[str]) -> float:
        """Calculate how well child objectives align with parent"""
        if not parent_objectives:
            return 0.0
        
        matched = sum(1 for obj in child_objectives if obj in parent_objectives)
        return matched / len(parent_objectives)
    
    def _calculate_strategic_alignment(self, child_priorities: List[str],
                                     parent_priorities: List[str]) -> float:
        """Calculate strategic priority alignment"""
        if not parent_priorities:
            return 1.0  # No priorities to align with
        
        matched = sum(1 for priority in child_priorities if priority in parent_priorities)
        return matched / max(len(child_priorities), 1)
    
    def _calculate_value_alignment(self, child_deliverables: List[str],
                                 parent_features: List[str]) -> float:
        """Calculate value/feature alignment"""
        if not parent_features:
            return 1.0
        
        # Simple keyword matching - could be enhanced with NLP
        match_score = 0
        for deliverable in child_deliverables:
            for feature in parent_features:
                if any(keyword in deliverable.lower() for keyword in feature.lower().split()):
                    match_score += 1
                    break
        
        return min(match_score / len(parent_features), 1.0)
```

#### Step 2.2: Create Vision Cascade Service

```python
# File: domain/services/vision_cascade_service.py

from typing import List, Dict, Optional
from ..entities.project import Project, ProjectVision
from ..entities.git_branch import TaskTree, BranchVision
from ..entities.task import Task, TaskVisionAlignment
from ..value_objects.priority import Priority

class VisionCascadeService:
    """Service for cascading vision down the hierarchy"""
    
    def cascade_project_vision_to_branch(self, project_vision: ProjectVision,
                                       branch_name: str) -> BranchVision:
        """Generate branch vision template from project vision"""
        # Select relevant objectives for this branch
        relevant_objectives = self._select_relevant_objectives(
            project_vision.objectives, branch_name
        )
        
        return BranchVision(
            branch_objectives=[obj.title for obj in relevant_objectives],
            branch_deliverables=[],  # To be defined by branch owner
            alignment_with_project=1.0,  # Starts fully aligned
            innovation_priorities=project_vision.innovation_priorities[:3],  # Top 3
            risk_factors=[],  # To be identified
            contributes_to_objectives=[obj.id for obj in relevant_objectives]
        )
    
    def cascade_branch_vision_to_task(self, branch_vision: BranchVision,
                                    task_title: str, task_description: str) -> TaskVisionAlignment:
        """Generate task vision alignment from branch vision"""
        # Analyze task to determine contribution
        contributing_objectives = self._analyze_task_contribution(
            task_title, task_description, branch_vision.branch_objectives
        )
        
        # Calculate initial scores based on keywords
        business_value = self._estimate_business_value(task_title, task_description)
        user_impact = self._estimate_user_impact(task_title, task_description)
        
        return TaskVisionAlignment(
            contributes_to_objectives=contributing_objectives,
            business_value_score=business_value,
            user_impact_score=user_impact,
            strategic_importance=self._determine_strategic_importance(business_value, user_impact),
            success_criteria=[],  # To be defined
            vision_notes=f"Auto-generated from branch vision"
        )
    
    def propagate_vision_updates(self, project: Project, updated_vision: ProjectVision) -> Dict[str, List[str]]:
        """Propagate vision updates down the hierarchy"""
        updates_needed = {
            "branches": [],
            "tasks": []
        }
        
        # Check each branch for needed updates
        for branch_id, branch in project.git_branchs.items():
            if branch.vision:
                # Check if branch vision needs updating
                current_alignment = self._calculate_alignment(branch.vision, project.vision)
                new_alignment = self._calculate_alignment(branch.vision, updated_vision)
                
                if new_alignment < current_alignment - 0.1:  # Significant decrease
                    updates_needed["branches"].append(branch.name)
            
            # Check tasks in branch
            for task in branch.all_tasks.values():
                if task.vision_alignment:
                    # Simple check - could be more sophisticated
                    if not any(obj in updated_vision.objectives 
                             for obj in task.vision_alignment.contributes_to_objectives):
                        updates_needed["tasks"].append(task.title)
        
        return updates_needed
    
    def _select_relevant_objectives(self, objectives: List[VisionObjective], 
                                  branch_name: str) -> List[VisionObjective]:
        """Select objectives relevant to a branch based on name/type"""
        # Simple keyword matching - could use ML/NLP for better selection
        relevant = []
        branch_keywords = branch_name.lower().split('_')
        
        for objective in objectives:
            obj_text = f"{objective.title} {objective.description}".lower()
            if any(keyword in obj_text for keyword in branch_keywords):
                relevant.append(objective)
        
        # If no matches, return top 3 objectives
        return relevant[:3] if relevant else objectives[:3]
    
    def _analyze_task_contribution(self, title: str, description: str, 
                                 branch_objectives: List[str]) -> List[str]:
        """Analyze which objectives a task contributes to"""
        contributing = []
        task_text = f"{title} {description}".lower()
        
        for objective in branch_objectives:
            obj_keywords = objective.lower().split()
            if any(keyword in task_text for keyword in obj_keywords if len(keyword) > 3):
                contributing.append(objective)
        
        # Default to first objective if no matches
        return contributing if contributing else branch_objectives[:1]
    
    def _estimate_business_value(self, title: str, description: str) -> float:
        """Estimate business value score based on keywords"""
        high_value_keywords = ["revenue", "customer", "efficiency", "cost", "performance", 
                             "security", "compliance", "scale", "automate"]
        
        text = f"{title} {description}".lower()
        matches = sum(1 for keyword in high_value_keywords if keyword in text)
        
        return min(5.0 + matches * 0.5, 10.0)
    
    def _estimate_user_impact(self, title: str, description: str) -> float:
        """Estimate user impact score based on keywords"""
        impact_keywords = ["user", "experience", "interface", "usability", "feature",
                          "improve", "enhance", "fix", "bug", "issue"]
        
        text = f"{title} {description}".lower()
        matches = sum(1 for keyword in impact_keywords if keyword in text)
        
        return min(5.0 + matches * 0.5, 10.0)
    
    def _determine_strategic_importance(self, business_value: float, user_impact: float) -> Priority:
        """Determine strategic importance based on scores"""
        combined_score = (business_value + user_impact) / 2
        
        if combined_score >= 9:
            return Priority.critical()
        elif combined_score >= 8:
            return Priority.urgent()
        elif combined_score >= 7:
            return Priority.high()
        elif combined_score >= 5:
            return Priority.medium()
        else:
            return Priority.low()
```

#### Step 2.3: Create Vision Metrics Service

```python
# File: domain/services/vision_metrics_service.py

from typing import List, Dict, Optional
from datetime import datetime, timedelta
from ..entities.project import Project
from ..value_objects.vision_objects import VisionMetric

class VisionMetricsService:
    """Service for tracking and calculating vision-related metrics"""
    
    def calculate_project_vision_health(self, project: Project) -> Dict[str, any]:
        """Calculate overall vision health for a project"""
        if not project.vision:
            return {"status": "undefined", "score": 0.0}
        
        health_metrics = {
            "alignment_score": self._calculate_alignment_score(project),
            "objective_progress": self._calculate_objective_progress(project),
            "coverage_score": self._calculate_coverage_score(project),
            "execution_score": self._calculate_execution_score(project)
        }
        
        overall_score = sum(health_metrics.values()) / len(health_metrics)
        
        return {
            "status": self._get_health_status(overall_score),
            "score": overall_score,
            "metrics": health_metrics,
            "recommendations": self._generate_recommendations(health_metrics)
        }
    
    def track_vision_progress(self, project: Project) -> Dict[str, any]:
        """Track progress towards vision objectives"""
        if not project.vision:
            return {"objectives": [], "overall_progress": 0.0}
        
        objective_progress = []
        for objective in project.vision.objectives:
            progress = objective.calculate_progress()
            days_remaining = (objective.deadline - datetime.now()).days
            
            objective_progress.append({
                "objective": objective.title,
                "progress": progress,
                "status": self._get_objective_status(progress, days_remaining),
                "days_remaining": days_remaining,
                "projected_completion": self._project_completion(objective, progress)
            })
        
        overall_progress = sum(obj["progress"] for obj in objective_progress) / len(objective_progress)
        
        return {
            "objectives": objective_progress,
            "overall_progress": overall_progress,
            "at_risk_objectives": [obj for obj in objective_progress if obj["status"] == "at_risk"]
        }
    
    def generate_vision_report(self, project: Project) -> Dict[str, any]:
        """Generate comprehensive vision report"""
        return {
            "project": project.name,
            "vision_health": self.calculate_project_vision_health(project),
            "progress": self.track_vision_progress(project),
            "alignment_analysis": self._analyze_alignment(project),
            "innovation_tracking": self._track_innovation(project),
            "risk_assessment": self._assess_vision_risks(project),
            "recommendations": self._generate_strategic_recommendations(project)
        }
    
    def _calculate_alignment_score(self, project: Project) -> float:
        """Calculate average alignment score across all branches"""
        if not project.git_branchs:
            return 0.0
        
        alignment_scores = []
        for branch in project.git_branchs.values():
            if branch.vision:
                alignment_scores.append(branch.vision.alignment_with_project)
        
        return sum(alignment_scores) / len(alignment_scores) if alignment_scores else 0.0
    
    def _calculate_objective_progress(self, project: Project) -> float:
        """Calculate average progress across all objectives"""
        if not project.vision:
            return 0.0
        
        progress_values = [obj.calculate_progress() for obj in project.vision.objectives]
        return sum(progress_values) / len(progress_values) if progress_values else 0.0
    
    def _calculate_coverage_score(self, project: Project) -> float:
        """Calculate how well tasks cover vision objectives"""
        if not project.vision:
            return 0.0
        
        total_objectives = len(project.vision.objectives)
        covered_objectives = set()
        
        for branch in project.git_branchs.values():
            for task in branch.all_tasks.values():
                if task.vision_alignment:
                    covered_objectives.update(task.vision_alignment.contributes_to_objectives)
        
        return len(covered_objectives) / total_objectives if total_objectives > 0 else 0.0
    
    def _calculate_execution_score(self, project: Project) -> float:
        """Calculate execution effectiveness"""
        total_tasks = 0
        vision_aligned_completed = 0
        
        for branch in project.git_branchs.values():
            for task in branch.all_tasks.values():
                if task.vision_alignment:
                    total_tasks += 1
                    if task.is_completed:
                        vision_aligned_completed += 1
        
        return vision_aligned_completed / total_tasks if total_tasks > 0 else 0.0
    
    def _get_health_status(self, score: float) -> str:
        """Get health status based on score"""
        if score >= 0.8:
            return "excellent"
        elif score >= 0.6:
            return "good"
        elif score >= 0.4:
            return "fair"
        else:
            return "poor"
    
    def _get_objective_status(self, progress: float, days_remaining: int) -> str:
        """Determine objective status based on progress and time"""
        if progress >= 100:
            return "completed"
        elif days_remaining < 0:
            return "overdue"
        elif progress < (100 - days_remaining):  # Simple linear expectation
            return "at_risk"
        else:
            return "on_track"
    
    def _project_completion(self, objective: VisionObjective, current_progress: float) -> Optional[datetime]:
        """Project completion date based on current progress rate"""
        if current_progress >= 100:
            return datetime.now()
        
        # Simple linear projection - could be enhanced with historical data
        days_elapsed = (datetime.now() - objective.created_at).days
        if days_elapsed == 0 or current_progress == 0:
            return None
        
        progress_per_day = current_progress / days_elapsed
        days_remaining = (100 - current_progress) / progress_per_day
        
        return datetime.now() + timedelta(days=int(days_remaining))
```

### Phase 3: Vision-Aware Features (Week 3-4)

#### Step 3.1: Implement Vision-Based Task Prioritization

```python
# File: application/services/vision_prioritization_service.py

from typing import List
from ...domain.entities.task import Task
from ...domain.entities.project import Project
from ...domain.services.vision_alignment_service import VisionAlignmentService

class VisionPrioritizationService:
    """Application service for vision-based task prioritization"""
    
    def __init__(self, vision_alignment_service: VisionAlignmentService):
        self.vision_alignment_service = vision_alignment_service
    
    def prioritize_tasks_by_vision(self, tasks: List[Task], project: Project) -> List[Task]:
        """Prioritize tasks based on vision alignment and strategic importance"""
        scored_tasks = []
        
        for task in tasks:
            score = self._calculate_vision_priority_score(task, project)
            scored_tasks.append((task, score))
        
        # Sort by score descending
        scored_tasks.sort(key=lambda x: x[1], reverse=True)
        
        return [task for task, _ in scored_tasks]
    
    def get_next_strategic_task(self, available_tasks: List[Task], project: Project) -> Optional[Task]:
        """Get the next task with highest strategic value"""
        prioritized = self.prioritize_tasks_by_vision(available_tasks, project)
        return prioritized[0] if prioritized else None
    
    def _calculate_vision_priority_score(self, task: Task, project: Project) -> float:
        """Calculate comprehensive vision priority score"""
        if not task.vision_alignment or not project.vision:
            return task.priority.to_numeric()  # Fallback to basic priority
        
        # Get vision scores
        vision_score = task.get_vision_priority_score()
        
        # Get alignment score
        branch = self._find_task_branch(task, project)
        if branch and branch.vision:
            alignment = self.vision_alignment_service.calculate_task_alignment(
                task.vision_alignment, branch.vision
            )
            alignment_score = alignment.overall_score
        else:
            alignment_score = 0.5  # Default medium alignment
        
        # Consider dependencies
        dependency_factor = self._calculate_dependency_factor(task, project)
        
        # Weighted combination
        return (vision_score * 0.5 + 
                alignment_score * 10 * 0.3 +  # Scale alignment to 0-10
                dependency_factor * 0.2)
    
    def _find_task_branch(self, task: Task, project: Project) -> Optional[TaskTree]:
        """Find which branch contains the task"""
        for branch in project.git_branchs.values():
            if branch.has_task(task.id.value):
                return branch
        return None
    
    def _calculate_dependency_factor(self, task: Task, project: Project) -> float:
        """Calculate priority boost for tasks that unblock others"""
        blocked_count = 0
        blocked_value = 0
        
        for branch in project.git_branchs.values():
            for other_task in branch.all_tasks.values():
                if task.id in other_task.dependencies:
                    blocked_count += 1
                    if other_task.vision_alignment:
                        blocked_value += other_task.vision_alignment.business_value_score
        
        # More blocked tasks = higher priority
        return min(5 + blocked_count * 0.5 + blocked_value * 0.1, 10)
```

#### Step 3.2: Create Vision Dashboard Components

```python
# File: application/services/vision_dashboard_service.py

from typing import Dict, List
from ...domain.entities.project import Project
from ...domain.services.vision_metrics_service import VisionMetricsService

class VisionDashboardService:
    """Application service for vision dashboard data"""
    
    def __init__(self, vision_metrics_service: VisionMetricsService):
        self.vision_metrics_service = vision_metrics_service
    
    def get_vision_overview(self, project: Project) -> Dict:
        """Get vision overview data for dashboard"""
        return {
            "project_name": project.name,
            "vision_defined": project.vision is not None,
            "vision_health": self.vision_metrics_service.calculate_project_vision_health(project),
            "objective_count": len(project.vision.objectives) if project.vision else 0,
            "coverage_percentage": self._calculate_vision_coverage(project),
            "alignment_summary": self._get_alignment_summary(project)
        }
    
    def get_objective_progress_data(self, project: Project) -> List[Dict]:
        """Get objective progress data for visualization"""
        if not project.vision:
            return []
        
        progress_data = []
        for objective in project.vision.objectives:
            progress_data.append({
                "id": objective.id,
                "title": objective.title,
                "progress": objective.calculate_progress(),
                "current_value": objective.current_value,
                "target_value": objective.target_value,
                "unit": objective.target_metric,
                "deadline": objective.deadline.isoformat(),
                "status": self._get_objective_status(objective)
            })
        
        return progress_data
    
    def get_strategic_alignment_matrix(self, project: Project) -> Dict:
        """Get strategic alignment data in matrix format"""
        matrix = {
            "branches": [],
            "objectives": []
        }
        
        if not project.vision:
            return matrix
        
        # Add objectives
        matrix["objectives"] = [obj.title for obj in project.vision.objectives]
        
        # Add branch alignment data
        for branch in project.git_branchs.values():
            branch_data = {
                "name": branch.name,
                "alignment_scores": []
            }
            
            if branch.vision:
                for objective in project.vision.objectives:
                    if objective.id in branch.vision.contributes_to_objectives:
                        # Calculate specific alignment
                        score = branch.vision.alignment_with_project
                    else:
                        score = 0.0
                    branch_data["alignment_scores"].append(score)
            else:
                branch_data["alignment_scores"] = [0.0] * len(matrix["objectives"])
            
            matrix["branches"].append(branch_data)
        
        return matrix
    
    def get_vision_insights(self, project: Project) -> List[Dict]:
        """Generate actionable insights from vision data"""
        insights = []
        
        # Check vision definition
        if not project.vision:
            insights.append({
                "type": "critical",
                "message": "No vision defined for project",
                "action": "Define project vision with clear objectives"
            })
            return insights
        
        # Check branch coverage
        branches_without_vision = [b.name for b in project.git_branchs.values() if not b.vision]
        if branches_without_vision:
            insights.append({
                "type": "warning",
                "message": f"{len(branches_without_vision)} branches lack vision definition",
                "action": f"Define vision for branches: {', '.join(branches_without_vision[:3])}"
            })
        
        # Check objective progress
        at_risk_objectives = []
        for objective in project.vision.objectives:
            if self._is_objective_at_risk(objective):
                at_risk_objectives.append(objective.title)
        
        if at_risk_objectives:
            insights.append({
                "type": "warning",
                "message": f"{len(at_risk_objectives)} objectives at risk",
                "action": f"Review and accelerate work on: {', '.join(at_risk_objectives[:2])}"
            })
        
        # Check alignment scores
        low_alignment_branches = []
        for branch in project.git_branchs.values():
            if branch.vision and branch.vision.alignment_with_project < 0.7:
                low_alignment_branches.append((branch.name, branch.vision.alignment_with_project))
        
        if low_alignment_branches:
            insights.append({
                "type": "info",
                "message": f"{len(low_alignment_branches)} branches have low alignment",
                "action": "Review and realign branch objectives with project vision"
            })
        
        return insights
    
    def _calculate_vision_coverage(self, project: Project) -> float:
        """Calculate percentage of work covered by vision"""
        total_tasks = sum(len(branch.all_tasks) for branch in project.git_branchs.values())
        vision_aligned_tasks = sum(
            sum(1 for task in branch.all_tasks.values() if task.vision_alignment)
            for branch in project.git_branchs.values()
        )
        
        return (vision_aligned_tasks / total_tasks * 100) if total_tasks > 0 else 0.0
    
    def _get_alignment_summary(self, project: Project) -> Dict:
        """Get summary of alignment across project"""
        high_alignment = 0
        medium_alignment = 0
        low_alignment = 0
        no_vision = 0
        
        for branch in project.git_branchs.values():
            if not branch.vision:
                no_vision += 1
            elif branch.vision.alignment_with_project >= 0.8:
                high_alignment += 1
            elif branch.vision.alignment_with_project >= 0.6:
                medium_alignment += 1
            else:
                low_alignment += 1
        
        return {
            "high": high_alignment,
            "medium": medium_alignment,
            "low": low_alignment,
            "undefined": no_vision
        }
    
    def _get_objective_status(self, objective: VisionObjective) -> str:
        """Get status of an objective"""
        progress = objective.calculate_progress()
        days_remaining = (objective.deadline - datetime.now()).days
        
        if progress >= 100:
            return "completed"
        elif days_remaining < 0:
            return "overdue"
        elif progress < (100 - days_remaining * 2):  # Rough heuristic
            return "at_risk"
        else:
            return "on_track"
    
    def _is_objective_at_risk(self, objective: VisionObjective) -> bool:
        """Check if objective is at risk of not being met"""
        return self._get_objective_status(objective) in ["at_risk", "overdue"]
```

### Phase 4: Integration and Testing (Week 4)

#### Step 4.1: Create Vision Integration Tests

```python
# File: tests/test_vision_integration.py

import pytest
from datetime import datetime, timedelta
from domain.entities.project import Project, ProjectVision
from domain.entities.git_branch import TaskTree, BranchVision
from domain.entities.task import Task, TaskVisionAlignment
from domain.value_objects.vision_objects import VisionObjective, VisionMetric
from domain.services.vision_alignment_service import VisionAlignmentService
from domain.services.vision_cascade_service import VisionCascadeService

class TestVisionIntegration:
    
    @pytest.fixture
    def sample_project_vision(self):
        return ProjectVision(
            objectives=[
                VisionObjective(
                    id="obj1",
                    title="Increase user engagement",
                    description="Improve user engagement metrics by 50%",
                    target_metric="engagement_rate",
                    current_value=40.0,
                    target_value=60.0,
                    deadline=datetime.now() + timedelta(days=90)
                ),
                VisionObjective(
                    id="obj2",
                    title="Reduce technical debt",
                    description="Reduce technical debt by 30%",
                    target_metric="debt_score",
                    current_value=100.0,
                    target_value=70.0,
                    deadline=datetime.now() + timedelta(days=180)
                )
            ],
            target_audience="Development teams",
            key_features=["Task automation", "AI assistance", "Vision tracking"],
            unique_value_proposition="AI-powered strategic task management",
            competitive_advantages=["AI integration", "Vision alignment"],
            success_metrics=[],
            strategic_alignment_score=1.0,
            innovation_priorities=["AI automation", "User experience", "Performance"]
        )
    
    def test_project_vision_creation(self, sample_project_vision):
        """Test creating project with vision"""
        project = Project.create("Test Project", "Test description")
        project.set_vision(sample_project_vision)
        
        assert project.vision is not None
        assert len(project.vision.objectives) == 2
        assert project.get_vision_alignment_score() == 1.0
    
    def test_vision_cascade_to_branch(self, sample_project_vision):
        """Test cascading vision from project to branch"""
        cascade_service = VisionCascadeService()
        
        branch_vision = cascade_service.cascade_project_vision_to_branch(
            sample_project_vision, "feature_user_engagement"
        )
        
        assert branch_vision is not None
        assert "Increase user engagement" in branch_vision.branch_objectives
        assert branch_vision.alignment_with_project == 1.0
        assert len(branch_vision.innovation_priorities) <= 3
    
    def test_vision_alignment_calculation(self, sample_project_vision):
        """Test vision alignment calculation"""
        alignment_service = VisionAlignmentService()
        
        branch_vision = BranchVision(
            branch_objectives=["Increase user engagement"],
            branch_deliverables=["New dashboard", "Analytics features"],
            alignment_with_project=0.9,
            contributes_to_objectives=["obj1"]
        )
        
        alignment = alignment_service.calculate_branch_alignment(
            branch_vision, sample_project_vision
        )
        
        assert alignment.overall_score > 0.5
        assert alignment.is_aligned()
    
    def test_task_vision_alignment(self):
        """Test task-level vision alignment"""
        task_alignment = TaskVisionAlignment(
            contributes_to_objectives=["Increase user engagement"],
            business_value_score=8.0,
            user_impact_score=9.0,
            strategic_importance=Priority.high(),
            success_criteria=["Dashboard loads in <2s", "User satisfaction >4/5"]
        )
        
        task = Task.create(
            TaskId.generate(),
            "Implement performance dashboard",
            "Create dashboard for performance metrics"
        )
        task.set_vision_alignment(task_alignment)
        
        assert task.vision_alignment is not None
        assert task.get_vision_priority_score() > 7.0
    
    def test_vision_hierarchy_validation(self, sample_project_vision):
        """Test complete vision hierarchy validation"""
        # Create project with vision
        project = Project.create("Test Project", "Description")
        project.set_vision(sample_project_vision)
        
        # Create branch with vision
        branch = project.create_git_branch("feature_branch", "Feature Branch", "Description")
        branch_vision = BranchVision(
            branch_objectives=["Increase user engagement"],
            branch_deliverables=["Dashboard"],
            alignment_with_project=0.8,
            contributes_to_objectives=["obj1"]
        )
        branch.set_branch_vision(branch_vision)
        
        # Create task with vision alignment
        task = Task.create(
            TaskId.generate(),
            "Build dashboard",
            "Build user dashboard"
        )
        task_alignment = TaskVisionAlignment(
            contributes_to_objectives=["Increase user engagement"],
            business_value_score=8.0,
            user_impact_score=7.0,
            strategic_importance=Priority.high(),
            success_criteria=["Dashboard complete"]
        )
        task.set_vision_alignment(task_alignment)
        branch.add_root_task(task)
        
        # Validate hierarchy
        alignment_service = VisionAlignmentService()
        issues = alignment_service.validate_vision_hierarchy(project)
        
        assert len(issues) == 0  # No validation issues
```

#### Step 4.2: Create Vision API Endpoints

```python
# File: api/vision_endpoints.py

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/vision", tags=["vision"])

# Request/Response Models
class VisionObjectiveRequest(BaseModel):
    title: str
    description: str
    target_metric: str
    current_value: float
    target_value: float
    deadline: datetime

class ProjectVisionRequest(BaseModel):
    objectives: List[VisionObjectiveRequest]
    target_audience: str
    key_features: List[str]
    unique_value_proposition: str
    competitive_advantages: List[str]
    innovation_priorities: List[str]

class VisionAlignmentRequest(BaseModel):
    contributes_to_objectives: List[str]
    business_value_score: float
    user_impact_score: float
    success_criteria: List[str]

# Endpoints
@router.post("/projects/{project_id}/vision")
async def set_project_vision(
    project_id: str, 
    vision_request: ProjectVisionRequest,
    vision_service: VisionApplicationService = Depends()
):
    """Set or update project vision"""
    try:
        await vision_service.set_project_vision(project_id, vision_request)
        return {"status": "success", "message": "Project vision updated"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/projects/{project_id}/vision")
async def get_project_vision(
    project_id: str,
    vision_service: VisionApplicationService = Depends()
):
    """Get project vision"""
    vision = await vision_service.get_project_vision(project_id)
    if not vision:
        raise HTTPException(status_code=404, detail="Vision not found")
    return vision

@router.post("/branches/{branch_id}/vision")
async def set_branch_vision(
    branch_id: str,
    vision_request: Dict,
    vision_service: VisionApplicationService = Depends()
):
    """Set or update branch vision"""
    try:
        await vision_service.set_branch_vision(branch_id, vision_request)
        return {"status": "success", "message": "Branch vision updated"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/tasks/{task_id}/vision-alignment")
async def set_task_vision_alignment(
    task_id: str,
    alignment_request: VisionAlignmentRequest,
    vision_service: VisionApplicationService = Depends()
):
    """Set task vision alignment"""
    try:
        await vision_service.set_task_vision_alignment(task_id, alignment_request)
        return {"status": "success", "message": "Task vision alignment updated"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/projects/{project_id}/vision-health")
async def get_vision_health(
    project_id: str,
    vision_metrics_service: VisionMetricsService = Depends()
):
    """Get project vision health metrics"""
    project = await get_project(project_id)  # Implement project retrieval
    return vision_metrics_service.calculate_project_vision_health(project)

@router.get("/projects/{project_id}/vision-dashboard")
async def get_vision_dashboard(
    project_id: str,
    dashboard_service: VisionDashboardService = Depends()
):
    """Get vision dashboard data"""
    project = await get_project(project_id)
    return {
        "overview": dashboard_service.get_vision_overview(project),
        "objectives": dashboard_service.get_objective_progress_data(project),
        "alignment_matrix": dashboard_service.get_strategic_alignment_matrix(project),
        "insights": dashboard_service.get_vision_insights(project)
    }

@router.post("/projects/{project_id}/vision-cascade")
async def cascade_vision(
    project_id: str,
    cascade_service: VisionCascadeService = Depends()
):
    """Cascade project vision to all branches"""
    project = await get_project(project_id)
    results = []
    
    for branch_id, branch in project.git_branchs.items():
        if not branch.vision:
            branch_vision = cascade_service.cascade_project_vision_to_branch(
                project.vision, branch.name
            )
            # Save branch vision
            results.append({
                "branch": branch.name,
                "status": "vision_created"
            })
    
    return {"cascaded_to": results}
```

## Migration Strategy

### Step 1: Database Migration

```sql
-- Add vision tables
CREATE TABLE project_visions (
    project_id VARCHAR(255) PRIMARY KEY,
    objectives JSONB NOT NULL,
    target_audience TEXT,
    key_features JSONB,
    unique_value_proposition TEXT,
    competitive_advantages JSONB,
    success_metrics JSONB,
    strategic_alignment_score FLOAT,
    innovation_priorities JSONB,
    risk_factors JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE branch_visions (
    branch_id VARCHAR(255) PRIMARY KEY,
    branch_objectives JSONB,
    branch_deliverables JSONB,
    alignment_with_project FLOAT,
    innovation_priorities JSONB,
    risk_factors JSONB,
    contributes_to_objectives JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE task_vision_alignments (
    task_id VARCHAR(255) PRIMARY KEY,
    contributes_to_objectives JSONB,
    business_value_score FLOAT,
    user_impact_score FLOAT,
    strategic_importance VARCHAR(50),
    success_criteria JSONB,
    vision_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add indexes
CREATE INDEX idx_project_visions_updated ON project_visions(updated_at);
CREATE INDEX idx_branch_visions_alignment ON branch_visions(alignment_with_project);
CREATE INDEX idx_task_alignments_importance ON task_vision_alignments(strategic_importance);
```

### Step 2: Data Migration Script

```python
# File: migrations/add_vision_support.py

async def migrate_existing_data():
    """Add default vision data to existing projects"""
    
    # Get all projects
    projects = await project_repository.get_all()
    
    for project in projects:
        # Create default project vision
        default_vision = ProjectVision(
            objectives=[
                VisionObjective(
                    id=f"{project.id}_obj_1",
                    title="Complete project successfully",
                    description="Deliver all project requirements",
                    target_metric="completion_percentage",
                    current_value=0.0,
                    target_value=100.0,
                    deadline=datetime.now() + timedelta(days=90)
                )
            ],
            target_audience="Project stakeholders",
            key_features=["Project deliverables"],
            unique_value_proposition="Successful project delivery",
            competitive_advantages=[],
            success_metrics=[],
            strategic_alignment_score=1.0
        )
        
        await vision_repository.save_project_vision(project.id, default_vision)
        
        # Create default branch visions
        for branch_id, branch in project.git_branchs.items():
            branch_vision = BranchVision(
                branch_objectives=[f"Complete {branch.name}"],
                branch_deliverables=[],
                alignment_with_project=1.0,
                contributes_to_objectives=[f"{project.id}_obj_1"]
            )
            
            await vision_repository.save_branch_vision(branch_id, branch_vision)
```

## Rollout Plan

### Week 1: Development Environment
1. Deploy vision infrastructure to dev
2. Run migration scripts
3. Test with sample projects
4. Gather developer feedback

### Week 2: Staging Environment
1. Deploy to staging
2. Run integration tests
3. Performance testing
4. Security review

### Week 3: Production Pilot
1. Enable for select projects
2. Monitor performance
3. Gather user feedback
4. Refine based on usage

### Week 4: Full Production
1. Enable for all projects
2. User training sessions
3. Documentation updates
4. Monitor adoption metrics

## Success Metrics

1. **Adoption Metrics**
   - % of projects with defined vision
   - % of tasks with vision alignment
   - Average alignment scores

2. **Impact Metrics**
   - Task completion rate improvement
   - Strategic objective achievement
   - User satisfaction scores

3. **Quality Metrics**
   - Vision consistency scores
   - Alignment validation pass rate
   - Vision update frequency