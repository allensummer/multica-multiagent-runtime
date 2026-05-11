"""Shared State Store data models."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class CheckpointGranularity(Enum):
    """Granularity level for checkpoint saves."""

    PER_NODE = "per_node"  # Save after each agent/node completes
    PER_PHASE = "per_phase"  # Save after each major phase
    MANUAL = "manual"  # Save only when explicitly requested


class EventType(Enum):
    """Types of events in the event log."""

    TASK_CREATED = "task_created"
    TASK_STARTED = "task_started"
    TASK_PROGRESS = "task_progress"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_BLOCKED = "task_blocked"
    TASK_UNBLOCKED = "task_unblocked"
    TASK_ESCALATED = "task_escalated"
    CHECKPOINT_SAVED = "checkpoint_saved"
    CHECKPOINT_RESTORED = "checkpoint_restored"
    AGENT_REGISTERED = "agent_registered"
    AGENT_DEREGISTERED = "agent_deregistered"


@dataclass
class ExecutorState:
    """State of a single executor agent."""

    agent_id: str
    agent_type: str
    current_task: str | None = None
    progress: float = 0.0
    state: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "current_task": self.current_task,
            "progress": self.progress,
            "state": self.state,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExecutorState":
        return cls(
            agent_id=data["agent_id"],
            agent_type=data["agent_type"],
            current_task=data.get("current_task"),
            progress=data.get("progress", 0.0),
            state=data.get("state", {}),
        )


@dataclass
class CheckpointSnapshot:
    """Complete state snapshot at a checkpoint."""

    master_state: dict[str, Any] = field(default_factory=dict)
    executor_states: dict[str, ExecutorState] = field(default_factory=dict)
    shared_context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "master_state": self.master_state,
            "executor_states": {k: v.to_dict() for k, v in self.executor_states.items()},
            "shared_context": self.shared_context,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CheckpointSnapshot":
        executor_states = {
            k: ExecutorState.from_dict(v)
            for k, v in data.get("executor_states", {}).items()
        }
        return cls(
            master_state=data.get("master_state", {}),
            executor_states=executor_states,
            shared_context=data.get("shared_context", {}),
        )


@dataclass
class Checkpoint:
    """A checkpoint representing task state at a specific point."""

    checkpoint_id: str
    parent_issue_id: str
    task_id: str
    step: int
    granularity: CheckpointGranularity
    snapshot: CheckpointSnapshot
    event_index: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "checkpoint_id": self.checkpoint_id,
            "parent_issue_id": self.parent_issue_id,
            "task_id": self.task_id,
            "step": self.step,
            "granularity": self.granularity.value,
            "snapshot": self.snapshot.to_dict(),
            "event_index": self.event_index,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Checkpoint":
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.now(timezone.utc)

        return cls(
            checkpoint_id=data["checkpoint_id"],
            parent_issue_id=data["parent_issue_id"],
            task_id=data["task_id"],
            step=data["step"],
            granularity=CheckpointGranularity(data["granularity"]),
            snapshot=CheckpointSnapshot.from_dict(data["snapshot"]),
            event_index=data.get("event_index", 0),
            created_at=created_at,
        )


@dataclass
class Event:
    """An immutable event in the event log."""

    event_id: str
    event_type: EventType
    task_id: str
    agent_id: str | None
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Event":
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        elif timestamp is None:
            timestamp = datetime.now(timezone.utc)

        return cls(
            event_id=data["event_id"],
            event_type=EventType(data["event_type"]),
            task_id=data["task_id"],
            agent_id=data.get("agent_id"),
            data=data.get("data", {}),
            timestamp=timestamp,
        )