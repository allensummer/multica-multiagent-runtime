"""High-level Checkpoint Manager API."""

import uuid
from datetime import datetime, timezone
from typing import Any

from checkpoint_manager.models import (
    Checkpoint,
    CheckpointGranularity,
    CheckpointSnapshot,
    ExecutorState,
)
from checkpoint_manager.store import CheckpointStore


class CheckpointManager:
    """High-level API for checkpoint save/restore operations.

    This class provides a simplified interface for managing checkpoints
    in a multi-agent collaboration context. It handles:
    - Creating checkpoints with appropriate metadata
    - Tracking executor states
    - Recovery from the latest checkpoint
    - Integration with @mention protocol for seamless recovery

    Usage:
        manager = CheckpointManager(FileCheckpointStore("./checkpoints"))

        # Save a checkpoint
        manager.save(
            task_id="ADM-123",
            parent_issue_id="ADM-123",
            step=1,
            granularity=CheckpointGranularity.PER_PHASE,
            master_state={"current_phase": "planning"},
            executor_states={"dev": ExecutorState("dev-1", "developer")}
        )

        # Get latest checkpoint
        latest = manager.get_latest("ADM-123")

        # Restore from checkpoint
        manager.restore(latest)
    """

    def __init__(self, store: CheckpointStore):
        """Initialize the checkpoint manager.

        Args:
            store: The storage backend to use
        """
        self.store = store

    def _generate_checkpoint_id(self) -> str:
        """Generate a unique checkpoint ID.

        Returns:
            A unique checkpoint identifier
        """
        return f"cp-{uuid.uuid4().hex[:12]}"

    def save(
        self,
        task_id: str,
        parent_issue_id: str,
        step: int,
        granularity: CheckpointGranularity,
        master_state: dict[str, Any] | None = None,
        executor_states: dict[str, ExecutorState] | None = None,
        shared_context: dict[str, Any] | None = None,
        event_index: int = 0,
    ) -> Checkpoint:
        """Save a checkpoint for a task.

        Args:
            task_id: The task identifier
            parent_issue_id: The parent issue this belongs to
            step: Current step number
            granularity: When this checkpoint was created
            master_state: Current master/parent agent state
            executor_states: States of executor agents
            shared_context: Shared context data
            event_index: Index into event log

        Returns:
            The created checkpoint
        """
        snapshot = CheckpointSnapshot(
            master_state=master_state or {},
            executor_states=executor_states or {},
            shared_context=shared_context or {},
        )

        checkpoint = Checkpoint(
            checkpoint_id=self._generate_checkpoint_id(),
            parent_issue_id=parent_issue_id,
            task_id=task_id,
            step=step,
            granularity=granularity,
            snapshot=snapshot,
            event_index=event_index,
            created_at=datetime.now(timezone.utc),
        )

        self.store.save(checkpoint)
        return checkpoint

    def get_latest(self, task_id: str) -> Checkpoint | None:
        """Get the most recent checkpoint for a task.

        Args:
            task_id: The task identifier

        Returns:
            The latest checkpoint, or None if no checkpoints exist
        """
        return self.store.get_latest(task_id)

    def get(self, checkpoint_id: str) -> Checkpoint | None:
        """Get a specific checkpoint by ID.

        Args:
            checkpoint_id: The checkpoint identifier

        Returns:
            The checkpoint if found, None otherwise
        """
        return self.store.get(checkpoint_id)

    def restore(self, checkpoint: Checkpoint) -> dict[str, Any]:
        """Restore task state from a checkpoint.

        Returns the complete state that can be used to resume
        the task from the checkpointed point.

        Args:
            checkpoint: The checkpoint to restore from

        Returns:
            Dictionary with restored state:
            {
                "task_id": ...,
                "step": ...,
                "master_state": ...,
                "executor_states": ...,
                "shared_context": ...,
                "event_index": ...
            }
        """
        return {
            "task_id": checkpoint.task_id,
            "step": checkpoint.step,
            "master_state": checkpoint.snapshot.master_state,
            "executor_states": checkpoint.snapshot.executor_states,
            "shared_context": checkpoint.snapshot.shared_context,
            "event_index": checkpoint.event_index,
        }

    def list_checkpoints(
        self, task_id: str | None = None, parent_issue_id: str | None = None
    ) -> list[Checkpoint]:
        """List checkpoints, optionally filtered.

        Args:
            task_id: If provided, list only checkpoints for this task
            parent_issue_id: If provided, list only checkpoints for this parent

        Returns:
            List of checkpoints
        """
        if task_id:
            return list(self.store.list_by_task(task_id))
        elif parent_issue_id:
            return list(self.store.list_by_parent(parent_issue_id))
        else:
            return []

    def delete(
        self, checkpoint_id: str | None = None, task_id: str | None = None
    ) -> int:
        """Delete checkpoint(s).

        Args:
            checkpoint_id: Specific checkpoint to delete
            task_id: If provided, delete all checkpoints for this task

        Returns:
            Number of checkpoints deleted
        """
        if checkpoint_id:
            deleted = self.store.delete(checkpoint_id)
            return 1 if deleted else 0
        elif task_id:
            return self.store.delete_task_checkpoints(task_id)
        else:
            return 0

    def should_auto_checkpoint(
        self,
        granularity: CheckpointGranularity,
        current_step: int,
        last_checkpoint_step: int | None,
    ) -> bool:
        """Determine if a checkpoint should be created based on granularity.

        Args:
            granularity: The configured granularity level
            current_step: Current execution step
            last_checkpoint_step: Step of the last checkpoint, or None

        Returns:
            True if a checkpoint should be created automatically
        """
        if granularity == CheckpointGranularity.MANUAL:
            return False
        elif granularity == CheckpointGranularity.PER_NODE:
            # Always checkpoint on per_node granularity
            return True
        elif granularity == CheckpointGranularity.PER_PHASE:
            # Checkpoint only if step changed significantly
            # For simplicity, checkpoint if step changed at all
            return last_checkpoint_step is None or current_step != last_checkpoint_step
        return False