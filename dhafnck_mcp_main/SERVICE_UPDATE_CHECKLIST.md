# Service User Context Update Checklist

## Services Needing Full Update:

- [ ] work_distribution_service.py (WorkDistributionService)
- [ ] dependencie_application_service.py (DependencieApplicationService)
      Repositories: _task_repository
- [ ] rule_application_service.py (RuleApplicationService)
      Repositories: _rule_repository
- [ ] feature_flag_service.py (FeatureFlagService)
- [ ] audit_service.py (AuditService)
- [ ] task_progress_service.py (TaskProgressService)
      Repositories: _task_repository, _subtask_repository
- [ ] context_validation_service.py (ContextValidationService)
- [ ] context_inheritance_service.py (ContextInheritanceService)
- [ ] context_delegation_service.py (ContextDelegationService)
- [ ] context_cache_service.py (ContextCacheService)
- [ ] git_branch_service.py (GitBranchService)
- [ ] response_enrichment_service.py (ResponseEnrichmentService)
- [ ] progress_tracking_service.py (ProgressTrackingService)
      Repositories: task_repository, context_repository
- [ ] workflow_analysis_service.py (WorkflowAnalysisService)
- [ ] progressive_enforcement_service.py (ProgressiveEnforcementService)
- [ ] parameter_enforcement_service.py (ParameterEnforcementService)

## Services Needing with_user Method Only:

- [ ] vision_analytics_service.py (VisionAnalyticsService)
- [ ] compliance_service.py (ComplianceService)
- [ ] task_context_sync_service.py (TaskContextSyncService)
- [ ] project_management_service.py (ProjectManagementService)
- [ ] hint_generation_service.py (HintGenerationService)
- [ ] automated_context_sync_service.py (AutomatedContextSyncService)
- [ ] unified_context_service.py (UnifiedContextService)

## Update Pattern Summary:
1. Add user_id parameter to __init__
2. Store self._user_id = user_id
3. Add _get_user_scoped_repository method
4. Add with_user method
5. Update repository calls to use scoped versions

# Detailed Instructions


=== Update Instructions for work_distribution_service.py ===
Class: WorkDistributionService
Repositories: None

1. Add to imports:
   from typing import Optional, Any

2. Update __init__ to add user_id parameter:
   def __init__(self, ..., user_id: Optional[str] = None):
       # existing code...
       self._user_id = user_id  # Store user context

3. Add _get_user_scoped_repository method after __init__

4. Add with_user method

5. In methods using repositories, replace:
   self.repository.method()
   With:
   repo = self._get_user_scoped_repository(self.repository)
   repo.method()


=== Update Instructions for dependencie_application_service.py ===
Class: DependencieApplicationService
Repositories: _task_repository

1. Add to imports:
   from typing import Optional, Any

2. Update __init__ to add user_id parameter:
   def __init__(self, ..., user_id: Optional[str] = None):
       # existing code...
       self._user_id = user_id  # Store user context

3. Add _get_user_scoped_repository method after __init__

4. Add with_user method

5. In methods using repositories, replace:
   self._task_repository.method()
   With:
   repo = self._get_user_scoped_repository(self._task_repository)
   repo.method()


=== Update Instructions for rule_application_service.py ===
Class: RuleApplicationService
Repositories: _rule_repository

1. Add to imports:
   from typing import Optional, Any

2. Update __init__ to add user_id parameter:
   def __init__(self, ..., user_id: Optional[str] = None):
       # existing code...
       self._user_id = user_id  # Store user context

3. Add _get_user_scoped_repository method after __init__

4. Add with_user method

5. In methods using repositories, replace:
   self._rule_repository.method()
   With:
   repo = self._get_user_scoped_repository(self._rule_repository)
   repo.method()


=== Update Instructions for feature_flag_service.py ===
Class: FeatureFlagService
Repositories: None

1. Add to imports:
   from typing import Optional, Any

2. Update __init__ to add user_id parameter:
   def __init__(self, ..., user_id: Optional[str] = None):
       # existing code...
       self._user_id = user_id  # Store user context

3. Add _get_user_scoped_repository method after __init__

4. Add with_user method

5. In methods using repositories, replace:
   self.repository.method()
   With:
   repo = self._get_user_scoped_repository(self.repository)
   repo.method()


=== Update Instructions for audit_service.py ===
Class: AuditService
Repositories: None

1. Add to imports:
   from typing import Optional, Any

2. Update __init__ to add user_id parameter:
   def __init__(self, ..., user_id: Optional[str] = None):
       # existing code...
       self._user_id = user_id  # Store user context

