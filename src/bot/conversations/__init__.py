"""Conversations package for FSM-based conversation management.

This package provides conversation state management using a typed Finite State
Machine architecture with declarative workflow definitions.
"""

from .persistence import StatePersistenceProtocol, TelegramContextPersistence
from .state_machine import (
    ConversationEvent,
    ConversationStateMachine,
    EventType,
    TransitionResult,
)
from .states import ConversationState
from .workflow_config import (
    InputType,
    StateConfig,
    TransitionConfig,
    WorkflowConfig,
    load_all_workflows,
    load_workflow,
)

__all__ = [
    "ConversationState",
    "ConversationEvent",
    "ConversationStateMachine",
    "EventType",
    "InputType",
    "StateConfig",
    "StatePersistenceProtocol",
    "TelegramContextPersistence",
    "TransitionConfig",
    "TransitionResult",
    "WorkflowConfig",
    "load_all_workflows",
    "load_workflow",
]
