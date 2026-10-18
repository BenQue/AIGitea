---
issue: 373
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/373
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - external-contract
  - security
  - shared-core
  - platform-governance
depends_on:
  - 371
status: approved
branch: change/373-broker-deproject
created: 2026-10-18
updated: 2026-10-18
---

# #373 计划

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 三份映射文档与 `06` 单票段落替换，本地 commit 后 STOP，重读合同 | - | pending |
| T02 | 预检接口退役：操作、manifest 字段、runtime、测试；采集器归档 | T01 | pending |
| T03 | 治理与 host-access 合同自洽化、注释去项目名、CI 模板注释；补拒绝用例 | T01 | pending |
| T04 | 基线收紧、路线与 ADR 状态、全量 smoke；Codex 独立审查 | T02, T03 | pending |
| T05 | 判级投影与 PR 候选（含删除清单），等第二次确认 | T04 | pending |

## Expected touch points

见 spec 的 `git_scope`。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC1 | `PYTHONPATH=codex/runtime python3 -m aisoft_host_access.cli --access-manifest codex/config/host-access-broker.json --governance-manifest codex/config/gitea-governance.json validate` 读 `operation_count=38` |
| AC2 | `test_gitea_governance.py`、`test_host_access.py` 新增与保留用例 |
| AC3 | `python3 -B codex/tests/check-project-leak.py` 与基线 diff |
| AC4 | `bash codex/tests/smoke.sh` 全绿；PR required CI |
| AC5 | Codex 独立审查结论写入 PR 候选说明 |

## 部署与回滚

无应用部署。合并后安装（不在本票 PR 内）：负责人在 Mac 运行 `sudo bash codex/install-host-access-broker.sh`，并删除已安装的旧模块 `/usr/local/lib/aisoft-host-access/aisoft_host_access/application_preflight.py`（installer 不删除源中已不存在的文件）；VM 侧同样重装并删除 `~/.local/lib/aisoft-loop/aisoft_host_access/application_preflight.py`。读回 `jq '.operations|length'` 为 38。回滚：revert 本 PR 后两台重装。
