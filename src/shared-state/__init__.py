"""
Shared State Store - Checkpoint + Event Log Storage Backend

Provides durable storage for multi-agent task state:
- Checkpoint snapshots for pause/resume
- Event log for audit trail and state replay
"""

from shared_state_store.base import BaseCheckpointSaver, BaseEventLog
from shared_state_store.file_store import FileCheckpointStore, FileEventLogStore
from shared_state_store.models import (
    Checkpoint,
    CheckpointGranularity,
    CheckpointSnapshot,
    Event,
    EventType,
    ExecutorState,
)

__all__ = [
    "BaseCheckpointSaver",
    "BaseEventLog",
    "FileCheckpointStore",
    "FileEventLogStore",
    "Checkpoint",
    "CheckpointGranularity",
    "CheckpointSnapshot",
    "Event",
    "EventType",
    "ExecutorState",
]