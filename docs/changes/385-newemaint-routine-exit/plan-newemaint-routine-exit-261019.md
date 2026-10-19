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
status: approved
branch: change/385-newemaint-routine-exit
created: 2026-10-19
updated: 2026-10-19
---

# #385 计划

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 两份 manifest 的 NewEMaint 条目与 06 两处表述，validate 与全量 smoke 绿 | - | done |
| T02 | PAT helper 测试改读合成夹具（Codex 首轮审查发现），roadmap 注明退出，Linux 容器跑 helper 测试 | T01 | done |
| T03 | Codex 只读复审结论记入 verification | T02 | done |
| T04 | 合并后两台重装、audit 与保护读回（负责人执行） | T03 | pending |

## Expected touch points

- T01：`codex/config/gitea-governance.json`、`codex/config/host-access-broker.json`、`06-运维手册与踩坑集.md`、本目录四份文档。
- T02：`codex/tools/gitea-pat-helper/helper_test.go`、`process_fixture_test.go`、`codex/tests/integration/test-gitea-pat-helper-process.py`、`codex/tests/smoke.sh`（删死豁免，Codex 复审建议）、`docs/governance/remediation-roadmap.md`。
- T03、T04：只改本目录 verification。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC1、AC2 | 源码 runtime 两个 `validate`；`git diff --stat origin/main` |
| AC3 | `check-project-leak.py` 经 smoke；`git diff` 06 |
| AC4 | `bash codex/tests/smoke.sh`；PR required CI |
| AC7 | python:3.12-bookworm 容器内 `test-gitea-pat-helper-linux.sh` 加 `--isolated-container` 进程测试 |
| AC8 | `git diff` roadmap |
| AC5 | Herdr 派 Codex 只读审查最终 diff |
| AC6 | 合并后 `host.access.audit --project newemaint` 与 `gitea.protection.read` 读回 |

## 部署与回滚

无应用部署。平台侧安装影响：合并后两台重装 broker（先 VM 后 Mac）。回滚为 revert 本 PR 后两台重装；负责人删账号排在 AC6 读回 PASS 之后。
