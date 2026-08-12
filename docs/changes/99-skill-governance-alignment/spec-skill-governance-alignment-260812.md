---
issue: 99
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/99
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - agent-governance
  - ci-change
depends_on: []
status: ready-for-review
branch: change/99-skill-governance-alignment
pr_url:
created: 2026-08-12
updated: 2026-08-12
---

# Spec

## 目标与原因

使 Claude/Codex 技能、项目模板、Claude skill 安装/drift 和 #89 验收记录重新精确服从现行
broker、readable change、small/complex、部署和证据分层合同。

## Acceptance criteria

- [ ] AC-1 Claude skill 不再指导直接 fetch/rebase/push；`BASE_BRANCH_STALE` 停止当前 pass，由
      Controller 经 broker `git.fetch.main` 取新基线并按 ancestry policy 重建候选。
- [ ] AC-2 Claude skill 统一表述：AI 可参与开发/测试首次部署并固化脚本；生产 script-only、无 AI。
- [ ] AC-3 Codex runbook 的 NewEmaint 首次消费使用 exact readable branch/docs/唯一 PR。
- [ ] AC-4 项目模板把纯数字对象限定为 evidence-derived maintenance compatibility；small 直进前
      必须完成 triage、mapped summary、AI 判级、可测/局部/可 revert、无强制风险和 `approved` 复核。
- [ ] AC-5 drift 对目标缺失、内容变化和 unexpected entry 均 rc=1 + 明确 `DRIFT:`；installer
      只在固定 managed tree 内清理 stale entry，拒绝 symlink target，重复安装 byte-identical/CLEAN。
- [ ] AC-6 #89 分开记录 runner prerequisite PASS、本地 smoke PASS、PR #90 首次远端 CI FAIL 与
      required context NOT CONFIGURED。
- [ ] AC-7 shell syntax、ShellCheck、targeted install/drift tests、full smoke 与两轴 review 通过。

## 接口、数据与兼容性影响

Claude installed skill 文件集合变为 exact managed tree；stale 文件会在显式运行 installer 时清理。
`check-drift.sh` 对 unexpected path 新增 fail-closed 输出。无 runtime API、标签、分支保护或部署影响。

## 风险与回滚约束

installer 只处理 `<target-home>/.claude/skills/aisoft-platform`，拒绝 symlink 根目标与特殊文件；
不读取 credential。回滚为人工 revert PR，并从已知 main 重新安装上一版 skill。

## 非目标

- 不修改当前运行遵循的根 `AGENTS.md`。
- 不在合并前重装 live Codex/Claude skill。
- 不修改 required-context manifest/fixtures，不执行 governance apply。
- 不合并、不部署、不改标签、不处理 GitHub #95。

## 未决问题

无；用户已批准本批治理修正。
