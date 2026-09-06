# GOSIM Agentic Factory - 设计规划

## 1. 项目定位

面向 GOSIM Shenzhen 2026 智能体软件工厂黑客松的**多角色协作 + 测试驱动（TDD）Agent Harness**。

核心目标：让 Agent 团队自主完成从需求到可运行代码的全流程，在统一沙箱中复刻 GitHub + Lark 四大功能模块（Actions、组织权限、审计、Rulesets）。

## 2. 设计原则

- **TDD 优先**：先写测试，再写代码，用测试驱动实现
- **角色分工**：模拟真实开发团队，每个 Agent 职责单一
- **可观测**：所有决策、工具调用、迭代过程全量记录
- **可复现**：相同输入 + 相同种子 = 相同产出
- **Token 高效**：精简 prompt，避免冗余上下文

## 3. 整体架构

```
┌─────────────────────────────────────────────────┐
│                  Harness 编排层                   │
│  Workflow（TDD主循环） · TaskQueue · Context     │
├─────────────────────────────────────────────────┤
│                  Agent 角色层                     │
│  PM · Architect · Tester · Coder · Reviewer · Fixer │
├─────────────────────────────────────────────────┤
│                  工具层                           │
│  FileTool · CommandTool · GitTool · TestTool     │
├─────────────────────────────────────────────────┤
│                  模型层                           │
│  LLM Client（Kimi/GLM/MiniMax/DeepSeek 网关）     │
└─────────────────────────────────────────────────┘
```

## 4. 多角色 Agent 设计

### 4.1 PM Agent（产品经理）
- **职责**：需求拆解、任务规划、优先级排序、进度追踪
- **输入**：原始需求规格
- **输出**：结构化任务列表（Task 列表，每个 Task 含描述、验收标准、依赖关系）
- **关键能力**：将大需求拆成可独立开发、可测试的小任务

### 4.2 Architect Agent（架构师）
- **职责**：技术选型、模块划分、接口定义、数据模型设计
- **输入**：单个 Task + 全局上下文
- **输出**：技术方案文档（模块划分、API 接口、数据结构、文件清单）
- **关键能力**：保证各模块接口一致，避免重复造轮子

### 4.3 Tester Agent（测试工程师）
- **职责**：根据需求和接口定义**先写测试用例**，运行测试，报告结果
- **输入**：Task + Architect 方案
- **输出**：测试代码 + 测试报告（通过/失败/错误信息）
- **关键能力**：边界用例覆盖、测试可执行性

### 4.4 Coder Agent（程序员）
- **职责**：根据测试用例和接口定义编写实现代码
- **输入**：Task + 测试代码 + 接口定义
- **输出**：实现代码
- **关键能力**：让测试通过，代码规范，可维护

### 4.5 Reviewer Agent（审查员）
- **职责**：代码审查、质量把关、报错分析
- **输入**：代码 + 测试报告
- **输出**：审查意见（通过/需修改 + 修改建议）
- **关键能力**：识别代码异味、安全隐患、架构问题

### 4.6 Fixer Agent（修复工程师）
- **职责**：根据测试失败和审查意见修复代码
- **输入**：失败测试 + 错误信息 + 审查意见
- **输出**：修复后的代码
- **关键能力**：精准定位问题，最小化修改

## 5. TDD 主工作流

```
┌──────────────────────────────────────────────────┐
│ 1. PM 接收需求 → 拆解为 Task 列表                  │
└──────────────────────┬───────────────────────────┘
                       ▼
┌──────────────────────────────────────────────────┐
│ 2. 从 TaskQueue 取一个 Task                        │
└──────────────────────┬───────────────────────────┘
                       ▼
┌──────────────────────────────────────────────────┐
│ 3. Architect 输出技术方案 + 接口定义                │
└──────────────────────┬───────────────────────────┘
                       ▼
┌──────────────────────────────────────────────────┐
│ 4. Tester 编写测试用例 → 运行测试（预期全红）        │
└──────────────────────┬───────────────────────────┘
                       ▼
┌──────────────────────────────────────────────────┐
│ 5. Coder 编写实现代码                              │
└──────────────────────┬───────────────────────────┘
                       ▼
┌──────────────────────────────────────────────────┐
│ 6. Tester 运行测试                                 │
│    ├─ 全部通过 → 进入 7                            │
│    └─ 有失败 → Reviewer 分析 → Fixer 修复 → 回到 6  │
└──────────────────────┬───────────────────────────┘
                       ▼
┌──────────────────────────────────────────────────┐
│ 7. Reviewer 代码审查                               │
│    ├─ 通过 → 提交，下一个 Task                      │
│    └─ 需修改 → Fixer 修复 → 回到 6                 │
└──────────────────────────────────────────────────┘
```

### 循环控制
- 单个 Task 最大修复轮次：5 轮
- 超过上限：标记为阻塞，记录原因，继续下一个 Task
- 全部 Task 完成后：PM 做整体验收

## 6. 工具层设计

### 6.1 FileTool
- `read_file(path)` → 文件内容
- `write_file(path, content)` → 写入文件
- `list_dir(path)` → 目录列表
- `create_dir(path)` → 创建目录

### 6.2 CommandTool
- `run(command, cwd, timeout)` → exit_code + stdout + stderr
- 支持超时控制（默认 60s）
- 沙箱路径隔离

### 6.3 GitTool
- `init()` → 初始化仓库
- `add(path)` → git add
- `commit(message)` → git commit
- `diff()` → 查看变更

