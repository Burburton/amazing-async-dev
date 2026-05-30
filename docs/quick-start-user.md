# 用户快速入门

**简单 3 步，开始使用 amazing-async-dev**

---

## 第一步：安装（1 分钟）

```bash
git clone https://github.com/Burburton/amazing-async-dev.git
cd amazing-async-dev
pip install -e .
```

---

## 第二步：创建你的第一个项目（1 分钟）

```bash
# 初始化
python cli/asyncdev.py init create

# 创建产品
python cli/asyncdev.py new-product create --product-id my-app --name "我的应用"

# 创建功能
python cli/asyncdev.py new-feature create --product-id my-app --feature-id feature-001 --name "第一个功能"
```

---

## 第三步：运行完整的一天循环（3 分钟）

### 早上：规划任务
```bash
python cli/asyncdev.py plan-day create --product-id my-app --feature-id feature-001 --task "创建 hello.txt"
```

### 白天：AI 执行
```bash
python cli/asyncdev.py run-day --project my-app --mode external
```
> 这会生成 `ExecutionPack.md`，交给任何 AI 工具执行

### 晚上：生成 review
```bash
python cli/asyncdev.py review-night generate --project my-app
```

### 第二天：继续
```bash
python cli/asyncdev.py resume-next-day continue-loop --project my-app --decision approve
```

---

## 你会看到什么

成功运行后，目录结构是这样的：

```
projects/my-app/
├── product-brief.yaml          # 产品定义
├── runstate.md                 # 当前状态 (planning → executing → reviewing)
├── features/feature-001/
│   └── feature-spec.yaml      # 功能范围和验收标准
├── execution-packs/
│   └── exec-*.md               # 今天 AI 的任务
├── execution-results/
│   └── exec-*.md               # AI 的输出结果
└── reviews/
    └── YYYY-MM-DD-review.md    # 每日 review 包
```

---

## 推荐：先用 Mock 模式测试

```bash
# 不实际执行任何操作，只是测试流程
python cli/asyncdev.py run-day --project my-app --mode mock
```

---

## 常见问题

| 问题 | 解决 |
|------|------|
| "Product already exists" | 使用其他 product-id，或删除 `projects/{id}` 目录 |
| "Feature not found" | 先运行 `new-feature create` 创建功能 |
| "RunState not in executing phase" | 先运行 `plan-day create` 规划任务 |

---

## 下一步

| 资源 | 用途 |
|------|------|
| [examples/single-feature-day-loop](../examples/single-feature-day-loop/) | 完整的 5-10 分钟演练 |
| [docs/cli-reference.md](cli-reference.md) | 所有命令详细参考 |
| [docs/operating-model.md](operating-model.md) | 工作流详细说明 |

---

**时间投入**：每天 20-30 分钟 review。AI 处理其他一切。
