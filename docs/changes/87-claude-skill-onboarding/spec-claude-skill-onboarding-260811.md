---
issue: 87
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/87
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - agent-governance
depends_on: []
status: contract-drafting
branch: change/87-claude-skill-onboarding
pr_url:
created: 2026-08-11
updated: 2026-08-11
---

# Spec

## 目标与原因

Claude 侧 `~/.claude/skills/aisoft-platform` 停在 2026-07-22 且在平台仓库无版本控制源，
落后三代合同（2026-08-11 审核 P0）。本变更把 Claude 技能源纳入仓库、提供确定性安装与
漂移检查，使两个 provider 的技能都从同一 protected `main` 交付。

## Acceptance criteria

- [ ] AC-1 `skill-for-claude/SKILL.md` 存在：description 触发词含治理项目名（NewEMaint、SFMDigitalBoard、HSDB、WMPDA、SapTableMigrate 等）；正文含 readable 元组、`$triage #N` 四步主路径、24 标签、host-access-broker、单闸门、工具分工默认偏好（Claude=开发/设计，Codex=维护/部署，provider 中立保留）。
- [ ] AC-2 `skill-for-claude/install.sh`：装 SKILL.md 并从 `skill-for-codex/references/` 单源拷贝 references；不装凭据/runtime/provider 状态。
- [ ] AC-3 `skill-for-claude/check-drift.sh`：未安装 → `NOT_INSTALLED` 且 exit 0；安装后与源一致 → `CLEAN`；不一致 → 列出 `DRIFT:` 项且 exit 1。独立运维工具，不进 smoke 硬门。
- [ ] AC-4 `codex/tests/test-install-claude-skills.sh`：临时 HOME 双次安装幂等（文件清单与内容 hash 一致）、references 与单源字节一致、无凭据形态；接入 smoke。
- [ ] AC-5 `bash codex/tests/smoke.sh` 全绿（含新 bash -n 与新测试）。
- [ ] AC-6 本变更不向真实 `~/.claude` 安装（部署须在 PR 人工合并后从 main 执行）；不改 skill-for-codex 语义。

## 接口/数据/兼容影响

新增文件与 smoke 两行接入；无 runtime/标签/部署影响。references 单源避免第二套合同
（08 §8：不复制 Codex skill 内容形成第二套合同——Claude 版 SKILL.md 是同一合同的入口投影，
参考文献直接复用 Codex 版文件）。

## 治理授权

本 spec 明确授权新增/修改：`skill-for-claude/{SKILL.md,install.sh,check-drift.sh}`、
`codex/tests/test-install-claude-skills.sh`、`codex/tests/smoke.sh`（仅新增两行调用）。
不授权修改 AGENTS.md、global-AGENTS.md、skill-for-codex、runtime。

## 非目标

- 不在本变更内执行 Mac 实际安装（合并后操作步骤见 verification 与 PR 说明）。
- 不解决 Matt skills 在 Claude harness 的完整安装（涉及用户全局 ~/.claude 与插件 1.2.3 版本
  取舍，留独立决策）。
- 不建立 VM 侧 Claude 技能路径（VM Claude 仅 headless analyzer）。
