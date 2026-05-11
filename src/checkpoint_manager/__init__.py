"""Checkpoint Manager - Multi-Agent Collaboration State Persistence.

This module provides checkpoint-based state persistence for long-running
multi-agent tasks in the Multica platform.

Core Components:
- Checkpoint: State snapshot at a specific point in task execution
- CheckpointStore: Pluggable storage backend (file, sqlite, redis)
- CheckpointManager: High-level API for save/restore operations

Granularity Levels:
- per_node: Save after each agent/node completes
- per_phase: Save after each major phase (planning, execution, review)
- manual: Save only when explicitly requested

Usage:
    manager = CheckpointManager(FileCheckpointStore("./checkpoints"))
    manager.save(task_id="ADM-123", step=1, state={"status": "planning"})
    checkpoint = manager.get_latest(task_id="ADM-123")
    manager.restore(checkpoint)
"""

from checkpoint_manager.models import (
    Checkpoint,
    CheckpointSnapshot,
    CheckpointGranularity,
    ExecutorState,
)
from checkpoint_manager.store import CheckpointStore
from checkpoint_manager.file_store import FileCheckpointStore
from checkpoint_manager.manager import CheckpointManager

__all__ = [
    "Checkpoint",
    "CheckpointSnapshot",
    "CheckpointGranularity",
    "ExecutorState",
    "CheckpointStore",
    "FileCheckpointStore",
    "CheckpointManager",
]