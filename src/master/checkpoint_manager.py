"""
Checkpoint Manager for state persistence and quick interruption recovery.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Optional
from enum import Enum
import json


class CheckpointStatus(Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    INTERRUPTED = "interrupted"


@dataclass
class Checkpoint:
    """Checkpoint data structure for state persistence.

    Attributes:
        task_id: Unique identifier for the task being checkpointed
        step: Current step/index in the execution sequence
        state: Arbitrary state data (serializable) at this checkpoint
        snapshot: Optional full state snapshot for recovery
        created_at: Timestamp when checkpoint was created
        status: Current status of the task
        metadata: Additional metadata dict
    """
    task_id: str
    step: int
    state: dict[str, Any] = field(default_factory=dict)
    snapshot: Optional[dict[str, Any]] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    status: CheckpointStatus = CheckpointStatus.ACTIVE
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert checkpoint to dictionary."""
        result = asdict(self)
        result["status"] = self.status.value
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Checkpoint":
        """Create checkpoint from dictionary."""
        missing = [f for f in ("task_id", "step") if f not in data]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")
        if isinstance(data.get("status"), str):
            data = dict(data)
            data["status"] = CheckpointStatus(data["status"])
        return cls(**data)

    def to_json(self) -> str:
        """Serialize checkpoint to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "Checkpoint":
        """Deserialize checkpoint from JSON string."""
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON for Checkpoint: {e}") from e
        return cls.from_dict(data)


@dataclass
class EventLogEntry:
    """Single entry in the event log.

    Attributes:
        event_id: Unique identifier for this event
        task_id: Associated task ID
        step: Step number when event occurred
        event_type: Type of event (e.g., "start", "checkpoint", "complete", "error")
        payload: Event-specific data
        timestamp: When the event occurred
    """
    event_id: str
    task_id: str
    step: int
    event_type: str
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))

    def to_dict(self) -> dict[str, Any]:
        """Convert event log entry to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EventLogEntry":
        """Create event log entry from dictionary."""
        return cls(**data)


