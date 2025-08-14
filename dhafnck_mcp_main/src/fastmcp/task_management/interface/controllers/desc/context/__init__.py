"""
Context Management Tool Descriptions Package

This module collects all context-related tool descriptions for the MCP interface.
Includes legacy context management and new hierarchical context features.
"""

from .manage_context_description import (
    MANAGE_CONTEXT_DESCRIPTION,
    MANAGE_CONTEXT_PARAMETERS
)


from .manage_unified_context_description import (
    MANAGE_UNIFIED_CONTEXT_DESCRIPTION,
    MANAGE_UNIFIED_CONTEXT_PARAMETERS
)

# Collect all context descriptions in the standard format expected by description_loader
CONTEXT_DESCRIPTIONS = {
    "manage_context": {
        "description": MANAGE_UNIFIED_CONTEXT_DESCRIPTION,
        "parameters": MANAGE_UNIFIED_CONTEXT_PARAMETERS
    },
    "manage_unified_context": {
        "description": MANAGE_UNIFIED_CONTEXT_DESCRIPTION,
        "parameters": MANAGE_UNIFIED_CONTEXT_PARAMETERS
    }
}

__all__ = [
    'MANAGE_CONTEXT_DESCRIPTION',
    'MANAGE_CONTEXT_PARAMETERS',
    'MANAGE_UNIFIED_CONTEXT_DESCRIPTION',
    'MANAGE_UNIFIED_CONTEXT_PARAMETERS',
    'CONTEXT_DESCRIPTIONS'
]