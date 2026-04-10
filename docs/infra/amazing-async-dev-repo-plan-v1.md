# amazing-async-dev 仓库级规划 v1

## 1. 仓库定位

### 一句话定位
一个面向个人开发者的异步 AI 开发操作系统，支持：

- 白天自动推进 feature
- 夜间人工 review 与决策
- 第二天基于状态继续推进

### 核心原则
- artifact-first
- day-sized execution
- human decision at night
- pause / resume by state
- small closed loops over big plans

### 非目标
第一版不做：
- 通用型多团队平台
- 复杂 UI 优先
- 大量插件生态
- 高并发多项目调度
- 很重的 orchestration engine
- 很多角色系统

---

## 2. 第一版要解决的问题

### 你的真实痛点
- 白天没有时间盯开发
- 晚上只有 1–2 小时
- 想同时推进多个产品想法
- AI 如果没有边界，很容易跑偏
- 第二天很难低成本续上上下文

### 第一版成功定义
如果做到下面 4 条，就算成功：

1. AI 能独立推进一个小 feature 半天以上
2. 晚上你能在 20–30 分钟内看懂结果
3. 真正需要你决定的事项不超过 1–3 个
4. 第二天 AI 能直接继续，不需要重新解释一遍背景

---

## 3. 仓库顶层结构

```text
amazing-async-dev/
├─ README.md
├─ AGENTS.md
├─ LICENSE
├─ .gitignore
├─ docs/
│  ├─ vision.md
│  ├─ operating-model.md
│  ├─ architecture.md
│  ├─ terminology.md
│  └─ decisions/
│     └─ 0001-core-philosophy.md
├─ schemas/
│  ├─ product-brief.schema.yaml
│  ├─ feature-spec.schema.yaml
│  ├─ runstate.schema.yaml
│  ├─ execution-pack.schema.yaml
│  ├─ execution-result.schema.yaml
│  └─ daily-review-pack.schema.yaml
├─ templates/
│  ├─ product-brief.template.md
│  ├─ feature-spec.template.md
│  ├─ runstate.template.md
│  ├─ execution-pack.template.md
│  ├─ execution-result.template.md
│  └─ daily-review-pack.template.md
├─ skills/
│  ├─ task-slicer.md
│  ├─ implement-and-verify.md
│  └─ nightly-summarizer.md
├─ workflows/
│  ├─ plan-day.md
│  ├─ run-day.md
│  ├─ review-night.md
│  └─ resume-next-day.md
├─ runtime/
│  ├─ README.md
│  ├─ orchestrator.py
│  ├─ state_store.py
│  ├─ review_pack_builder.py
│  └─ adapters/
│     ├─ llm_adapter.py
│     ├─ filesystem_adapter.py
│     └─ git_adapter.py
├─ cli/
│  ├─ asyncdev.py
│  └─ commands/
│     ├─ init_project.py
│     ├─ plan_day.py
│     ├─ run_day.py
│     ├─ review_night.py
│     └─ resume_next_day.py
├─ projects/
│  └─ demo-product/
│     ├─ product-brief.md
│     ├─ backlog/
│     ├─ features/
│     ├─ runstate.md
│     ├─ logs/
│     └─ reviews/
├─ tests/
│  ├─ test_runstate.py
│  ├─ test_review_pack.py
│  └─ test_task_slicing.py
└─ examples/
   └─ single-feature-day-loop/
```

---

## 4. 核心对象模型

第一版最重要的不是代码量，而是对象清晰。

### 4.1 ProductBrief
代表一个产品想法的最小起点。

#### 字段
- `product_id`
- `name`
- `problem`
- `target_user`
- `core_value`
- `non_goals`
- `constraints`
- `success_signal`
- `initial_feature_candidates`

#### 作用
把“我想做个产品”压成可以继续拆解的对象。

### 4.2 FeatureSpec
代表一个适合几天内推进的小 feature。

