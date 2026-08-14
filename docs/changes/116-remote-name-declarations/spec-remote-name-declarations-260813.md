---
issue: 116
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/116
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
depends_on: []
status: ready-for-review
branch: change/116-remote-name-declarations
pr_url:
created: 2026-08-13
updated: 2026-08-13
---

# Spec

## 目标与原因

让 rsdesign-new 与 sfm-digital-board 的 Mac broker Git 通路可用：两仓 Mac checkout 的
`origin` 是 GitHub（受保护，不得改写），Gitea 通路应经各自 `gitea` remote。#73 已为此
建立 strict `git_remote_name` 声明机制（NewEMaint 先例）；本变更把该声明补到两个项目
条目。

## Acceptance criteria

- [ ] AC-1 `codex/config/host-access-broker.json` 中 rsdesign-new 与 sfm-digital-board
      条目各含 `"git_remote_name": "gitea"`；diff 恰为这两行插入，其余字节不变。
- [ ] AC-2 `bash codex/tests/test-host-access-broker.sh` 与 full smoke 全绿。
- [ ] AC-3（合并后，人工重装 Mac/VM 后验收）：两仓 `mac.git.bind` 与
      `host.onboarding.check` PASS；GitHub `origin` 的 fetch/push URL 保持不变。
- [ ] AC-4 不修改 broker runtime 代码、schema、其他项目条目或任何业务仓库；测试仅
      更新声明集合守卫断言，其余断言不变。

## 接口、数据与兼容性影响

纯 manifest 声明；`git_remote_name` 为 #73 既有 schema 字段（contract.py strict 校验、
未声明默认 `origin` 的兼容行为不变）。声明后 broker 对两仓只用 `gitea` remote，并要求
其 fetch/push URL 精确等于 governance 派生 Gitea URL；GitHub `origin` 不进入 broker
通路且不得被 broker 创建/改写（既有合同）。

## 治理授权（精确文件清单）

- 修改 `codex/config/host-access-broker.json`（仅上述两行插入）
- 修改 `codex/tests/test-host-access-broker.sh` 与
  `codex/runtime/tests/test_host_access.py`（仅更新钉住声明集合的守卫断言：由
  「仅 newemaint 声明」改为「newemaint/rsdesign-new/sfm-digital-board 三者声明
  gitea、其余项目不得声明/默认 origin」——守卫断言与 manifest 是同一合同的两面，
  必须同步演进）

清单外治理文件不得触碰。

## 风险与回滚约束

回滚 = revert 单 PR + 人工重装两端。声明错误由 fail-closed 校验拦截，无静默风险。

## 非目标

- 不改 broker runtime/schema；不为其他项目加声明；测试改动仅限声明集合守卫断言。
- 不在本 PR 内执行安装或 adoption 验收（AC-3 属合并后人工步骤）。
- 不处理三仓对齐 Issue 本身的内容回补。

## 未决问题

无。
