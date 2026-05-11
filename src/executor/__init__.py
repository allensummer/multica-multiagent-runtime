"""
Executor Agent Pool - Dynamic agent registration and task dispatch.

Provides:
- Dynamic Executor registration/discovery
- Task distribution based on skill matching
- @mention protocol integration with Master Agent
- Checkpoint integration for fault tolerance
"""

from executor_pool.executor import Executor, ExecutorStatus
from executor_pool.pool import ExecutorPool
from executor_pool.protocol import (
    MessageType,
    RejectReason,
    TaskAssignMessage,
    TaskResultMessage,
    TaskProgressMessage,
    TaskRejectedMessage,
    validate_agent_id,
    create_task_assign_text,
    create_task_rejected_text,
)

__all__ = [
    "Executor",
    "ExecutorStatus",
    "ExecutorPool",
    "MessageType",
    "RejectReason",
    "TaskAssignMessage",
    "TaskResultMessage",
    "TaskProgressMessage",
    "TaskRejectedMessage",
    "validate_agent_id",
    "create_task_assign_text",
    "create_task_rejected_text",
]