# Vision Domain Models

## Overview

This document provides detailed specifications for the domain models that support vision integration in the task management system. These models follow Domain-Driven Design (DDD) principles and maintain clear boundaries between domain logic and infrastructure concerns.

## Core Domain Models

### 1. Vision Value Objects

Value objects are immutable and represent concepts without identity.

#### VisionObjective

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass(frozen=True)
class VisionObjective:
    """
    Represents a measurable objective within a vision.
    Immutable value object ensuring objective integrity.
    """
    id: str
    title: str
    description: str
    target_metric: str
    current_value: float
    target_value: float
    deadline: datetime
    measurement_method: str
    created_at: datetime
    
    def __post_init__(self):
        """Validate objective data"""
        if not self.title:
            raise ValueError("Objective title cannot be empty")
        if self.current_value < 0 or self.target_value < 0:
            raise ValueError("Objective values cannot be negative")
        if self.deadline <= self.created_at:
            raise ValueError("Deadline must be after creation date")
    
    def calculate_progress(self) -> float:
        """Calculate progress percentage towards objective"""
        if self.target_value == self.current_value:
            return 0.0 if self.target_value == 0 else 100.0
        
        if self.target_value == 0:
            return 0.0
        
        progress = (self.current_value / self.target_value) * 100
        return min(max(progress, 0.0), 100.0)
    
    def days_remaining(self) -> int:
        """Calculate days until deadline"""
        return max((self.deadline - datetime.now()).days, 0)
    
    def is_overdue(self) -> bool:
        """Check if objective is past deadline"""
        return datetime.now() > self.deadline
    
    def is_at_risk(self) -> bool:
        """Determine if objective is at risk of not being met"""
        if self.is_overdue() and self.calculate_progress() < 100:
            return True
        
        # Simple linear projection
        days_total = (self.deadline - self.created_at).days
        days_elapsed = (datetime.now() - self.created_at).days
        
        if days_total <= 0 or days_elapsed <= 0:
            return False
        
        expected_progress = (days_elapsed / days_total) * 100
        actual_progress = self.calculate_progress()
        
        return actual_progress < (expected_progress * 0.8)  # 20% buffer
```

#### VisionMetric

```python
from enum import Enum

class MetricType(Enum):
    PERCENTAGE = "percentage"
    NUMBER = "number"
    CURRENCY = "currency"
    TIME = "time"
    RATIO = "ratio"

class MetricTrend(Enum):
    HIGHER_BETTER = "higher_better"
    LOWER_BETTER = "lower_better"
    TARGET_RANGE = "target_range"

@dataclass(frozen=True)
class VisionMetric:
    """
    Represents a key performance indicator for vision tracking.
    """
    id: str
    name: str
    description: str
    current_value: float
    target_value: float
    unit: str
    metric_type: MetricType
    trend_direction: MetricTrend
    
    # Thresholds
    threshold_critical: float
    threshold_warning: float
    threshold_good: float
    threshold_excellent: float
    
    # Metadata
    data_source: str
    measurement_frequency: str  # Daily, Weekly, Monthly
    last_updated: datetime
    
    def get_status(self) -> str:
        """Get current metric status based on thresholds"""
        if self.trend_direction == MetricTrend.HIGHER_BETTER:
            if self.current_value >= self.threshold_excellent:
                return "excellent"
            elif self.current_value >= self.threshold_good:
                return "good"
            elif self.current_value >= self.threshold_warning:
                return "warning"
            else:
                return "critical"
        elif self.trend_direction == MetricTrend.LOWER_BETTER:
            if self.current_value <= self.threshold_excellent:
                return "excellent"
            elif self.current_value <= self.threshold_good:
                return "good"
            elif self.current_value <= self.threshold_warning:
                return "warning"
            else:
                return "critical"
        else:  # TARGET_RANGE
            distance_from_target = abs(self.current_value - self.target_value)
            target_range = abs(self.threshold_good - self.target_value)
            
            if distance_from_target <= target_range * 0.1:
                return "excellent"
            elif distance_from_target <= target_range:
                return "good"
            elif distance_from_target <= target_range * 1.5:
                return "warning"
            else:
                return "critical"
    
    def format_value(self) -> str:
        """Format metric value for display"""
        if self.metric_type == MetricType.PERCENTAGE:
            return f"{self.current_value:.1f}%"
        elif self.metric_type == MetricType.CURRENCY:
            return f"${self.current_value:,.2f}"
        elif self.metric_type == MetricType.TIME:
            return f"{self.current_value:.1f} {self.unit}"
        elif self.metric_type == MetricType.RATIO:
            return f"{self.current_value:.2f}:1"
        else:
            return f"{self.current_value:,.1f} {self.unit}"
