---
issue: 23
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/23
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - security
  - shared-core
  - ci-change
  - external-contract
  - compatibility
  - migration
  - platform-governance
depends_on: []
status: pending
branch: change/23
pr_url:
created: 2026-08-02
updated: 2026-08-02
---

# Verification

## 环境与版本

- Source baseline：`origin/main@b806317cc87a58049719fff103af2c9d7c14ed56`
- Candidate branch：`change/23`
- Official lifecycle evidence：NOT RUN，实施时按 component 记录 URL/retrieved date
- Reference projects/servers：NOT RUN，实施时建立脱敏 inventory

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| planning contract parse + AC map | PASS | `load_contract` 通过；14 条 AC 全部映射 |
| catalog/schema/profile fixtures | NOT RUN | 等待实现 |
| validator/lock/CLI tests | NOT RUN | 等待实现 |
| installer repeatability | NOT RUN | 等待实现 |
| `bash codex/tests/smoke.sh` | PASS（planning baseline） | 105 项 Python tests 与全部 shell/static smoke 通过；实现后必须重跑 |
| official lifecycle source review | NOT RUN | 等待调研 |
| NewEmaint/reference project dry-run | NOT RUN | 只读，不实施 upgrade |
| Gitea PR CI | NOT RUN | PR 尚未创建 |
| 项目 migration/test deployment/production | NOT RUN | 不在本 Change 范围 |

## Acceptance criteria 结果

- AC-1 至 AC-14：NOT RUN，等待实现、调研和 reference dry-run。

## 重复部署/执行

- lock generation 第一次/第二次 byte comparison：NOT RUN
- installer 第一次/第二次：NOT RUN
- validator offline rerun：NOT RUN
- 无真实应用部署。

## 故意失败与回滚

- expired exception/EOL/mutable tag/tampered lock：NOT RUN；预期 fail closed。
- official source conflict：NOT RUN；预期 component 不进入 preferred。
- 项目文件 mutation 检查：NOT RUN；预期 reference dry-run 零修改。

## 遗留风险与未完成项

- Issue 中的版本方向仍是 candidate，未完成 official-source 与 compatibility 验证前不能写入
  approved catalog。
- Catalog candidate/CI 通过不等于项目升级、测试部署或 production 验收。
- #22 必须在 #23 交付后整合 lock contract，不能复制版本事实源。