### 6.4 TestTool
- `run_tests(test_path)` → 测试结果（通过数/失败数/详情）
- 解析测试输出，结构化返回

## 7. 上下文与记忆系统

### 7.1 SharedContext（全局共享上下文）
```python
{
  "project_root": "工作目录路径",
  "requirements": "原始需求",
  "tasks": [Task],           # 全部任务
  "current_task": Task,      # 当前任务
  "architecture": {},        # 架构决策记录
  "files": {},               # 文件内容缓存
  "test_results": [],        # 历史测试结果
  "fix_history": [],         # 修复历史
  "token_usage": 0,          # Token 消耗统计
}
```

### 7.2 Task 数据结构
```python
{
  "id": "task_001",
  "title": "实现 Actions 工作流定义",
  "description": "...",
  "acceptance_criteria": ["..."],
  "dependencies": ["task_000"],
  "status": "pending|in_progress|testing|review|done|blocked",
  "files": ["src/actions/workflow.py"],
  "test_files": ["tests/test_workflow.py"],
  "attempts": 0,
}
```

### 7.3 轨迹记录（Trace）
每个 Agent 的每次调用都记录：
- 时间戳、角色、输入 prompt、输出、工具调用、Token 消耗
- 写入 `traces/` 目录，JSON Lines 格式
- 用于赛后审计和复现

## 8. 技术选型

| 层级 | 选型 | 理由 |
|---|---|---|
| 语言 | Python 3.11+ | 生态成熟，开发快 |
| Agent 框架 | LangGraph | 状态机式工作流，适合多角色编排 |
| 模型调用 | OpenAI 兼容 SDK | 官方网关是 OpenAI 兼容接口 |
| 配置管理 | Pydantic | 数据模型校验，你熟悉 |
| 日志 | structlog | 结构化日志，方便轨迹分析 |
| 测试 | pytest | Python 标准，Agent 生成的测试也用 pytest |

## 9. 分阶段开发计划

### Phase 1：基础骨架（1-2天）
- [ ] 项目目录结构 + requirements.txt
- [ ] LLM Client 封装（支持多模型切换）
- [ ] 工具层实现（FileTool / CommandTool / GitTool / TestTool）
- [ ] SharedContext 数据结构
- [ ] TaskQueue 实现
- **验证**：工具层单元测试通过

### Phase 2：单 Agent 跑通（2-3天）
- [ ] Coder Agent 实现（最简单的角色）
- [ ] Tester Agent 实现
- [ ] 简单 TDD 循环：Tester 写测试 → Coder 写代码 → 跑测试
- **验证**：给定一个简单需求（如"实现一个计算器类"），能自主完成开发并通过测试

### Phase 3：多角色协作（3-4天）
- [ ] PM Agent 实现（需求拆解）
- [ ] Architect Agent 实现
- [ ] Reviewer Agent 实现
- [ ] Fixer Agent 实现
- [ ] 完整 TDD 工作流编排（LangGraph）
- **验证**：给定中等复杂度需求，全流程自主完成，测试通过率 > 80%

### Phase 4：优化与调优（2-3天）
- [ ] Token 效率优化（prompt 精简、上下文裁剪）
- [ ] 错误恢复机制（超时、模型失败、循环上限）
- [ ] 轨迹记录完善
- [ ] 并行任务支持（多个 Coder 同时开发不同模块）
- **验证**：在赛题样例上跑通，记录基线数据

### Phase 5：赛题适配（初赛期间）
- [ ] 对接 ARC-Bench 平台
- [ ] 适配官方模型网关
- [ ] 针对赛题（Actions/权限/审计/Rulesets）优化 prompt
- [ ] 完整跑通初赛赛题

## 10. 目录结构

```
gosim-agentic-factory/
├── DESIGN.md                    # 本文档
├── README.md
├── requirements.txt
├── .gitignore
├── src/
│   ├── __init__.py
│   ├── main.py                  # 入口
│   ├── config.py                # 配置
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base_agent.py        # Agent 基类
│   │   ├── pm_agent.py
│   │   ├── architect_agent.py
│   │   ├── coder_agent.py
│   │   ├── tester_agent.py
│   │   ├── reviewer_agent.py
│   │   └── fixer_agent.py
│   ├── harness/
│   │   ├── __init__.py
│   │   ├── workflow.py          # LangGraph 工作流
│   │   ├── task_queue.py
│   │   ├── context.py           # SharedContext
│   │   └── trace.py             # 轨迹记录
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── file_tool.py
│   │   ├── command_tool.py
│   │   ├── git_tool.py
│   │   └── test_tool.py
│   └── models/
│       ├── __init__.py
│       └── llm_client.py
├── tests/                       # 项目自身测试
│   ├── test_file_tool.py
│   ├── test_command_tool.py
│   └── ...
├── traces/                      # 运行轨迹（gitignore）
└── workspace/                   # Agent 工作目录（gitignore）
```

## 11. 风险与应对

| 风险 | 应对 |
|---|---|
| 模型输出不稳定 | 增加重试机制 + 输出格式校验（Pydantic） |
| Token 消耗过高 | 上下文裁剪 + 摘要压缩 + 多模型路由 |
| 修复循环死锁 | 最大轮次限制 + 策略降级（换模型/换思路） |
| 多 Agent 上下文不一致 | SharedContext 单一数据源，每次操作前同步 |
| 赛题平台对接问题 | 提前看研习营资料，预留适配层 |