```

#### VisionAlignment

```python
@dataclass(frozen=True)
class VisionAlignment:
    """
    Represents alignment between vision levels.
    Used to measure how well child visions align with parent visions.
    """
    objective_alignment: float  # 0.0 to 1.0
    strategic_alignment: float  # 0.0 to 1.0
    value_alignment: float      # 0.0 to 1.0
    innovation_alignment: float = 0.8  # Default high alignment
    risk_alignment: float = 0.8        # Default high alignment
    
    def __post_init__(self):
        """Validate alignment values"""
        for field_name, field_value in [
            ("objective_alignment", self.objective_alignment),
            ("strategic_alignment", self.strategic_alignment),
            ("value_alignment", self.value_alignment),
            ("innovation_alignment", self.innovation_alignment),
            ("risk_alignment", self.risk_alignment)
        ]:
            if not 0.0 <= field_value <= 1.0:
                raise ValueError(f"{field_name} must be between 0.0 and 1.0")
    
    @property
    def overall_score(self) -> float:
        """Calculate weighted overall alignment score"""
        weights = {
            "objective": 0.35,
            "strategic": 0.25,
            "value": 0.20,
            "innovation": 0.10,
            "risk": 0.10
        }
        
        score = (
            self.objective_alignment * weights["objective"] +
            self.strategic_alignment * weights["strategic"] +
            self.value_alignment * weights["value"] +
            self.innovation_alignment * weights["innovation"] +
            self.risk_alignment * weights["risk"]
        )
        
        return round(score, 3)
    
    def is_aligned(self, threshold: float = 0.7) -> bool:
        """Check if alignment meets minimum threshold"""
        return self.overall_score >= threshold
    
    def get_alignment_level(self) -> str:
        """Get human-readable alignment level"""
        score = self.overall_score
        if score >= 0.9:
            return "excellent"
        elif score >= 0.8:
            return "strong"
        elif score >= 0.7:
            return "good"
        elif score >= 0.6:
            return "moderate"
        elif score >= 0.5:
            return "weak"
        else:
            return "poor"
    
    def get_improvement_areas(self) -> List[str]:
        """Identify areas needing alignment improvement"""
        areas = []
        threshold = 0.7
        
        if self.objective_alignment < threshold:
            areas.append("objective alignment")
        if self.strategic_alignment < threshold:
            areas.append("strategic alignment")
        if self.value_alignment < threshold:
            areas.append("value proposition alignment")
        if self.innovation_alignment < threshold:
            areas.append("innovation priority alignment")
        if self.risk_alignment < threshold:
            areas.append("risk assessment alignment")
        
        return areas
```

### 2. Vision Entities

Entities have identity and can change over time while maintaining that identity.

#### ProjectVision

```python
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime
import uuid

