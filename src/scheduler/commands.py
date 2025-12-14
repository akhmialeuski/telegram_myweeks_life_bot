"""Scheduler IPC commands and responses.

This module defines the data structures used for Inter-Process Communication (IPC)
between the main application and the scheduler worker process.
"""

from dataclasses import dataclass, field
from enum import StrEnum, auto
from typing import Any


class SchedulerCommandType(StrEnum):
    """Types of commands that can be sent to the scheduler worker."""

    SCHEDULE_JOB = auto()
    REMOVE_JOB = auto()
    RESCHEDULE_JOB = auto()
    GET_JOB = auto()
    GET_ALL_JOBS = auto()
    PAUSE = auto()
    RESUME = auto()
    SHUTDOWN = auto()
    HEALTH_CHECK = auto()


@dataclass(frozen=True, slots=True)
class SchedulerCommand:
    """Command sent to the scheduler worker.

    :ivar id: Unique identifier for the command (for matching with response)
    :ivar type: Type of command
    :ivar payload: Command-specific data
    """

    id: str
    type: SchedulerCommandType
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SchedulerResponse:
    """Response from the scheduler worker.

    :ivar command_id: ID of the command this response is for
    :ivar success: Whether the command was successful
    :ivar data: Response data (if any)
    :ivar error: Error message (if failed)
    """

    command_id: str
    success: bool
    data: Any | None = None
    error: str | None = None
