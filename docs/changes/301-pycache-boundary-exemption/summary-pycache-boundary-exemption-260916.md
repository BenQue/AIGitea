---
issue: 301
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/301
change_type: test
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 检查器给 SCOPES 内未受版本控制的 Python 字节码开豁免，属功能性更改；它是 required CI 经 smoke 执行的固定证据闸门，而 in-tree pyc 会被 current 回归子进程执行，触发 ci-change 与 security 强制 complex
risk_flags:
  - ci-change
  - security
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-pycache-boundary-exemption-260916.md
  spec: spec-pycache-boundary-exemption-260916.md
  plan: plan-pycache-boundary-exemption-260916.md
  verification: verification-pycache-boundary-exemption-260916.md
confidence: high
override_reason: ''
depends_on: []
status: pr-open
branch: change/301-pycache-boundary-exemption
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/303
created: 2026-09-16
updated: 2026-09-16
---

## 问题/需求总结

`codex/tests/check-release-evidence-boundary.py` 的 `disk_files()` 直接遍历文件系统、
不读 `.gitignore`，于是本地手工跑 `python3 -m unittest`（未带 `-B`）留下的
`codex/runtime/aisoft_release/__pycache__/*.pyc` 被算进「当前文件集」，
`validate()` 的 `disk_files(root) != set(files)` 判定为边界被破坏，报：

```
FAIL: release evidence boundary: current file set differs from the fixed baseline
```

smoke 自己调用该检查时用 `python3 -B`，CI 与干净 checkout 不复现；只有本地开发会话
会撞，而且恰好是在改动之后第一次跑 smoke 时撞，最容易被误归因成自己的改动，
并把人引向受 #65 冻结保护的 `docker-release/` 与 `codex/runtime/aisoft_release/`。

## 影响范围

- 唯一被修改的产品文件：`codex/tests/check-release-evidence-boundary.py`。
  它不在自己的 `SCOPES` 里，因此本次变更不触碰 #65 的证据闸门授权边界。
- 新增一份反向证明测试（落点在 `codex/runtime/tests/`，由 smoke 现有的
  `unittest discover` 自动发现，避免为注册新 `codex/tests/test-*.sh` 而修改 smoke.sh）。
- 不修改 `docker-release/`、`codex/runtime/aisoft_release/` 与任何 pin/baseline 常量。

## 初步方案与建议

两处必须成对落地，缺一不可：

1. **文件集豁免收窄到字节码产物**：`disk_files()` 只跳过「父目录名为 `__pycache__`
   且后缀为 `.pyc`」的常规文件。既不是路径豁免（`__pycache__` 里的非 `.pyc` 文件
   仍然计入），也不是内容豁免（SCOPES 内任何一个普通文件出现仍然变红）。
2. **回归子进程不得执行 in-tree 字节码**：`command_env()` 追加
   `PYTHONPYCACHEPREFIX=<临时目录>`，让 `current_regression` 的解释器把 cache 查找
   重定向到树外。没有这一步，第 1 步会在闸门上开一个真实的洞（见「风险」）。

## 风险

已实测确认（本机 CPython 3.14，见「判级证据」第 3 条）：一个 header 的 mtime/size
与源文件匹配的 `__pycache__/*.pyc` **会被优先执行**，即使解释器带 `-B`——`-B` 只禁写、
不禁读。因此若只做第 1 步，`current_release_regression: PASS` 就可能是一份对
「与 pin 的源码字节不同的字节码」的证据，而这正是本闸门要排除的情形。
第 2 步把这个洞堵上：`PYTHONPYCACHEPREFIX` 同时改变写入与**查找**路径，
使树内 `__pycache__` 对子进程不可见。

次要风险：`PYTHONPYCACHEPREFIX` 以 `PYTHON` 开头，而 `command_env()` 现有逻辑会
过滤掉继承环境里所有 `PYTHON*` 键——必须在过滤之后显式写入，顺序不能颠倒。

## AI 判级

```yaml
change_type: test
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 检查器给 SCOPES 内未受版本控制的 Python 字节码开豁免，属功能性更改；它是 required CI 经 smoke 执行的固定证据闸门，而 in-tree pyc 会被 current 回归子进程执行，触发 ci-change 与 security 强制 complex
risk_flags:
  - ci-change
  - security
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- `contract_effect=change`：`disk_files()` 存在的目的就是抓 SCOPES 内 git 看不见的
  未跟踪新增文件（`validate()` 里它与 `index` 是两个独立比较项）。豁免 `.pyc` 是
  对该闸门判定集合的**收窄**，不是修复一个坏掉的实现，因此不是 `restore`。
  `contract_effect=change` 在 `classification.route()` 里直接强制 complex。
- `risk_flags: ci-change`：该检查器由 `codex/tests/smoke.sh:234` 执行，smoke 是
  required CI 的硬门。先例 #205 同为 `change_type: test`，因触及 required CI
  脚本而判 complex；#203 未触及闸门语义，判 small。本次改的是闸门语义本身。
- `risk_flags: security`：本机实测，在 `pkg/m.py` 旁放一个内容为 `TAMPERED`、
  header 的 mtime/size 与源文件对齐的 `__pycache__/m.cpython-314.pyc`，
  `python3 -B -c "import pkg.m"` 打印 `TAMPERED`；加 `PYTHONPYCACHEPREFIX` 后
  打印 `SOURCE`。这使「字节码豁免」成为一个需要在 spec 里显式论证并补偿的
  安全边界决策，而不是一行 filter。
- 根因已在本仓复现：植入 `codex/runtime/aisoft_release/__pycache__/runner.cpython-313.pyc`
  后 `validate(root)` 报 `current file set differs from the fixed baseline`，
  `disk_files(root) - set(baseline_files(root))` 恰为该单个 `.pyc`；删除后恢复 PASS。
- `required_docs` 含 `verification`：验收标准第 3 条（「完整 smoke 在有/无
  `__pycache__` 两种状态下结论一致」）是一次本地脏树实验，required CI 的工作树
  永远是干净的，无法由 diff review 加 required CI 复现，按 `03` §3 欠一份验证记录。
- `change_control`：`codex/config/gitea-governance.json` 中 `aisoft-platform` 未声明
  `change_control`，取默认 `production`，因此 complex 需要 `spec` 与 `plan`。
- 路由实测：`Classification.from_yaml(...).route(change_control="production")` 返回
  `effective_complexity='complex'`、`lifecycle_label='spec-drafting'`、
  `complexity_label='complexity/complex'`、`required_docs=('summary','spec','plan','verification')`。

### 缺失的 acceptance criteria 或决策

- 无。Issue 正文已给出三条可测验收标准，且第 2 条明确要求反向证明。
