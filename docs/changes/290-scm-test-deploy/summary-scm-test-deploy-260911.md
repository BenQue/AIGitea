---
issue: 290
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/290
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - security
  - deployment
status: pr-open
branch: change/290-scm-test-deploy
created: 2026-09-11
updated: 2026-09-11
reason: 既有host-role权限增加仅测试例外，强制complex
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-scm-test-deploy-260911.md
  spec: spec-scm-test-deploy-260911.md
  plan: plan-scm-test-deploy-260911.md
  verification: verification-scm-test-deploy-260911.md
override_reason: ''
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/291
depends_on: []
---

# SCM 测试部署

用户已批准部署工具把测试系统部署在scm-ci上。来源NewEMaint #79后续部署需求，目标平台仓，无未完成依赖。当前基点64f1cda（执行时exact Git commit为事实源）。不新建role，不改scm-ci服务器身份。

## AI 判级

权限与部署规则改变，change/platform/complex；已有environment=test|production可表达边界，无须新增schema字段。

T01 独立治理合同步骤已提交为 `75906433a77edbac6f6db603b5760a6a117100a8` 并停止。
后续独立任务已重新读取 AGENTS、技能、live Issue 与已批准语义文档，沿用原实现授权完成
T02 runtime 与测试。T03 本地 release 回归 107 项通过，语义文档检查与 diff 检查通过。

用户已确认推送并明确要求创建最终 PR；唯一 PR #291 已创建，policy 为 `manual`。
当前阶段为 PR CI 验证；required CI 通过后进入 `READY_FOR_REVIEW`，由人合并。
T02 runtime 与测试已本地原子提交为 `b2cc0a3`，T03 文档与验证单独本地提交。
适用 AGENTS.md 第 29 行允许 exact change 分支内按 plan frontier 本地 commit；
已纠正先前将交接概括误读为禁止本地 commit 的说明。远程 Git/Gitea 操作仍走 typed broker。
分支已通过 typed broker 推送。映射的 verification 记录本地收尾时的验收快照；
当前 PR/CI 以 #291 的 exact head 与 Gitea 回读为准，installed、company live 仍为 NOT RUN。

2026-09-11：用户明确“同意方案 B”。新增 AC-6/AC-7 已写入 spec：保留历史 #65 evidence 与真实
harness，固定历史 fake 回归和当前 exact runner/source/行为校验分开执行；不新增真实 Docker 授权。
T04 为独立治理合同提交并停止，fresh run 继续 T05/T06。当前 CI FAIL 不改写成 PASS；本次批准
解除合同增补的决策等待，后续实现/测试/同一 PR 修复无需重问推送和建 PR。
