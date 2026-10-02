---
issue: 289
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/289
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - shared-core
  - platform-governance
depends_on: []
status: approved
branch: change/289-required-docs-source
created: 2026-10-02
updated: 2026-10-02
---

# #289 实施与验收计划

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 独立治理说明：冻结声明事实源/route 最低要求/部署边界；提交后停止，等待 fresh run 重读 | - | completed |
| T02 | 缺失声明文件从 resolver/audit/Loop 到 terminal 全路径红；受限 publisher 仍可首次创建；含 targeted/mock 测试 | T01 | pending |
| T03 | 历史 fixture/legacy/三档 lifecycle 和平台、SFM 当前对比；全量验证、审查、classification 读回及最终 PR 候选 | T02 | pending |

T01 完成后以会话停顿落实 fresh run，runtime 在下一次续办中读取更新合同再动手。T02 是一个可单独复现的端到端切片，测试伴随实现；T03 收口验收，不建立第二 PR。父 Issue 内完成 Txx，不建子 Issue。

## Expected touch points

- T01：README.md、03-Issue-Spec-Plan与单闸门开发流程.md、本 change 的 summary/spec/plan/verification；不改 AGENTS.md。
- T02：codex/runtime/aisoft_loop/contract.py（声明/存在性与 required roles）、classification.py（仅保留已声明角色，现有复杂判级不放宽）、change_audit.py、cli.py（新增只读 required JSON）、documents.py（受限初次 publisher）、codex/tools/mark-completed-issues.sh；相应 runtime/tests/test_contract.py、test_classification.py、test_change_audit.py、test_cli.py、test_documents.py、codex/tests/test-mark-completed-issues.sh 和固定历史 fixture。
- T03：对应测试与本 change 的验证证据；不改其它 change 文档或 SFM 工作树。若 controller 不需要代码修改就不触及；现有 load_contract 消费方通过共享结果获得严格行为。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Ticket | Verification command or review |
|---|---|---|
| AC-1 | T02/T03 | 真实历史 summary fixture 的三个 CLI（resolve-documents/resolve-required-documents/check-change-documents）及 load_contract；targeted runtime tests |
| AC-2 | T02 | python3 -m unittest discover -s codex/runtime/tests -p test_contract.py；test_classification.py / test_change_audit.py |
| AC-3 | T02 | bash codex/tests/test-mark-completed-issues.sh；非法合同 --apply mock 日志零写入 |
| AC-4 | T02/T03 | test-mark-completed-issues.sh 三档矩阵与 legacy fixture；test_contract.py |
| AC-5 | T02 | test_documents.py / test_cli.py，首次创建、部分未完成合同与不可绕过 reader |
| AC-6 | T03 | PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli check-change-documents --repo <platform-or-SFM> --porcelain；与 evidence/*-audit-baseline.txt 逐项比较 |
| AC-7 | T01/T03 | 文档 review；PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests；bash -n 两个受影响脚本；shellcheck（存在时）；bash codex/tests/smoke.sh |

执行命令均带 PYTHONDONTWRITEBYTECODE=1 / PYTHONPATH=codex/runtime；真实输出写 verification。SFM 基线不全绿，按原有 GAP 清单不新增且合法目录不回退验收。全部闸门完成后真实运行 classification --verify 289，只有 type 和 complexity 两维均 projected 才请求最终 PR 提交确认。

## 部署与回滚

本 Issue 无部署或安装；deployment_lifecycle=none 不变。回滚使用受控 revert PR，manual 合并；不 direct push main、force、自动合并或更改 CI context。完成本地门禁不代表 PR CI、installed/live 或现场执行。

## 依赖与归属

depends_on=[]，无硬依赖；#286 是文件交叠关联。实现前读取 worktree owners；若 #286 先合并，由本 owner rebase #289 并重新验证，不进入或改写 #286 的 worktree。新调度已授权本 Issue 独立处理，旧调度顺序记为历史证据。
