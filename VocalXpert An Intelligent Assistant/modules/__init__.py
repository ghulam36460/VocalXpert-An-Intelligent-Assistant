"""
VocalXpert Modules Package

This package contains all the core modules for VocalXpert:
- state_machine: Centralized state management for the application
- ai_chat: AI-powered chat using Groq API
- normal_chat: Offline chat and knowledge base
- app_control: System control (apps, volume, etc.)
- web_scrapping: Web scraping and search
- and more...
"""

# Export state machine for easy access
from .state_machine import (
    AssistantState,
    StateEvent,
    StateMachine,
    CommandState,
    CommandPipeline,
    get_state_machine,
    reset_state_machine,
    current_state,
    trigger,
    can_trigger,
    is_idle,
    is_busy,
)

__all__ = [
    "AssistantState",
    "StateEvent",
    "StateMachine",
    "CommandState",
    "CommandPipeline",
    "get_state_machine",
    "reset_state_machine",
    "current_state",
    "trigger",
    "can_trigger",
    "is_idle",
    "is_busy",
]
