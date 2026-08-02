---
issue: 22
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/22
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
  - artifact
  - deployment
  - migration
  - rollback
  - platform-governance
depends_on:
  - 23
status: pending
branch: change/22
pr_url:
created: 2026-08-02
updated: 2026-08-02
---

# Verification

## 环境与版本

- Source baseline：`origin/main@b806317cc87a58049719fff103af2c9d7c14ed56`
- Candidate branch：`change/22`
- Dependency：Issue #23 尚未交付
- Docker/Compose：local candidate 使用 fake adapter；真实 AppServer `NOT RUN`

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| planning contract parse + AC map | PASS | `load_contract` 通过；12 条 AC 全部映射；dependency 为 #23 |
| contract/profile/transport/runner tests | NOT RUN | 等待实现 |
| installer repeatability smoke | NOT RUN | 等待实现 |
| `bash codex/tests/smoke.sh` | PASS（planning baseline） | 105 项 Python tests 与全部 shell/static smoke 通过；实现后必须重跑 |
| #23 dependency + integration | NOT RUN | 等待 #23 合并 |
| Gitea PR CI | NOT RUN | PR 尚未创建 |
| Registry test AppServer | NOT RUN | 不在当前授权范围 |
| offline-bundle test AppServer | NOT RUN | 不在当前授权范围 |
| production promotion | NOT RUN | 不在当前授权范围 |

## Acceptance criteria 结果

- AC-1 至 AC-12：NOT RUN，等待实现、依赖交付和真实验证。

## 重复部署/执行

- installer 第一次/第二次：NOT RUN
- fake deploy 第一次/同 SHA 第二次：NOT RUN
- 真实 test deploy：NOT RUN

## 故意失败与回滚

- Compose/archive tamper：NOT RUN；预期 mutation 前失败。
- `scm-ci` target role：NOT RUN；预期 deploy denied。
- health failure：NOT RUN；预期 previous release 回切。
- PostgreSQL restore：NOT RUN；runtime 不自动 restore。

## 遗留风险与未完成项

- #23 profile/catalog/lock 尚未交付，#22 不得进入 review-ready。
- Fake Docker 证据不等于真实 Registry、TLS、offline media、AppServer 或 production。
- NewEmaint 消费与全部环境部署属于独立 Change/Gate。
