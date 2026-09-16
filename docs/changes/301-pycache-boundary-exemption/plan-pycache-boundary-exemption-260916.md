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
status: verified
branch: change/301-pycache-boundary-exemption
created: 2026-09-16
updated: 2026-09-16
---

# Implementation plan：release evidence boundary 的 Python 字节码豁免

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 回归子进程不再加载工作树内字节码：`command_env()` 注入 `PYTHONPYCACHEPREFIX`，带篡改 `.pyc` 的反向测试 | - | done |
| T02 | `disk_files()` 只跳过 `__pycache__/*.pyc`，带三条反向证明测试 | T01 | done |
| T03 | 双状态全量 smoke 与 verification 记录 | T02 | done |

**顺序不可颠倒**：T01 是 T02 的补偿措施。先落 T02 会让工作树短暂处于
「豁免已生效、隔离尚未到位」的状态——那正是 spec 里论证的洞。先 T01 后 T02，
每一个 commit 的闸门强度都不低于合并前。

## Expected touch points

- T01：`codex/tests/check-release-evidence-boundary.py`（`command_env()` 与新增
  `cache_prefix()`）；`codex/runtime/tests/test_release_evidence_boundary.py`
  新增 `BytecodeCacheIsolationTests`。
- T02：`codex/tests/check-release-evidence-boundary.py`（`disk_files()` 与新增
  `is_bytecode_artifact()`）；`codex/runtime/tests/test_release_evidence_boundary.py`
  改写 `test_ignored_and_untracked_files_including_bytecode_are_rejected`。
- T03：`docs/changes/301-pycache-boundary-exemption/verification-pycache-boundary-exemption-260916.md`。

测试全部落在**既有的** `codex/runtime/tests/test_release_evidence_boundary.py`：
检查器的行为合同本来就钉在那里——它原有一条用例把「包括字节码在内的未跟踪文件
一律拒绝」写死，本次要改的正是它，另起一个模块只会让同一条合同有两份说法。
该文件匹配 `test_release*.py`，因此既被 smoke 的 `unittest discover`（默认
`test*.py`）执行，也被检查器自己的 `current_regression()` 执行；两条路径都不需要
修改 `smoke.sh`。它的用例只在自己的临时 root 上操作，不改写真实工作树。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | `test_evidence_boundary_checker.py` 中植入 `__pycache__/*.pyc` 后 `validate(root)` 不抛异常；外加 T03 的真实 `python3 codex/tests/check-release-evidence-boundary.py` |
| AC-2 | 同文件两条反向测试：SCOPE 内新增普通文件 → `BoundaryError`；`__pycache__` 内非 `.pyc` 文件 → `BoundaryError` |
| AC-3 | `bash codex/tests/smoke.sh` 各跑一次（工作树含 / 不含 `__pycache__`），照抄退出码 |
| AC-4 | 测试断言 `command_env()` 返回的 env 含 `PYTHONPYCACHEPREFIX`；并用一个 header 对齐的篡改 `.pyc` 证明该 env 下 import 得到源码行为、缺省 env 下得到篡改行为 |

## 部署与回滚

无部署影响。回滚为单 commit `git revert`；该文件无持久状态、无迁移、无外部依赖。