class EventLog:
    """Event log for recording and replaying execution sequences."""

    def __init__(self, task_id: str):
        """Initialize event log for a task.

        Args:
            task_id: The task ID this event log belongs to
        """
        self.task_id = task_id
        self.entries: list[EventLogEntry] = []

    def append(self, event: EventLogEntry) -> None:
        """Append an event to the log."""
        self.entries.append(event)

    def append_entry(
        self,
        step: int,
        event_type: str,
        payload: Optional[dict[str, Any]] = None,
        event_id: Optional[str] = None,
    ) -> EventLogEntry:
        """Convenience method to create and append an event."""
        if event_id is None:
            event_id = f"{self.task_id}-event-{len(self.entries)}"
        entry = EventLogEntry(
            event_id=event_id,
            task_id=self.task_id,
            step=step,
            event_type=event_type,
            payload=payload or {},
        )
        self.append(entry)
        return entry

    def get_events(self, event_type: Optional[str] = None) -> list[EventLogEntry]:
        """Get all events, optionally filtered by type."""
        if event_type is None:
            return list(self.entries)
        return [e for e in self.entries if e.event_type == event_type]

    def replay(self) -> list[EventLogEntry]:
        """Get all events for replay in order."""
        return list(self.entries)

    def clear(self) -> None:
        """Clear all entries from the event log."""
        self.entries.clear()

    def to_dict(self) -> dict[str, Any]:
        """Convert event log to dictionary."""
        return {
            "task_id": self.task_id,
            "entries": [e.to_dict() for e in self.entries],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EventLog":
        """Create event log from dictionary."""
        log = cls(task_id=data["task_id"])
        log.entries = [EventLogEntry.from_dict(e) for e in data.get("entries", [])]
        return log

    def to_json(self) -> str:
        """Serialize event log to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "EventLog":
        """Deserialize event log from JSON string."""
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON for EventLog: {e}") from e
        return cls.from_dict(data)


class CheckpointManager:
    """Manager for checkpoint save/restore operations."""

    def __init__(self, multica_cli: Any = None):
        """Initialize checkpoint manager."""
        self._checkpoints: dict[str, Checkpoint] = {}
        self._event_logs: dict[str, EventLog] = {}
        self._multica_cli = multica_cli

    def save_checkpoint(
        self,
        task_id: str,
        step: int,
        state: dict[str, Any],
        snapshot: Optional[dict[str, Any]] = None,
        status: CheckpointStatus = CheckpointStatus.ACTIVE,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Checkpoint:
        """Save a checkpoint for a task."""
        checkpoint = Checkpoint(
            task_id=task_id,
            step=step,
            state=state,
            snapshot=snapshot,
            status=status,
            metadata=metadata or {},
        )
        self._checkpoints[task_id] = checkpoint
        return checkpoint

    def get_checkpoint(self, task_id: str) -> Optional[Checkpoint]:
        """Retrieve a checkpoint for a task."""
        return self._checkpoints.get(task_id)

    def delete_checkpoint(self, task_id: str) -> bool:
        """Delete a checkpoint for a task."""
        if task_id in self._checkpoints:
            del self._checkpoints[task_id]
            return True
        return False

    def list_checkpoints(self) -> list[Checkpoint]:
        """List all saved checkpoints."""
        return list(self._checkpoints.values())

    def get_or_create_event_log(self, task_id: str) -> EventLog:
        """Get existing event log or create new one for task."""
        if task_id not in self._event_logs:
            self._event_logs[task_id] = EventLog(task_id)
        return self._event_logs[task_id]

    def get_event_log(self, task_id: str) -> Optional[EventLog]:
        """Get event log for a task if it exists."""
        return self._event_logs.get(task_id)

    def recover_state(self, task_id: str) -> Optional[dict[str, Any]]:
        """Recover the most recent state for a task."""
        checkpoint = self.get_checkpoint(task_id)
        if checkpoint is None:
            return None
        return checkpoint.state.copy()

    def recover_with_snapshot(self, task_id: str) -> Optional[dict[str, Any]]:
        """Recover state using full snapshot if available."""
        checkpoint = self.get_checkpoint(task_id)
        if checkpoint is None:
            return None
        if checkpoint.snapshot is not None:
            return checkpoint.snapshot.copy()
        return checkpoint.state.copy()

    async def save_checkpoint_to_issue(
        self,
        task_id: str,
        step: int,
        state: dict[str, Any],
        parent_issue_id: str,
        snapshot: Optional[dict[str, Any]] = None,
        status: CheckpointStatus = CheckpointStatus.ACTIVE,
    ) -> Optional[str]:
        """Save checkpoint as a sub-Issue in Multica."""
        if self._multica_cli is None:
            return None

        checkpoint = self.save_checkpoint(task_id, step, state, snapshot, status)
        description = f"""## Checkpoint for task {task_id}

```json
{checkpoint.to_json()}
```"""

        result = self._multica_cli.run(
            ["issue", "create",
             "--title", f"Checkpoint: {task_id} (step {step})",
             "--description-stdin"],
            input=description,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None

    async def recover_from_issue(
        self,
        task_id: str,
        checkpoint_issue_id: str,
    ) -> Optional[Checkpoint]:
        """Recover checkpoint from a Multica sub-Issue."""
        if self._multica_cli is None:
            return None

        result = self._multica_cli.run(
            ["issue", "get", checkpoint_issue_id, "--output", "json"],
        )
        if result.returncode != 0:
            return None

        import json
        issue_data = json.loads(result.stdout)
        description = issue_data.get("description", "")

        import re
        json_match = re.search(r"```json\n(.*?)\n```", description, re.DOTALL)
        if not json_match:
            raise ValueError(f"Checkpoint JSON not found in issue description for task {task_id}")
        try:
            checkpoint_data = json.loads(json_match.group(1))
            return Checkpoint.from_dict(checkpoint_data)
        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(f"Failed to parse checkpoint JSON for task {task_id}: {e}") from e