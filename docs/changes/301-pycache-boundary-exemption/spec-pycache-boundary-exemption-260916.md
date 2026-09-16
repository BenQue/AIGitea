---
issue: 301
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/301
change_type: test
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - ci-change
  - security
depends_on: []
status: contract-drafting
branch: change/301-pycache-boundary-exemption
created: 2026-09-16
updated: 2026-09-16
---

# Spec：release evidence boundary 的 Python 字节码豁免

## 目标与原因

`codex/tests/check-release-evidence-boundary.py` 是 #65 冻结范围的证据闸门，由
`codex/tests/smoke.sh` 在 required CI 中执行。它的 `disk_files()` 直接遍历文件系统，
把 SCOPES 内所有常规文件算进「当前文件集」，再与固定 baseline 的 git 文件集比较。

本地开发会话手工跑 `python3 -m unittest`（未带 `-B`）会在
`codex/runtime/aisoft_release/__pycache__/` 留下 `.pyc`；它们不受版本控制、
不出现在 git index，于是闸门报

```
FAIL: release evidence boundary: current file set differs from the fixed baseline
```

该红与开发者的改动无关，信息量只有一行，并把人指向受 #65 冻结保护的目录。
CI 与干净 checkout 不复现（smoke 用 `python3 -B` 调用它），所以只有本地会撞，
而且总是在改完之后第一次跑 smoke 时撞——最容易被误归因成自己越界。

本变更让闸门对「Python 字节码产物」这一类产物免疫，同时**不降低**它对
「跑的字节 = 审过的字节」的保证强度。

## 这不是一个纯粹的过滤问题

`-B` 只禁止**写**字节码，不禁止**读**。一个 header 的 mtime/size 与源文件对齐的
`__pycache__/*.pyc` 会被解释器优先执行，源文件根本不会被编译。实测（本机 CPython 3.14）：

```
--- default (-B):            TAMPERED
--- PYTHONPYCACHEPREFIX:     SOURCE
```

即：在 `pkg/m.py`（内容 `VALUE = "SOURCE"`）旁放一个编译自 `VALUE = "TAMPERED"`、
header 被改写成与当前源文件 mtime/size 一致的 `.pyc`，`python3 -B -c "import pkg.m"`
打印 `TAMPERED`。

`validate()` 的文件集比较今天是唯一能发现这种 in-tree 字节码的检查项
（内容 pin 只覆盖 `.py` 的 bytes，index 比较看不见未跟踪文件）。而
`current_regression()` 正是在 `root` 里 `import` `aisoft_release` 的。
因此**只做过滤**会让 `current_release_regression: PASS` 变成一份可能对
「与 pin 不同的字节码」成立的证据——这恰好是本闸门要排除的情形。

结论：豁免必须与隔离成对落地。

## Acceptance criteria

- [ ] AC-1：`codex/runtime/aisoft_release/` 下存在 `__pycache__/*.pyc` 时，
      `python3 codex/tests/check-release-evidence-boundary.py` 仍然退出码 0 并输出 JSON。
- [ ] AC-2：豁免只针对 Python 字节码产物。在任一 SCOPE 内新增一个普通文件时
      检查必须变红；`__pycache__` 目录内的非 `.pyc` 文件同样必须使检查变红。
      两条都有自动化测试反向证明。
- [ ] AC-3：完整 `bash codex/tests/smoke.sh` 在有 `__pycache__` 与无 `__pycache__`
      两种状态下结论一致（均通过）。
- [ ] AC-4：`check()` 的回归子进程不加载工作树内的 `__pycache__`；
      有自动化测试证明被篡改的 in-tree `.pyc` 不会改变回归所执行的行为。

## 接口、数据与兼容性影响

- 唯一被修改的产品文件：`codex/tests/check-release-evidence-boundary.py`。
  它不在自己的 `SCOPES` 里，因此本变更不触碰 #65 的证据闸门授权边界。
- 不修改 `docker-release/`、`codex/runtime/aisoft_release/`、`BASELINE`、
  `CURRENT_SOURCE_PINS`、`CONTENT_EXEMPT`、`SCOPES` 或任何 sha256 常量。
- 不修改 `codex/tests/smoke.sh`：反向证明测试落在既有的
  `codex/runtime/tests/test_release_evidence_boundary.py`，由 smoke 已有的
  `unittest discover` 与检查器自己的 `current_regression()` 两条路径执行。
- 检查器的 JSON 输出键集合不变。
- 对调用方唯一可见的行为变化：SCOPES 内出现 `__pycache__/*.pyc` 时由 FAIL 变为 PASS。

## 风险与回滚约束

| 风险 | 处置 |
|---|---|
| 豁免被写成路径豁免（整个 `__pycache__` 目录跳过） | 判据必须同时要求父目录名为 `__pycache__` **且** 后缀为 `.pyc`；测试反向证明 `__pycache__/README.md` 仍然变红 |
| 豁免被写成内容豁免（任意未跟踪文件跳过） | 测试反向证明 SCOPE 内新增普通文件仍然变红 |
| 被篡改的 in-tree `.pyc` 被回归执行 | `command_env()` 注入 `PYTHONPYCACHEPREFIX` 指向临时目录，使查找与写入都绕开工作树 |
| `PYTHONPYCACHEPREFIX` 被 `command_env()` 既有的 `PYTHON*` 过滤吃掉 | 必须在过滤之后写入；测试断言返回的 env 里该键存在 |
| 临时目录泄漏 | 由 `check()` 用 `tempfile.TemporaryDirectory` 管理生命周期，进程退出即清理 |

回滚：`git revert` 单个 commit。该文件无持久状态、无迁移、无外部依赖。

## 非目标

- 不改变 #65 的授权边界，不推进任何 pin。
- 不为检查器引入 `.gitignore` 解析或任何 git 忽略语义（那会把 git 配置变成闸门的输入）。
- 不改变 `smoke.sh` 的调用方式。
- 不处理 SCOPES 之外目录的 `__pycache__`（检查器本来就不看它们）。

## 未决问题

无。
