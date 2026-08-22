---
issue: 139
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/139
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - agent-governance
depends_on:
  - 136
status: pr-open
branch: change/139-push-lease-doc-sync
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/140
created: 2026-08-22
updated: 2026-08-22
---

# Spec

## 目标与原因

使 `skill-for-claude/SKILL.md` 与 `06-运维手册与踩坑集.md` 重新精确服从 Issue #136 之后的
`git.push.change` 推送语义，并把「三条约束互锁」这一历史故障与新错误码 `REMOTE_BRANCH_MOVED`
写入运维手册，使后续 agent 与运维人在遇到该失败时能按文档自行恢复，而不是靠重读 broker 源码。

本变更是独立、只修改治理合同的受控步骤：按根 `AGENTS.md`，治理文件必须先由不受目标文件治理的
受控步骤应用并停止，后续 fresh run 重新读取后才能实施 runtime。因此本变更不含任何 runtime 修改，
也不执行 installed broker 或全局 skill 的重装。

## 本变更授权修改的确切文件

- `skill-for-claude/SKILL.md`
- `06-运维手册与踩坑集.md`
- `docs/changes/139-push-lease-doc-sync/` 下的映射文档

其它受保护文件（`AGENTS.md`、`codex/runtime/`、controller、CI/部署脚本、`codex/config/` manifests）
不在授权范围内。

## Acceptance criteria

- [ ] AC-1 `skill-for-claude/SKILL.md` 第 5 条按新推送语义重写：`BASE_BRANCH_STALE` 的处置为
      经 broker `git.fetch.main` 取新基线 → 本地 `git rebase origin/main` → 经 broker
      `git.push.change` 重推；并明确 remote 访问仍只走 broker（agent 不直接 `git fetch`/
      `git push`），rebase 属本地操作故不受该约束。
- [ ] AC-2 同一节写明 `REMOTE_BRANCH_MOVED` 的含义与处置：远端分支在 broker 读取 lease 之后被
      改动，推送**被拒绝而非覆盖**；处置是重新 fetch 看清远端变化后再判断，不得以提高 force
      力度绕过。
- [ ] AC-3 `06-运维手册与踩坑集.md` 的 broker 段落新增内容，且同时覆盖 (a) 三条约束互锁的历史
      故障、触发条件与误导性现象（旧码为无信息量的 `HOST_COMMAND_FAILED`）；(b) 新的
      `--force-with-lease` 推送语义，含 `<remote-sha>` 来源、远端分支不存在时的空 expectation
      语义、force 够不到 `main` 的两层约束；(c) `REMOTE_BRANCH_MOVED` 的触发条件与处置；
      (d) source 合并不等于 installed broker 生效。
- [ ] AC-4 核对 `codex/skills/` 与 `skill-for-codex/` 下的对应表述，并在 plan 的「测试与验收
      映射」记录结论：需要改则改，不需要改则给出不改的理由。
- [ ] AC-5 grep 可验证：`REMOTE_BRANCH_MOVED` 在 `skill-for-claude/SKILL.md` 与
      `06-运维手册与踩坑集.md` 中均有命中；`skill-for-claude/SKILL.md` 不再出现
      「Agent 不直接 fetch/rebase/push」式的连带禁止 rebase 表述。
- [ ] AC-6 `bash codex/tests/smoke.sh` 通过；`git diff --stat origin/main` 仅含
      `skill-for-claude/SKILL.md`、`06-运维手册与踩坑集.md` 与
      `docs/changes/139-push-lease-doc-sync/` 下文档。
- [ ] AC-7 plan 的「部署与回滚」节明确记录两项本次**不做**的部署动作及其原因。

## 接口、数据与兼容性影响

无 runtime API、broker typed 操作、标签、分支保护、CI context 或部署影响。变更面是 agent 可读
指导与运维手册文本。

对 agent 行为的合同影响一项：在 `BASE_BRANCH_STALE` 后，Mac 交互流程的 agent 由「停止当前 pass
等待 Controller」改为「取新基线 → 本地 rebase → 经 broker 重推」。`BASE_BRANCH_STALE` 与
`MERGE_COMMIT_DENIED` 两条 runtime 检查本身不变，本变更不放宽基线新鲜与线性历史要求。

`skill-for-claude/SKILL.md` 是仓库源；已安装的 `~/.claude/skills/aisoft-platform/` 是部署产物，
两者由独立的安装步骤同步，本变更不触碰后者。

## 风险与回滚约束

回滚为人工 revert 本 PR：两份文档回到 #99/#73 的表述。因不含 runtime、配置或已部署产物变更，
revert 无残留副作用，也不需要任何主机操作。

主要风险是文档描述的行为在两台主机重装 installed broker 前尚未生效；缓解方式是在 `06` 中显式
写出这一生效边界，而不是默认读者已知。

## 非目标

- 不修改 `codex/runtime/` 下任何 runtime 代码，不改 CI 或部署脚本，不改 `codex/config/` manifests。
- 不重装 Mac 与 gitea-ci VM 的 installed broker。
- 不重装或改写全局 `~/.claude/skills/aisoft-platform/`。
- 不修改本次运行正在遵循的根 `AGENTS.md`。
- 不放宽 `BASE_BRANCH_STALE` / `MERGE_COMMIT_DENIED` 的 runtime 检查。
- 不合并、不部署、不改 live 标签。

## 未决问题

无。
