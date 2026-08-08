---
issue: 58
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/58
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - schema-change
  - security
  - external-contract
  - shared-core
  - artifact
  - deployment
  - compatibility
  - rollback
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
documents:
  summary: 00-summary.md
  spec: 01-spec.md
  plan: 02-plan.md
  verification: 03-verification.md
depends_on:
  - 22
  - 27
  - 37
  - 40
status: pr-open
branch: change/58
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/64
created: 2026-08-08
updated: 2026-08-08
---

# Issue #58 summary

## 变更摘要

修复 `docker-release` producer artifact conformance 错误依赖 target Docker/Compose
compatibility 的职责混杂。将 artifact verification、target readiness、image staging、database
migration、application activation/health、status 与 rollback 拆成稳定、可单独授权和审计的阶段，
同时保留既有 `verify/deploy/status/rollback` 调用方的兼容入口。

新分阶段能力使用显式 versioned artifact contract，并为既有 state 提供 fail-closed migration；
不会通过放宽 compatibility matrix 让 Compose 5.1.4 变绿。没有同等级 disposable Engine 29 /
containerd consumer E2E 证据时，该组合继续保持 `NOT RUN / BLOCKED`，不得进入 supported matrix。

## 实时基线

- fresh fetched Gitea `main`: `58daf44b0d48daa93d0fe6d9b95e910f191b1357`
- Issue #58 的四个 basename 按用户在本任务开始时的明确要求保留；`documents` 映射使其兼容
  后续由 Issue #60 / PR #62 引入的语义角色 resolver，不扩散为新的默认 writer 约定。
- `change/58` 已在 Issue #61 / PR #63 合并后再次 rebase 到 fresh main；host access broker 的
  新增文件保持原样，本 Change 没有扩大到其职责范围。
- 已知旧 live main `e46890952cd5bf7b55624a5f99d7e16593237984` 是当前 main 的父提交。
- PR #40 merge SHA `825995faf1ecf40dc0981c46281c0213c86bd421` 是当前 main 祖先。
- live Gitea 未发现既有 `change/58` branch 或关联 PR。
- `main` 禁止 direct push/force push，merge allowlist 为 `admin`；required status check 当前未启用。
- canonical checkout 的用户未跟踪 `.DS_Store` 保持未修改；实现只在 Codex 独立 worktree 的
  `change/58` 分支进行。

## 授权状态

用户已批准本 Issue 的 Spec、Plan 和实现，以及推送 `change/58`、创建 `Closes #58` PR。
没有授权真实 Docker/VM mutation、DockerLab/AppServer/production 操作、Secret 读取、真实
PostgreSQL migration/restore、Gitea 权限修改、merge 或 deployment。
