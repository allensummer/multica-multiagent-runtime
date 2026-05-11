"""Checkpoint storage backend interface."""

from abc import ABC, abstractmethod
from typing import Iterator

from checkpoint_manager.models import Checkpoint


class CheckpointStore(ABC):
    """Abstract interface for checkpoint storage backends.

    Implement this interface to provide different storage mechanisms
    (file, sqlite, redis, etc.).

    All methods must be implemented to ensure consistent behavior
    across storage backends.
    """

    @abstractmethod
    def save(self, checkpoint: Checkpoint) -> None:
        """Save a checkpoint to storage.

        Args:
            checkpoint: The checkpoint to save

        Raises:
            StorageError: If save fails
        """
        ...

    @abstractmethod
    def get(self, checkpoint_id: str) -> Checkpoint | None:
        """Retrieve a checkpoint by ID.

        Args:
            checkpoint_id: Unique identifier of the checkpoint

        Returns:
            The checkpoint if found, None otherwise
        """
        ...

    @abstractmethod
    def get_latest(self, task_id: str) -> Checkpoint | None:
        """Get the most recent checkpoint for a task.

        Args:
            task_id: The task identifier

        Returns:
            The latest checkpoint for the task, None if no checkpoints exist
        """
        ...

    @abstractmethod
    def list_by_task(self, task_id: str) -> Iterator[Checkpoint]:
        """List all checkpoints for a task in chronological order.

        Args:
            task_id: The task identifier

        Yields:
            Checkpoints for the task from oldest to newest
        """
        ...

    @abstractmethod
    def list_by_parent(self, parent_issue_id: str) -> Iterator[Checkpoint]:
        """List all checkpoints for a parent issue.

        Args:
            parent_issue_id: The parent issue identifier

        Yields:
            All checkpoints belonging to the parent issue
        """
        ...

    @abstractmethod
    def delete(self, checkpoint_id: str) -> bool:
        """Delete a checkpoint by ID.

        Args:
            checkpoint_id: The checkpoint to delete

        Returns:
            True if deleted, False if not found
        """
        ...

    @abstractmethod
    def delete_task_checkpoints(self, task_id: str) -> int:
        """Delete all checkpoints for a task.

        Args:
            task_id: The task identifier

        Returns:
            Number of checkpoints deleted
        """
        ...


class StorageError(Exception):
    """Base exception for storage-related errors."""

    pass


class CheckpointNotFoundError(StorageError):
    """Raised when a checkpoint cannot be found."""

    pass


class CheckpointSaveError(StorageError):
    """Raised when checkpoint save fails."""

    pass


class CheckpointReadError(StorageError):
    """Raised when checkpoint read or deserialization fails."""

    pass