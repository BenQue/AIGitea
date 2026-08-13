---
issue: 111
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/111
change_type: bugfix
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - credential-handling
  - shared-core
depends_on: []
status: ready-for-review
branch: change/111-profile-token-file
pr_url:
created: 2026-08-13
updated: 2026-08-13
---

# Plan：平台工具统一 GITEA_TOKEN_FILE 解析（#111）

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 共享解析库 `codex/agent/gitea-token.sh` + 单元测试 `test-gitea-token-lib.sh` + smoke 接入 | - | pending |
| T02 | 5 个工具接入解析库 + 5 个对应测试补两形态与 fail-closed 用例 | T01 | pending |
| T03 | 漂移防护测试 `test-gitea-token-consumers.sh` + smoke 接入 | T02 | pending |
| T04 | `06-运维手册与踩坑集.md` 🕳️19 升级顺序规则 | - | pending |

## Expected touch points

- T01：`codex/agent/gitea-token.sh`（新增）、`codex/tests/test-gitea-token-lib.sh`
  （新增）、`codex/tests/smoke.sh`（bash -n/ShellCheck/运行接入；
  `codex/agent/*.sh` 的 ShellCheck 通配已自动覆盖新库）。
- T02：`codex/tools/aisoft-project-check.sh`、
  `codex/tools/ensure-gitea-collaborator.sh`、`codex/tools/mark-deployed-issues.sh`、
  `codex/tools/sync-gitea-labels.sh`、`codex/tools/sync-gitea-repository-settings.sh`；
  `codex/tests/test-project-check.sh`、`codex/tests/test-ensure-gitea-collaborator.sh`、
  `codex/tests/test-mark-deployed-issues.sh`、`codex/tests/test-sync-gitea-labels.sh`、
  `codex/tests/test-sync-gitea-repository-settings.sh`。
- T03：`codex/tests/test-gitea-token-consumers.sh`（新增）、
  `codex/tests/smoke.sh`（运行接入）。
- T04：`06-运维手册与踩坑集.md`（踩坑集表新增 🕳️19 一行）。

以上为范围提示，不授权超出 spec 治理授权清单的改动。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | 每工具测试新增「仅 `GITEA_TOKEN_FILE`」用例：`bash codex/tests/test-project-check.sh`、`test-ensure-gitea-collaborator.sh`、`test-mark-deployed-issues.sh`、`test-sync-gitea-labels.sh`、`test-sync-gitea-repository-settings.sh` 全 PASS |
| AC-2 | `test-project-check.sh` 中「env 只含 `GITEA_TOKEN_FILE` 的 `--remote`」用例：labels-readback/ci-context 正常执行（aligned fixture 退出 0），无 `远程配置缺失: GITEA_TOKEN`；合并后运维会话对 emaintenance/hsdb/rsdesign/sfm 实测复核 |
| AC-3 | 代码评审：解析逻辑仅存在于 `codex/agent/gitea-token.sh`，5 工具均 source；`test-gitea-token-consumers.sh` 兜底 |
| AC-4 | `bash codex/tests/test-gitea-token-lib.sh`（两形态/并存文件优先/缺失/空/644/symlink/非法字符/不落 stdout）；各工具测试含 644 fail-closed 用例；`bash codex/tests/smoke.sh` 全绿 |
| AC-5 | 评审 `06-运维手册与踩坑集.md` 🕳️19 行内容 |
| AC-6 | `bash codex/tests/test-gitea-token-consumers.sh` PASS；人为构造只认内联的临时脚本时应 FAIL（开发期自测，不入库） |

改动脚本全部过 `bash -n` 与 ShellCheck（本机 `/opt/homebrew/bin/shellcheck`）。

## 部署与回滚

- 无部署动作。工具随仓库 checkout 生效（Mac 与 VM `/mnt/mac` 权威路径）；
  VM `$AGENT_DIR` 安装面（`ensure-gitea-collaborator.sh` + 新库）在下次按运维
  节奏运行 `install-vm.sh` 时更新，更新前旧安装面行为不变（仍只认内联，
  与合并前一致，无中间态破坏——本变更本身就是「消费者过渡期双形态」路径，
  符合 🕳️19 升级顺序规则）。
- 回滚：revert 单个 PR 即恢复原状；无数据、无标签、无远程配置变更。
- 合并后运维复核（AC-2 实测）：VM 侧对四个已迁移项目运行
  `aisoft-project-check --remote`，确认两项远程检查不再因 token 形态 GAP。
