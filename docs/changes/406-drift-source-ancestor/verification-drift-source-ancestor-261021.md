---
issue: 406
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/406
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
depends_on:
  - 397
status: verified
branch: change/406-drift-source-ancestor
created: 2026-10-21
updated: 2026-10-21
---

# 验证记录

## 基线与范围

- 基线：`main` = `b2a154d5`；Mac 与 VM 于 2026-10-21 07:48Z 在该提交重装 broker，读回均 `RESULT PASS`（用户实测，见 R16 线程）。
- 范围：`codex/tools/check-installed-drift.py`、`codex/tests/fixtures/installed-drift/test-installed-drift.py`、本目录四份文档。`credential_rotation.py` 未改。
- 候选 head：`01ba7cd9`（T00 `29f4972f`、T01 `bf702522`、Codex 第 1 轮修复 `01ba7cd9`）。

### 改动前观测（合并后无法重放）

在 scratchpad 克隆主检出，于 `b2a154d5` 之上提交一个只改 `README.md` 的提交并把 `refs/remotes/origin/main` 指向它，对**本机真实安装面**只读运行（`--host mac`）：

- main 上的旧检查器：`INSTALLED GAP: install-host-access-broker`，`GAP rotation-source-binding`，`RATCHET regressed`，`RESULT GAP`。
- 候选检查器（`bf702522` 与 `01ba7cd9` 各跑一次）：四个 mac 适用面全部 `INSTALLED PASS`，`RESULT PASS`。

先红：新增 4 个夹具用例在改检查器之前运行，`FAILED (failures=10)`（各子用例在旧「等于 HEAD」语义下 GAP）。

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | PASS | 夹具 `test_rotation_source_may_be_an_ancestor_of_main`：安装后前进一个只改文档的提交，六个安装面全 PASS；本机真实安装面同场景 `RESULT PASS`（见上） |
| AC-2 | PASS | `test_rotation_source_change_after_install_is_gap`：提交改 `credential_rotation.py` 后报 `rotation-file-digest-differ` |
| AC-3 | PASS | `test_rotation_source_outside_main_history_is_gap`：非祖先真实提交、指向祖先的 annotated tag 对象、tree 对象、`HEAD`、`HEAD~1`、`--all`、40/64 位零值、空串，全部 `rotation-source-binding`，恢复后 PASS |
| AC-4 | PASS | `test_rotation_helper_build_binds_install_commit_not_head`：声明 helper 且 main 前进只改文档 PASS；`source_commit` 改为新 HEAD 报 `helper-provenance-binding`；改 `.go` 报 GAP；改 `build.py` 报 `helper-build-input-differ` |
| AC-5 | PASS | 反向证明（每次改后用备份 `cmp` 还原）：还原「等于 HEAD」→ AC-1 与 AC-4 用例 FAIL；去掉 SHA 形状校验 → `HEAD`、`HEAD~1` 子用例 FAIL；helper 绑定改回 HEAD → AC-4 用例 FAIL；去掉 `cat-file` 类型校验 → tag 对象子用例 FAIL；去掉整树比对 → AC-4 用例 FAIL |
| AC-6 | PASS | `bash codex/tests/test-installed-drift.sh` 44 项 OK（`bf702522` 与 `01ba7cd9` 各一次）；`bash codex/tests/smoke.sh` exit 0（同两个 head 各一次，本机 `rg` 为真实 `/opt/homebrew/bin/rg`）；Codex `codex exec -s read-only` 第 1 轮 CHANGES_REQUESTED（F1 helper 的 `build.py` 构建输入未覆盖、F2 未钉对象类型），`01ba7cd9` 修复后第 2 轮 `VERDICT: PASS` |
| AC-7 | NOT RUN | 合并后的两台重装与读回、以及之后再一次文档合并后的读回，晚于本 PR，记入交接 `governance-remediation-handoff-406.md` |

## 遗留风险与未完成项

- VM 侧候选检查器未在合并前实跑（NOT RUN）；代码路径与 Mac 相同，合并后两台读回补证。
- helper 树内任何改动（包括其 README）都会让声明了 helper 的 VM 面报 `helper-build-input-differ`，需要重装；这是保守取舍，Codex 第 2 轮认可。
- 轮换命令本身仍要求传入安装记录里的 `source_sha`（不是当前 HEAD）；本 PR 不改轮换闸门。
- 检查器接受 40 与 64 位 SHA，但轮换工具只接受 40 位；本 PR 不宣称支持 SHA-256 仓库。
