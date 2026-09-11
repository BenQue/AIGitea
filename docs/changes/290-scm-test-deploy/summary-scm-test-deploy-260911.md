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

来源为 NewEMaint #79 后续部署需求。仅当受保护 profile 同时声明 `host_role=scm-ci` 与
`environment=test` 时允许既有六个部署动作；生产仍拒绝，不新增角色或绕过其它保护。
权限与部署规则改变，判级为 platform/complex。

用户已批准合同、推送和唯一 manual PR #291，并明确“同意方案 B”。T01 独立合同提交
`7590643`、T04 独立增补提交 `aba17f7` 后均已停止；后续 fresh run 已重读合同实施。
远程 Git/Gitea 通过 typed broker；不重复请求已经给出的 push/PR 授权。

方案 B 已实现：固定历史基线的临时本地 clone 运行原 fake harness；当前 checkout 独立验证
runner 精确六行修订、其它受控文件原字节、文件集合/模式及 index/磁盘一致性。运行前后检测
漂移，任何子检查失败都使整体失败；保留全部其它 smoke 硬门和 full Python suite。
旧 #65 evidence、real/fake harness、fixtures 和 compatibility matrix 均未改动。

本地 release suite 124 项通过，包含 offline-bundle 部署、幂等与失败回滚及 16 项检查器正反例。
完整 smoke 结果与 CI head 见映射的 verification；PR #291 为唯一交付入口，required CI 通过
后才进入 READY_FOR_REVIEW，由人合并。当前 real Docker、installed、company live 均 NOT RUN。
