---
issue: 132
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/132
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 向 governance 与 host-access 两份 strict manifest 新增一个受管仓库与项目，触及平台治理与访问控制合同
risk_flags:
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
documents:
  summary: summary-localwms-manifest-onboarding-260820.md
  spec: spec-localwms-manifest-onboarding-260820.md
  plan: plan-localwms-manifest-onboarding-260820.md
  verification: verification-localwms-manifest-onboarding-260820.md
status: spec-drafting
branch: change/132-localwms-manifest-onboarding
pr_url: ''
created: 2026-08-20
updated: 2026-08-20
---

## 问题/需求总结

LocalWMS 进入其工程路线图 M0（Gitea 入库 + 最小 CI）。`admin/LocalWMS` 已由人工创建并推送初始历史（`refs/heads/main` = `253a3136855b4dc05723931dd013151e25206ecc`，16 个提交，与 Mac canonical checkout 零差异；`private: true`、`default_branch: main`、协作者为空）。

onboarding runbook §1.1 规定未在 manifest 登记的仓库不得继续接入，且该约束由工具 fail-closed 强制：

- `gitea-governance.sh check --repository admin/LocalWMS` → `BLOCKED_EXTERNAL: requested repository is not explicitly managed`
- `account-spec --username localwms-agent --token-kind project-agent` → `BLOCKED_EXTERNAL: service account is not declared by the manifest`

因此账号创建、权限校准与 broker 绑定全部阻塞在本登记之前。

## 影响范围

两份 manifest 各新增一条数据条目，以及三处「随受管对象数量变化」的既有测试期望值。无 schema 变更、无工具实现变更、无既有项目条目改动：

- `codex/config/gitea-governance.json` → `repositories[]` 新增 `LocalWMS`
- `codex/config/host-access-broker.json` → `projects[]` 新增 `localwms`
- `codex/tests/test-host-access-broker.sh` → `project_count` 断言 9 → 10
- `codex/runtime/tests/test_host_access.py` → `len(projects)` 断言 9 → 10
- `codex/runtime/tests/test_gitea_governance.py` → `len(repositories)` 断言 9 → 10，且 private 精确集合加入 `LocalWMS`

后三项是平台 fail-closed 契约测试的必然结果：这些断言刻意钉死受管对象的数量与集合，任何新增受管仓库都必须显式更新它们。

## AI 判级

```yaml
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - platform-governance
required_docs: [summary, spec, plan, verification]
override_reason: ''
```

治理 manifest 属强制 complex 类别（Agent/治理一律 complex）。`contract_effect: add` —— 只新增受管对象，不改变既有合同语义。

## 结论

按 spec 定义的两条精确条目登记 LocalWMS，解除后续 §1.1 流程的阻塞。本变更不创建任何账号、凭据、权限或部署。
