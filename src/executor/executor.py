"""Executor Agent implementation."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class ExecutorStatus(Enum):
    """Executor operational status."""

    IDLE = "idle"  # Available for tasks
    BUSY = "busy"  # Currently executing a task
    BLOCKED = "blocked"  # Waiting on dependencies
    OFFLINE = "offline"  # Not available


@dataclass
class Executor:
    """An executor agent that can run tasks assigned by Master.

    Attributes:
        executor_id: Unique identifier for this executor
        executor_type: Type/category (e.g., "developer", "reviewer", "sre")
        skills: List of skill identifiers this executor can perform
        status: Current operational status
        current_task_id: Task ID currently being executed (if any)
        metadata: Additional executor-specific data
        registered_at: When this executor was registered
        last_heartbeat: Last activity timestamp
    """

    executor_id: str
    executor_type: str
    skills: list[str] = field(default_factory=list)
    status: ExecutorStatus = ExecutorStatus.IDLE
    current_task_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    registered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_heartbeat: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "executor_id": self.executor_id,
            "executor_type": self.executor_type,
            "skills": self.skills,
            "status": self.status.value,
            "current_task_id": self.current_task_id,
            "metadata": self.metadata,
            "registered_at": self.registered_at.isoformat(),
            "last_heartbeat": self.last_heartbeat.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Executor":
        registered_at = data.get("registered_at")
        if isinstance(registered_at, str):
            registered_at = datetime.fromisoformat(registered_at)

        last_heartbeat = data.get("last_heartbeat")
        if isinstance(last_heartbeat, str):
            last_heartbeat = datetime.fromisoformat(last_heartbeat)

        return cls(
            executor_id=data["executor_id"],
            executor_type=data["executor_type"],
            skills=data.get("skills", []),
            status=ExecutorStatus(data.get("status", "idle")),
            current_task_id=data.get("current_task_id"),
            metadata=data.get("metadata", {}),
            registered_at=registered_at or datetime.now(timezone.utc),
            last_heartbeat=last_heartbeat or datetime.now(timezone.utc),
        )

    def can_execute(self, required_skills: list[str]) -> bool:
        """Check if executor has all required skills."""
        return all(skill in self.skills for skill in required_skills)

    def match_score(self, required_skills: list[str]) -> float:
        """Calculate skill match score (0.0 - 1.0)."""
        if not required_skills:
            return 1.0
        matched = sum(1 for skill in required_skills if skill in self.skills)
        return matched / len(required_skills)

    def update_heartbeat(self) -> None:
        """Update last heartbeat timestamp."""
        self.last_heartbeat = datetime.now(timezone.utc)

    def is_stale(self, max_age_seconds: float = 300.0) -> bool:
        """Check if heartbeat is stale (executor may have crashed).

        Args:
            max_age_seconds: Maximum age in seconds before considered stale (default 5 min)

        Returns:
            True if (now - last_heartbeat) > max_age_seconds
        """
        age = (datetime.now(timezone.utc) - self.last_heartbeat).total_seconds()
        return age > max_age_seconds