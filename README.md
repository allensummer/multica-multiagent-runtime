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

## Implementation Phases

### Phase 1: Core Infrastructure
- [ ] Executor Agent Pool 建立
- [ ] Shared State Store 实现
- [ ] 基础通信协议

### Phase 2: Persistence
- [ ] Checkpoint 机制
- [ ] Event Log 机制
- [ ] 状态恢复流程

### Phase 3: Error Handling
- [ ] Error Classification
- [ ] Root Cause Analysis 集成
- [ ] Recovery Strategies

### Phase 4: Advanced Features
- [ ] 自适应 Executor 扩缩容
- [ ] 智能任务分解
- [ ] 性能监控与优化

## License

MIT