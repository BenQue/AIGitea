---
issue: 385
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/385
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - security
  - platform-governance
depends_on: []
status: verified
branch: change/385-newemaint-routine-exit
created: 2026-10-19
updated: 2026-10-19
---

# #385 验证记录

## 基线与范围

- Commit SHA: `e93e17f`（实现提交 `65b943e`、`bbb333c`、`e93e17f`）
- 基线：`origin/main` = `f49f15a`
- 环境: macOS 本机源码 runtime（`codex/tools/host-access-broker.sh` 在源码树内读仓库 manifest）；gitea-ci 本地 Gitea
- 本记录负责证明的 acceptance criteria: AC1–AC8

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| 改动前 `host.access.audit --project newemaint`（仓库 manifest） | BLOCKED_EXTERNAL | `{"code": "HTTP_403", "status": "BLOCKED_EXTERNAL"}`，退出码 20，2026-10-19 |
| 改动前 `gitea.protection.read --project newemaint` | PASS | `merge_whitelist_usernames: ["admin"]`，`updated_at` 2026-09-19 |
| 候选 manifest 下同一条 audit | PASS | `routine_merge.enabled=false`、`identity=null`、`merge_allowlist_state=converged` |
| `aisoft_gitea_governance.cli validate`（仓库 manifest，`65b943e` 起） | PASS | `"result": "PASS"`，7 个仓库 |
| `aisoft_host_access.cli validate`（同上） | PASS | `operation_count 38`、`project_count 7`、`status PASS` |
| macOS 全量 `bash codex/tests/smoke.sh` @ `65b943e` 首跑 | FAIL | 红在 #379 守卫：本机残留未跟踪的 `codex/skills/.DS_Store`（Finder 产物，非本 diff）；删除该文件与空目录后重跑 rc=0 |
| macOS 全量 smoke @ `bbb333c` | PASS | rc=0，`Codex platform static smoke checks passed.` |
| macOS 全量 smoke @ `e93e17f` | PASS | rc=0；`PASS: project-leak (4 baseline files, 11 hits)`，与改动前相同 |
| `python:3.12-bookworm` 容器 `test-gitea-pat-helper-linux.sh`（`bbb333c` 的测试改动） | PASS | `go test -race` 两包 `ok`；`PASS: pinned native Linux helper build/model/race/process checks` |
| 同容器 `test-gitea-pat-helper-process.py --isolated-container --fixture` | PASS | `PASS: actual Linux helper isolated model inspect/exact revoke/driver-error canary/other-token preservation; live NOT RUN` |
| 守卫反向证明：`real_manifest_ref` 对 `65b943e` 版进程测试 / 新版 | PASS | 命中 1 / 0 |
| `bash -n` 与 `shellcheck -S warning codex/tests/smoke.sh` | PASS | 无输出 |
| Codex 只读审查第 1 轮（Herdr，`65b943e`） | FAIL | P1：`helper_test.go` 的 `TestCanonicalManifestBindings` 读真实 manifest 并要求 NewEMaint routine 绑定，置空后 `main.go` 返回 `TARGET_UNMANAGED`，会红在 required CI；另建议 roadmap 注明退出。依据为源码调用链，未在旧测试上实跑 |
| Codex 只读复审（Herdr，`65b943e..bbb333c`） | PASS-WITH-NITS | P1 关闭；非阻塞：删 smoke 对进程测试的死豁免，已在 `e93e17f` 处理 |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC1 | PASS | `git diff f49f15a e93e17f -- codex/config`：governance 三处、host-access 一处；LocalWMS 未变（Codex 第 1 轮逐字节核对） |
| AC2 | PASS | 两个 validate PASS；diff 文件全部在 spec `git_scope` 内（Codex 复审核对 12 项） |
| AC3 | PASS | `06` 第 569、606 行改为「待定（原定对象随 #385 退役）」；泄漏计数 11 不变 |
| AC4 | 本机 PASS，CI 待 PR | smoke @ `e93e17f` rc=0；PR required CI 尚未运行 |
| AC5 | PASS | Codex 第 1 轮 FAIL → 修复 → 复审 PASS-WITH-NITS → nit 已处理 |
| AC6 | NOT RUN | 合并后由负责人执行两台重装与读回 |
| AC7 | PASS | 容器内 helper 构建/race/进程测试全绿；守卫反向证明 1/0 |
| AC8 | PASS | roadmap 总规则 2 已注明 |

## 遗留风险与未完成项

- AC6 需负责人在合并后执行两台重装；会话内 sudo 不可用。PAT helper 测试源属于其安装 provenance，重装后 `check-installed-drift` 才会与新源一致。
- 删除 `newemaint-routine-merger` 账号与凭据文件由负责人在 AC6 读回 PASS 之后做，之后回告 NewEMaint #294。
