---
issue: 287
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/287
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - shared-core
  - schema-change
  - external-contract
  - platform-governance
depends_on: []
status: approved
branch: change/287-profile-semantic-lock
created: 2026-10-02
updated: 2026-10-02
---

# #287 Implementation plan

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 应用哈希覆盖、格式与迁移的 architecture 文档合同；独立提交并停止，等待 fresh run 重读 | - | completed |
| T02 | V2 新生成与严格 V1/V2 校验闭环，说明稳定/机器漂移/显式迁移可在 CLI 验证 | T01 | pending |
| T03 | 补足兼容/故意失败/全量回归与实际 receipts，形成唯一 manual PR 候选 | T02 | pending |

本图在同一个 #287 下执行，不新建 child Issue；用户已在合同启动确认中认可粒度与依赖。

## Expected touch points

- T01：仅 `architecture/README.md` 与新 `architecture/decisions/0007-profile-machine-checksum.md`；治理合同应用完成后停止，不同轮 runtime。
- T02：`codex/runtime/aisoft_architecture/lockfile.py`、`cli.py`，必要时新增专门 hash helper；新增 `architecture/schemas/architecture-lock-v2.schema.json`，保留 V1 schema 原样；targeted tests 和历史 before/after test fixtures。禁止引入新依赖。
- T03：现有 architecture 测试补覆盖、必要测试 fixture；本 Change verification/summary/plan 真实结果同步；若 T02 契约失败只做合同内追加修复。
- 不修改 shell/CI/controller/AGENTS/skills/broker/installer。若发现必须改这些范围，停止并提出具体合同冲突。

## 数据库迁移

无。V1→V2 是输出格式迁移；本平台不迁移其它仓 lock，不修改平台 reference locks。

## 测试与验收映射

| Acceptance criterion | Ticket | Verification command or review |
|---|---|---|
| AC-1 | T02；T03 复核 | `PYTHONPATH=codex/runtime python3 -m unittest tests.test_architecture_lock tests.test_architecture_cli -v`：新增历史 V2 回归与 prose 探针 |
| AC-2 | T02；T03 复核 | 同 targeted suites：逐字段合法 drift 与非法 schema/semantic 探针，漏 bump delivery 精确 LOCK_DRIFT |
| AC-3 | T02；T03 复核 | 同 targeted suites：V1 reference、prose drift、篡改、版本/marker/额外字段拒绝 |
| AC-4 | T02；T03 复核 | CLI 临时目录生成/validate 两次，核对原 V1 字节未变与同输出 identity |
| AC-5 | T02 硬门；T03 全量复核 | `PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests -t codex/runtime -p 'test_architecture*.py' -v` 与 release integration suite |
| AC-6 | T03 | `bash codex/tests/smoke.sh`；若实际改 shell 则额外相应 bash -n 与 ShellCheck（可用），未改不伪造结果 |
| AC-7 | T01 文档应用；T03 文档与实现一致性复核 | README/ADR 与实现 diff review；`PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli check-change-documents --repo .` |
| AC-8 | T01/T02/T03 各自范围复核 | `git diff --name-only origin/main`、`git status --short` 和保存的 broker/本地 receipt 核对；仅本 owner worktree |

## 依赖与并发

`depends_on: []`。#288 可独立调查，不要求它先合并。实现前和最终候选前经 broker fresh fetch，核对 origin/main；最新 main 已变时本 writer 自行 rebase 并按影响重验。不能在别人的 worktree 解冲突。

## 部署与回滚

无部署。回滚遵循 spec 的 V2 已被消费后的双 reader 边界；不使用批量重 lock 消除失败。

## 确认与交付

用户已确认完整合同。T01 独立合同步骤并停止；fresh run 执行 T02/T03，持续完成实现/测试/修复。T03 完成后真实 `apply-classification-labels.sh --verify 287` projected，再请求绑定 #287、exact branch、manual 的唯一最终 PR 提交确认。未确认不 push/PR。CI 绿后停 READY_FOR_REVIEW，用户人工合并；merge 后自动核对/精确清理/归档。
