---
issue: 106
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/106
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - platform-governance
  - agent-behavior
depends_on: []
status: spec-review
branch: change/106-project-align-capability
pr_url:
created: 2026-08-12
updated: 2026-08-12
---

# Implementation plan

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | align checklist reference 草案（AC-1）+ runbook「初始化=对齐」声明与指向（AC-5） | - | pending |
| T02 | NewEMaint 人工对齐反馈回灌：NewEMaint #65/PR #66（2026-08-12 人工合并）完成实战盘点，反馈已修订进 spec §检查合同（pointer-sections/labels-readback/delivery-profile 三处语义）（AC-6） | -（外部闸门已清；实际先于 T01 完成，checklist reference 起草时直接采用已收敛语义） | completed |
| T03 | 两侧 SKILL.md 对齐入口固化 + check-drift CLEAN 验证（AC-2） | T02 | pending |
| T04 | `aisoft-project-check.sh` 检查器 + `test-project-check.sh` + smoke 接入（AC-3、AC-4；可派 Codex，#101 前置已解除） | T02 | pending |
| T05 | 终验与 PR 汇总：smoke 全绿、边界复核（AC-7）、PR 描述引用 NewEMaint 证据 | T03、T04 | pending |

T02 的外部依赖是顺序闸门：NewEMaint 侧 Issue 未完成前不得开始 T03/T04；其反馈只允许
修订 checklist 措辞与 pointer-sections 比对语义，不得扩大 spec 能力边界（扩界即停，
升级给人另立 Issue）。

2026-08-12 状态：#65/PR #66 已人工合并，T02 完成，T03/T04 解除阻塞。NewEMaint 实战
盘点范围外记录的平台侧问题（VM profile 凭据、provider 漂移、broker 标签读回缺口等）
按用户决定在 NewEMaint #65 线跟进，不进入本 change 范围。NewEMaint 剩余两项未盘点
缺口（`docs/changes/_template/` 缺失、交付形态声明行）已在 #65 留评论记录，将由
aisoft-project-check 首跑复现并走 NewEMaint 后续小 PR 回补。

## Expected touch points

- T01：`skill-for-codex/references/project-align.md`（新增）、
  `skill-for-codex/references/onboarding-runbook.md`（开头/§2/§8）。
- T02：同 T01 文件的修订 + 本目录 spec/summary 的 `updated`；NewEMaint 侧证据
  留在其自身 Issue，不进本仓。
- T03：`skill-for-claude/SKILL.md`、`skill-for-codex/SKILL.md`。
- T04：`codex/tools/aisoft-project-check.sh`（新增）、
  `codex/tests/test-project-check.sh`（新增）、`codex/tests/smoke.sh`（接入一行）。
- T05：无新文件；只跑验证与更新 summary `pr_url`/状态。

以上为范围提示，不授权触碰 spec §治理授权清单之外的文件。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | 人工评审 reference：逐项含指向、无合同正文复制；`grep -c` 断言不含 runbook 正文特征串 |
| AC-2 | `bash skill-for-claude/install.sh && bash skill-for-claude/check-drift.sh` → `CLEAN` |
| AC-3 | `bash -n codex/tools/aisoft-project-check.sh`；ShellCheck（若可用）；fixture 手跑六项 |
| AC-4 | `bash codex/tests/test-project-check.sh`；`bash codex/tests/smoke.sh` 全绿 |
| AC-5 | 人工评审 runbook diff：声明在位、只指向不复制 |
| AC-6 | NewEMaint 侧 Issue 链接 + 回灌 diff 评审 |
| AC-7 | `git diff --stat origin/main` 文件清单 ⊆ spec §治理授权清单 |

## 部署与回滚

无部署影响：纯平台仓工具与文档，合并即生效于 source；已安装技能按既有
install/check-drift 流程另行逐机更新。回滚 = revert 单 PR。不需要映射的
`verification` 文档（无 deploy/migration risk flag）。
