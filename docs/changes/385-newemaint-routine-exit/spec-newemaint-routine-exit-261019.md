---
issue: 385
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/385
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - security
  - platform-governance
depends_on: []
status: approved
branch: change/385-newemaint-routine-exit
created: 2026-10-19
updated: 2026-10-19
git_scope:
  - docs/changes/385-newemaint-routine-exit/summary-newemaint-routine-exit-261019.md
  - docs/changes/385-newemaint-routine-exit/spec-newemaint-routine-exit-261019.md
  - docs/changes/385-newemaint-routine-exit/plan-newemaint-routine-exit-261019.md
  - docs/changes/385-newemaint-routine-exit/verification-newemaint-routine-exit-261019.md
  - codex/config/gitea-governance.json
  - codex/config/host-access-broker.json
  - 06-运维手册与踩坑集.md
---

# #385 spec：NewEMaint 退出 routine 合并

## 目标与原因

NewEMaint 一直由负责人手动合并，routine merger pilot 从未在用。负责人 2026-10-18 决定撤掉，2026-10-19 确认一步到位（NewEMaint #294）。平台侧要做的只是让 manifest 不再声明这个 pilot。现状下 NewEMaint 的 `host.access.audit` 因为 routine 段要用 merger 自己的 token 调 `/api/v1/user` 而 `BLOCKED_EXTERNAL / HTTP_403`（06 踩坑 33），这条 audit 是 NewEMaint #294 验收的前提。

## 立案前取证（2026-10-19，源码 runtime，只读）

- 当前 manifest：`host.access.audit --project newemaint` → `BLOCKED_EXTERNAL / HTTP_403`，退出码 20。
- 候选 manifest（下面 AC1 的改动）：`aisoft_gitea_governance.cli validate` PASS；`aisoft_host_access.cli validate` PASS（38 个操作、7 个项目）；同一条 audit → `PASS`，`routine_merge.enabled=false`、`identity=null`、`merge_allowlist_state=converged`。
- NewEMaint main 保护现场读回 `merge_whitelist_usernames: ["admin"]`（2026-09-19 已改）。Issue 范围第 4 步「收敛白名单」现场已经满足，不需要 governance apply，只需合并重装后读回。
- 运行时代码与测试不含 NewEMaint 常量；#380 起测试读 `codex/tests/fixtures/manifests/` 的合成夹具，夹具 README 写明项目退出不碰夹具。Issue 范围第 2 步「同步 fixture 与摘要」因此无事可做，`non_target_repositories_sha256` 随 pilot 对象一起删除。
- 两份 manifest 都不是使用层发布包成员，不需要发布新版本。

## Acceptance criteria

- [ ] AC1 manifest：同一个提交里，`gitea-governance.json` 的 NewEMaint 一项 `routine_auto_merge_enabled` 改 `false`、`routine_merge_agent` 改 `null`、删除整个 `routine_live_pilot`；`host-access-broker.json` 的 `newemaint` 项目 `routine_merge_agent` 改 `null`（合同要求两边逐字一致，只改一边会让 broker 全部 fail closed）。其它项目字节不变，LocalWMS 的已禁用 merger 声明不动。
- [ ] AC2 两个 validate 对仓库 manifest PASS；`git diff` 只触及 AC1 的四个值与 `git_scope` 列出的文件。
- [ ] AC3 `06` 第 569 行凭据表与第 606 行 #316 段把「首个现场对象为 `newemaint-routine-merger`」改为「首个现场对象待定，原定对象随 #385 退役」（该账号即将删除）；踩坑 33 是历史记录，不改。泄漏基线只降不升。
- [ ] AC4 macOS 本机全量 `bash codex/tests/smoke.sh` 全绿；PR required CI 绿。
- [ ] AC5 Codex 经 Herdr 对最终 diff 做一次只读独立审查，结论记入 verification。
- [ ] AC6 合并后（负责人执行，会话内 sudo 不可用）：gitea-ci VM 与 Mac 依次重装 `codex/install-host-access-broker.sh`，回执写安装的 source SHA；随后 `host.access.audit --project newemaint` 读回 PASS，`gitea.protection.read` 读回白名单只有 `admin`。结果记入 verification 并回告 NewEMaint #294。

## 接口、数据与兼容性影响

- 平台从此没有任何启用 routine 合并的项目；`gitea.pull.merge.routine` 操作保留，对所有项目返回未启用。通用 `routine_live_pilot` schema 与 `routine_merge_agent_policy` 不变。
- pilot 的非目标仓封印摘要随 pilot 消失。它只为 pilot 期间防止其它仓悄悄变更而设，之后的 manifest 改动仍受受保护 `main`、PR 与两台重装约束。
- 重装前，已安装 runtime 仍读旧 manifest，NewEMaint audit 继续 403，不比现在更差；其余项目不受影响。

## 风险与回滚约束

- 只改一边 manifest 会让 broker 全部 fail closed：AC2 的两个 validate 与 smoke 拦截；合并后先装 VM 读回，再装 Mac。
- 回滚：revert 本 PR 后两台重装。负责人删掉 `newemaint-routine-merger` 账号与凭据之后，回滚只能恢复声明、不能恢复 pilot，要重新 bootstrap，因此删账号排在 AC6 读回 PASS 之后。

## 非目标

- 删除 `newemaint-routine-merger` 账号、Mac canonical store 与 VM 下的 `projects/newemaint/routine-merge-agent.token` 及 ownership marker：负责人做。
- 其它项目的 routine 配置、通用 schema、governance `rollback` 命令、#316 PAT 轮换 helper。
- Issue 备选的两步走（先禁用后置空，让 apply 移除 collaborator）：负责人已选一步到位，collaborator 关系随删账号清除。
- NewEMaint 侧 #294–#297 的实现。

## 未决问题

无。
