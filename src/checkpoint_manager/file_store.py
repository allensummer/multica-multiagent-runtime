"""File-based checkpoint storage backend."""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Iterator

from checkpoint_manager.models import Checkpoint
from checkpoint_manager.store import CheckpointReadError, CheckpointStore, StorageError

logger = logging.getLogger(__name__)


class FileCheckpointStore(CheckpointStore):
    """File-based checkpoint storage.

    Stores checkpoints as JSON files in a directory structure:
    <base_path>/
        <parent_issue_id>/
            <task_id>/
                <checkpoint_id>.json

    This is a lightweight implementation suitable for development and
    small-scale usage. For production, consider SQLite or Redis backend.

    Attributes:
        base_path: Root directory for checkpoint storage
    """

    def __init__(self, base_path: str | Path):
        """Initialize file-based checkpoint store.

        Args:
            base_path: Root directory for checkpoint files
        """
        self.base_path = Path(base_path)
        self._ensure_directory()

    def _ensure_directory(self) -> None:
        """Ensure base directory exists."""
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_checkpoint_path(self, checkpoint: Checkpoint) -> Path:
        """Get the file path for a checkpoint.

        Args:
            checkpoint: The checkpoint

        Returns:
            Path to the checkpoint JSON file
        """
        return (
            self.base_path
            / checkpoint.parent_issue_id
            / checkpoint.task_id
            / f"{checkpoint.checkpoint_id}.json"
        )

    def _get_task_dir(self, parent_issue_id: str, task_id: str) -> Path:
        """Get the directory for a task's checkpoints.

        Args:
            parent_issue_id: Parent issue ID
            task_id: Task ID

        Returns:
            Path to the task's checkpoint directory
        """
        return self.base_path / parent_issue_id / task_id

    def _get_parent_dir(self, parent_issue_id: str) -> Path:
        """Get the directory for a parent issue's checkpoints.

        Args:
            parent_issue_id: Parent issue ID

        Returns:
            Path to the parent's checkpoint directory
        """
        return self.base_path / parent_issue_id

    def _parse_checkpoint_id(self, filename: str) -> str:
        """Extract checkpoint ID from filename.

        Args:
            filename: JSON filename

        Returns:
            Checkpoint ID
        """
        return filename[:-5]  # Remove .json extension

    def _read_checkpoint(self, path: Path) -> Checkpoint | None:
        """Read a checkpoint from a file path.

        Args:
            path: Path to the checkpoint JSON file

        Returns:
            The checkpoint if file exists and valid

        Raises:
            CheckpointReadError: If the file cannot be read or deserialized
        """
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return Checkpoint.from_dict(data)
        except json.JSONDecodeError as e:
            logger.warning("Checkpoint file %s is corrupted (JSON decode error): %s", path, e)
            raise CheckpointReadError(f"Checkpoint file {path} is corrupted: {e}") from e
        except KeyError as e:
            logger.warning("Checkpoint file %s is missing required field: %s", path, e)
            raise CheckpointReadError(f"Checkpoint file {path} is missing required field: {e}") from e
        except OSError as e:
            logger.warning("Failed to read checkpoint file %s: %s", path, e)
            raise CheckpointReadError(f"Failed to read checkpoint file {path}: {e}") from e

    def _write_checkpoint(self, checkpoint: Checkpoint) -> None:
        """Write a checkpoint to file.

        Args:
            checkpoint: The checkpoint to write

        Raises:
            CheckpointSaveError: If write fails
        """
        path = self._get_checkpoint_path(checkpoint)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(checkpoint.to_dict(), f, indent=2, ensure_ascii=False)
        except OSError as e:
            raise StorageError(f"Failed to save checkpoint: {e}") from e

    def save(self, checkpoint: Checkpoint) -> None:
        """Save a checkpoint to file storage.

        Args:
            checkpoint: The checkpoint to save

        Raises:
            CheckpointSaveError: If save fails
        """
        self._write_checkpoint(checkpoint)

    def get(self, checkpoint_id: str) -> Checkpoint | None:
        """Retrieve a checkpoint by ID.

        Note: This requires scanning files, as we don't maintain
        an index. For production, use a database backend.

        Args:
            checkpoint_id: Unique identifier of the checkpoint

        Returns:
            The checkpoint if found, None otherwise
        """
        if not self.base_path.exists():
            return None

        for parent_dir in self.base_path.iterdir():
            if not parent_dir.is_dir():
                continue
            for task_dir in parent_dir.iterdir():
                if not task_dir.is_dir():
                    continue
                checkpoint_path = task_dir / f"{checkpoint_id}.json"
                if checkpoint_path.exists():
                    return self._read_checkpoint(checkpoint_path)
        return None

    def get_latest(self, task_id: str) -> Checkpoint | None:
        """Get the most recent checkpoint for a task.

        Args:
            task_id: The task identifier

        Returns:
            The latest checkpoint for the task, None if no checkpoints exist
        """
        latest: Checkpoint | None = None
        latest_time: datetime | None = None

        for checkpoint in self.list_by_task(task_id):
            if latest_time is None or checkpoint.created_at > latest_time:
                latest = checkpoint
                latest_time = checkpoint.created_at

        return latest

    def list_by_task(self, task_id: str) -> Iterator[Checkpoint]:
        """List all checkpoints for a task in chronological order.

        Args:
            task_id: The task identifier

        Yields:
            Checkpoints for the task from oldest to newest

        Raises:
            CheckpointReadError: If a checkpoint file cannot be read
        """
        if not self.base_path.exists():
            return

        for parent_dir in self.base_path.iterdir():
            if not parent_dir.is_dir():
                continue
            task_dir = parent_dir / task_id
            if not task_dir.exists():
                continue
            for checkpoint_file in sorted(task_dir.glob("*.json")):
                try:
                    checkpoint = self._read_checkpoint(checkpoint_file)
                    yield checkpoint
                except CheckpointReadError:
                    # Skip corrupted checkpoints but log the error
                    logger.warning("Skipping corrupted checkpoint %s in task %s", checkpoint_file, task_id)
                    continue

    def list_by_parent(self, parent_issue_id: str) -> Iterator[Checkpoint]:
        """List all checkpoints for a parent issue.

        Args:
            parent_issue_id: The parent issue identifier

        Yields:
            All checkpoints belonging to the parent issue

        Raises:
            CheckpointReadError: If a checkpoint file cannot be read
        """
        parent_dir = self._get_parent_dir(parent_issue_id)
        if not parent_dir.exists():
            return

        for task_dir in parent_dir.iterdir():
            if not task_dir.is_dir():
                continue
            for checkpoint_file in sorted(task_dir.glob("*.json")):
                try:
                    checkpoint = self._read_checkpoint(checkpoint_file)
                    yield checkpoint
                except CheckpointReadError:
                    # Skip corrupted checkpoints but log the error
                    logger.warning("Skipping corrupted checkpoint %s in parent %s", checkpoint_file, parent_issue_id)
                    continue

    def delete(self, checkpoint_id: str) -> bool:
        """Delete a checkpoint by ID.

        Args:
            checkpoint_id: The checkpoint to delete

        Returns:
            True if deleted, False if not found
        """
        for parent_dir in self.base_path.iterdir():
            if not parent_dir.is_dir():
                continue
            for task_dir in parent_dir.iterdir():
                if not task_dir.is_dir():
                    continue
                checkpoint_path = task_dir / f"{checkpoint_id}.json"
                if checkpoint_path.exists():
                    checkpoint_path.unlink()
                    return True
        return False

    def delete_task_checkpoints(self, task_id: str) -> int:
        """Delete all checkpoints for a task.

        Args:
            task_id: The task identifier

        Returns:
            Number of checkpoints deleted
        """
        count = 0
        for parent_dir in self.base_path.iterdir():
            if not parent_dir.is_dir():
                continue
            task_dir = parent_dir / task_id
            if not task_dir.exists():
                continue
            for checkpoint_file in task_dir.glob("*.json"):
                checkpoint_file.unlink()
                count += 1
            # Try to remove task_dir if empty
            try:
                task_dir.rmdir()
            except OSError:
                pass
            # Try to remove parent dir if empty
            try:
                parent_dir.rmdir()
            except OSError:
                pass
        return count