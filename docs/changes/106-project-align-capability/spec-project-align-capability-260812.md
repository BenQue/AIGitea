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

# Spec

## 目标与原因

初始化新项目与更新已接入项目统一为一个幂等能力：「把项目对齐到平台当前合同」。
对已对齐仓库运行是 no-op；对未接入仓库运行等价于 onboarding；对存量漂移仓库运行
产出精确缺口清单并按平台既有流程（逐仓独立 Issue + 小 PR）修复。

能力分两层：

1. **对齐入口（Agent 行为）**：复合技能 `aisoft-platform` 的共享 reference
   `project-align.md`——checklist 驱动的对齐操作指引。checklist 只指向
   onboarding-runbook 章节、`templates/` 路径与工具命令，不复制第二份事实源。
2. **确定性检查器（平台工具）**：`codex/tools/aisoft-project-check.sh`——只读、
   确定性、可 gate 的 PASS/GAP 检查，同 `check-drift.sh` 思路，覆盖对齐状态中
   可机器判定的子集。

## 检查合同（aisoft-project-check）

调用形态（固定参数，不接受任意 shell）：

```bash
codex/tools/aisoft-project-check.sh --repo <目标仓库checkout> [--kind software|docs] [--remote] [--today YYYY-MM-DD]
```

- `--repo`：目标仓库本地 checkout 绝对路径（必填）。
- `--kind`：`software`（默认）或 `docs`；`docs` 仓库对 `architecture-lock`、
  `delivery-profile` 输出 `SKIP`（附声明原因），不虚构部署合同（runbook §1）。
- `--remote`：显式启用远程读回检查；需要 `AGENT_ENV_FILE`（复用
  `sync-gitea-labels.sh` 的凭据模式：`GITEA_URL/GITEA_OWNER/GITEA_REPO/GITEA_TOKEN`，
  token 经 curl stdin config 传输，不进 argv/日志）。缺省时远程检查输出 `SKIP`。

六项检查（check id 固定）：

| id | 判定 | 事实源 |
|---|---|---|
| `pointer-sections` | 目标仓 `AGENTS.md`「平台声明（常驻指针）」「每 Issue 开发路径」两节与模板当前版本逐字节一致（剥离模板复制注释；标题行 `<项目名>` 占位除外）；`CLAUDE.md` 内容恰为 `@AGENTS.md`。不要求「工具分工」「项目事实」标题在位——项目可保留自有章节结构（NewEMaint #65/PR #66 纯新增对齐已由人合并背书），交付形态事实由 `delivery-profile` 检查负责 | `templates/project/AGENTS.md`、`templates/project/CLAUDE.md` |
| `change-templates` | 目标仓 `docs/changes/_template/{summary,spec,plan,verification}.md` 与平台同名模板 byte-identical | `templates/docs/changes/_template/` |
| `architecture-lock` | `.aisoft/architecture.json` 存在且 strict JSON；`.aisoft/architecture.lock.json` 已提交（NewEMaint 参照布局；CLI 的 `--lock` 为显式路径参数，无仓根约定），且 `aisoft-architecture validate --lock` 通过；校验日期缺省当日 UTC、可经检查器 `--today` 透传复现 | `architecture/bin/aisoft-architecture` |
| `labels-readback`（远程） | GET `/repos/{owner}/{repo}/labels` 与 canonical manifest 24 个标签逐名存在，name 缺失或 color/description 漂移均 GAP；此外非 manifest 标签若侵入受管命名空间（`type/*`、`complexity/*`、`triage/*` 前缀）同样 GAP（NewEMaint 实测存在 `complexity/standard`、`type/data|reliability|security` 等冲突遗留），其余项目本地标签仅输出 `INFO:` 行不计 GAP | `codex/config/gitea-labels.json` |
| `ci-context`（远程） | governance manifest 中该仓库的 required status contexts 与 live branch protection 读回一致；禁止直推在位 | `codex/config/gitea-governance.json` |
| `delivery-profile` | `AGENTS.md` 全文存在明确交付形态声明：命中已知 delivery profile 标识符集合（`docker-release/v2`、`PM2`、`Windows/IIS` 等固定列表）之一，或模板「交付形态」bullet 块（该 bullet 起至下一 bullet/标题前的全部续行）已填写；命中范围内不得残留 `<...>` 占位符。不要求特定节标题 | 目标仓 `AGENTS.md` |

输出合同：逐项一行 `PASS: <id>`、`GAP: <id> — <单行原因>` 或 `SKIP: <id> — <单行原因>`，
末行 `result: pass=<n> gap=<n> skip=<n>`。退出码 `0`=无 GAP、`1`=≥1 GAP、`64`=用法错误。
工具只读：不写目标仓、不写平台仓、无远程 mutation；本地检查零网络零凭据。相同输入
（仓库状态 + live 状态 + 校验日期）输出确定相同；`--today` 透传给 architecture 校验，
缺省为当日 UTC——transition exception 到期当日 fail closed 属对齐语义的一部分。

