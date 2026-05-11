"""Executor Pool - Manages executor registration, discovery, and task dispatch."""

import uuid
from datetime import datetime, timezone
from threading import Lock
from typing import Any

from executor_pool.executor import Executor, ExecutorStatus


class ExecutorPool:
    """Manages a pool of executor agents.

    Provides:
    - Dynamic executor registration
    - Skill-based executor discovery
    - Load balancing across available executors
    - Task assignment and tracking
    """

    def __init__(self):
        self._executors: dict[str, Executor] = {}
        self._lock = Lock()

    def register(
        self,
        executor_id: str,
        executor_type: str,
        skills: list[str],
        metadata: dict[str, Any] | None = None,
    ) -> Executor:
        """Register a new executor agent.

        Args:
            executor_id: Unique identifier for the executor
            executor_type: Type/category (e.g., "developer", "reviewer")
            skills: List of skill identifiers
            metadata: Optional additional metadata

        Returns:
            The registered Executor instance
        """
        with self._lock:
            executor = Executor(
                executor_id=executor_id,
                executor_type=executor_type,
                skills=skills,
                metadata=metadata or {},
            )
            self._executors[executor_id] = executor
            return executor

    def deregister(self, executor_id: str) -> bool:
        """Remove an executor from the pool.

        Returns:
            True if executor was removed, False if not found
        """
        with self._lock:
            if executor_id in self._executors:
                del self._executors[executor_id]
                return True
            return False

    def get_executor(self, executor_id: str) -> Executor | None:
        """Get an executor by ID."""
        return self._executors.get(executor_id)

    def list_executors(
        self,
        status: ExecutorStatus | None = None,
        skill: str | None = None,
    ) -> list[Executor]:
        """List executors with optional filtering.

        Args:
            status: Filter by status (e.g., IDLE only)
            skill: Filter by required skill (must have this skill)

        Returns:
            List of matching Executors
        """
        with self._lock:
            executors = list(self._executors.values())

        if status is not None:
            executors = [e for e in executors if e.status == status]

        if skill is not None:
            executors = [e for e in executors if skill in e.skills]

        return executors

    def find_best_executor(
        self,
        required_skills: list[str],
        max_heartbeat_age: float = 300.0,
    ) -> Executor | None:
        """Find the best available executor for given skills.

        Selection criteria (in order):
        1. Must have all required skills
        2. Must be IDLE and not stale (heartbeat recent)
        3. Highest skill match score
        4. Longest idle time (oldest heartbeat)

        Args:
            required_skills: List of skills required for the task
            max_heartbeat_age: Max seconds since last heartbeat (default 300s = 5min).
                               Stale executors are skipped.

        Returns:
            Best matching Executor or None if no suitable executor
        """
        idle_executors = self.list_executors(status=ExecutorStatus.IDLE)

        # Filter: has skills, not stale
        capable = [
            e for e in idle_executors
            if e.can_execute(required_skills) and not e.is_stale(max_heartbeat_age)
        ]

        if not capable:
            return None

        # Sort by match score (desc), then by oldest heartbeat (asc)
        capable.sort(
            key=lambda e: (-e.match_score(required_skills), e.last_heartbeat)
        )

        return capable[0]

    def assign_task(self, executor_id: str, task_id: str) -> bool:
        """Assign a task to an executor.

        Args:
            executor_id: Target executor ID
            task_id: Task ID to assign

        Returns:
            True if assignment succeeded, False otherwise
        """
        with self._lock:
            executor = self._executors.get(executor_id)
            if executor is None or executor.status != ExecutorStatus.IDLE:
                return False

            executor.status = ExecutorStatus.BUSY
            executor.current_task_id = task_id
            executor.last_heartbeat = datetime.now(timezone.utc)
            return True

    def release_executor(self, executor_id: str, new_status: ExecutorStatus = ExecutorStatus.IDLE) -> bool:
        """Release an executor from current task.

        Args:
            executor_id: Executor to release
            new_status: Status to set (default IDLE)

        Returns:
            True if released, False if executor not found
        """
        with self._lock:
            executor = self._executors.get(executor_id)
            if executor is None:
                return False

            executor.status = new_status
            executor.current_task_id = None
            executor.last_heartbeat = datetime.now(timezone.utc)
            return True

    def update_status(self, executor_id: str, status: ExecutorStatus) -> bool:
        """Update executor status."""
        with self._lock:
            executor = self._executors.get(executor_id)
            if executor is None:
                return False
            executor.status = status
            executor.last_heartbeat = datetime.now(timezone.utc)
            return True

    def heartbeat(self, executor_id: str) -> bool:
        """Update executor heartbeat (indicates executor is alive)."""
        with self._lock:
            executor = self._executors.get(executor_id)
            if executor is None:
                return False
            executor.last_heartbeat = datetime.now(timezone.utc)
            return True

    def get_stale_executors(self, max_age_seconds: float = 300.0) -> list[Executor]:
        """Get executors with stale heartbeats.

        Args:
            max_age_seconds: Maximum age in seconds before considered stale

        Returns:
            List of executors with stale heartbeats
        """
        with self._lock:
            return [
                e for e in self._executors.values()
                if e.is_stale(max_age_seconds)
            ]

    def mark_stale_unavailable(self, max_age_seconds: float = 300.0) -> int:
        """Mark stale executors as OFFLINE.

        Args:
            max_age_seconds: Maximum age in seconds before considered stale

        Returns:
            Number of executors marked unavailable
        """
        count = 0
        with self._lock:
            for executor in self._executors.values():
                if executor.is_stale(max_age_seconds) and executor.status == ExecutorStatus.IDLE:
                    executor.status = ExecutorStatus.OFFLINE
                    count += 1
        return count

    def get_pool_stats(self, max_heartbeat_age: float = 300.0) -> dict[str, Any]:
        """Get current pool statistics.

        Args:
            max_heartbeat_age: Max seconds before considered stale (for stats reporting)

        Returns:
            Dictionary with total count, by_status, by_type, and staleness info
        """
        with self._lock:
            executors = list(self._executors.values())

        stale_count = sum(1 for e in executors if e.is_stale(max_heartbeat_age))

        return {
            "total": len(executors),
            "by_status": {
                status.value: sum(1 for e in executors if e.status == status)
                for status in ExecutorStatus
            },
            "by_type": {
                exec_type: sum(1 for e in executors if e.executor_type == exec_type)
                for exec_type in set(e.executor_type for e in executors)
            },
            "staleness": {
                "checked_executors": len(executors),
                "stale_count": stale_count,
                "max_heartbeat_age_seconds": max_heartbeat_age,
            },
        }