---
issue: 366
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/366
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - agent-governance
  - cross-module
depends_on:
  - 364
status: analyzed
branch: change/366-agents-contract-slim
created: 2026-10-17
updated: 2026-10-17
git_scope:
  - docs/changes/366-agents-contract-slim/summary-agents-contract-slim-261017.md
  - docs/changes/366-agents-contract-slim/spec-agents-contract-slim-261017.md
  - docs/changes/366-agents-contract-slim/plan-agents-contract-slim-261017.md
  - AGENTS.md
  - README.md
  - 03-Issue-Spec-Plan与单闸门开发流程.md
  - 04-Agent编排与定时任务.md
  - 06-运维手册与踩坑集.md
  - 08-双工具共存与实施.md
  - docs/agents/issue-tracker.md
  - docs/agents/triage-labels.md
  - templates/docs/agents/issue-tracker.md
  - templates/docs/agents/triage-labels.md
  - skill-for-claude/aisoft-platform/SKILL.md
  - skill-for-claude/issue-session-flow/SKILL.md
  - skill-for-codex/SKILL.md
  - skill-for-codex/references/private-gitea-access.md
  - codex/skills/aisoft-matt-workflow/SKILL.md
  - codex/skills/issue-session-flow/SKILL.md
  - codex/runtime/tests/test_main_integration.py
  - codex/runtime/tests/test_controller.py
  - codex/runtime/tests/test_host_access.py
  - codex/tests/smoke.sh
  - docs/governance/remediation-roadmap.md
---

## 目标

执行 ADR 0001 D9 与整改路线 R1：`AGENTS.md` 只写维护层稳定规则且不超过 5 KB；单张 Issue 的合同不再出现在 `AGENTS.md`、技能和 `docs/agents/`；triage 加入 ADR D4 准入问题；修复 macOS 上的既有测试失败。

## 决定

- **新 `AGENTS.md`**：按 7 节组织（边界、Issue 与命名、判级与确认、开发编排、Git 合并与部署、治理文件、凭据与验证）加一行目录。smoke 现有对 `AGENTS.md` 的全部短语守卫原样保留。
- **#327 段落**：#327 已于 2026-10-06 关闭，它的“当前收缩合同”是单票状态。13 个文件中的整段删除；仍有效的稳定规则只在 `03` 写一处：main 整合只用普通 fast-forward 并保留 original/current remote tip 的祖先关系，拒绝非法 DAG/tree/范围与并发漂移，禁止 force；Agent/provider 只追加本 Issue 的线性本地 commit。延期项与 FAIL/GAP/NOT RUN 只留在 #327 自己的 `docs/changes/`。
- **钉住段落的测试**：`test_agent_configuration_matches_canonical_templates` 去掉对 `[#327 spec]` 链接的特殊处理，恢复为 `docs/agents/` 与模板逐字节一致；`smoke.sh` 对应注释同步。
- **准入问题**：`triage-labels.md` 与模板加一节，内容取 ADR D4，两者逐字节一致。
- **macOS 测试**：canonical 测试的临时目录在 macOS 上位于符号链接 `/var` 之下，被 `_manifest_digest` 的“路径不得经过链接”检查拒绝。只在测试里对临时目录取 `resolve()`，产品检查不变。
- **平台使用合同**：起草移到 R6，本票不做。

## 迁移对照表（旧 `AGENTS.md` → 新位置）

| 旧规则 | 新位置 |
|---|---|
| 先读 README 与相关分册 | 新 `AGENTS.md` 开头指针与目录行 |
| Issue 主键与命名元组 | 新 `AGENTS.md` §Issue 与命名 |
| slug 2–4 段、≤32 字符、含字母；文档名与 `documents` 映射细则 | `03` 命名章节（缺的补上） |
| 纯编号 legacy 只作兼容；调用方不能用 `legacy` 开关绕过 | 主旨留新 `AGENTS.md`；开关细则迁 `03` |
| AI 判级、`awaiting-triage` | 新 `AGENTS.md` §判级与确认 |
| small 适用清单（Bug 修复、纯文档、只补测试、局部重构） | 主旨留新 `AGENTS.md`；清单迁 `03` 判级章节（已有则不重复） |
| complex 强制清单 | 新 `AGENTS.md` §判级与确认 |
| `approved` 与两个确认点 | 新 `AGENTS.md` §判级与确认 |
| Development Loop 停止条件 | 新 `AGENTS.md` §判级与确认 |
| 治理文件只能由 complex spec 授权、独立受控步骤应用 | 新 `AGENTS.md` §治理文件 |
| AI 参与开发/测试部署；生产只跑确定性脚本 | 新 `AGENTS.md` §Git、合并与部署 |
| 受保护 main、CI context、测试硬门、不可变制品、可回滚 | 新 `AGENTS.md` §Git、合并与部署 |
| Claude 与 Codex 配置独立 | 新 `AGENTS.md` §边界 |
| 凭据、回滚说明、smoke | 新 `AGENTS.md` §凭据与验证 |
| onboarding：`$aisoft-matt-workflow` 校验清单、`$setup-matt-pocock-skills`、tracker `Other`、不另建 Gitea 模板 | 主干留新 `AGENTS.md`；校验清单与“不另建模板”迁 `04` |
| 主路径与兼容 adapter | 新 `AGENTS.md` §开发编排 |
| Agent 本地 commit、Controller push 与 PR、提交确认绑定 exact Issue/branch/policy | 主旨留新 `AGENTS.md`；确认绑定细则已在 `docs/agents/issue-tracker.md`，不重复 |
| #327 当前 Git 收缩合同、#327 生效与延期 | 删除；稳定规则迁 `03` 一处（见“决定”） |
| routine auto 适用条件、manifest 分类、固定 disabled 的仓、broker typed operation | 主旨留新 `AGENTS.md`；细则迁 `03` routine 章节（已有则不重复） |
| merger 身份限制、Gitea 1.26.4 无 merge-only ACL、fail closed 无 fallback | 迁 `03` routine 章节 |
| `triage/ready-for-agent` 不等于 `approved`；禁止项清单 | 新 `AGENTS.md` |
| `IMPLEMENT_PROVIDER=none` | 新 `AGENTS.md` |
| 目录逐项说明 | 新 `AGENTS.md` 一行目录，完整说明在 `README.md` |
| Git：只提交相关文件；不直接改试点应用的 `main` | 新 `AGENTS.md` §Git、合并与部署 |

## 验收标准

- AC1：`wc -c AGENTS.md` ≤ 5120；smoke 对 `AGENTS.md` 的全部短语守卫通过。
- AC2：上表每一行在最终 diff 中都能找到落点。
- AC3：`docs/changes/` 与 `archive/` 之外 `rg '#327 当前'` 无命中。
- AC4：`docs/agents/triage-labels.md` 与模板逐字节一致并包含准入问题。
- AC5：macOS 本机 `bash codex/tests/smoke.sh` 全绿；PR CI 绿。

## 边界

- `git_scope` 为全部范围。不改 runtime 产品代码、broker、CI workflow、installer、manifest；不改 live 标签；不安装技能。
- 不动 NewEMaint 依赖的平台能力。
