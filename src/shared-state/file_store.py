"""File-based implementation of Shared State Store."""

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any

from shared_state_store.base import BaseCheckpointSaver, BaseEventLog
from shared_state_store.models import (
    Checkpoint,
    CheckpointSnapshot,
    Event,
    EventType,
    ExecutorState,
)


class FileCheckpointStore(BaseCheckpointSaver):
    """File-based checkpoint storage.

    Stores checkpoints as JSON files in a directory structure:
        <root>/<task_id>/checkpoint_<index>.json
    """

    def __init__(self, root_dir: str | Path):
        self.root_dir = Path(root_dir)
        self._lock = Lock()

    def _task_dir(self, task_id: str) -> Path:
        return self.root_dir / task_id

    def _checkpoint_path(self, task_id: str, checkpoint_id: str) -> Path:
        return self._task_dir(task_id) / f"checkpoint_{checkpoint_id}.json"

    def save(self, checkpoint: Checkpoint) -> None:
        """Save a checkpoint to disk."""
        with self._lock:
            task_dir = self._task_dir(checkpoint.task_id)
            task_dir.mkdir(parents=True, exist_ok=True)
            path = self._checkpoint_path(checkpoint.task_id, checkpoint.checkpoint_id)
            with open(path, "w") as f:
                json.dump(checkpoint.to_dict(), f, indent=2)

    def load(self, checkpoint_id: str) -> Checkpoint | None:
        """Load a checkpoint by scanning for matching ID."""
        for checkpoint_path in self.root_dir.rglob(f"checkpoint_{checkpoint_id}.json"):
            with open(checkpoint_path) as f:
                data = json.load(f)
                return Checkpoint.from_dict(data)
        return None

    def list_by_task(self, task_id: str) -> list[Checkpoint]:
        """List all checkpoints for a task."""
        task_dir = self._task_dir(task_id)
        if not task_dir.exists():
            return []

        checkpoints = []
        for path in task_dir.glob("checkpoint_*.json"):
            with open(path) as f:
                data = json.load(f)
                checkpoints.append(Checkpoint.from_dict(data))

        checkpoints.sort(key=lambda c: c.created_at)
        return checkpoints

    def get_latest(self, task_id: str) -> Checkpoint | None:
        """Get the most recent checkpoint for a task."""
        checkpoints = self.list_by_task(task_id)
        return checkpoints[-1] if checkpoints else None

    def delete(self, checkpoint_id: str) -> None:
        """Delete a checkpoint."""
        with self._lock:
            for path in self.root_dir.rglob(f"checkpoint_{checkpoint_id}.json"):
                path.unlink()

    def delete_all_for_task(self, task_id: str) -> None:
        """Delete all checkpoints for a task."""
        with self._lock:
            task_dir = self._task_dir(task_id)
            if task_dir.exists():
                for path in task_dir.glob("checkpoint_*.json"):
                    path.unlink()


class FileEventLogStore(BaseEventLog):
    """File-based event log storage.

    Appends events to a log file per task:
        <root>/<task_id>/event_log.jsonl

    Each line is a JSON-serialized event for efficient append.
    """

    def __init__(self, root_dir: str | Path):
        self.root_dir = Path(root_dir)
        self._lock = Lock()

    def _log_path(self, task_id: str) -> Path:
        return self.root_dir / task_id / "event_log.jsonl"

    def _ensure_dir(self, task_id: str) -> Path:
        path = self._log_path(task_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def append(self, event: Event) -> None:
        """Append an event to the log with durability guarantee.

        Uses fsync to ensure the event is flushed to disk before returning.
        This prevents event loss on crash.
        """
        with self._lock:
            path = self._ensure_dir(event.task_id)
            with open(path, "a") as f:
                f.write(json.dumps(event.to_dict()) + "\n")
                f.flush()
                os.fsync(f.fileno())

    def get_events(
        self,
        task_id: str | None = None,
        event_type: str | None = None,
        after_index: int = 0,
        limit: int = 100,
    ) -> list[Event]:
        """Get events filtered by task and/or type."""
        if task_id is None:
            events = []
            for log_path in self.root_dir.rglob("event_log.jsonl"):
                events.extend(self._read_events_from_path(log_path))
        else:
            path = self._log_path(task_id)
            if not path.exists():
                return []
            events = self._read_events_from_path(path)

        # Filter by event type if specified
        if event_type is not None:
            events = [e for e in events if e.event_type.value == event_type]

        # Apply pagination
        events = events[after_index : after_index + limit]
        return events

    def _read_events_from_path(self, path: Path) -> list[Event]:
        """Read all events from a log file."""
        events = []
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line:
                    events.append(Event.from_dict(json.loads(line)))
        return events

    def get_event_count(self, task_id: str | None = None) -> int:
        """Get total event count."""
        if task_id is None:
            count = 0
            for log_path in self.root_dir.rglob("event_log.jsonl"):
                with open(log_path) as f:
                    count += sum(1 for line in f if line.strip())
            return count
        else:
            path = self._log_path(task_id)
            if not path.exists():
                return 0
            with open(path) as f:
                return sum(1 for line in f if line.strip())

    def replay_from(self, task_id: str, from_index: int = 0) -> list[Event]:
        """Replay events from a given index."""
        path = self._log_path(task_id)
        if not path.exists():
            return []
        events = self._read_events_from_path(path)
        return events[from_index:]

    def replay_full(self, task_id: str) -> list[Event]:
        """Replay all events for a task from the beginning."""
        return self.replay_from(task_id, from_index=0)