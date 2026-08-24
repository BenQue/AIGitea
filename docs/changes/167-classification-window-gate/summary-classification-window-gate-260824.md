---
issue: 167
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/167
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 给会话合同加一道合并前的判级投影闸门，新增只读 verify 模式与 broker 陈旧安装的失败翻译，并改写两个 Claude skill 与 03/06 治理文档；属平台与 Agent 治理变更，强制 complex
risk_flags:
  - platform-governance
  - agent-governance
required_docs:
  - summary
  - spec
  - plan
documents:
  summary: summary-classification-window-gate-260824.md
  spec: spec-classification-window-gate-260824.md
  plan: plan-classification-window-gate-260824.md
confidence: high
override_reason: ''
depends_on: []
status: pr-open
branch: change/167-classification-window-gate
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/170
created: 2026-08-24
updated: 2026-08-24
---

## 问题/需求总结

判级投影（`codex/tools/apply-classification-labels.sh`，#160）有一个**不可见的截止时间：合并**。
合并把 Issue 变成 closed，工具按 #160 的既定姿态直接跳过且没有 override 开关，于是
`type/*` 与 `complexity/*` 永远补不上了。没有任何环节会在窗口关闭前提醒。

缺口有三段，都指向同一件事——**这条投影没有读回，也没有闸门**：

1. **计划模式不是验证。** 计划模式只回答「我会写什么」，从不读回 Issue 当前的标签。
   投影过和从没投影过，输出逐字相同（`set-classification / applied:false`），
   所以执行者手上根本没有一条能回答「这个 Issue 现在到底有没有标签」的命令。
2. **失败信息说的不是失败的原因。** 未重装的 broker 把新 typed 操作报成
   `REQUEST_DENIED: requested operation is not allowlisted`（`06` 踩坑 20）。这句话读起来是
   权限问题，实际是「你装的那份操作表是旧的」。而且 broker 把它打在 **stderr**、工具只捕获
   stdout，所以它以一行无解释的裸文本抵达终端。
3. **会话合同里没有它的位置。** `aisoft-platform` 的会话标准动作把第 4 步写成一次动作，
   没说它有截止时间；`issue-session-flow` 的待合并块与收尾 7 步完全没提它。
   于是「投影没做成」不构成任何一步的阻塞。

## 影响范围

**现场证据**（2026-08-24 经 broker `gitea.issue.labels.read` 读回，与合并后 summary 对照）：

| Issue | Gitea 实际标签 | 合并后 summary 的判级 |
|---|---|---|
| #138 | `['completed']` | `platform` / `complex` |
| #146 | `['completed']` | `platform` / `complex` |
| #148 | `['completed']` | `platform` / `complex` |
| #163 | `['completed']` | `platform` / `complex` |

四个都缺 `type/*` 与 `complexity/*`。#163 是在 #160 交付**之后**错过的——工具在，人也跑了计划，
只是 `--apply` 撞上未重装的 broker，而 Mac 的 `sudo` 只能由人执行；等 broker 到 30 个操作时
PR 已合并。这说明缺的不是能力，是**闸门与读回**。

改动落在：工具（新增只读 verify 模式 + 失败翻译）、两个 Claude skill（把闸门写进必经路径）、
`03` §11 与 `06` 踩坑 20（把窗口、处置与历史结论写成可查的合同）。

## 初步方案与建议

- **AC-1 闸门**：`apply-classification-labels.sh --verify N` 读回 Issue 当前标签并与映射 summary
  的判级比对，只在两个维度都可见时退 0。`issue-session-flow` 的待合并块新增 `判级:` 一行，
  内容必须是这条命令的真实读回；不是 `projected` 就不进入待合并。窗口关闭前的最后一个
  会话必经点因此被占住。
- **AC-2 翻译**：捕获 broker 的 stderr，`REQUEST_DENIED` + `not allowlisted` 翻译成
  `broker-operation-missing`，正文直接给出「操作表是安装期固定的，两台重装」与命令，并指向
  `06` 踩坑 20。
- **AC-3 不动写路径**：verify 是只读的，用的 `gitea.issue.read` 与 `gitea.issue.labels.read`
  都是既有非 mutating 操作。closed 且未投影时 verify 报 `projection-window-closed` 并
  **不给 remedy**——没有可执行的补救，这正是 #160 的姿态。不新增 override，不新增 typed 操作。
- **AC-4 历史处置**：接受上表四个 Issue 缺 `type/*`、`complexity/*`，结论与依据写进 `03` §11，
  不改写任何已关闭 Issue。

**一条自我约束**：本修复不得依赖它要修的那个前提。verify 用的两个操作在 29 操作的旧 broker
里就存在，所以即使 broker 是旧表，闸门仍然工作——它会先报「没投影」，`--apply` 再报
「需要重装」，两句连起来正好是 #163 当时缺的那段推理。

## 风险

- **把闸门写进 skill = 改 Agent 行为合同**，必须由 spec 明确授权，且 skill 源改完要跑
  `skill-for-claude/install.sh` 才对已安装副本生效（本仓已有 `check-drift.sh` 与
  `test-install-claude-skills.sh` 覆盖该机制，本次不改它）。
- **误报会侵蚀闸门**。verify 只有四种结论（`projected` / `projection-missing` /
  `projection-mismatch` / `projection-window-closed`），每种都由读回证据决定，不做推测；
  读不出证据时（文档缺失、判级未决、broker 不可用）一律计为失败而不是「看起来没问题」。
- **verify 与 plan 的退出语义不同**：verify 里「说不清」= 失败，plan 里仍是非失败 skip。
  这是刻意的——闸门的问题是「是不是已经投影了」，「我不知道」不等于「是」。plan/apply 的
  既有退出语义一个字节都不改。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 给会话合同加一道合并前的判级投影闸门，新增只读 verify 模式与 broker 陈旧安装的失败翻译，并改写两个 Claude skill 与 03/06 治理文档；属平台与 Agent 治理变更，强制 complex
risk_flags:
  - platform-governance
  - agent-governance
required_docs:
  - summary
  - spec
  - plan
confidence: high
override_reason: ''
```

### 判级证据

- `contract_effect: add`：新增一条会话必经的闸门与一个工具模式，两者此前都不存在。
- 改 `skill-for-claude/*/SKILL.md` 即改 Agent 行为合同，改 `03` 即改平台流程合同——
  AGENTS.md 对 Agent 与平台治理变更一律强制 complex，不看范围大小。
- 不需要 `verification`：本仓 `deployment_lifecycle: none`（#163），本次无部署链路、
  无迁移、无外部契约变更，终态是 `completed`。

### 缺失的 acceptance criteria 或决策

- 无。AC-1..AC-5 由 Issue 正文给定；AC-4 要求的处置结论在本变更内给出并落进 `03` §11。
