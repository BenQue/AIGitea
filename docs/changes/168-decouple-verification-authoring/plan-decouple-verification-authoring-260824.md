---
issue: 168
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/168
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - agent-governance
depends_on: []
status: approved
branch: change/168-decouple-verification-authoring
created: 2026-08-24
updated: 2026-08-24
---

# Plan · 把「何时声明 verification」的判据从题材换成证据来源

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | `03` §3 的 canonical 规则：目录树注释 + 新小节「何时声明 `verification`」 | - | done |
| T02 | `verification.md` 模板重构：部署三段收敛为一节条件段落 + 不部署时的合格标准 | T01 | done |
| T03 | 5 处复述与 T01 对齐：`summary.md` 模板、`gitea-analyze-change` 第 10 条、两个 `*-analyzer.sh` prompt、`gitea-development-loop` 第 2 条第 3 项 | T01 | done |
| T04 | 回归证据：全历史 `resolve-documents`/`check-change-documents`、`bash -n`、`smoke.sh`，并把 AC-2 的实例写成本 change 的 `verification` 文档 | T02, T03 | done |

T01 先行是因为其余四处都是它的复述——canonical 出处未定稿之前对齐没有基准。

## Expected touch points

- T01：`03-Issue-Spec-Plan与单闸门开发流程.md`（§3；**不动 §11**）
- T02：`templates/docs/changes/_template/verification.md`（正文段落；front matter 原样）
- T03：`templates/docs/changes/_template/summary.md`、
  `codex/skills/gitea-analyze-change/SKILL.md`、
  `codex/skills/gitea-development-loop/SKILL.md`、
  `codex/agent/codex-analyzer.sh`、`codex/agent/claude-analyzer.sh`
- T04：`docs/changes/168-decouple-verification-authoring/verification-*.md`（新增）

范围提示，不授权扩大 spec §5 的授权清单。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | Review `03` §3 新小节：存在二行判定表 + 「不隐含要部署」一句；`grep -n "何时声明" 03-*.md`；与 §11 逐句比对无冲突 |
| AC-2 | Review 新模板：部署内容只剩一节且带 `TEMPLATE_CONDITIONAL` 删除指示；实例检查 `! grep -nE '^#{2,3} (部署验收\|重复部署\|故意失败)' docs/changes/168-*/verification-*.md`（标题锚定，避免把正文里对该节的说明误判为残留段落） |
| AC-3 | 退役措辞零命中：`grep -rn "for deployment or migration\|部署或迁移再追加\|deploy/migration 必须" 03-*.md templates/docs/changes/_template/ codex/skills/ codex/agent/`。**不能**只 grep `部署或迁移`——新模板与 `03` §3 用「实际部署或迁移」界定条件段落的适用范围，那是新规则的一部分，不是残留 |
| AC-4 | `git status --porcelain docs/changes/` 只有本 change 新目录；`PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli check-change-documents --repo .` 改动前后同为 `changes=75 pass=2 gap=0`（本 change 目录并入后为 76） |
| AC-5 | `bash -n codex/agent/codex-analyzer.sh`、`bash -n codex/agent/claude-analyzer.sh`、`bash codex/tests/smoke.sh` |

## 部署与回滚

无部署影响。回滚 = revert 本 PR。

本变更虽不部署，`required_docs` 仍含 `verification`：AC-2 的证据是一份「照新模板
写出来的文档」，而实例无法从 diff 中读出——按 T01 写入的新规则，这落在「不能由
diff review + required CI 复现」一侧。映射的 `verification` 文档同时是该规则的
第一次自我应用与 AC-2 的交付物。
