---
issue: 254
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/254
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - deployment
depends_on:
  - 250
status: approved
branch: change/254-claude-install-source-guard
created: 2026-09-05
updated: 2026-09-05
---

# Spec: skill-for-claude/install.sh 接入共用 source guard

## 目标与原因

让仓库里最后一个未接入的 installer 与其余七个使用同一份 staleness 闸门实现，使
「源 checkout 落后 upstream」在写入与 prune 之前被拒绝，而不是装成旧版并报成功。

原因见 summary：本 installer 的 prune 语义会在源陈旧时删掉只有新版合同才有的文件，
`check-drift.sh` 比对的是同一份陈旧 checkout，因此没有任何既有信号能发现这次错装。

## Acceptance criteria

- [ ] AC-1：`skill-for-claude/install.sh` 在安装前打印 `source checkout` 与
  `source commit`（含 upstream 同步状态）以及 `skills`、`references` 两个可读量；
  幂等重复执行时同样打印。
- [ ] AC-2：源 checkout 落后 upstream 时以 `ERROR: skill-for-claude/install:` 开头
  fail-closed 退出，且拒绝发生在任何文件系统写入与任何 prune 之前；错误信息给出
  `merge --ff-only` 补救。
- [ ] AC-3：无 remote、detached HEAD、非 git 目录时降级为
  `WARNING: skill-for-claude/install:` 后正常安装。
- [ ] AC-4：复用 `codex/lib/install-source-guard.sh`，不新增第二份实现；
  `skill-for-claude/install.sh` 中不出现自有的 `rev-list --count`。
- [ ] AC-5：`codex/tests/test-installer-source-guard.sh` 的 `INSTALLERS` 含
  `skill-for-claude/install`，输出的 installer 数为 8，× 3 source states 全绿。
- [ ] AC-6：`codex/tests/test-install-claude-skills.sh` 仍然全绿，包括
  `undeclared skill source` 用例。
- [ ] AC-7：`06` 踩坑 20 的逐 installer 清单含本条，且不再声称有 installer 未接入。
- [ ] AC-8：`bash codex/tests/smoke.sh` 全绿。
- [ ] AC-9：在本机真实 `HOME` 上执行一次安装，provenance 四行出现且安装成功；
  再用一个落后 upstream 的临时 clone 执行同一命令，观测到拒绝，且真实
  `~/.claude/skills/` 的文件清单与内容哈希零变化。

## 接口、数据与兼容性影响

- 新增外部行为：陈旧源下的非零退出。调用方是人工重装与 `04`/`06` 的运维步骤，
  没有自动化调用方把本脚本的退出码当作幂等信号消费。
- 不改 `skills.manifest` 格式、managed tree 布局、prune 语义、symlink 拒绝顺序，
  以及 `check-drift.sh` 的任何行为。
- 不改 `codex/lib/install-source-guard.sh` 本身；本次只新增一个调用方。
- 可读量新增两行输出，`test-install-claude-skills.sh` 已有断言均针对具体消息而非
  完整输出，不受影响。

## 风险与回滚约束

- 回滚方式：revert 本次单一 PR。guard 是纯新增调用，无迁移、无状态、无持久化配置，
  revert 后 installer 回到接入前行为。
- 风险面集中在「本该能装的场景被拒装」。三条降级路径（无 upstream、detached HEAD、
  非 git 目录）由 AC-3 与既有测试矩阵覆盖。

## 非目标

- 不改 skill 内容、`skills.manifest`、managed tree 布局与 prune 语义。
- 不改 `check-drift.sh`。
- 不把 `skill-for-claude/install.sh` 加入 smoke 的 shellcheck 清单（现状只 `bash -n`）；
  本次单独手工跑 shellcheck 并在 verification 记录结果。
- 不改 `codex/lib/install-source-guard.sh` 的实现或输出格式。
- 不执行任何部署。

## 未决问题

- 无。
