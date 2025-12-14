"""Scheduler package for background job scheduling.

This package provides scheduling infrastructure including:
- SchedulerPortProtocol: Abstract interface for scheduling operations
- APSchedulerAdapter: Implementation using APScheduler
- Domain models: ScheduleTrigger, JobInfo
"""

from .adapters import APSchedulerAdapter

__all__: list[str] = [
    "APSchedulerAdapter",
]
