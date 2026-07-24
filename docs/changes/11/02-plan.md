---
issue: 11
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/11
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - shared-core-component
  - external-contract
depends_on: []
status: implemented
branch: change/11
pr_url:
created: 2026-07-24
updated: 2026-07-24
---

# Implementation plan

## 任务分解

1. 在 `contract.py` 中加入兼容旧文档的 `depends_on` 解析和严格验证，并把结果写入 `Contract.dependencies`。
2. 在 controller provider request 与 PR body 中公开依赖；增加 `awaiting_dependencies` 持久状态，确保等待期间不重跑 provider。
3. 使用现有 `GiteaClient.get_issue` 逐项确认依赖 Issue 同时 closed 且带 `deployed`；API 错误沿既有外部阻塞路径失败关闭。
4. 更新 change 模板和 03/04 分册，明确 Gitea PR CI 测 head、依赖护栏不等于锁。
5. 添加合同与 controller 回归，先覆盖失败场景，再运行完整平台 smoke。

## 涉及文件

- `codex/runtime/aisoft_loop/contract.py`
- `codex/runtime/aisoft_loop/controller.py`
- `codex/runtime/tests/test_contract.py`
- `codex/runtime/tests/test_controller.py`
- `templates/docs/changes/_template/00-summary.md`
- `templates/docs/changes/_template/01-spec.md`
- `templates/docs/changes/_template/02-plan.md`
- `templates/docs/changes/_template/03-verification.md`
- `03-Issue-Spec-Plan与单闸门开发流程.md`
- `04-Agent编排与定时任务.md`
- `docs/changes/11/`

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | `PYTHONPATH=codex/runtime python3 -m unittest codex.runtime.tests.test_contract -v` 验证缺省与合法列表 |
| AC-2 | 同一测试覆盖 self、duplicate、non-integer、zero、negative |
| AC-3 | `test_controller.py` 断言 PR body 的依赖清单和无依赖文本 |
| AC-4 | `test_controller.py` 断言 CI success + pending dependency 返回 `CONTINUE`、单 PR、单 provider turn |
| AC-5 | 同一 controller/state 二次运行，在依赖 closed+deployed 后进入 `READY_FOR_REVIEW` |
| AC-6 | `bash codex/tests/smoke.sh` |

## 部署与回滚

无应用部署。回滚使用 Gitea PR revert；`depends_on` 缺省兼容保证回滚前后旧项目合同可读。
