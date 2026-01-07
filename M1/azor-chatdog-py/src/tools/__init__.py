"""
Tools module for AZØR chatdog.
Contains tool/function declarations for LLM tool calling.
"""

from .clarification_tool import (
    create_clarification_tool,
    ask_user_for_clarification
)

__all__ = [
    'create_clarification_tool',
    'ask_user_for_clarification'
]
