"""Rule Application Service

DDD application service for rule management operations.
"""

from typing import Dict, Any, Optional
from ..use_cases.create_rule import CreateRuleUseCase
from ..use_cases.get_rule import GetRuleUseCase
from ..use_cases.list_rules import ListRulesUseCase
from ..use_cases.update_rule import UpdateRuleUseCase
from ..use_cases.delete_rule import DeleteRuleUseCase
from ..use_cases.validate_rule import ValidateRuleUseCase
from ...domain.repositories.rule_repository import RuleRepository
from ...domain.enums.rule_enums import RuleFormat, RuleType


class RuleApplicationService:
    """Application service for rule management operations"""
    
    def __init__(self, rule_repository: RuleRepository):
        self._rule_repository = rule_repository
        
        # Initialize use cases
        self._create_rule_use_case = CreateRuleUseCase(rule_repository)
        self._get_rule_use_case = GetRuleUseCase(rule_repository)
        self._list_rules_use_case = ListRulesUseCase(rule_repository)
        self._update_rule_use_case = UpdateRuleUseCase(rule_repository)
        self._delete_rule_use_case = DeleteRuleUseCase(rule_repository)
        self._validate_rule_use_case = ValidateRuleUseCase(rule_repository)
    
    async def create_rule(
        self,
        rule_path: str,
        content: str,
        rule_type: RuleType,
        rule_format: RuleFormat,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new rule"""
        return await self._create_rule_use_case.execute(
            rule_path=rule_path,
            content=content,
            rule_type=rule_type,
            rule_format=rule_format,
            metadata=metadata
        )
    
    async def get_rule(self, rule_path: str) -> Dict[str, Any]:
        """Get a rule by path"""
        return await self._get_rule_use_case.execute(rule_path)
    
    async def list_rules(
        self,
        filters: Optional[Dict[str, Any]] = None,
        metadata_only: bool = False
    ) -> Dict[str, Any]:
        """List rules with optional filters"""
        return await self._list_rules_use_case.execute(filters, metadata_only)
    
    async def update_rule(
        self,
        rule_path: str,
        content: Optional[str] = None,
        metadata_updates: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Update an existing rule"""
        return await self._update_rule_use_case.execute(
            rule_path=rule_path,
            content=content,
            metadata_updates=metadata_updates
        )
    
    async def delete_rule(self, rule_path: str, force: bool = False) -> Dict[str, Any]:
        """Delete a rule"""
        return await self._delete_rule_use_case.execute(rule_path, force)
    
    async def validate_rule(self, rule_path: Optional[str] = None) -> Dict[str, Any]:
        """Validate a rule or all rules"""
        return await self._validate_rule_use_case.execute(rule_path)
    
    async def backup_rules(self, backup_path: str) -> Dict[str, Any]:
        """Backup all rules"""
        try:
            success = await self._rule_repository.backup_rules(backup_path)
            if success:
                return {
                    "success": True,
                    "message": f"Rules backed up successfully to {backup_path}",
                    "backup_path": backup_path
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to backup rules"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to backup rules: {str(e)}"
            }
    
    async def restore_rules(self, backup_path: str) -> Dict[str, Any]:
        """Restore rules from backup"""
        try:
            success = await self._rule_repository.restore_rules(backup_path)
            if success:
                return {
                    "success": True,
                    "message": f"Rules restored successfully from {backup_path}",
                    "backup_path": backup_path
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to restore rules"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to restore rules: {str(e)}"
            }
    
    async def cleanup_obsolete_rules(self) -> Dict[str, Any]:
        """Clean up obsolete rules"""
        try:
            cleaned_paths = await self._rule_repository.cleanup_obsolete_rules()
            return {
                "success": True,
                "message": f"Cleaned up {len(cleaned_paths)} obsolete rules",
                "cleaned_paths": cleaned_paths
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to cleanup obsolete rules: {str(e)}"
            }
    
    async def get_rule_statistics(self) -> Dict[str, Any]:
        """Get statistics about rules"""
        try:
            stats = await self._rule_repository.get_rule_statistics()
            return {
                "success": True,
                "statistics": stats
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get rule statistics: {str(e)}"
            }
    
    async def get_rule_dependencies(self, rule_path: str) -> Dict[str, Any]:
        """Get dependencies for a rule"""
        try:
            dependencies = await self._rule_repository.get_rule_dependencies(rule_path)
            return {
                "success": True,
                "rule_path": rule_path,
                "dependencies": dependencies
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get rule dependencies: {str(e)}"
            }
    
    async def get_dependent_rules(self, rule_path: str) -> Dict[str, Any]:
        """Get rules that depend on the specified rule"""
        try:
            dependent_rules = await self._rule_repository.get_dependent_rules(rule_path)
            return {
                "success": True,
                "rule_path": rule_path,
                "dependent_rules": dependent_rules
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get dependent rules: {str(e)}"
            }
    
    async def get_rules_by_type(self, rule_type: str) -> Dict[str, Any]:
        """Get rules by type"""
        try:
            rules = await self._rule_repository.get_rules_by_type(rule_type)
            return {
                "success": True,
                "rule_type": rule_type,
                "rules": [
                    {
                        "path": rule.metadata.path,
                        "type": rule.metadata.type.value,
                        "format": rule.metadata.format.value,
                        "description": rule.metadata.description,
                        "tags": rule.metadata.tags
                    }
                    for rule in rules
                ]
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get rules by type: {str(e)}"
            }
    
    async def get_rules_by_tag(self, tag: str) -> Dict[str, Any]:
        """Get rules by tag"""
        try:
            rules = await self._rule_repository.get_rules_by_tag(tag)
            return {
                "success": True,
                "tag": tag,
                "rules": [
                    {
                        "path": rule.metadata.path,
                        "type": rule.metadata.type.value,
                        "format": rule.metadata.format.value,
                        "description": rule.metadata.description,
                        "tags": rule.metadata.tags
                    }
                    for rule in rules
                ]
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get rules by tag: {str(e)}"
            }