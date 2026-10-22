---
issue: 416
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/416
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 收口第二轮总验收的平台侧 PARTIAL，改泄漏守卫与 ADR D3 例外、readiness 主机语义、smoke 钉子、收尾技能与治理表，属于 Agent 与平台治理变更并发使用层新版本
risk_flags:
  - agent-governance
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-round2-partial-closeout-261022.md
  spec: spec-round2-partial-closeout-261022.md
  plan: plan-round2-partial-closeout-261022.md
  verification: verification-round2-partial-closeout-261022.md
route:
  process: complex-production
  tier: frontier
  effort: max
  skills: to-spec, to-tickets, executing-plans, verification-before-completion
  method: spec-plan
  verify: full+reverse-proof
  review: cross-provider
  confirm: 2
confidence: high
override_reason: ''
depends_on: []
status: approved
branch: change/416-round2-partial-closeout
pr_url:
created: 2026-10-22
updated: 2026-10-22
---

## 问题/需求总结

第二轮 Codex 总验收（PIN `0bcc3cd8`）结论 ACCEPT WITH FOLLOW-UPS。负责人 2026-10-22 决定退出条件 4 按路线图括号读法收口：
每个 PARTIAL 有承载 Issue 或登记为接受的例外。本 Issue 承载平台仓侧五项：#412 回写错误、D3 残留、readiness 主机语义、
smoke 正文钉子、D6/D9 例外登记。合同见映射 spec。PAT 轮换（#417）与 NewEMaint 升包（NewEMaint#324）不在本批。

## 影响范围

- 治理表：`docs/governance/remediation-roadmap.md`、`review-evidence-index.md`。
- D3：`docs/adr/0001-platform-boundary.md` 例外登记，`codex/tests/check-project-leak.py` 与基线，01/07/12–15 分册的示例名，
  四个 `codex/tools/` 文件的站点默认值。
- readiness：`codex/tools/aisoft-platform-readiness.sh` 与测试，`06`、`skills/issue-session-flow` 收尾节的主机口径。
- smoke：`codex/tests/smoke.sh` 与 `smoke-pin-baseline.json`。
- 使用层：`issue-session-flow` 是发布包成员，发 1.12.0。

## 初步方案与建议

逐条处置 D3 残留：能在不动安装字节或已发布快照的前提下改掉的就改掉，其余在 ADR D3 下登记为例外并写理由，由守卫机器核对
「基线里每个文件都在例外表里」。readiness 仿 #413 的 drift，在非 macOS 主机上拒绝并给出指引，`--render-readme` 照旧可在任何主机跑。
smoke 把 `AGENTS.md` 的整句钉子换成章节结构检查。路线图先改错，再登记 D6/D9 例外与退出条件 4 的收口。

## 风险

- `bootstrap-gitea-service-account.sh` 是 broker installer 安装的文件，合并后需两台重装，否则 VM 漂移检查报 GAP。
- 路线图与审查索引是并行批次共享的表，集成按 `03` §1，冲突时从 `origin/main` 重建只补本批的行。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 收口第二轮总验收的平台侧 PARTIAL，改泄漏守卫与 ADR D3 例外、readiness 主机语义、smoke 钉子、收尾技能与治理表，属于 Agent 与平台治理变更并发使用层新版本
risk_flags:
  - agent-governance
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- 改 ADR 0001、`issue-session-flow` 技能与平台治理表：AGENTS.md「判级与确认」把 Agent 与平台治理列为强制 complex。
- readiness 在 VM 内拒绝要经 `orb -m <site.orbstack_machine>` 实测，不能由 diff review 与 required CI 重放，因此声明 `verification`。

### 缺失的 acceptance criteria 或决策

- 无。AC-1 的 `1db191e` 只指 :62 的「`main` = `1db191e`」一句；R15 行的合并 SHA `1db191e` 是正确事实，保留。
