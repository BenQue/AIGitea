---
issue: 243
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/243
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags: []
depends_on:
  - 222
status: contract-drafting
branch: change/243-issue-entry-label-sweep
created: 2026-09-05
updated: 2026-09-05
---

# Implementation plan · 243 issue-entry-label-sweep

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 治理合同：清扫节、衍生 Issue 正文要求与默认认领方、skill 入口标签说明，单独提交后停止 | - | pending |
| T02 | broker typed 参数 `entry_label` 与创建时一次性标签写入，含全部同步点与单元测试 | T01 | pending |
| T03 | 真实 Gitea 写入与读回、安装期确认、判级投影与 verification 记录 | T02 | pending |

T01 是治理文件的独立受控步骤：只改治理合同，单独 commit，提交后停止并重新读取改动后的文件，
再进入 T02。T02 不得触碰任何治理文件；T01 不得触碰任何 runtime 文件。

## Expected touch points

**T01（治理合同，单独 commit）**

- `skill-for-claude/issue-session-flow/SKILL.md` —— 新增「开放 Issue 清扫」节
- `codex/skills/issue-session-flow/SKILL.md` —— 同一合同的英文表述
- `skill-for-claude/aisoft-platform/SKILL.md` —— 会话标准动作第 1 步补入口标签参数
- `03-Issue-Spec-Plan与单闸门开发流程.md` —— 衍生 Issue 正文要求与默认认领方
- `docs/agents/issue-tracker.md` —— 同一条约定的英文表述
- `codex/tests/smoke.sh` —— 钉住两份 skill 的新节标题与两条 03/tracker 短语

**T02（runtime，不含治理文件）**

- `codex/runtime/aisoft_host_access/contract.py` —— `EXPECTED_OPERATIONS` 的 `gitea.issue.create`
- `codex/runtime/aisoft_host_access/broker.py` —— `execute()` 参数表、`_gitea()` 的创建分支、
  入口标签校验与 id 解析
- `codex/runtime/aisoft_host_access/runner.py` —— `issue_create()` 签名
- `codex/runtime/aisoft_host_access/cli.py` —— `--entry-label`
- `codex/config/host-access-broker.json` —— 该操作的 `arguments`
- `codex/runtime/tests/test_host_access.py` —— 操作表、创建路由测试，以及逐字钉死
  `execute()` kwargs 的 `test_cli_exposes_only_typed_issue_and_pull_fields`
- `codex/tests/test-host-access-broker.sh` —— `gitea.issue.create` 的 `arguments` 断言
  （`operation_count` 保持 33，本次不新增操作）

**T03（证据）**

- `docs/changes/243-issue-entry-label-sweep/verification-issue-entry-label-sweep-260905.md`
- summary 的 `status`

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | 用候选 manifest 调 `python3 -m aisoft_host_access.cli ... broker --operation gitea.issue.create --entry-label needs-analysis` 建一条真实需要的衍生 Issue，再 `--operation gitea.issue.labels.read --number <新编号>` 读回 |
| AC-2 | `--operation host.access.audit`，核对 project agent 身份与 token scope |
| AC-3 | `codex/runtime/tests/test_host_access.py` 新增的四条否定用例，加一次真实的缺参数调用 |
| AC-4 | `bash codex/tests/test-host-access-broker.sh`，并逐项对照 `06` 踩坑 20 的七处清单 |
| AC-5 | `rg -n '开放 Issue 清扫' skill-for-claude/issue-session-flow/SKILL.md` 与 codex 侧对应短语；smoke 守卫 |
| AC-6 | `rg` 核对 `03` 与 `docs/agents/issue-tracker.md` 的新增段落；smoke 守卫 |
| AC-7 | `bash codex/tests/smoke.sh` |

反向证明：每条新增守卫都先临时改坏被守卫的文件，确认 smoke 变红，再改回。

## 部署与回滚

无部署。参数合同的生效需要在 Mac 与 gitea-ci VM 两台执行
`sudo bash codex/install-host-access-broker.sh`；这是合并后的运维步骤，不在本次 PR 的授权内，
未执行就如实写进未执行项。回滚方式是 revert 本次 merge commit 并在两台重装。
