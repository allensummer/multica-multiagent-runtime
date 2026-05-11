"""@mention Protocol for Master-Executor communication."""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class MessageType(Enum):
    """Types of @mention messages between Master and Executors."""

    TASK_ASSIGN = "task_assign"
    TASK_RESULT = "task_result"
    TASK_PROGRESS = "task_progress"
    TASK_REJECTED = "task_rejected"
    CHECKPOINT_SAVE = "checkpoint_save"
    CHECKPOINT_RESTORE = "checkpoint_restore"


class RejectReason(Enum):
    """Reasons an executor may reject a task."""

    SKILL_MISMATCH = "skill_mismatch"
    CAPACITY_FULL = "capacity_full"
    EXECUTOR_UNAVAILABLE = "executor_unavailable"
    INVALID_REQUEST = "invalid_request"


@dataclass
class TaskAssignMessage:
    """Message format for task assignment from Master to Executor."""

    task_id: str
    task_description: str
    required_skills: list[str]
    priority: str
    checkpoint_after: bool
    master_agent_id: str
    executor_agent_id: str


@dataclass
class TaskRejectedMessage:
    """Message format for task rejection from Executor to Master."""

    task_id: str
    reason: RejectReason
    details: str
    executor_agent_id: str
    master_agent_id: str

    def to_mention_text(self) -> str:
        """Convert to @mention text for posting to issue."""
        return f"""[@Master](mention://agent/{self.master_agent_id})

Task {self.task_id} rejected.

Reason: {self.reason.value}
Details: {self.details}

Executor: {self.executor_agent_id}
"""


@dataclass
class TaskResultMessage:
    """Message format for task completion result."""

    task_id: str
    success: bool
    result: Any
    checkpoint_id: str | None
    executor_agent_id: str
    master_agent_id: str

    def to_mention_text(self) -> str:
        """Convert to @mention text for posting to issue."""
        status = "completed" if self.success else "failed"
        checkpoint_info = f"\nCheckpoint ID: {self.checkpoint_id}" if self.checkpoint_id else ""
        return f"""[@Master](mention://agent/{self.master_agent_id})

Task {self.task_id} {status}.

Result: {self.result}{checkpoint_info}

Executor: {self.executor_agent_id}
"""


@dataclass
class TaskProgressMessage:
    """Message format for progress updates."""

    task_id: str
    progress: float
    current_step: int
    total_steps: int
    checkpoint_id: str
    executor_agent_id: str
    master_agent_id: str

    def to_mention_text(self) -> str:
        """Convert to @mention text for posting to issue."""
        return f"""[@Master](mention://agent/{self.master_agent_id})

Task {self.task_id} progress: {self.progress:.0%} (Step {self.current_step}/{self.total_steps})

Checkpoint ID: {self.checkpoint_id}
Executor: {self.executor_agent_id}
"""


def validate_agent_id(agent_id: str | None, agent_type: str) -> None:
    """Validate that agent ID is properly set.

    Args:
        agent_id: The agent ID to validate
        agent_type: Human-readable type for error message (e.g., "Master", "Executor")

    Raises:
        ValueError: If agent_id is None or empty
    """
    if not agent_id or not agent_id.strip():
        raise ValueError(
            f"{agent_type} agent ID is not bound. "
            f"Set the {agent_type.lower()}_agent_id before sending messages."
        )


def create_task_assign_text(
    task_id: str,
    task_description: str,
    required_skills: list[str],
    priority: str,
    checkpoint_after: bool,
    master_agent_id: str,
    executor_agent_id: str,
) -> str:
    """Generate task assignment @mention text.

    Args:
        task_id: Unique task identifier
        task_description: Description of the task to execute
        required_skills: List of skills required for this task
        priority: Task priority (high/medium/low)
        checkpoint_after: Whether to save checkpoint after completion
        master_agent_id: Master's agent ID (for reply routing)
        executor_agent_id: Executor's agent ID (the @mention target)

    Returns:
        Formatted @mention text for posting

    Raises:
        ValueError: If any required ID is not bound
    """
    validate_agent_id(master_agent_id, "Master")
    validate_agent_id(executor_agent_id, "Executor")

    skills_str = ", ".join(required_skills) if required_skills else "none"
    checkpoint_hint = "Yes" if checkpoint_after else "No"

    return f"""[@Executor](mention://agent/{executor_agent_id})

Task {task_id} assigned.

Description: {task_description}

Required skills: {skills_str}
Priority: {priority}
Checkpoint after completion: {checkpoint_hint}

Reply to: [@Master](mention://agent/{master_agent_id})
"""


def create_task_rejected_text(
    task_id: str,
    reason: RejectReason,
    details: str,
    executor_agent_id: str,
    master_agent_id: str,
) -> str:
    """Generate task rejection @mention text.

    Args:
        task_id: The task that was rejected
        reason: Reason for rejection
        details: Detailed explanation
        executor_agent_id: Rejecting executor's agent ID
        master_agent_id: Master's agent ID

    Returns:
        Formatted @mention text for posting

    Raises:
        ValueError: If any required ID is not bound
    """
    validate_agent_id(master_agent_id, "Master")
    validate_agent_id(executor_agent_id, "Executor")

    return f"""[@Master](mention://agent/{master_agent_id})

Task {task_id} rejected by {executor_agent_id}.

Reason: {reason.value}
Details: {details}
"""