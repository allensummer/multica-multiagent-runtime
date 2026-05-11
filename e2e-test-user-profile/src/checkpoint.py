"""
Checkpoint Manager - E2E Test Implementation
多Agent协作任务状态保存与恢复机制
"""

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Any
from pathlib import Path


@dataclass
class Checkpoint:
    """Checkpoint 数据结构"""
    checkpoint_id: str
    task_id: str
    phase: str
    state: dict[str, Any]
    timestamp: str
    agent_id: str
    metadata: Optional[dict[str, Any]] = None


class CheckpointManager:
    """Checkpoint 管理器 - 支持 per_phase 粒度"""

    def __init__(self, checkpoint_dir: str = ".checkpoints"):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def save_checkpoint(
        self,
        task_id: str,
        phase: str,
        state: dict[str, Any],
        agent_id: str,
        metadata: Optional[dict[str, Any]] = None
    ) -> Checkpoint:
        """
        保存 checkpoint

        Args:
            task_id: 任务ID
            phase: 阶段名称 (如 "phase1", "phase2", "completed")
            state: 任务状态数据
            agent_id: Agent ID
            metadata: 额外元数据

        Returns:
            创建的 Checkpoint 对象
        """
        checkpoint_id = f"ckpt_{task_id}_{phase}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        checkpoint = Checkpoint(
            checkpoint_id=checkpoint_id,
            task_id=task_id,
            phase=phase,
            state=state,
            timestamp=datetime.now().isoformat(),
            agent_id=agent_id,
            metadata=metadata or {}
        )

        # 保存到文件
        filepath = self.checkpoint_dir / f"{checkpoint_id}.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(asdict(checkpoint), f, indent=2, ensure_ascii=False)

        # 更新索引
        self._update_index(checkpoint)

        return checkpoint

    def load_checkpoint(self, task_id: str, phase: Optional[str] = None) -> Optional[Checkpoint]:
        """
        加载 checkpoint

        Args:
            task_id: 任务ID
            phase: 阶段名称，如果为 None 则加载最新的

        Returns:
            Checkpoint 对象，如果不存在则返回 None
        """
        index_file = self.checkpoint_dir / f"{task_id}_index.json"

        if not index_file.exists():
            return None

        with open(index_file, 'r', encoding='utf-8') as f:
            index = json.load(f)

        checkpoints = index.get('checkpoints', [])

        if phase:
            # 查找指定阶段的 checkpoint
            for ckpt_data in reversed(checkpoints):
                if ckpt_data['phase'] == phase:
                    return self._load_checkpoint_file(ckpt_data['checkpoint_id'])
        else:
            # 返回最新的 checkpoint
            if checkpoints:
                return self._load_checkpoint_file(checkpoints[-1]['checkpoint_id'])

        return None

    def _load_checkpoint_file(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """从文件加载 checkpoint"""
        filepath = self.checkpoint_dir / f"{checkpoint_id}.json"

        if not filepath.exists():
            return None

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return Checkpoint(**data)

    def _update_index(self, checkpoint: Checkpoint):
        """更新任务索引"""
        index_file = self.checkpoint_dir / f"{checkpoint.task_id}_index.json"

        if index_file.exists():
            with open(index_file, 'r', encoding='utf-8') as f:
                index = json.load(f)
        else:
            index = {'task_id': checkpoint.task_id, 'checkpoints': []}

        # 添加新 checkpoint 到索引
        index['checkpoints'].append({
            'checkpoint_id': checkpoint.checkpoint_id,
            'phase': checkpoint.phase,
            'timestamp': checkpoint.timestamp
        })

        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)

    def list_checkpoints(self, task_id: str) -> list[dict]:
        """列出任务的所有 checkpoint"""
        index_file = self.checkpoint_dir / f"{task_id}_index.json"

        if not index_file.exists():
            return []

        with open(index_file, 'r', encoding='utf-8') as f:
            index = json.load(f)

        return index.get('checkpoints', [])

    def get_latest_checkpoint_id(self, task_id: str) -> Optional[str]:
        """获取最新 checkpoint ID"""
        checkpoints = self.list_checkpoints(task_id)
        if checkpoints:
            return checkpoints[-1]['checkpoint_id']
        return None