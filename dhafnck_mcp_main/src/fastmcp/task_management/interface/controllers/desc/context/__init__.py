"""
Context Management Tool Descriptions Package

This module collects all context-related tool descriptions for the MCP interface.
Includes legacy context management and new hierarchical context features.
"""

from .manage_context_description import (
    MANAGE_CONTEXT_DESCRIPTION,
    MANAGE_CONTEXT_PARAMETERS
)

from .manage_hierarchical_context_description import (
    MANAGE_HIERARCHICAL_CONTEXT_DESCRIPTION,
    MANAGE_HIERARCHICAL_CONTEXT_PARAMETERS
)

from .manage_delegation_queue_description import (
    MANAGE_DELEGATION_QUEUE_DESCRIPTION,
    MANAGE_DELEGATION_QUEUE_PARAMETERS
)

from .validate_context_inheritance_description import (
    VALIDATE_CONTEXT_INHERITANCE_DESCRIPTION,
    VALIDATE_CONTEXT_INHERITANCE_PARAMETERS
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
    "manage_hierarchical_context": {
        "description": MANAGE_HIERARCHICAL_CONTEXT_DESCRIPTION,
        "parameters": MANAGE_HIERARCHICAL_CONTEXT_PARAMETERS
    },
    "manage_delegation_queue": {
        "description": MANAGE_DELEGATION_QUEUE_DESCRIPTION,
        "parameters": MANAGE_DELEGATION_QUEUE_PARAMETERS
    },
    "validate_context_inheritance": {
        "description": VALIDATE_CONTEXT_INHERITANCE_DESCRIPTION,
        "parameters": VALIDATE_CONTEXT_INHERITANCE_PARAMETERS
    }
}

__all__ = [
    'MANAGE_CONTEXT_DESCRIPTION',
    'MANAGE_CONTEXT_PARAMETERS',
    'MANAGE_HIERARCHICAL_CONTEXT_DESCRIPTION',
    'MANAGE_HIERARCHICAL_CONTEXT_PARAMETERS',
    'MANAGE_DELEGATION_QUEUE_DESCRIPTION',
    'MANAGE_DELEGATION_QUEUE_PARAMETERS',
    'VALIDATE_CONTEXT_INHERITANCE_DESCRIPTION',
    'VALIDATE_CONTEXT_INHERITANCE_PARAMETERS',
    'MANAGE_UNIFIED_CONTEXT_DESCRIPTION',
    'MANAGE_UNIFIED_CONTEXT_PARAMETERS',
    'CONTEXT_DESCRIPTIONS'
]