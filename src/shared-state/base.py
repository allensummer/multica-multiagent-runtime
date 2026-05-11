"""Base interfaces for Shared State Store."""

from abc import ABC, abstractmethod
from typing import Any

from shared_state_store.models import Checkpoint, Event


class BaseCheckpointSaver(ABC):
    """Abstract interface for checkpoint storage.

    Implementations can use file system, database, or remote storage.
    """

    @abstractmethod
    def save(self, checkpoint: Checkpoint) -> None:
        """Save a checkpoint."""
        ...

    @abstractmethod
    def load(self, checkpoint_id: str) -> Checkpoint | None:
        """Load a checkpoint by ID."""
        ...

    @abstractmethod
    def list_by_task(self, task_id: str) -> list[Checkpoint]:
        """List all checkpoints for a task, ordered by creation time."""
        ...

    @abstractmethod
    def get_latest(self, task_id: str) -> Checkpoint | None:
        """Get the most recent checkpoint for a task."""
        ...

    @abstractmethod
    def delete(self, checkpoint_id: str) -> None:
        """Delete a checkpoint."""
        ...

    @abstractmethod
    def delete_all_for_task(self, task_id: str) -> None:
        """Delete all checkpoints for a task."""
        ...


class BaseEventLog(ABC):
    """Abstract interface for event log storage.

    Events are immutable - only append operations are allowed.
    Supports replay for state reconstruction.
    """

    @abstractmethod
    def append(self, event: Event) -> None:
        """Append an event to the log."""
        ...

    @abstractmethod
    def get_events(
        self,
        task_id: str | None = None,
        event_type: str | None = None,
        after_index: int = 0,
        limit: int = 100,
    ) -> list[Event]:
        """Get events filtered by task and/or type."""
        ...

    @abstractmethod
    def get_event_count(self, task_id: str | None = None) -> int:
        """Get total event count, optionally filtered by task."""
        ...

    @abstractmethod
    def replay_from(
        self, task_id: str, from_index: int = 0
    ) -> list[Event]:
        """Replay all events from a given index for a task."""
        ...

    @abstractmethod
    def replay_full(self, task_id: str) -> list[Event]:
        """Replay all events for a task from the beginning."""
        ...