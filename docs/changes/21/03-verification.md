---
issue: 21
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/21
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - security
  - shared-core
  - ci-change
  - deployment
  - migration
  - destructive-operation
  - rollback
  - platform-governance
depends_on: []
status: pending
branch: change/21
pr_url:
created: 2026-08-02
updated: 2026-08-02
---

# Verification

## 环境与版本

- Source baseline：`origin/main@b806317cc87a58049719fff103af2c9d7c14ed56`
- Candidate branch：`change/21`
- `gitea-ci`：待实施时重新读取 identity 与状态
- `prod-sim` planning baseline：ID `01KX3FFXSJVYPDHZVY4MZB7CQZ`，Ubuntu
  `resolute` ARM64，running，约 3.9 GB；删除前必须重新读取

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| planning contract parse + AC map | PASS | `load_contract` 通过；14 条 AC 全部映射 |
| `orb delete --help` / `orb info prod-sim` | PASS（只读 planning） | 当前 CLI 确认删除永久丢失文件；name/ID 与 Issue 追加范围一致 |
| host-role schema/guard tests | NOT RUN | 等待实现 |
| `bash codex/tests/smoke.sh` | PASS（planning baseline） | 105 项 Python tests 与全部 shell/static smoke 通过；实现后必须重跑 |
| Gitea PR CI | NOT RUN | PR 尚未创建 |
| `gitea-ci` 两次 inventory | NOT RUN | 开发会话执行 |
| `rsdesign-new` AppServer migration/old shutdown | NOT RUN | 需应用仓 Issue/PR 与 live Gate |
| SFM smoke cleanup | NOT RUN | 需应用仓 Issue/PR 与 live Gate |
| MyApp/Redis/Nginx/artifact cleanup | NOT RUN | 逐项 Gate |
| `prod-sim` pre-delete inventory | NOT RUN | 开发会话执行 |
| `prod-sim` delete/post-check | NOT RUN | 用户已授权精确 VM；仍须前置检查 |

## Acceptance criteria 结果

- AC-1 至 AC-14：NOT RUN，等待实现与真实验证。

## 重复部署/执行

- host-role guard 第一次：NOT RUN
- host-role guard 第二次：NOT RUN
- `gitea-ci` inventory 第一次/第二次：NOT RUN
- `prod-sim` 删除只允许执行一次；以删除前双读和删除后双读替代重复 destructive action。

## 故意失败与回滚

- `scm-ci` 请求 application start：NOT RUN；预期 denied 且零 mutation。
- identity mismatch/profile 权限错误：NOT RUN；预期 fail closed。
- 应用迁移失败回切：NOT RUN。
- `prod-sim` identity/引用不满足：NOT RUN；预期停止删除。
- `prod-sim` 删除后整机原地 rollback：不可能；恢复路径为依据版本化基线重新创建。

## 遗留风险与未完成项

- 任何 planning baseline 都可能漂移，所有 live 操作前必须重新采集。
- 除 `prod-sim` 外的 destructive action 仍需逐项明确授权。
- PR 人工合并和所有未执行 live Gate 保持 `NOT RUN/BLOCKED`。