#### 字段
- `feature_id`
- `title`
- `goal`
- `user_value`
- `scope`
- `out_of_scope`
- `acceptance_criteria`
- `dependencies`
- `risks`
- `notes_for_ai`

#### 作用
把 feature 定义成可执行边界。

### 4.3 RunState
这是整个系统最核心的对象。

#### 字段
- `project_id`
- `feature_id`
- `current_phase`
- `active_task`
- `task_queue`
- `completed_outputs`
- `open_questions`
- `blocked_items`
- `decisions_needed`
- `last_action`
- `next_recommended_action`
- `artifacts`
- `updated_at`

#### 作用
让系统能：
- 中断
- 恢复
- 第二天继续
- 生成 review pack

### 4.4 ExecutionPack
白天发给 AI 的执行包。

#### 字段
- `execution_id`
- `feature_id`
- `task_id`
- `goal`
- `task_scope`
- `must_read`
- `allowed_tools`
- `constraints`
- `deliverables`
- `verification_steps`
- `stop_conditions`

#### 作用
避免 AI 白天“自己越做越多”。

### 4.5 ExecutionResult
执行完成后的标准输出。

#### 字段
- `execution_id`
- `status`
- `completed_items`
- `artifacts_created`
- `verification_result`
- `issues_found`
- `blocked_reasons`
- `decisions_required`
- `recommended_next_step`

#### 作用
让白天执行结果可结构化回收。

### 4.6 DailyReviewPack
晚上给你看的唯一核心产物。

#### 字段
- `date`
- `project_id`
- `feature_id`
- `today_goal`
- `what_was_completed`
- `evidence`
- `problems_found`
- `blocked_items`
- `decisions_needed`
- `recommended_options`
- `tomorrow_plan`

#### 作用
压缩你的夜间认知成本。

---

## 5. 核心流程设计

### 5.1 `plan-day`
用途：从 backlog 里选出今天最适合推进的任务。

#### 输入
- `ProductBrief`
- `FeatureSpec`
- 当前 `RunState`

#### 输出
- 更新后的 `RunState`
- 一个 `ExecutionPack`

#### 规则
- 每天只推进一个主目标
- task 必须可在半天到一天内完成
- 超过边界直接拆小
- 有关键决策未完成则不自动开跑

### 5.2 `run-day`
用途：白天 AI 自动执行。

#### 输入
- `ExecutionPack`

#### 输出
- `ExecutionResult`
- 更新后的 `RunState`

#### 白天运行时必须遵守
- 只在 scope 内行动
- 完成 deliverables 后停止
- 遇到 stop condition 必须停
- 必须留下 evidence
- 必须输出 next step 建议

### 5.3 `review-night`
用途：生成你的夜间 review 包。

#### 输入
- `ExecutionResult`
- `RunState`

#### 输出
- `DailyReviewPack`

#### 你的操作
- approve
- revise
- defer
- change priority
- redefine scope

### 5.4 `resume-next-day`
用途：次日继续。

#### 输入
- 昨晚 decision
- 最新 `RunState`

#### 输出
- 新一轮 `ExecutionPack`

---

## 6. 第一版 CLI 设计

CLI 不求多，但要真能跑。

### 命令列表
```bash
asyncdev init
asyncdev new-product
asyncdev new-feature
asyncdev plan-day
asyncdev run-day
asyncdev review-night
asyncdev resume-next-day
```

### 命令说明

#### `asyncdev init`
初始化仓库结构。

#### `asyncdev new-product`
创建 `ProductBrief`。

#### `asyncdev new-feature`
从产品中创建一个 `FeatureSpec`。

#### `asyncdev plan-day`
读取 `RunState`，生成当天任务。

#### `asyncdev run-day`
运行当天执行循环。

#### `asyncdev review-night`
生成 nightly review pack。

#### `asyncdev resume-next-day`
读取你的 decision，推进下一轮。

---

## 7. AGENTS.md 应该怎么写

