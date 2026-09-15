---
issue: 293
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/293
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - agent-governance
  - external-contract
depends_on: []
status: contract-drafting
branch: change/293-delivery-producer-align
created: 2026-09-15
updated: 2026-09-15
---

# Plan · 对齐本机构建-离线交付合同

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 12-Windows §2/§3/§5/§8/§13 改写（spec A-01–A-11） | - | pending |
| T02 | 07 §1 改写（spec B-01–B-03）与确认点 1 认可后的 §2 图（B-04） | - | pending |
| T03 | onboarding-runbook §4.2/§4.4/§4.5 增补（spec C-01–C-04） | - | pending |
| T04 | templates/project/AGENTS.md 项目事实新增两字段（spec D-01–D-02） | - | pending |
| T05 | 全量回归、skill 重装回 CLEAN、verification 填写、AC-1 rg 自证 | T01, T02, T03, T04 | pending |

T01–T04 各自独立、各一个原子 commit；T05 汇总验证并提交 verification，随后进入
`AWAITING_PR_CONFIRMATION`（AC-6 由人完成）。

## Expected touch points

- T01：`12-Windows平台自动部署方案.md`
- T02：`07-内网与生产平移路线.md`
- T03：`skill-for-codex/references/onboarding-runbook.md`
- T04：`templates/project/AGENTS.md`
- T05：`docs/changes/293-delivery-producer-align/verification-delivery-producer-align-260915.md`；
  本机 `~/.claude/skills/aisoft-platform/references/onboarding-runbook.md`（经 installer，不在仓库内）

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | `rg -n '公司 Windows x64 Runner 构建\|唯一正式权威源\|与公司 Gitea 无关系' 12-Windows平台自动部署方案.md` 为 0 命中；三份文档「统一事实句」diff review |
| AC-2 | `rg -n 'versioned release bundle\|GitHub Release\|GitHub 不进入公司信任链' 07-内网与生产平移路线.md` 命中 §1 |
| AC-3 | `rg -n 'locked-mode\|buildx\|emulated\|release_producer\|transport' skill-for-codex/references/onboarding-runbook.md` 命中 §4.2/§4.4/§4.5 |
| AC-4 | `rg -n 'release_producer\|transport' templates/project/AGENTS.md` 命中「项目事实」 |
| AC-5 | `PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests`；`bash codex/tests/smoke.sh`；`PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli check-change-documents --repo .`；`bash codex/tests/test-project-check.sh` |
| AC-6 | PR candidate 输出 policy=manual；人合并；不部署 |

## 部署与回滚

无部署影响；回滚为 revert 唯一 PR。`verification` 文档仍须写，因为 AC-1 跨文档 rg、check-drift
前后观测与全量 Python 测试不在 required CI（只跑 smoke）里。
