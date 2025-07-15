"""AI Memory Manager - Handles AI work session continuity and memory persistence"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import json
import hashlib
from enum import Enum

class ConflictResolution(Enum):
    MERGE = "merge"
    OVERRIDE = "override"
    REJECT = "reject"
    MANUAL = "manual"

@dataclass
class AIWorkSession:
    """Represents an AI work session with memory"""
    session_id: str
    task_id: str
    ai_client: str
    started_at: datetime
    last_update: datetime
    version: int
    updates: List[Dict[str, Any]] = field(default_factory=list)
    memory: Dict[str, Any] = field(default_factory=dict)

@dataclass
class UpdateConflict:
    """Represents a conflict between updates"""
    type: str
    severity: str  # low, medium, high
    current_value: Any
    update_value: Any
    resolution_hint: str
    timestamp: datetime

class AIMemoryManager:
    """Manages AI memory and work session continuity"""
    
    def __init__(self, storage_backend, conflict_resolver=None):
        self._storage = storage_backend
        self._conflict_resolver = conflict_resolver or ConflictResolver()
        self._active_sessions: Dict[str, AIWorkSession] = {}
    
    async def create_work_session(
        self,
        task_id: str,
        ai_client: str,
        initial_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new AI work session with memory initialization"""
        
        # Generate session ID
        session_id = self._generate_session_id(task_id, ai_client)
        
        # Load previous AI memory if exists
        ai_memory = await self._load_ai_memory(task_id, ai_client)
        
        # Create session
        session = AIWorkSession(
            session_id=session_id,
            task_id=task_id,
            ai_client=ai_client,
            started_at=datetime.now(timezone.utc),
            last_update=datetime.now(timezone.utc),
            version=initial_context.get("version", 1),
            memory=ai_memory
        )
        
        # Store session
        self._active_sessions[session_id] = session
        await self._persist_session(session)
        
        # Generate work session token
        token = self._generate_work_token(session)
        
        return {
            "session_id": session_id,
            "token": token,
            "ai_memory": ai_memory,
            "continue_from": ai_memory.get("last_checkpoint"),
            "version": session.version
        }
    
    async def continue_work_session(
        self,
        work_token: str,
        task_id: str,
        ai_client: str
    ) -> Optional[AIWorkSession]:
        """Continue a previous work session"""
        
        # Decode token
        token_data = self._decode_work_token(work_token)
        
        if token_data["task_id"] != task_id:
            return None
        
        # Load or create session
        session = await self._load_session(token_data["session_id"])
        
        if not session:
            # Create new session with continuity
            return await self.create_work_session(task_id, ai_client, {
                "version": token_data.get("version", 1),
                "previous_session": token_data["session_id"]
            })
        
        return session
    
    async def update_with_conflict_resolution(
        self,
        task_id: str,
        updates: Dict[str, Any],
        work_token: Optional[str] = None,
        ai_client: str = "unknown"
    ) -> Dict[str, Any]:
        """Apply updates with automatic conflict resolution"""
        
        # Get current state
        current_state = await self._storage.get_task_state(task_id)
        current_version = current_state.get("version", 1)
        
        # Decode token if provided
        token_version = None
        if work_token:
            token_data = self._decode_work_token(work_token)
            token_version = token_data.get("version")
        
        # Check for conflicts
        if token_version and token_version < current_version:
            # Conflict detected - resolve it
            resolution_result = await self._resolve_conflict(
                current_state,
                updates,
                token_version,
                current_version,
                ai_client
            )
            
            if resolution_result["action"] == ConflictResolution.REJECT:
                return {
                    "success": False,
                    "error": "Update rejected due to conflict",
                    "conflict": resolution_result["conflict"],
                    "current_version": current_version
                }
            
            # Apply resolved updates
            updates = resolution_result["resolved_updates"]
        
        # Apply updates
        new_state = await self._apply_updates(current_state, updates, ai_client)
        new_version = current_version + 1
        
        # Persist state
        await self._storage.save_task_state(task_id, new_state, new_version)
        
        # Update AI memory
        await self._update_ai_memory(task_id, ai_client, updates)
        
        # Generate new token
        new_token = self._generate_work_token(AIWorkSession(
            session_id=self._generate_session_id(task_id, ai_client),
            task_id=task_id,
            ai_client=ai_client,
            started_at=datetime.now(timezone.utc),
            last_update=datetime.now(timezone.utc),
            version=new_version,
            updates=[updates]
        ))
        
        return {
            "success": True,
            "version": new_version,
            "work_token": new_token,
            "applied_updates": updates,
            "ai_memory_updated": True
        }
    
    async def _resolve_conflict(
        self,
        current_state: Dict[str, Any],
        updates: Dict[str, Any],
        update_version: int,
        current_version: int,
        ai_client: str
    ) -> Dict[str, Any]:
        """Resolve conflicts between concurrent updates"""
        
        conflicts = self._detect_conflicts(current_state, updates)
        
        if not conflicts:
            # No real conflicts, just version mismatch
            return {
                "action": ConflictResolution.MERGE,
                "resolved_updates": updates
            }
        
        # Categorize conflicts by severity
        high_severity = [c for c in conflicts if c.severity == "high"]
        
        if high_severity:
            # High severity conflicts need manual resolution
            return {
                "action": ConflictResolution.MANUAL,
                "conflict": high_severity[0],
                "all_conflicts": conflicts
            }
        
        # Try smart merge for low/medium conflicts
        merged_updates = await self._smart_merge(
            current_state,
            updates,
            conflicts,
            ai_client
        )
        
        return {
            "action": ConflictResolution.MERGE,
            "resolved_updates": merged_updates,
            "conflicts_resolved": len(conflicts)
        }
    
    def _detect_conflicts(
        self,
        current: Dict[str, Any],
        updates: Dict[str, Any]
    ) -> List[UpdateConflict]:
        """Detect conflicts between current state and updates"""
        
        conflicts = []
        
        # Check vision objective conflicts
        if "vision_objectives" in updates:
            current_objectives = current.get("vision", {}).get("objectives", [])
            update_objectives = updates["vision_objectives"]
            
            if self._has_contradictory_objectives(current_objectives, update_objectives):
                conflicts.append(UpdateConflict(
                    type="vision_contradiction",
                    severity="high",
                    current_value=current_objectives,
                    update_value=update_objectives,
                    resolution_hint="Vision objectives conflict - requires review",
                    timestamp=datetime.now(timezone.utc)
                ))
        
        # Check metric conflicts
        if "metrics" in updates:
            for metric, value in updates["metrics"].items():
                current_value = current.get("metrics", {}).get(metric)
                if current_value and abs(current_value - value) > current_value * 0.5:
                    conflicts.append(UpdateConflict(
                        type="metric_deviation",
                        severity="medium",
                        current_value=current_value,
                        update_value=value,
                        resolution_hint=f"Large change in {metric}",
                        timestamp=datetime.now(timezone.utc)
                    ))
        
        return conflicts
    
    async def _smart_merge(
        self,
        current: Dict[str, Any],
        updates: Dict[str, Any],
        conflicts: List[UpdateConflict],
        ai_client: str
    ) -> Dict[str, Any]:
        """Intelligently merge updates based on conflict types"""
        
        merged = updates.copy()
        
        for conflict in conflicts:
            if conflict.type == "metric_deviation":
                # For metrics, use weighted average based on recency
                metric_name = conflict.resolution_hint.split()[-1]
                merged["metrics"][metric_name] = (
                    conflict.current_value * 0.3 + conflict.update_value * 0.7
                )
            
            elif conflict.type == "list_append":
                # For lists, merge with deduplication
                current_list = conflict.current_value or []
                update_list = conflict.update_value or []
                merged_list = list(dict.fromkeys(current_list + update_list))
                merged[conflict.resolution_hint] = merged_list
        
        # Add merge metadata
        merged["_merge_info"] = {
            "merged_at": datetime.now(timezone.utc).isoformat(),
            "ai_client": ai_client,
            "conflicts_resolved": len(conflicts)
        }
        
        return merged
    
    async def _update_ai_memory(
        self,
        task_id: str,
        ai_client: str,
        updates: Dict[str, Any]
    ) -> None:
        """Update AI-specific memory"""
        
        memory_key = f"ai_memory:{task_id}:{ai_client}"
        current_memory = await self._storage.get(memory_key) or {}
        
        # Update memory sections
        if "preferences" in updates:
            current_memory["preferences"] = updates["preferences"]
        
        if "learned_context" in updates:
            current_memory["learned_context"] = {
                **current_memory.get("learned_context", {}),
                **updates["learned_context"]
            }
        
        # Track work patterns
        if "work_patterns" not in current_memory:
            current_memory["work_patterns"] = []
        
        current_memory["work_patterns"].append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "update_type": updates.get("type", "general"),
            "focus_areas": updates.get("focus_areas", [])
        })
        
        # Keep only recent patterns
        current_memory["work_patterns"] = current_memory["work_patterns"][-10:]
        
        # Update last checkpoint
        current_memory["last_checkpoint"] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "progress": updates.get("progress", {}),
            "next_steps": updates.get("next_steps", [])
        }
        
        await self._storage.set(memory_key, current_memory)
    
    def _generate_work_token(self, session: AIWorkSession) -> str:
        """Generate a work session token"""
        token_data = {
            "session_id": session.session_id,
            "task_id": session.task_id,
            "ai_client": session.ai_client,
            "version": session.version,
            "timestamp": session.last_update.isoformat()
        }
        
        # Create a compact token
        token_json = json.dumps(token_data, separators=(',', ':'))
        return hashlib.sha256(token_json.encode()).hexdigest()[:16] + ":" + token_json
    
    def _decode_work_token(self, token: str) -> Dict[str, Any]:
        """Decode a work session token"""
        try:
            parts = token.split(":", 1)
            if len(parts) == 2:
                return json.loads(parts[1])
        except:
            pass
        return {}
    
    def _generate_session_id(self, task_id: str, ai_client: str) -> str:
        """Generate unique session ID"""
        timestamp = datetime.now(timezone.utc).isoformat()
        return f"{task_id}_{ai_client}_{timestamp}".replace(":", "-")


class ConflictResolver:
    """Default conflict resolver implementation"""
    
    def _has_contradictory_objectives(
        self,
        current: List[Dict[str, Any]],
        updates: List[Dict[str, Any]]
    ) -> bool:
        """Check if objectives are contradictory"""
        # Simple check - can be enhanced
        current_titles = {obj.get("title", "").lower() for obj in current}
        update_titles = {obj.get("title", "").lower() for obj in updates}
        
        # Check for opposing objectives
        opposing_pairs = [
            ("increase", "decrease"),
            ("maximize", "minimize"),
            ("expand", "reduce")
        ]
        
        for curr in current_titles:
            for upd in update_titles:
                for pos, neg in opposing_pairs:
                    if pos in curr and neg in upd:
                        return True
                    if neg in curr and pos in upd:
                        return True
        
        return False