@dataclass
class ProjectVision:
    """
    Vision entity for projects.
    Represents the strategic vision and objectives for a project.
    """
    # Identity
    project_id: str
    version: int = 1
    
    # Core Vision Components
    objectives: List[VisionObjective]
    target_audience: str
    key_features: List[str]
    unique_value_proposition: str
    competitive_advantages: List[str]
    
    # Metrics and Measurement
    success_metrics: List[VisionMetric]
    kpis: Dict[str, VisionMetric] = field(default_factory=dict)
    
    # Strategic Elements
    strategic_alignment_score: float
    innovation_priorities: List[str] = field(default_factory=list)
    growth_strategy: Optional['GrowthStrategy'] = None
    
    # Risk Management
    risk_factors: List['RiskFactor'] = field(default_factory=list)
    risk_mitigation_strategies: List[str] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: str = "system"
    approved_by: Optional[str] = None
    approval_date: Optional[datetime] = None
    
    # Domain Events
    _events: List['VisionEvent'] = field(default_factory=list, init=False)
    
    def update_objective(self, objective_id: str, current_value: float) -> None:
        """Update progress on a specific objective"""
        for i, obj in enumerate(self.objectives):
            if obj.id == objective_id:
                # Create new objective with updated value (immutability)
                updated_obj = VisionObjective(
                    id=obj.id,
                    title=obj.title,
                    description=obj.description,
                    target_metric=obj.target_metric,
                    current_value=current_value,
                    target_value=obj.target_value,
                    deadline=obj.deadline,
                    measurement_method=obj.measurement_method,
                    created_at=obj.created_at
                )
                self.objectives[i] = updated_obj
                self.updated_at = datetime.now()
                
                # Raise domain event
                self._events.append(ObjectiveUpdatedEvent(
                    project_id=self.project_id,
                    objective_id=objective_id,
                    old_value=obj.current_value,
                    new_value=current_value,
                    timestamp=self.updated_at
                ))
                break
    
    def add_objective(self, objective: VisionObjective) -> None:
        """Add a new objective to the vision"""
        if any(obj.id == objective.id for obj in self.objectives):
            raise ValueError(f"Objective with id {objective.id} already exists")
        
        self.objectives.append(objective)
        self.updated_at = datetime.now()
        self.version += 1
        
        self._events.append(ObjectiveAddedEvent(
            project_id=self.project_id,
            objective=objective,
            timestamp=self.updated_at
        ))
    
    def calculate_overall_progress(self) -> float:
        """Calculate overall vision progress"""
        if not self.objectives:
            return 0.0
        
        total_progress = sum(obj.calculate_progress() for obj in self.objectives)
        return total_progress / len(self.objectives)
    
    def get_at_risk_objectives(self) -> List[VisionObjective]:
        """Get objectives that are at risk"""
        return [obj for obj in self.objectives if obj.is_at_risk()]
    
    def validate(self) -> List[str]:
        """Validate vision completeness and consistency"""
        issues = []
        
        if not self.objectives:
            issues.append("Vision must have at least one objective")
        
        if not self.target_audience:
            issues.append("Target audience must be defined")
        
        if not self.unique_value_proposition:
            issues.append("Unique value proposition must be defined")
        
        if not 0.0 <= self.strategic_alignment_score <= 1.0:
            issues.append("Strategic alignment score must be between 0 and 1")
        
        # Check for duplicate objective IDs
        objective_ids = [obj.id for obj in self.objectives]
        if len(objective_ids) != len(set(objective_ids)):
            issues.append("Duplicate objective IDs found")
        
        return issues
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            "project_id": self.project_id,
            "version": self.version,
            "objectives": [
                {
                    "id": obj.id,
                    "title": obj.title,
                    "description": obj.description,
                    "progress": obj.calculate_progress(),
                    "deadline": obj.deadline.isoformat()
                }
                for obj in self.objectives
            ],
            "target_audience": self.target_audience,
            "key_features": self.key_features,
            "unique_value_proposition": self.unique_value_proposition,
            "competitive_advantages": self.competitive_advantages,
            "strategic_alignment_score": self.strategic_alignment_score,
            "innovation_priorities": self.innovation_priorities,
            "overall_progress": self.calculate_overall_progress(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
```

#### BranchVision

```python
@dataclass
class BranchVision:
    """
    Vision entity for git branches (task trees).
    Represents how a branch contributes to project vision.
    """
    # Identity
    branch_id: str
    project_id: str
    version: int = 1
    
    # Branch-specific Objectives
    branch_objectives: List[str]
    branch_deliverables: List[str]
    expected_outcomes: List['ExpectedOutcome']
    
    # Alignment
    alignment_with_project: float  # 0.0 to 1.0
    contributes_to_objectives: List[str]  # Project objective IDs
    
    # Innovation and Technical Approach
    innovation_priorities: List[str]
    technical_approach: str
    technology_stack: List[str] = field(default_factory=list)
    
    # Risk and Constraints
    risk_factors: List['RiskFactor'] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    
    # Success Criteria
    acceptance_criteria: List[str]
    quality_standards: List['QualityStandard']
    definition_of_done: List[str] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: str = "system"
    
    # Domain Events
    _events: List['VisionEvent'] = field(default_factory=list, init=False)
    
    def update_alignment(self, new_alignment: float) -> None:
        """Update alignment score with validation"""
        if not 0.0 <= new_alignment <= 1.0:
            raise ValueError("Alignment must be between 0.0 and 1.0")
        
        old_alignment = self.alignment_with_project
        self.alignment_with_project = new_alignment
        self.updated_at = datetime.now()
        
        self._events.append(BranchAlignmentUpdatedEvent(
            branch_id=self.branch_id,
            old_alignment=old_alignment,
            new_alignment=new_alignment,
            timestamp=self.updated_at
        ))
    
    def add_deliverable(self, deliverable: str) -> None:
        """Add a new deliverable to the branch"""
        if deliverable not in self.branch_deliverables:
            self.branch_deliverables.append(deliverable)
            self.updated_at = datetime.now()
            self.version += 1
    
    def complete_deliverable(self, deliverable: str) -> None:
        """Mark a deliverable as completed"""
        # This would typically update a more complex deliverable object
        # For now, we'll just track it in events
        self._events.append(DeliverableCompletedEvent(
            branch_id=self.branch_id,
            deliverable=deliverable,
            timestamp=datetime.now()
        ))
    
    def validate_against_project(self, project_vision: ProjectVision) -> List[str]:
        """Validate branch vision against project vision"""
        issues = []
        
        # Check objective contribution
        project_obj_ids = [obj.id for obj in project_vision.objectives]
        for obj_id in self.contributes_to_objectives:
            if obj_id not in project_obj_ids:
                issues.append(f"Contributing to non-existent objective: {obj_id}")
        
        if not self.contributes_to_objectives:
            issues.append("Branch must contribute to at least one project objective")
        
        # Check innovation alignment
        for priority in self.innovation_priorities:
            if priority not in project_vision.innovation_priorities:
                issues.append(f"Innovation priority '{priority}' not in project priorities")
        
        # Check minimum alignment
        if self.alignment_with_project < 0.5:
            issues.append("Branch alignment with project is below minimum threshold (0.5)")
        
        return issues
```

#### TaskVisionAlignment

```python
@dataclass
class TaskVisionAlignment:
    """
    Vision alignment entity for individual tasks.
    Represents how a task contributes to branch and project vision.
    """
    # Identity
    task_id: str
    branch_id: str
    version: int = 1
    
    # Contribution Mapping
    contributes_to_objectives: List[str]  # Branch objective names
    expected_impact: str
    
    # Value Scoring
    business_value_score: float  # 0.0 to 10.0
    user_impact_score: float     # 0.0 to 10.0
    technical_debt_impact: float # -10.0 to 10.0 (negative reduces debt)
    innovation_score: float      # 0.0 to 10.0
    
    # Strategic Importance
    strategic_importance: Priority
    urgency_factor: float = 1.0  # Multiplier for time-sensitive tasks
    
    # Success Definition
    success_criteria: List[str]
    acceptance_criteria: List[str]
    measurable_outcomes: List['MeasurableOutcome']
    
    # Context and Rationale
    vision_notes: str
    strategic_rationale: str
    stakeholder_value: Dict[str, str] = field(default_factory=dict)
    
    # Innovation and Risk
    innovation_opportunities: List[str] = field(default_factory=list)
    identified_risks: List[str] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: str = "system"
    validated_by: Optional[str] = None
    validation_date: Optional[datetime] = None
    
    def calculate_priority_score(self) -> float:
        """Calculate comprehensive priority score"""
        # Base scores
        base_score = (
            self.business_value_score * 0.3 +
            self.user_impact_score * 0.25 +
            self.innovation_score * 0.15 +
            max(self.technical_debt_impact, 0) * 0.1  # Only positive impact
        )
        
        # Strategic importance modifier
        importance_modifiers = {
            Priority.critical(): 2.0,
            Priority.urgent(): 1.5,
            Priority.high(): 1.2,
            Priority.medium(): 1.0,
            Priority.low(): 0.8
        }
        
        strategic_modifier = importance_modifiers.get(
            self.strategic_importance, 1.0
        )
        
        # Apply modifiers
        final_score = base_score * strategic_modifier * self.urgency_factor
        
        # Normalize to 0-10 scale
        return min(max(final_score, 0.0), 10.0)
    
    def update_scores(self, business_value: Optional[float] = None,
                     user_impact: Optional[float] = None,
                     innovation: Optional[float] = None) -> None:
        """Update individual scores with validation"""
        if business_value is not None:
            if not 0.0 <= business_value <= 10.0:
                raise ValueError("Business value must be between 0 and 10")
            self.business_value_score = business_value
        
        if user_impact is not None:
            if not 0.0 <= user_impact <= 10.0:
                raise ValueError("User impact must be between 0 and 10")
            self.user_impact_score = user_impact
        
        if innovation is not None:
            if not 0.0 <= innovation <= 10.0:
                raise ValueError("Innovation score must be between 0 and 10")
            self.innovation_score = innovation
        
        self.updated_at = datetime.now()
        self.version += 1
    
    def add_measurable_outcome(self, outcome: 'MeasurableOutcome') -> None:
        """Add a measurable outcome to track"""
        self.measurable_outcomes.append(outcome)
        self.updated_at = datetime.now()
    
    def validate(self) -> List[str]:
        """Validate task vision alignment"""
        issues = []
        
        if not self.contributes_to_objectives:
            issues.append("Task must contribute to at least one objective")
        
        if not self.success_criteria:
            issues.append("Task must have at least one success criterion")
        
        if not self.strategic_rationale:
            issues.append("Strategic rationale must be provided")
        
        # Validate score ranges
        if not 0.0 <= self.business_value_score <= 10.0:
            issues.append("Business value score out of range")
        
        if not 0.0 <= self.user_impact_score <= 10.0:
            issues.append("User impact score out of range")
        
        if not -10.0 <= self.technical_debt_impact <= 10.0:
            issues.append("Technical debt impact out of range")
        
        return issues
```

### 3. Supporting Value Objects

#### ExpectedOutcome

```python
@dataclass(frozen=True)
class ExpectedOutcome:
    """Value object representing an expected outcome"""
    description: str
    success_indicator: str
    measurement_method: str
    target_date: datetime
    
    def is_measurable(self) -> bool:
        """Check if outcome has clear measurement criteria"""
        return bool(self.success_indicator and self.measurement_method)
```

#### RiskFactor

```python
from enum import Enum

class RiskSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class RiskLikelihood(Enum):
    RARE = "rare"
    UNLIKELY = "unlikely"
    POSSIBLE = "possible"
    LIKELY = "likely"
    CERTAIN = "certain"

@dataclass(frozen=True)
class RiskFactor:
    """Value object representing a risk factor"""
    id: str
    description: str
    severity: RiskSeverity
    likelihood: RiskLikelihood
    impact_areas: List[str]
    mitigation_strategy: str
    
    def calculate_risk_score(self) -> int:
        """Calculate risk score (1-25)"""
        severity_scores = {
            RiskSeverity.LOW: 1,
            RiskSeverity.MEDIUM: 2,
            RiskSeverity.HIGH: 3,
            RiskSeverity.CRITICAL: 5
        }
        
        likelihood_scores = {
            RiskLikelihood.RARE: 1,
            RiskLikelihood.UNLIKELY: 2,
            RiskLikelihood.POSSIBLE: 3,
            RiskLikelihood.LIKELY: 4,
            RiskLikelihood.CERTAIN: 5
        }
        
        return severity_scores[self.severity] * likelihood_scores[self.likelihood]
    
    def get_risk_level(self) -> str:
        """Get risk level based on score"""
        score = self.calculate_risk_score()
        if score >= 20:
            return "critical"
        elif score >= 12:
            return "high"
        elif score >= 6:
            return "medium"
        else:
            return "low"
```

#### QualityStandard

```python
@dataclass(frozen=True)
class QualityStandard:
    """Value object representing a quality standard"""
    name: str
    description: str
    acceptance_threshold: float
    measurement_method: str
    validation_approach: str
    
    def is_met(self, measured_value: float) -> bool:
        """Check if standard is met"""
        return measured_value >= self.acceptance_threshold
```

#### MeasurableOutcome

```python
@dataclass(frozen=True)
class MeasurableOutcome:
    """Value object for task-level measurable outcomes"""
    description: str
    metric: str
    baseline_value: float
    target_value: float
    measurement_date: datetime
    
    def calculate_improvement(self) -> float:
        """Calculate expected improvement percentage"""
        if self.baseline_value == 0:
            return 100.0 if self.target_value > 0 else 0.0
        
        improvement = ((self.target_value - self.baseline_value) / 
                      abs(self.baseline_value)) * 100
        return round(improvement, 1)
```

### 4. Domain Events

```python
from abc import ABC
from datetime import datetime

class VisionEvent(ABC):
    """Base class for vision-related domain events"""
    def __init__(self, timestamp: datetime = None):
        self.timestamp = timestamp or datetime.now()
        self.event_id = str(uuid.uuid4())

class ObjectiveAddedEvent(VisionEvent):
    """Event raised when objective is added to vision"""
    def __init__(self, project_id: str, objective: VisionObjective, **kwargs):
        super().__init__(**kwargs)
        self.project_id = project_id
        self.objective = objective

class ObjectiveUpdatedEvent(VisionEvent):
    """Event raised when objective progress is updated"""
    def __init__(self, project_id: str, objective_id: str, 
                 old_value: float, new_value: float, **kwargs):
        super().__init__(**kwargs)
        self.project_id = project_id
        self.objective_id = objective_id
        self.old_value = old_value
        self.new_value = new_value

class BranchAlignmentUpdatedEvent(VisionEvent):
    """Event raised when branch alignment changes"""
    def __init__(self, branch_id: str, old_alignment: float, 
                 new_alignment: float, **kwargs):
        super().__init__(**kwargs)
        self.branch_id = branch_id
        self.old_alignment = old_alignment
        self.new_alignment = new_alignment

class DeliverableCompletedEvent(VisionEvent):
    """Event raised when branch deliverable is completed"""
    def __init__(self, branch_id: str, deliverable: str, **kwargs):
        super().__init__(**kwargs)
        self.branch_id = branch_id
        self.deliverable = deliverable

class VisionValidationFailedEvent(VisionEvent):
    """Event raised when vision validation fails"""
    def __init__(self, entity_type: str, entity_id: str, 
                 validation_errors: List[str], **kwargs):
        super().__init__(**kwargs)
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.validation_errors = validation_errors
```

### 5. Aggregate Roots

```python
class VisionAggregate:
    """
    Aggregate root for vision management.
    Ensures consistency across vision hierarchy.
    """
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.project_vision: Optional[ProjectVision] = None
        self.branch_visions: Dict[str, BranchVision] = {}
        self.task_alignments: Dict[str, TaskVisionAlignment] = {}
        self._events: List[VisionEvent] = []
    
    def set_project_vision(self, vision: ProjectVision) -> None:
        """Set project vision with validation"""
        validation_errors = vision.validate()
        if validation_errors:
            raise ValueError(f"Invalid project vision: {', '.join(validation_errors)}")
        
        self.project_vision = vision
        self._events.extend(vision._events)
        vision._events.clear()
    
    def add_branch_vision(self, branch_id: str, vision: BranchVision) -> None:
        """Add branch vision with project alignment validation"""
        if not self.project_vision:
            raise ValueError("Project vision must be set before branch vision")
        
        validation_errors = vision.validate_against_project(self.project_vision)
        if validation_errors:
            self._events.append(VisionValidationFailedEvent(
                entity_type="BranchVision",
                entity_id=branch_id,
                validation_errors=validation_errors
            ))
            raise ValueError(f"Invalid branch vision: {', '.join(validation_errors)}")
        
        self.branch_visions[branch_id] = vision
        self._events.extend(vision._events)
        vision._events.clear()
    
    def add_task_alignment(self, task_id: str, alignment: TaskVisionAlignment) -> None:
        """Add task alignment with branch validation"""
        branch_vision = self.branch_visions.get(alignment.branch_id)
        if not branch_vision:
            raise ValueError(f"Branch vision not found for branch {alignment.branch_id}")
        
        # Validate task objectives exist in branch
        for obj in alignment.contributes_to_objectives:
            if obj not in branch_vision.branch_objectives:
                raise ValueError(f"Task objective '{obj}' not in branch objectives")
        
        validation_errors = alignment.validate()
        if validation_errors:
            raise ValueError(f"Invalid task alignment: {', '.join(validation_errors)}")
        
        self.task_alignments[task_id] = alignment
    
    def calculate_vision_health(self) -> Dict[str, float]:
        """Calculate overall vision health metrics"""
        if not self.project_vision:
            return {"overall": 0.0}
        
        # Calculate objective progress
        objective_progress = self.project_vision.calculate_overall_progress()
        
        # Calculate branch alignment average
        if self.branch_visions:
            branch_alignment = sum(
                bv.alignment_with_project for bv in self.branch_visions.values()
            ) / len(self.branch_visions)
        else:
            branch_alignment = 0.0
        
        # Calculate task coverage
        if self.task_alignments:
            avg_task_priority = sum(
                ta.calculate_priority_score() for ta in self.task_alignments.values()
            ) / len(self.task_alignments)
            task_coverage = avg_task_priority / 10.0  # Normalize to 0-1
        else:
            task_coverage = 0.0
        
        overall = (objective_progress / 100 * 0.4 + 
                  branch_alignment * 0.3 + 
                  task_coverage * 0.3)
        
        return {
            "overall": overall,
            "objective_progress": objective_progress,
            "branch_alignment": branch_alignment,
            "task_coverage": task_coverage
        }
    
    def get_events(self) -> List[VisionEvent]:
        """Get and clear accumulated events"""
        events = self._events.copy()
        self._events.clear()
        return events
```

## Usage Examples

### Creating a Complete Vision Hierarchy

```python
# Create project vision
project_vision = ProjectVision(
    project_id="proj-123",
    objectives=[
        VisionObjective(
            id="obj-1",
            title="Improve system performance",
            description="Reduce average response time by 50%",
            target_metric="response_time_ms",
            current_value=1000.0,
            target_value=500.0,
            deadline=datetime.now() + timedelta(days=90),
            measurement_method="APM monitoring",
            created_at=datetime.now()
        )
    ],
    target_audience="End users and developers",
    key_features=["Performance optimization", "Caching layer"],
    unique_value_proposition="Fastest response times in the industry",
    competitive_advantages=["Advanced caching", "Optimized algorithms"],
    success_metrics=[],
    strategic_alignment_score=0.95
)

# Create branch vision
branch_vision = BranchVision(
    branch_id="branch-456",
    project_id="proj-123",
    branch_objectives=["Implement caching layer", "Optimize database queries"],
    branch_deliverables=["Redis cache integration", "Query optimization"],
    expected_outcomes=[
        ExpectedOutcome(
            description="50% reduction in response time",
            success_indicator="Average response time < 500ms",
            measurement_method="Performance tests",
            target_date=datetime.now() + timedelta(days=60)
        )
    ],
    alignment_with_project=0.9,
    contributes_to_objectives=["obj-1"],
    innovation_priorities=["Distributed caching"],
    technical_approach="Implement Redis cache with intelligent invalidation",
    acceptance_criteria=["All endpoints < 500ms", "Cache hit rate > 80%"],
    quality_standards=[]
)

# Create task alignment
task_alignment = TaskVisionAlignment(
    task_id="task-789",
    branch_id="branch-456",
    contributes_to_objectives=["Implement caching layer"],
    expected_impact="Reduce database load by 70%",
    business_value_score=9.0,
    user_impact_score=8.5,
    technical_debt_impact=2.0,
    innovation_score=7.0,
    strategic_importance=Priority.high(),
    success_criteria=["Cache integration complete", "Performance tests pass"],
    acceptance_criteria=["Unit tests pass", "Integration tests pass"],
    measurable_outcomes=[
        MeasurableOutcome(
            description="Response time improvement",
            metric="average_response_ms",
            baseline_value=1000.0,
            target_value=400.0,
            measurement_date=datetime.now() + timedelta(days=30)
        )
    ],
    vision_notes="Critical for performance objectives",
    strategic_rationale="Caching is the most effective way to reduce response times"
)

# Create aggregate and validate
vision_aggregate = VisionAggregate("proj-123")
vision_aggregate.set_project_vision(project_vision)
vision_aggregate.add_branch_vision("branch-456", branch_vision)
vision_aggregate.add_task_alignment("task-789", task_alignment)

# Check vision health
health = vision_aggregate.calculate_vision_health()
print(f"Vision health: {health['overall']:.2%}")
```

## Best Practices

1. **Immutability**: Value objects should be immutable to ensure consistency
2. **Validation**: Always validate at domain boundaries
3. **Event Sourcing**: Track all vision changes through domain events
4. **Aggregate Consistency**: Use aggregates to maintain consistency rules
5. **Rich Domain Models**: Include business logic in domain entities, not services