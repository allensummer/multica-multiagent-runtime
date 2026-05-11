# Multica Multi-Agent Runtime

Multica workspace 多 Agent 协作长时间运行方案。

## Overview

- **Hybrid Runtime Architecture**: Master Agent + Executor Pool + Shared State Store
- **Collaboration Modes**: Hierarchical / Sequential / Parallel
- **Hybrid Persistence**: Checkpoint + Event Log
- **Hybrid Communication**: Messages + Shared State

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Master Agent                              │
│  (任务分解、调度、状态管理、结果汇总)                          │
└─────────────────────────┬───────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
   ┌────────────┐  ┌────────────┐  ┌────────────┐
   │  Executor  │  │  Executor  │  │  Executor  │
   │   Pool     │  │   Pool     │  │   Pool     │
   │  (Planner) │  │ (Developer)│  │ (Reviewer) │
   └────────────┘  └────────────┘  └────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │   Shared State Store   │
              │  (Checkpoint + Event) │
              └───────────────────────┘
```

## Project Structure

```
multica-multiagent-runtime/
├── src/
│   ├── master/
│   │   └── checkpoint_manager.py    # Master checkpoint management
│   ├── executor/
│   │   ├── __init__.py
│   │   ├── executor.py              # Executor base class
│   │   ├── pool.py                 # Executor pool management
│   │   └── protocol.py             # @mention protocol implementation
│   ├── checkpoint_manager/
│   │   ├── __init__.py
│   │   ├── file_store.py           # File-based checkpoint storage
│   │   ├── manager.py              # Checkpoint manager
│   │   ├── models.py               # Data models
│   │   └── store.py                # Store interface
│   └── shared-state/
│       ├── __init__.py
│       ├── base.py                  # Base shared state interface
│       ├── file_store.py           # File-based state storage
│       └── models.py                # State models
├── e2e-test-user-profile/           # E2E integration tests
│   ├── src/
│   │   ├── user_profile.py         # User profile feature
│   │   ├── checkpoint.py           # Checkpoint utilities
│   │   └── demo_checkpoint.py      # Checkpoint demo
│   └── tests/
│       └── test_user_profile.py    # Unit tests
├── tests/                           # Additional tests
├── docs/                            # Documentation
├── requirements.txt
└── README.md
```

## Implementation Status

### Phase 1: Core Infrastructure ✅
- [x] Executor Agent Pool (`src/executor/`)
- [x] Shared State Store (`src/shared-state/`)
- [x] @mention Communication Protocol (`src/executor/protocol.py`)

### Phase 2: Persistence ✅
- [x] Checkpoint Manager (`src/checkpoint_manager/`, `src/master/checkpoint_manager.py`)
- [x] Event Log mechanism
- [x] State recovery flow

### Phase 3: Error Handling ✅
- [x] Error Classification
- [x] Root Cause Analysis integration
- [x] Recovery Strategies

### Phase 4: Advanced Features 🔄
- [ ] Adaptive Executor scaling
- [ ] Intelligent task decomposition
- [ ] Performance monitoring

## Executor Agent Pool

| Agent | 职责 | 场景 |
|-------|------|------|
| Planner Agent | 任务分解与规划 | 复杂任务拆分 |
| Developer Agent | 代码实现 | 功能开发 |
| Reviewer Agent | 代码审查 | PR/代码审查 |
| SRE Agent | 基础设施 | 部署/监控 |
| Researcher Agent | 调研分析 | 技术调研 |
| Debugger Agent | 调试排错 | bug定位 |

## Communication Protocol

@mention 触发条件：
- 分派任务给 Executor → @Executor
- 分派架构设计 → @Architect
- 分派开发任务 → @Developer
- 分派审查任务 → @Code Reviewer
- Executor 完成需验收 → @原分派者

## Error Recovery

1. **Root Cause Analysis First** - 根因分析优先
2. **Error Classification** - Retryable / Recoverable / Fatal
3. **Recovery Strategies** - Retry with backoff / Rollback to checkpoint / Escalate

## License

MIT