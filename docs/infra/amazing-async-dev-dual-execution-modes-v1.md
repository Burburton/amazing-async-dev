# amazing-async-dev 双执行模式设计 v1

## 1. 设计结论

**主模式先走 External Tool Mode。**  
**Live API Mode 作为增强模式预留，但不作为当前主路径。**

原因：

- 当前开发习惯已经稳定依赖外部编程工具
- Coding Plan 本身更适合编程工具通道
- 现阶段最重要的是先把 workflow 跑顺
- 程序内直连 API 更适合下一阶段逐步接入

---

## 2. 设计目标

`amazing-async-dev` 需要支持两种白天执行方式，但它们都必须服务同一个核心闭环：

- `plan-day`
- `run-day`
- `review-night`
- `resume-next-day`

不管底层怎么执行，系统都要统一围绕这几个对象运转：

- `FeatureSpec`
- `RunState`
- `ExecutionPack`
- `ExecutionResult`
- `DailyReviewPack`

**执行模式可以不同，但对象模型和状态流必须统一。**

---

## 3. 两种模式的定位

## 3.1 External Tool Mode

### 定位
`amazing-async-dev` 负责生成执行包和回收结果，真正的 AI 编码执行交给外部编程工具。

### 典型工具
- Qwen Code
- OpenCode
- Claude Code
- Cline
- 其他支持 Coding Plan 或兼容编程工具协议的工具

### 适合当前阶段的原因
- 最贴合现有开发习惯
- 可以直接复用 Coding Plan
- 更快验证 workflow 是否成立
- 不需要先解决程序内 API 集成复杂度

---

## 3.2 Live API Mode

### 定位
`amazing-async-dev` 自己在 `run-day` 中发起模型调用，直接获得结构化结果。

### 适合后续阶段的原因
- 更适合程序内自动化闭环
- 更利于结构化输出控制
- 更适合未来接 runtime、状态机、失败恢复
- 更适合长期平台化扩展

---

## 4. 总体架构

建议把执行层抽象成统一接口。

```python
class ExecutionEngine:
    def run(self, execution_pack, feature_spec, runstate) -> "ExecutionResult":
        ...
```

然后实现两种引擎：

```python
class ExternalToolEngine(ExecutionEngine):
    ...

class LiveAPIEngine(ExecutionEngine):
    ...
```

`orchestrator.py` 不关心底层是哪种模式，只关心：

1. 读取对象
2. 选择执行引擎
3. 获得 `ExecutionResult`
4. 更新 `RunState`
5. 触发 `review-night`

---

## 5. External Tool Mode 设计

## 5.1 目标
让 `run-day` 输出一个明确的、可交给外部编程工具执行的 `ExecutionPack`，并约定结果回写方式。

## 5.2 `run-day` 行为

默认情况下：

```bash
asyncdev run-day
```

等价于：

```bash
asyncdev run-day --mode external
```

它做这些事：

1. 读取 `FeatureSpec` 和 `RunState`
2. 生成或确认 `ExecutionPack`
3. 把执行包保存到固定路径
4. 输出下一步说明
5. 等待外部工具执行并生成结果

## 5.3 外部工具执行方式

用户把 `ExecutionPack` 交给外部工具，例如：

- Qwen Code
- OpenCode
- Claude Code
- Cline

## 5.4 回写约定

外部工具执行后，结果必须写到固定位置，例如：

```text
projects/<project_id>/features/<feature_id>/execution-result.md
```

或者示例模式下：

```text
examples/single-feature-day-loop/output/execution-result.md
```

## 5.5 `review-night` 行为

`review-night` 读取：

- `ExecutionResult`
- `RunState`

生成：

- `DailyReviewPack`

## 5.6 优点

- 最贴合当前开发习惯
- 直接复用 Coding Plan 的价值
- 不需要先解决 API 直连复杂度
- 更快验证 workflow 是否成立

## 5.7 缺点

- 中间有人为操作
- 结果回写需要约定
- 自动化程度不如 API 直连
- 不同外部工具输出风格可能不一致

---

## 6. Live API Mode 设计