3. Add _get_user_scoped_repository method after __init__

4. Add with_user method

5. In methods using repositories, replace:
   self.repository.method()
   With:
   repo = self._get_user_scoped_repository(self.repository)
   repo.method()


=== Update Instructions for task_progress_service.py ===
Class: TaskProgressService
Repositories: _task_repository, _subtask_repository

1. Add to imports:
   from typing import Optional, Any

2. Update __init__ to add user_id parameter:
   def __init__(self, ..., user_id: Optional[str] = None):
       # existing code...
       self._user_id = user_id  # Store user context

3. Add _get_user_scoped_repository method after __init__

4. Add with_user method

5. In methods using repositories, replace:
   self._task_repository.method()
   With:
   repo = self._get_user_scoped_repository(self._task_repository)
   repo.method()


=== Update Instructions for context_validation_service.py ===
Class: ContextValidationService
Repositories: None

1. Add to imports:
   from typing import Optional, Any

2. Update __init__ to add user_id parameter:
   def __init__(self, ..., user_id: Optional[str] = None):
       # existing code...
       self._user_id = user_id  # Store user context

3. Add _get_user_scoped_repository method after __init__

4. Add with_user method

5. In methods using repositories, replace:
   self.repository.method()
   With:
   repo = self._get_user_scoped_repository(self.repository)
   repo.method()


=== Update Instructions for context_inheritance_service.py ===
Class: ContextInheritanceService
Repositories: None

1. Add to imports:
   from typing import Optional, Any

2. Update __init__ to add user_id parameter:
   def __init__(self, ..., user_id: Optional[str] = None):
       # existing code...
       self._user_id = user_id  # Store user context

3. Add _get_user_scoped_repository method after __init__

4. Add with_user method

5. In methods using repositories, replace:
   self.repository.method()
   With:
   repo = self._get_user_scoped_repository(self.repository)
   repo.method()


=== Update Instructions for context_delegation_service.py ===
Class: ContextDelegationService
Repositories: None

1. Add to imports:
   from typing import Optional, Any

2. Update __init__ to add user_id parameter:
   def __init__(self, ..., user_id: Optional[str] = None):
       # existing code...
       self._user_id = user_id  # Store user context

3. Add _get_user_scoped_repository method after __init__

4. Add with_user method

5. In methods using repositories, replace:
   self.repository.method()
   With:
   repo = self._get_user_scoped_repository(self.repository)
   repo.method()


=== Update Instructions for context_cache_service.py ===
Class: ContextCacheService
Repositories: None

1. Add to imports:
   from typing import Optional, Any

2. Update __init__ to add user_id parameter:
   def __init__(self, ..., user_id: Optional[str] = None):
       # existing code...
       self._user_id = user_id  # Store user context

3. Add _get_user_scoped_repository method after __init__

4. Add with_user method

5. In methods using repositories, replace:
   self.repository.method()
   With:
   repo = self._get_user_scoped_repository(self.repository)
   repo.method()


=== Update Instructions for git_branch_service.py ===
Class: GitBranchService
Repositories: None

1. Add to imports:
   from typing import Optional, Any

2. Update __init__ to add user_id parameter:
   def __init__(self, ..., user_id: Optional[str] = None):
       # existing code...
       self._user_id = user_id  # Store user context

3. Add _get_user_scoped_repository method after __init__

4. Add with_user method

5. In methods using repositories, replace:
   self.repository.method()
   With:
   repo = self._get_user_scoped_repository(self.repository)
   repo.method()


=== Update Instructions for response_enrichment_service.py ===
Class: ResponseEnrichmentService
Repositories: None

1. Add to imports:
   from typing import Optional, Any

2. Update __init__ to add user_id parameter:
   def __init__(self, ..., user_id: Optional[str] = None):
       # existing code...
       self._user_id = user_id  # Store user context

3. Add _get_user_scoped_repository method after __init__

4. Add with_user method

5. In methods using repositories, replace:
   self.repository.method()
   With:
   repo = self._get_user_scoped_repository(self.repository)
   repo.method()


=== Update Instructions for progress_tracking_service.py ===
Class: ProgressTrackingService
Repositories: task_repository, context_repository

1. Add to imports:
   from typing import Optional, Any

2. Update __init__ to add user_id parameter:
   def __init__(self, ..., user_id: Optional[str] = None):
       # existing code...
       self._user_id = user_id  # Store user context

3. Add _get_user_scoped_repository method after __init__

