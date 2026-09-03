---
issue: 237
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/237
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - ci-guard
depends_on:
  - 233
status: pending
branch: change/237-deproject-company-delivery
created: 2026-09-03
updated: 2026-09-03
---

# Verification · 去项目化收尾

## 基线与范围

- Commit SHA: 待填写（随最后一个 ticket 提交）
- 基线：`origin/main` = `c98b2e5`（Merge PR #236，#233 prune-stale-docs）
- 环境: Mac 本机 checkout（`/Users/benque/MyDocs/AISoftPlatform`，worktree
  `/private/tmp/issue-237-deproject-company-delivery`）
- 本记录负责证明的 acceptance criteria: AC-1～AC-6（spec 同名条目）

## 基线观测（改动前，只能在此刻留下）

| Command / check | Result | Evidence |
|---|---|---|
| `grep -rci NewEmaint company-delivery/ \| grep -v ':0$'` | 合计 23 | `README.md` 9、`runbook.md` 8、`compatibility/newemaint-company-pilot-v1.json` 1、`schema/inventory-v1` 2、`inventory-v2` 1、`inventory-v3` 1、`templates/handoff-manifest.example.json` 1（与 Issue 正文 23 处一致） |
| `find company-delivery -type f \| wc -l` | 19 | 与 spec 判定表 D-01～D-19 一一对应 |
| `grep -n '新项目默认' *.md` | 2 处 | `07…md:141`（§5.1 标题，本 Issue 范围）、`01…md:106`（「不再接受为新项目默认」——否定句，不把任何形态当默认，不在范围） |
| `grep -rn -i 'newemaint' codex/runtime/aisoft_company_delivery/` | 4 处 | `bundle.py:33` `COMPATIBILITY_PATH`、`contract.py:49`/`:357`、`collector.py:350` timer unit 名（runtime 绑定标识符，非目标） |
| `grep -n 'newemaint-prod' codex/runtime/tests/test_company_delivery.py` | 1 处 | `:2926` 测试钉住 runbook 短语 `aisoft-docker-release-gate <action> newemaint-prod <full-sha>` |
| `bash codex/tests/smoke.sh`（worktree = `origin/main`） | PASS，rc=0 | `Ran 651 tests … OK` + `Codex platform static smoke checks passed.` |
| `bash skill-for-claude/check-drift.sh` | CLEAN，rc=0 | 两份 SKILL.md 与源码一致（#233 references 已在本会话之外重装） |

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| 待执行 | NOT RUN | 待填写 |

命令与输出照实抄。改动前才观测得到的证据（基线状态、改动前后对比、先看着测试红）
只有写在这里才留得下来——改动合并后就无法重放。

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | NOT RUN | 待填写 |
| AC-2 | NOT RUN | 待填写 |
| AC-3 | NOT RUN | 待填写 |
| AC-4 | NOT RUN | 待填写 |
| AC-5 | NOT RUN | 待填写 |
| AC-6 | NOT RUN | 待填写 |

## 遗留风险与未完成项

- 待填写。

合格标准：每条 acceptance criterion 都有一条真实执行过的命令或一次真实观测支撑；
不得把 `NOT RUN` 改写为通过；不可达的环境与未执行项在此显式写明。