`AGENTS.md` 不写成很长的总规则大全，只写 4 部分：

### 7.1 Mission
这个仓库是为“日级异步开发闭环”服务的。

### 7.2 Required Objects
AI 行动前必须读取：
- current product brief
- active feature spec
- current runstate
- current execution pack

### 7.3 Hard Rules
- 不得越出 task scope
- 不得自行扩大目标
- 遇到决策型问题必须暂停并记录
- 所有行动都要回写 runstate
- 每天必须输出 review pack

### 7.4 End-of-run Checklist
- deliverables 完成了吗
- evidence 留下了吗
- blocked / decision 写了吗
- next action 写了吗

---

## 8. docs 应该先写哪些

### `docs/vision.md`
写清楚：
- 为什么做这个仓
- 它服务谁
- 成功是什么样

### `docs/operating-model.md`
写清楚：
- 白天怎么跑
- 晚上怎么 review
- 第二天怎么续接

### `docs/architecture.md`
写清楚：
- 对象
- 流程
- 状态更新关系

### `docs/terminology.md`
统一术语：
- product
- feature
- task
- runstate
- execution pack
- review pack
- blocked
- decision

---

## 9. 第一版 skills 规划

第一版只做 3 个 skill。

### 9.1 `task-slicer`
职责：
- 把 feature 切成日级 task
- 保证每个 task 边界稳定
- 给出 stop conditions

### 9.2 `implement-and-verify`
职责：
- 实现
- 自检
- 输出 evidence
- 写 execution result

### 9.3 `nightly-summarizer`
职责：
- 从 runstate 和 result 生成 review pack
- 压缩成适合你夜间阅读的格式

---

## 10. 第一版 runtime 规划

先做轻量版本，不要上来就重量级。

### v0
- 文件系统存储状态
- Python CLI
- 本地 markdown/yaml 对象
- 手动触发命令

### v1
- 增加 SQLite 状态存储
- 支持 pause/resume
- 支持 execution log
- 支持失败恢复

### v2
- 再考虑 durable workflow runtime
- 再考虑外部审批入口
- 再考虑 dashboard

---

## 11. 第一批 feature 规划

仓库初始化后，第一批只做 3 个 feature。

### Feature 001
**Core Object System**
- 定义 6 个核心对象
- 提供 schema + template
- 提供示例数据

### Feature 002
**Day Loop CLI**
- `plan-day`
- `run-day`
- `review-night`
- `resume-next-day`

### Feature 003
**Single Feature Demo**
- 用一个 demo product 跑通完整闭环
- 产出真实 `DailyReviewPack`

---

## 12. 推荐的开发顺序

### 第 1 周
- 写 README
- 写 vision / operating-model / terminology
- 定义 objects schema + templates

### 第 2 周
- 实现 CLI 基础命令
- 实现 runstate 读写
- 实现 review pack 生成

### 第 3 周
- 做 demo product
- 跑一轮完整白天/晚上闭环

### 第 4 周
- 修正对象设计
- 补 tests
- 补失败与 blocked 场景

---

## 13. README 首页建议结构

### 标题
`amazing-async-dev`

### 副标题
Personal Async AI Development OS

### 简介
A lightweight development operating system for solo builders who want AI to make steady progress during the day and only need human review and direction at night.

### 解决的问题
- too little maker time
- too many product ideas
- AI drifts without boundaries
- context is hard to resume the next day

### 核心机制
- artifact-first workflow
- day-sized execution packs
- runstate-based resume
- nightly human review packs

### 当前阶段
v0: single-feature daily loop

---

## 14. 你现在就该做的事

第一步，不写实现，先落 5 个文件：

- `README.md`
- `docs/vision.md`
- `docs/operating-model.md`
- `templates/runstate.template.md`
- `templates/daily-review-pack.template.md`

因为这 5 个文件会决定整个仓库是不是围绕你的真实节奏设计。

第二步，再开始 Feature 001。
