---
issue: 317
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/317
change_type: bugfix
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - data-migration
  - external-contract
  - shared-core
  - rollback
  - security
  - platform-governance
depends_on: []
status: contract-drafting
branch: change/317-migration-rollback-guard
created: 2026-10-02
updated: 2026-10-02
---

# 实施 Ticket graph

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 发布并可读回独立 release 兼容治理合同，完成后停止等待 fresh run | - | pending |
| T02 | public phased lifecycle 实现 v3 DB position 与 exact compatibility gate，从状态记录到 activate/rollback/错误输出可验收 | T01 + fresh run | pending |
| T03 | legacy deploy 与所有恢复路径统一 gate，consumer 说明、边界回归与最终候选 | T02 | pending |

不新建子 Issue；所有 ticket 保持 #317。T01 合同批准前不应用。T01 完成后停止当前运行；后续 fresh run 沿用该批准，不增加第三个产品确认点。

## Expected touch points 与明确 allowlist

- T01：`docker-release/README.md`、`docker-release/contracts/migration-rollback-v1.md`、本 Issue 映射文档。只应用治理合同，不触 runtime/schema/test。
- T02：`codex/runtime/aisoft_release/runner.py`、`state.py`、`contract.py`、`errors.py`；同目录新增受限 compatibility 模块；`docker-release/schema/state-v3.schema.json`、target profile v1 schema 的 optional field、compatibility evidence v1 schema；release phase/state/CLI/safety tests 及现有 fixture support；`cli.py` 仅若安全结构化错误需要调整，既有 CLI 参数不扩展。
- T03：同一 runner public deploy/restoration path；相应 runner/phases/contract/safety/CLI/evidence tests；consumer contract 说明、脱敏 example 与本 Issue verification。原 v1/v2 state schema 原字节保持。
- 禁止 AGENTS.md、CLAUDE.md、controller/provider、broker、CI workflow、任何 installer、host permission/grant、应用仓文件改动。

## 测试与验收映射

| Ticket / AC | Verification command or review |
|---|---|
| T01 | docs diff review；`PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli check-change-documents --repo .`；确认仅合同文档，并记录停止点 |
| T02 / AC-01,03,04,05,06,07 | `PYTHONPATH=codex/runtime python3 -m unittest tests.test_release_phases tests.test_release_rollback_compatibility tests.test_release_contract tests.test_release_safety` |
| T02 / AC-08,09 | `PYTHONPATH=codex/runtime python3 -m unittest tests.test_release_cli tests.test_release_gate`；包括安全字段及 argv 出口 |
| T03 / AC-02,04,06,08 | `PYTHONPATH=codex/runtime python3 -m unittest tests.test_release_runner tests.test_release_phases tests.test_release_rollback_compatibility` |
| T03 / AC-01–09 | `PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests -p 'test_release*.py'`；`bash codex/tests/smoke.sh` |
| T03 / AC-10 | consumer 文档人工 diff review，说明仅使用最终人工 merged SHA，未提供不存在的 pin；scope diff 检查 |
| 最终候选 | classification --apply → 独立 --verify #317 两维 projected；local commit clean；唯一 Issue/branch/worktree/docs tuple |

新增测试文件名是预计实施接口；批准前不存在，尚未运行上述修复验证。

## 数据库迁移

无真实数据库迁移。本票仅改变本地 deployment state 的受限读升级和写版本；FakeDocker 不操作真实 DB。未知旧 state 不自动生成可信位置，兼容依据独立 operator 管理。

## 部署与回滚

不部署、不安装。两次重复、一次故意健康失败及失败回退阻止在临时 fixture 执行，报告 source/local 事实；真实 Docker/公司现场验收 NOT RUN，属于消费项目独立授权。

本票代码出现问题用 forward fix 或保留 guard 的源码 revert，state v3 不强行降级。不能恢复旧 state/数据库绕过新的保护。

## 最终确认与交付

只有本地 AC 验证、完整 smoke、diff review 和真实 classification --verify projected 后才请求 exact #317 / change/317-migration-rollback-guard / manual 的最终 PR 提交确认。随后 broker push、pushed_head 与候选 SHA 比对、唯一 Closes #317 PR、回填实际 pr_url、required CI。停 READY_FOR_REVIEW，由人合并。merge 后证明 exact SHA 在 origin/main、确定性终态检查/清理/归档；NewEMaint #229 在其会话继续更新 pin。
