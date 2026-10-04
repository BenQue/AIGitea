---
issue: 334
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/334
change_type: docs
requested_complexity: auto
assessed_complexity: small
effective_complexity: small
contract_effect: unchanged
reason: 仅同步 README、编号分册与模块 README 的已合并事实、状态和导航；不修改治理规则、Agent 指导、runtime、脚本、CI、manifest 或历史证据，合同效果 unchanged，局部可 revert，无强制复杂风险。
risk_flags: []
required_docs:
  - summary
  - verification
confidence: high
override_reason: ''
documents:
  summary: summary-refresh-platform-docs-261004.md
  verification: verification-refresh-platform-docs-261004.md
depends_on: []
status: approved
branch: change/334-refresh-platform-docs
pr_url:
created: 2026-10-04
updated: 2026-10-04
---

## 问题/需求总结

用户要求全面检查并更新项目文档，重点为根 README。2026-10-04 broker fresh-fetch 确认 protected main 为
`dc9aa468580f92a73dfa054c6f04ef5113f56694`；原根 checkout HEAD 为 `5c2cd726c9aeaee9d17541d8feb049e33881bbac`。
稳定源码持续更新，README 日期和总览则停在 9 月上旬，并存在 #289/#288 已完成却仍写待实施的问题。

## 影响范围

README、01/03/04/07/08/09/12-Linux 编号分册、architecture/README 与 PAT helper README 的状态、链接和既有流程展示。
当前入口的逐项审查和全部近期 merge 来源在映射 verification；其它参考文档按核查结论保留。
不改 AGENTS.md、CLAUDE.md、skills/references、治理规则、代码/脚本、CI、manifest、catalog 和历史 Change evidence。
只读扫描发现的安装布局链接不误判为源码缺失。

## 初步方案与建议

T01（small 合成 ticket）：以 exact stable main 核对文档 → 同步当前总览与过时状态 → 运行链接/文档/现有断言和 full smoke → 本地 commit → AWAITING_PR_CONFIRMATION。
README 保留 v3.6 合同编号，不因文档刷新发明新 runtime release。源码、历史本地测试、安装、现场/部署各有边界。

## 风险

- 不把 merged、required CI、历史 as-built 或 source-only PASS 写成现场启用/健康/部署证明。
- #327 仍 open，不承诺其 FF 路径已交付；#333 已有 approved 标签但仍 open，本次未核对现场完成。
- 历史 verification 的提交前 NOT RUN/pr-open 是快照，保留原文；当前状态由 main Git history 和 fresh Gitea 读回确认。
- 回滚：revert 本 Issue 文档 commit；未做 installed/live mutation，无运行环境恢复动作。

## AI 判级

```yaml
change_type: docs
requested_complexity: auto
assessed_complexity: small
effective_complexity: small
contract_effect: unchanged
reason: 仅同步 README、编号分册与模块 README 的已合并事实、状态和导航；不修改治理规则、Agent 指导、runtime、脚本、CI、manifest 或历史证据，合同效果 unchanged，局部可 revert，无强制复杂风险。
risk_flags: []
required_docs:
  - summary
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- 纯文档状态/导航同步；01/03 的更新只反映 #290/#289 已合并实现，不重写批准规则。
- 当前 governing AGENTS/skills 未编辑，无 forced risk；small 不需要 spec/plan。
- fresh remote、开放 Issue 和改前 inventory 是一次性观测，required CI 不可复现，故声明 verification。

### 缺失的 acceptance criteria 或决策

- 无。用户“请全面检查一下，并更新”授权本次纯文档实施；PR 提交仍待第二确认点。

## 授权与归属

Issue #334 / change/334-refresh-platform-docs / Policy manual。
Worktree `/private/tmp/issue-334-refresh-platform-docs`；session `01a104d6-3f9a-72c2-b4bc-6f5e9e03361a`，claim created。
只实施本 Issue；根 main 和其它会话 worktree 不写入。

## 本地结果与 PR 候选

2026-10-04 本地核对完成：更新 10 份现有文档；完整默认 locale smoke exit 0，1111 runtime tests
与 static smoke passed；32 项既有相关断言、语义文档与本地链接检查通过。
会话进入 AWAITING_PR_CONFIRMATION，Policy manual；分类真实读回 projected。
尚未 push / 创建 PR / 运行本票远端 CI / 合并，未安装或部署。
