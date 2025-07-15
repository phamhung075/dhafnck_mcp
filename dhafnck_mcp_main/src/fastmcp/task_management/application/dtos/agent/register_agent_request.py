"""Register Agent Request DTO"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class RegisterAgentRequest:
    """Request DTO for registering an agent"""
    
    project_id: str
    agent_id: str
    name: str
    call_agent: Optional[str] = None
    
    def __post_init__(self):
        """Validate the request after initialization"""
        if not self.project_id or not self.project_id.strip():
            raise ValueError("Project ID is required")
        
        if not self.agent_id or not self.agent_id.strip():
            raise ValueError("Agent ID is required")
        
        if not self.name or not self.name.strip():
            raise ValueError("Agent name is required")