## 6.1 目标
让 `run-day --mode live` 直接调用模型，返回结构化 `ExecutionResult`。

## 6.2 `run-day` 行为

```bash
asyncdev run-day --mode live
```

它做这些事：

1. 读取 `ExecutionPack`
2. 拼装 prompt / request
3. 调用模型
4. 解析结构化输出
5. 生成 `ExecutionResult`
6. 更新 `RunState`

## 6.3 API 来源建议

建议后续先接：

- 百炼通用 API Key
- 百炼兼容 OpenAI 的调用模式

## 6.4 v1 范围

只做最小能力：

- 单 provider
- 单 model
- 单次调用
- 结构化输出
- 基本错误处理

先不要做：

- streaming
- tool calling
- 多 provider
- 长 autonomous loop
- 重型 retry framework

## 6.5 优点

- 自动化程度高
- 更利于以后接完整 runtime
- 更适合结构化输出控制
- 更适合系统内闭环

## 6.6 缺点

- 集成复杂度更高
- 需要处理 API 调用细节
- 需要更严格的输出解析
- 现在做会分散对 workflow 本身的注意力

---

## 7. 两种模式的统一边界

不管哪种模式，下面这些必须一致。

### 输入一致
都必须消费：

- `FeatureSpec`
- `RunState`
- `ExecutionPack`

### 输出一致
都必须产出：

- `ExecutionResult`

### 状态更新一致
都必须回写：

- `RunState`

### 夜间 review 一致
都必须进入：

- `DailyReviewPack`

**模式不同，只影响 `run-day` 如何得到结果，不影响系统其他层。**

---

## 8. CLI 设计建议

## 当前默认

```bash
asyncdev run-day
```

默认等价于：

```bash
asyncdev run-day --mode external
```

## 明确支持两种模式

```bash
asyncdev run-day --mode external
asyncdev run-day --mode live
```

## 以后可以再加

```bash
asyncdev run-day --mode mock
```

建议主定位为：

- `external` = 当前主模式
- `live` = 增强模式
- `mock` = 内部调试模式

---

## 9. 仓库目录建议

```text
runtime/
├─ orchestrator.py
├─ state_store.py
├─ review_pack_builder.py
├─ engines/
│  ├─ external_tool_engine.py
│  └─ live_api_engine.py
└─ adapters/
   ├─ external_tool_adapter.py
   └─ llm_api_adapter.py
```

## 各自职责

### `external_tool_engine.py`
负责：

- 生成执行说明
- 组织外部执行输入
- 等待或读取回写结果

### `live_api_engine.py`
负责：

- 调模型
- 获取结构化输出
- 生成 `ExecutionResult`

### `external_tool_adapter.py`
负责：

- 格式化给外部工具的输入
- 处理回写结果路径与格式

### `llm_api_adapter.py`
负责：

- 封装 API 调用
- 解析模型输出
- 返回统一对象

---

## 10. 推荐实施顺序

## Phase 1
正式把 External Tool Mode 定成主路径。

要做的事：

- `run-day` 默认 external
- 固定 `ExecutionPack` 输出位置
- 固定 `ExecutionResult` 回写位置
- 写清楚给外部工具的执行说明

## Phase 2
把 External Tool Mode 用真实小任务跑顺。

要做的事：

- 选一个真实小 feature
- 白天交给外部工具执行
- 晚上 review
- 次日续接

## Phase 3
再做 Live API Mode 的最小版本。

要做的事：

- 单 provider
- 单 model
- 结构化输出
- `run-day --mode live`

---

## 11. 当前正式策略

建议当前在仓库中明确写成：

- `External Tool Mode` 是默认执行模式
- `Live API Mode` 是预留增强模式
- 所有对象与状态流统一
- `run-day` 的默认语义是“发出执行包并消费结果”，不是“必须程序内直连模型”

---

## 12. 一句话结论

`amazing-async-dev` 当前应以 **External Tool Mode** 为主线，把已经跑顺的 Coding Plan + 编程工具链用起来；同时在架构上预留 **Live API Mode**，让未来的程序内直连执行可以无缝接入。
