---
issue: 419
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/419
change_type: docs
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - agent-governance
depends_on: []
branch: change/419-root-docs-route-policy
created: 2026-10-22
updated: 2026-10-22
git_scope:
  - AGENTS.md
  - README.md
  - docs/changes/419-root-docs-route-policy/plan-root-docs-route-policy-261022.md
  - docs/changes/419-root-docs-route-policy/spec-root-docs-route-policy-261022.md
  - docs/changes/419-root-docs-route-policy/summary-root-docs-route-policy-261022.md
  - docs/changes/419-root-docs-route-policy/verification-root-docs-route-policy-261022.md
  - docs/governance/remediation-roadmap.md
  - docs/governance/review-evidence-index.md
---

# 根目录文档对齐 R10b 路由表

## 目标与原因

R10b 把路由表放进 `skills/aisoft-platform/references/route-policy.md`，规定它是开发方式的唯一来源，并按工具给出默认入口。
根目录的 AGENTS.md 与 README 是两端会话最先读到的文档，仍写着路由表之前的单一路径，会把 Claude 会话引到 Codex 的入口上。
本批只把这两份文档恢复到已合并的合同，不新增规则。

## Acceptance criteria

- [ ] AC-1：AGENTS.md「开发编排」写明开发方式以路由表为准并带链接，按路由表「默认入口」写出按计划执行时 Claude/Cursor 用 superpowers `executing-plans`、Codex 用 `$implement #N Txx`；smoke 钉住的 AGENTS.md 字面量全部保留；`wc -c AGENTS.md` ≤ 5120。
- [ ] AC-2：README §4 的「路由表」带链接；§5 文档导航有路由表一行，链接到 route-policy.md。
- [ ] AC-3：README §5 里 08 的显示名与 08 一级标题一致。
- [ ] AC-4：README §8 Matt 残余项只列没有证据的部分，与 `08` §5、§7.1 的措辞一致，不新增完成声明。
- [ ] AC-5：README 不新增手写日期或版本（smoke R14 检查通过）；`skills/`、`usage/`、`templates/` 无 diff，`usage/bundle.json` 不变。
- [ ] AC-6：`bash codex/tests/smoke.sh` 通过；反向证明：删掉 AC-1 的路由表链接后 AC 检查命令变红。
- [ ] AC-7：Codex 只读交叉审查候选 head 得 PASS，记入 verification 的「交叉审查」节与 `docs/governance/review-evidence-index.md`；路线图第二轮表追加本批一行。

## 接口、数据与兼容性影响

只改文档，无接口、数据或 schema 影响。不进使用发布包，项目侧无感知。

## 风险与回滚约束

整批 revert 即回滚。AGENTS.md 是 fresh run 重读的治理文件，合并后新会话按新措辞执行；措辞与路由表逐字对应，不引入新的执行规则。

## 非目标

- 不改 `skills/aisoft-platform/SKILL.md`、`usage/CONTRACT.md`、`templates/project/AGENTS.md`、`docs/agents/issue-tracker.md` 中的同一句（范围 B，需发版）。
- 不改 01–08 分册正文，不新增 smoke 钉子。

## 未决问题

无。
