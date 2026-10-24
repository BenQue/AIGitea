---
issue: 430
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/430
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
depends_on: []
branch: change/430-greenfield-planning
created: 2026-10-24
updated: 2026-10-24
---

# Verification：合同准备证据

本文件仅记录实际观察。实施计划和预期结果不是已通过的验收。

## 当前证据

| 检查 | 结果 | 证据与限制 |
|---|---|---|
| main 基线 | PASS | 2026-10-24 经 broker fresh-fetch，`origin/main=08aac8d5b9af4d334c53bcf34029870f09e50bf0`；本票从该点建分支 |
| 开放 Issue 查重 | PASS | 创建前开放项为 #429 与 #417；均非本需求，未修改 |
| Issue 创建 | PASS | broker 返回 open Issue #430，入口标签 needs-analysis；后续标签以最后读回为准 |
| exact worktree/claim | PASS | `change/430-greenfield-planning`，`/private/tmp/issue-430-greenfield-planning`，owner session `01a16e1b-1085-7712-b5a8-c100d9f74629`；尚无 push |
| 现行合同核对 | PASS | 已读 README、ADR 0001/0002、03/04/08、route-policy、issue-session-flow、aisoft-matt-workflow、getting-started 与 usage 合同/分发实现；这是设计依据，不是新方法运行证据 |
| 受限 publisher | PASS | 使用现有 `publish_spec`/`publish_plan`，输入 broker fresh-read 的 open Issue #430，在 exact branch 首次生成两个映射目标；未跳过路径、日期或 Ticket graph 检查 |
| 文档检查与角色解析 | PASS | `aisoft check-change-documents --porcelain`：change-documents/change-pr-url 均 PASS；`resolve-documents 430` 返回本票四个语义角色映射 |
| 路由解析 | PASS | `aisoft resolve-route 430 --provider codex`：R3 + G1，differences={}；policy SHA256 `184608fd3d3553e7a688712adb99ba98f62e81e9e919e96233f422126486ff40` |
| 草稿结构检查 | PASS | 一次性本地校验：15 个唯一 scope 路径、11 个 AC 均映射、3 个 pending Txx、10 个场景；非 summary 无 status/pr_url；此项不证明方法实际效果 |
| 判级与生命周期读回 | PASS | `classify --apply 430` 后另行 `classify --verify 430`；broker fresh-read 返回 open，且恰有 type/platform、complexity/complex、spec-drafting 三标签，没有 approved |
| Issue 完整正文读回 | PASS | 已通过 broker 回填完整 summary/spec/plan、精确路径/摘要与 Claude 委托，再 fresh-read 逐字相等；初次完整发布 36280 bytes，SHA256 `a6e5355b52e28569df89c1e070b972a83c34047262b3870be97273a0c87d546e`，标签仍为 spec-drafting；此摘要仅指该次发布，不冒充随后提交信息回填后的正文摘要 |
| 新方法实现 / T01–T03 | NOT RUN | 尚未 approved；全部 pending |
| 完整 smoke / 隔离发布包 / 场景核验 | NOT RUN | 属于实施后的验收，本轮不把基线测试冒充新功能验证 |
| Claude 内部材料评估 | NOT RUN | 由负责人交付 Claude；此前通用方案评议不计入本票 |
| 最终实现独立审查 / PR CI | NOT RUN | 没有实施提交或 PR |
| 全局安装 / 下游项目采用 / live / 部署 / UAT | NOT RUN | 不在本票实施范围 |

## 后续记录方式

按 plan 的 AC—任务—场景矩阵追加真实结果及证据位置。每条区分 source/local/isolated export/installed/live/UAT；失败和未运行保持原义。独立审查绑定实际 BASE、HEAD、文件范围、审查 provider 与 finding 处理结果。

本票仅准备合同，未发最终 PR，也未授予任何部署或安装权限。完整 spec/plan 已放入同一 Issue 正文，Claude 评估不依赖未发布分支或聊天历史。固定本地合同提交后，Issue 头部仅回填 exact candidate commit 与最新文档摘要，并再次经 broker fresh-read 核对正文和标签；最终回执保留在本次准备证据目录，交付报告引用实际结果。

本次准备证据目录：`/private/tmp/aisoft-greenfield-contract-261024-h029jbgw`。其中 broker 响应与一次性校验结果是本地辅助证据，不是需要下游安装的制品；Issue 正文和本票文件是评估所需的正式内容。