## Acceptance criteria

- [ ] AC-1 `skill-for-codex/references/project-align.md` 存在：定义幂等对齐语义
      （核对→缺口逐项走目标仓独立 Issue/小 PR→复检至全 PASS；已对齐仓库重跑
      no-op），checklist 覆盖 runbook §2 共享项目契约、§5 标签、§9 architecture
      声明与 delivery profile 声明；每项仅含指向（runbook 章节号 / `templates/`
      路径 / 工具命令），不复制合同正文段落。
- [ ] AC-2 `skill-for-claude/SKILL.md` 与 `skill-for-codex/SKILL.md` 均含对齐入口，
      指向该 reference；安装后 `skill-for-claude/check-drift.sh` 输出 `CLEAN`
      （新 reference 被既有 references/*.md 迭代自动覆盖，check-drift 本身不改）。
- [ ] AC-3 `codex/tools/aisoft-project-check.sh` 按 §检查合同实现六项检查、输出
      与退出码合同；`bash -n` 通过；ShellCheck（若环境可用）无 error。
- [ ] AC-4 `codex/tests/test-project-check.sh` 覆盖：全对齐 fixture 全 PASS/exit 0、
      六项逐一制造缺口各报对应 GAP/exit 1、`--kind docs` 两项 SKIP、无
      `--remote` 时远程项 SKIP、用法错误 exit 64；已接入 `codex/tests/smoke.sh`
      且 smoke 全绿。
- [ ] AC-5 onboarding-runbook 开头声明「初始化新项目与更新存量项目是同一对齐
      操作」，§2 与 §8 指向 align reference 与检查器命令；不复制 checklist 正文。
- [ ] AC-6 NewEMaint 人工对齐（NewEMaint #65，PR #66 已于 2026-08-12 人工合并）反馈
      已回灌检查合同（pointer-sections 放宽后两节标题要求、labels-readback 增加
      冲突命名空间检测、delivery-profile 改为事实命中）；最终 PR 描述引用该证据链接。
- [ ] AC-7 不修改平台 `AGENTS.md`、broker、labels/governance manifest、CI 定义与
      任何业务仓库；不安装或更新任何 live skill（安装走既有 install 流程另行执行）。

## 接口、数据与兼容性影响

- 新增只读工具与技能 reference；无 schema、无迁移、无 API 变更。
- 远程读回凭据复用既有 `AGENT_ENV_FILE` 模式，不新增 Secret 形态或存储位置。
- `check-drift.sh`、`install.sh` 合同不变（reference 目录迭代自动覆盖新文件）。
- 检查器不替代 `gitea-governance.sh check`（治理权限校准）与
  `host.onboarding.check`（host 接入聚合）；三者边界在 reference 中注明。

## 治理授权（精确文件清单）

本 spec 授权且仅授权以下治理文件操作：

- 新增 `skill-for-codex/references/project-align.md`
- 修改 `skill-for-claude/SKILL.md`、`skill-for-codex/SKILL.md`（增加对齐入口指针）
- 修改 `skill-for-codex/references/onboarding-runbook.md`（「初始化=对齐」声明与指向）
- 新增 `codex/tools/aisoft-project-check.sh`、`codex/tests/test-project-check.sh`
- 修改 `codex/tests/smoke.sh`（仅接入新测试）

清单之外的治理文件（含平台 `AGENTS.md`、`codex/config/*`、broker、CI workflow）
不在授权范围；实施 run 不得触碰。

## 风险与回滚约束

- 全部为新增文件与文档型修改，单 PR revert 即完整回滚；无状态残留。
- 检查器只读，误报最坏后果是多开一个核对 Issue；漏报由 NewEMaint 人工对齐
  验证环节兜底。
- 技能源修改在人工合并前不影响任何已安装技能；合并后按既有 install/check-drift
  流程逐机更新。

## 非目标

- 不执行任何仓库的实际对齐（NewEMaint 人工对齐是 NewEMaint 侧独立 Issue）。
- 检查器不自动开 Issue/PR、不写标签、不修复缺口——修复始终走人机协作的
  Issue/小 PR 流程。
- 不改 Matt triage projector、controller、labels manifest 与 24 标签定义。
- 不启用任何项目 provider；不安装/启用 live skills 或 systemd 单元。
- 不覆盖 host-role、host-access-broker、docker-release 等 host 侧合同的检查
  （由 `host.onboarding.check` 等既有工具负责）。

## 未决问题

无。pointer-sections 比对语义原以「前两节逐字节 + 后两节标题在位」起草；NewEMaint
人工对齐（#65/PR #66，2026-08-12 人工合并）以纯新增方式保留自有章节结构并获合并
背书，已按 T02 回灌为「前两节逐字节 + CLAUDE.md + 事实型 delivery-profile 检查」，
同时扩充 labels-readback 的冲突命名空间检测。语义已收敛，无遗留争点。
