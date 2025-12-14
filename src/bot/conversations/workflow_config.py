"""Workflow configuration models for FSM.

This module defines Pydantic models for parsing and validating
workflow YAML configuration files. These configurations define
the conversation state machine transitions, guards, and actions
in a declarative manner.

The workflow configuration system allows defining:
- States and their input types
- Validation rules for each state
- Transitions based on validation outcomes
- Guard conditions for conditional transitions
- Actions to execute during transitions
"""

from enum import Enum
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class InputType(str, Enum):
    """Type of input expected in a state.

    Determines how the state machine processes incoming messages.
    """

    TEXT = "text"
    CALLBACK = "callback"
    NONE = "none"


class TransitionConfig(BaseModel):
    """Configuration for a state transition.

    Defines the target state and optional conditions/actions
    for a transition.

    :ivar target: Target state name after transition
    :ivar guard: Optional condition function name to check before transition
    :ivar action: Optional action function name to execute during transition
    """

    target: str = Field(description="Target state name")
    guard: str | None = Field(
        default=None, description="Optional guard condition function name"
    )
    action: str | None = Field(
        default=None, description="Optional action function name"
    )


class StateConfig(BaseModel):
    """Configuration for a conversation state.

    Defines the expected input type, validation rules, and
    possible transitions from this state.

    :ivar input_type: Type of input expected (text, callback, none)
    :ivar validation: Optional validation method name
    :ivar on_valid: Transition when input is valid
    :ivar on_invalid: Transition when input is invalid
    :ivar on_timeout: Optional transition on state timeout
    :ivar timeout_seconds: Optional timeout duration in seconds
    """

    input_type: InputType = Field(
        default=InputType.NONE, description="Expected input type"
    )
    validation: str | None = Field(
        default=None, description="Validation method name from ValidationService"
    )
    on_valid: TransitionConfig | None = Field(
        default=None, description="Transition on valid input"
    )
    on_invalid: TransitionConfig | None = Field(
        default=None, description="Transition on invalid input"
    )
    on_timeout: TransitionConfig | None = Field(
        default=None, description="Transition on timeout"
    )
    timeout_seconds: int | None = Field(
        default=None, description="State timeout in seconds"
    )


class WorkflowConfig(BaseModel):
    """Configuration for a complete conversation workflow.

    Contains the workflow name, initial state, and all state
    definitions with their transitions.

    :ivar name: Workflow identifier
    :ivar initial_state: Starting state name
    :ivar states: Dictionary mapping state names to their configurations
    """

    name: str = Field(description="Workflow identifier")
    initial_state: str = Field(description="Initial state name")
    states: dict[str, StateConfig] = Field(
        default_factory=dict, description="State definitions"
    )


def load_workflow(file_path: Path) -> WorkflowConfig:
    """Load and parse a workflow configuration from YAML file.

    Reads a YAML file and validates it against the WorkflowConfig
    schema using Pydantic.

    :param file_path: Path to the workflow YAML file
    :type file_path: Path
    :returns: Parsed and validated workflow configuration
    :rtype: WorkflowConfig
    :raises FileNotFoundError: If workflow file doesn't exist
    :raises yaml.YAMLError: If YAML parsing fails
    :raises pydantic.ValidationError: If configuration is invalid
    """
    with file_path.open(encoding="utf-8") as f:
        data: dict[str, Any] = yaml.safe_load(f)
    return WorkflowConfig.model_validate(data)


def load_all_workflows(workflows_dir: Path) -> dict[str, WorkflowConfig]:
    """Load all workflow configurations from a directory.

    Scans the specified directory for YAML files and loads
    each as a workflow configuration.

    :param workflows_dir: Path to directory containing workflow YAML files
    :type workflows_dir: Path
    :returns: Dictionary mapping workflow names to configurations
    :rtype: dict[str, WorkflowConfig]
    :raises FileNotFoundError: If workflows directory doesn't exist
    """
    workflows: dict[str, WorkflowConfig] = {}
    if not workflows_dir.exists():
        return workflows

    for yaml_file in workflows_dir.glob("*.yaml"):
        workflow = load_workflow(yaml_file)
        workflows[workflow.name] = workflow

    return workflows
