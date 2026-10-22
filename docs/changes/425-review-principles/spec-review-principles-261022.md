---
issue: 425
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/425
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
depends_on: []
branch: change/425-review-principles
created: 2026-10-22
updated: 2026-10-22
git_scope:
  - docs/changes/425-review-principles/plan-review-principles-261022.md
  - docs/changes/425-review-principles/proposals/engineering-principles.patch
  - docs/changes/425-review-principles/spec-review-principles-261022.md
  - docs/changes/425-review-principles/summary-review-principles-261022.md
  - docs/changes/425-review-principles/verification-review-principles-261022.md
  - docs/governance/review-evidence-index.md
  - skills/aisoft-platform/references/engineering-principles.md
  - usage/bundle.json
---

# Spec：补充审查思想

## 目标与来源

以理解变更、发现真实问题、独立判断、风险匹配、完整修复和持续学习指导审查判断，不把外部实践移植成平台具体流程。
思想参考 Anthropic 的 [How the Claude Code team does code review](https://claude.dev/blog/solving-code-review-at-anthropic/)（2026-10-15，2026-10-22 阅读）。文章中的规模、角色分工、并行审查与自动化实践只是来源背景，不构成我们的阶段、轮次、工具或上线效果承诺。

## 精确候选与决定

基线 `9964f740ec6b4328714c1c5244da8ea7b6d9cc8a`（fresh `origin/main`）。冻结的 [治理 patch](proposals/engineering-principles.patch) 只改现有 reference；应用后的全文 SHA-256 必须为 `07c78311875b6c99a68a131d8b1adaf5894d8faf1cb02902e9335bd19983f456`。
保留引言和四项原有工程原则，在来源前加入“让审查发现真实问题，并促进理解与收敛”及五条正文，末尾补充来源与适用边界。此文案已由 Claude Code 审议并经负责人批准。
沿用既有分发机制，`usage/bundle.json` 只用现有 `--release` 追加 1.15.0 / minor；成员集合与所有已发布历史保持不变。

## Acceptance criteria

- [ ] AC-1：原则全文与批准候选字节一致；原有引言和四部分不变；保留 Karpathy 来源并补 Anthropic 来源。
- [ ] AC-2：新增内容只表达审查思想，不增加固定轮次、角色、字段、阈值、状态、路由、门禁、命令或工具要求；具体流程继续由现有平台和项目合同决定。
- [ ] AC-3：bundle 历史仅追加，成员集合不变；隔离构建的 Codex / Claude / Cursor reference 均与源码字节一致；不安装到真实 HOME、不执行项目采用。
- [ ] AC-4：精确 scope、语义文档与现有必需回归通过；下列反例逐项文本审议通过，不把文本审议称为实际模型效果或 UAT。
- [ ] AC-5：治理受控步骤 commit 后停止；fresh Claude Code 进程重读合同，独立审查 exact head；仅形成 source/local 证据，完成后停在最终 PR 确认前。

## 场景与反例

| 场景 | 原则应支持的判断 | 必须排除的误读 |
|---|---|---|
| 个人偏好与项目规范冲突 | 区分真实缺陷、偏好与既有标准；帮助理解取舍 | 因为不争论风格而忽略项目规范 |
| 多个 AI 给出相同意见 | 回到触发条件、影响和证据，人对重要取舍负责 | 模型一致就自动通过或自动阻断 |
| 小改动触及高影响行为 | 根据影响、损害与可逆性分配注意力 | 按行数自动免审或新增统一门禁 |
| 修复后复审与新证据出现 | 聚焦修复及影响，保留可靠新证据 | 重复旧问题，或以收敛为由压制新缺陷 |
| 同类问题跨出本次合同 | 完整解决本次涉及的问题，范围外另记 | 擅自扩大本次改动 |
| 遗漏与误报反复发生 | 在既有合同内考虑更早验证，兼顾缺陷后果和处理成本 | 新增硬指标、固定复盘仪式或自动修改流程 |

## 授权目标与边界

front matter 的八个 `git_scope` 路径是本 Issue 全部写入范围。审议索引只追加本 Issue 行；无路线图批次、E2E 或项目采用事件，不改相关表。
不修改 AGENTS.md / CLAUDE.md、03 / 08、route-policy、技能入口、usage/CONTRACT.md、runtime/test/CI/broker/安装/部署脚本、权限/凭据或项目文件。原则正文不是上述流程的替代合同。

## 兼容与回滚

无接口、schema、运行时代码或依赖变化。既有项目继续 pin 旧包，源码与隔离导出通过不表示实际安装或行为改善。
未发布候选可撤销本 Issue 提交；合并后按新 Issue/PR revert 本批原则增量并追加修正版 bundle，不重写已发布历史，不自动改变项目 pin。

## 未决问题

无。负责人已批准精确候选及按既有治理推进；本合同不添加确认点。
