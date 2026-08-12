---
issue: 107
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/107
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - platform-governance
depends_on: []
status: contract-drafting
branch: change/107-vm-profile-tool-install
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/109
created: 2026-08-12
updated: 2026-08-12
---

# 实施计划

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | summary/spec/plan/verification 四份映射文档，`resolve-documents 107` 可解析 | - | done |
| T02 | `_vm_profile` preflight + 可区分 typed 错误码，并透传工具自身错误契约（AC-1..AC-3b） | T01 | done |
| T03 | runtime 测试覆盖 preflight/透传/fail-closed 共 9 例（AC-4） | T02 | done |
| T04 | `06-运维手册与踩坑集.md` 安装面归属表与踩坑条目 18（AC-5） | T01 | done |
| T05 | VM 内安装 + profile 迁移验收，两次幂等 + 故意失败回滚，回填 verification（AC-8..AC-12） | T02, T03 | done |
| T06 | smoke（VM 内）全绿、经 broker 推分支并开 PR（AC-6） | T03, T04, T05 | done |

T02/T03 是代码垂直切片；T04 是独立文档切片；T05 是运维切片，须在 T02 落地后执行，
以便用新错误码验证「工具缺失」路径的可诊断性。

## Expected touch points

- T01：`docs/changes/107-vm-profile-tool-install/{summary,spec,plan,verification}-vm-profile-tool-install-260812.md`
- T02：`codex/runtime/aisoft_host_access/broker.py`（仅 `_vm_profile` 分支）
- T03：`codex/runtime/tests/test_host_access.py`
- T04：`06-运维手册与踩坑集.md`
- T05：无仓库文件改动，除 verification 回填
- T06：summary/spec/plan/verification 的 `pr_url` 回填

范围提示，不授权扩大 spec 的非目标边界。

## 数据库迁移

无。本次的「迁移」是 VM 侧 project profile 布局迁移（#61 合同），不涉及任何数据库。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 / AC-2 / AC-3 | `python3 -m pytest codex/runtime/tests/test_host_access.py -k vm_profile`（或仓库既有 runner） |
| AC-4 | 同上，三条分支各有独立用例，使用注入的 fake runner，不接触真实 VM |
| AC-5 | 复核 `06-运维手册与踩坑集.md` 新增章节 |
| AC-6 | `bash codex/tests/smoke.sh` |
| AC-7 | `git diff origin/main --stat` 核对触碰文件集合；`git worktree list` 确认未动他会话分支 |
| AC-8 | VM 内 `ls -l /usr/local/libexec/aisoft/ /usr/local/lib/aisoft-host-access /usr/local/share/aisoft/` |
| AC-9 | `host-access-broker --project newemaint --operation vm.profile.read-back` |
| AC-10 | `host-access-broker --project newemaint --operation vm.profile.plan` |
| AC-11 | 连续两次执行安装器，比对第二次输出为 `already current (no-op)` |
| AC-12 | 故意失败演练（见下）与 `vm.profile.rollback` 路径 |

## 部署与回滚

本次有 VM 侧执行影响，因此映射 `verification` 文档并按合同执行：

- **两次重复执行**：`install-host-access-broker.sh` 连跑两次；第一次应报
  `installed host-access-broker/v1 candidate`，第二次应报
  `host-access-broker/v1 candidate already current (no-op)`。
- **一次故意失败与回滚**：构造一个必然失败的 profile 操作（如对未在 manifest 声明 VM
  profile 的项目请求 `vm.profile.*`，预期 `TARGET_UNAVAILABLE`；以及在工具缺失状态下先跑
  一次 preflight 分支），确认失败被判定并且不留下半完成状态；若 `apply` 已产生变更，
  用 `vm.profile.rollback` 与 `vm_profile_policy.backup_root` 恢复并读回验证。
- **不部署任何应用、不启用 timer/service、不重签令牌。**
- 交付停在人工合并最终 PR。
