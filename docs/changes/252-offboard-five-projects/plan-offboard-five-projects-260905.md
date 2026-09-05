---
issue: 252
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/252
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - agent-governance
  - security
  - shared-core
depends_on: []
status: contract-drafting
branch: change/252-offboard-five-projects
created: 2026-09-05
updated: 2026-09-05
---

# Implementation plan 统一退出五个项目

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 治理 commit：两份 manifest 删五条、重新 pin non-target 摘要、contract.py 收紧 VM profile 集合与 timer 白名单；`validate` 现算通过 | - | pending |
| T02 | 测试 commit：`test-host-access-broker.sh` 与四份 runtime/shell 测试改用保留项目或合成夹具，#172 回归用例仍在，smoke 全绿 | T01 | pending |
| T03 | 文档 commit：01/03/06 活语句更新，06 新增退出顺序与回滚踩坑条目 | T01 | pending |
| T04 | verification 文档：源码级回滚演练、人工交接项清单与 NOT RUN 记录 | T01, T02, T03 | pending |

治理文件变更（T01）与 runtime 测试变更（T02）分属不同 commit，文档（T03）再分一个，
满足 AGENTS.md 对治理与实现分离的要求。T01 自身必须可独立 revert。

## Expected touch points

T01
- `codex/config/host-access-broker.json`
- `codex/config/gitea-governance.json`
- `codex/runtime/aisoft_host_access/contract.py`

T02
- `codex/tests/test-host-access-broker.sh`
- `codex/runtime/tests/test_host_access.py`
- `codex/runtime/tests/test_gitea_governance.py`
- `codex/tests/test-bootstrap-gitea-service-account.sh`
- `codex/tests/test-apply-classification-labels.sh`
- `codex/tests/test-project-check.sh`

T03
- `01-基础设施-VM-Gitea-Runner.md`
- `03-Issue-Spec-Plan与单闸门开发流程.md`
- `06-运维手册与踩坑集.md`
- `README.md` 与 02/05/07 只在读作当前状态处微调，历史证据不动

不授权扩大 spec。`smoke.sh` 只读不改。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | `jq -r '[.projects[].project_id]' codex/config/host-access-broker.json` 与 `jq -r '[.repositories[].name]' codex/config/gitea-governance.json` |
| AC-2 | `PYTHONPATH=codex/runtime python3 -m aisoft_host_access.cli --access-manifest codex/config/host-access-broker.json --governance-manifest codex/config/gitea-governance.json validate` |
| AC-3 | `python3 -c` 现算 `repository_declarations_sha256(..., exclude_name='NewEMaint')` 与 manifest 取值比对 |
| AC-4 | diff review 加 AC-2 的 `validate` 通过 |
| AC-5 | `bash codex/tests/smoke.sh` |
| AC-6 | 定位并展示改后测试中承载该断言的用例 |
| AC-7 | `git diff origin/main -- codex/tests/smoke.sh` 对守卫行为空 |
| AC-8 | smoke 内的 `test-project-check.sh` 与 `test_gitea_governance.py` 全绿 |
| AC-9 | diff review |
| AC-10 | diff review |
| AC-11 | 在临时副本上 revert 后跑 `validate`，读回 `project_count: 10`，再还原 |
| AC-12 | verification 中的人工交接项清单，逐条 NOT RUN 或实测 |
| AC-13 | 人工重装后由人执行 broker 命令回填；本次预期 NOT RUN |

## 部署与回滚

无应用部署。平台侧生效需要两台重装 broker 与 host-role，属人工交接项。

回滚：`git revert` T01 的治理 commit 后两台重装即恢复十项目治理；VM profile 与
Gitea 身份按 onboarding runbook 重新接入。源码级回滚由 AC-11 在本次实测。