4. Add with_user method

5. In methods using repositories, replace:
   self.task_repository.method()
   With:
   repo = self._get_user_scoped_repository(self.task_repository)
   repo.method()


=== Update Instructions for workflow_analysis_service.py ===
Class: WorkflowAnalysisService
Repositories: None

1. Add to imports:
   from typing import Optional, Any

2. Update __init__ to add user_id parameter:
   def __init__(self, ..., user_id: Optional[str] = None):
       # existing code...
       self._user_id = user_id  # Store user context

3. Add _get_user_scoped_repository method after __init__

4. Add with_user method

5. In methods using repositories, replace:
   self.repository.method()
   With:
   repo = self._get_user_scoped_repository(self.repository)
   repo.method()


=== Update Instructions for progressive_enforcement_service.py ===
Class: ProgressiveEnforcementService
Repositories: None

1. Add to imports:
   from typing import Optional, Any

2. Update __init__ to add user_id parameter:
   def __init__(self, ..., user_id: Optional[str] = None):
       # existing code...
       self._user_id = user_id  # Store user context

3. Add _get_user_scoped_repository method after __init__

4. Add with_user method

5. In methods using repositories, replace:
   self.repository.method()
   With:
   repo = self._get_user_scoped_repository(self.repository)
   repo.method()


=== Update Instructions for parameter_enforcement_service.py ===
Class: ParameterEnforcementService
Repositories: None

1. Add to imports:
   from typing import Optional, Any

2. Update __init__ to add user_id parameter:
   def __init__(self, ..., user_id: Optional[str] = None):
       # existing code...
       self._user_id = user_id  # Store user context

3. Add _get_user_scoped_repository method after __init__

4. Add with_user method

5. In methods using repositories, replace:
   self.repository.method()
   With:
   repo = self._get_user_scoped_repository(self.repository)
   repo.method()


=== Update Instructions for vision_analytics_service.py ===
Class: VisionAnalyticsService
Status: Already has user_id, needs with_user method

Add this method:

    def with_user(self, user_id: str) -> 'VisionAnalyticsService':
        """Create a new service instance scoped to a specific user."""
        # Note: Update constructor params based on actual __init__ signature
        return VisionAnalyticsService(..., user_id=user_id)



=== Update Instructions for compliance_service.py ===
Class: ComplianceService
Status: Already has user_id, needs with_user method

Add this method:

    def with_user(self, user_id: str) -> 'ComplianceService':
        """Create a new service instance scoped to a specific user."""
        # Note: Update constructor params based on actual __init__ signature
        return ComplianceService(..., user_id=user_id)



=== Update Instructions for task_context_sync_service.py ===
Class: TaskContextSyncService
Status: Already has user_id, needs with_user method

Add this method:

    def with_user(self, user_id: str) -> 'TaskContextSyncService':
        """Create a new service instance scoped to a specific user."""
        # Note: Update constructor params based on actual __init__ signature
        return TaskContextSyncService(..., user_id=user_id)



=== Update Instructions for project_management_service.py ===
Class: ProjectManagementService
Status: Already has user_id, needs with_user method

Add this method:

    def with_user(self, user_id: str) -> 'ProjectManagementService':
        """Create a new service instance scoped to a specific user."""
        # Note: Update constructor params based on actual __init__ signature
        return ProjectManagementService(..., user_id=user_id)



=== Update Instructions for hint_generation_service.py ===
Class: HintGenerationService
Status: Already has user_id, needs with_user method

Add this method:

    def with_user(self, user_id: str) -> 'HintGenerationService':
        """Create a new service instance scoped to a specific user."""
        # Note: Update constructor params based on actual __init__ signature
        return HintGenerationService(..., user_id=user_id)



=== Update Instructions for automated_context_sync_service.py ===
Class: AutomatedContextSyncService
Status: Already has user_id, needs with_user method

Add this method:

    def with_user(self, user_id: str) -> 'AutomatedContextSyncService':
        """Create a new service instance scoped to a specific user."""
        # Note: Update constructor params based on actual __init__ signature
        return AutomatedContextSyncService(..., user_id=user_id)



=== Update Instructions for unified_context_service.py ===
Class: UnifiedContextService
Status: Already has user_id, needs with_user method

Add this method:

    def with_user(self, user_id: str) -> 'UnifiedContextService':
        """Create a new service instance scoped to a specific user."""
        # Note: Update constructor params based on actual __init__ signature
        return UnifiedContextService(..., user_id=user_id)


