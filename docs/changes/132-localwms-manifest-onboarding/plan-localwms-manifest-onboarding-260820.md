---
issue: 132
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/132
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - platform-governance
depends_on: []
status: pr-open
branch: change/132-localwms-manifest-onboarding
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/133
created: 2026-08-20
updated: 2026-08-20
---

# Plan · LocalWMS manifest 登记（#132）

## 依赖图

```
T01 ──> T02 ──> T03 ──> T04
```

## T01 · 插入 governance 条目

在 `codex/config/gitea-governance.json` 的 `repositories[]` 中，于 `HSDB` 与 `myapp` 之间插入 spec §1 的条目。保持 2 空格缩进与既有键序，不得重排文件其余部分。

**验收**：`git diff --numstat` 对该文件为 `10 0`（纯新增）。

## T02 · 插入 broker 条目

在 `codex/config/host-access-broker.json` 的 `projects[]` 中，于 `hsdb` 与 `myapp` 之间插入 spec §2 的条目。

**验收**：`git diff --numstat` 对该文件为 `7 0`（纯新增）；`operations[]` 长度仍为 26。

## T03 · 同步契约测试期望值

按 spec §3 更新三处受管对象数量/集合断言。不得放松 `operation_count == 26` 或 `merge_operation_count == 0`。

**验收**：`bash codex/tests/test-host-access-broker.sh` 退出码 0。

## T04 · 合同校验

依次执行并全部通过：

1. `gitea-governance.sh --manifest <manifest> validate` 退出码 0；
2. `account-spec --username localwms-agent --token-kind project-agent` 返回 spec JSON，不再是 `BLOCKED_EXTERNAL`；
3. 既有 9 个 governance 条目与 9 个 broker 条目逐字段全等，两份文件其余顶层键全等。

**验收**：三项结果写入 verification 文档。

另需 `bash codex/tests/smoke.sh` 退出码 0，且输出行数与 `origin/main` baseline 一致（证明既未新增失败，也未跳过既有用例）。

## 合并后（不属本 PR）

按 runbook §1.1：`bootstrap-gitea-service-account.sh`（人工 site-admin）→ `bootstrap-manager`（人工 site-admin）→ `check` → `apply` → broker `host.access.audit` / `mac.git.bind` / `host.onboarding.check` → LocalWMS 自身的 typed Issue/change/PR/CI canary。
