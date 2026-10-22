---
issue: 425
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/425
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
depends_on: []
branch: change/425-review-principles
created: 2026-10-22
updated: 2026-10-22
---

# Plan：共享工程原则的审查思想

本计划交付纲领文档；其中步骤不写进原则正文，也不改变平台具体流程。

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 受控应用批准文案和 bundle 追加登记，局部核验，独立 commit 后停止治理写入 | - | done |
| T02 | fresh Claude Code 重读合同、只读审议；完成回归、隔离导出与证据记录，形成最终 PR 候选 | T01 | done |

## Expected touch points

- T01：只应用冻结 patch 到原则正文，以现有工具生成 1.15.0 minor release；不改成员集合和历史。先检查 candidate SHA-256、原有章节、diff、文档与 bundle baseline，原子 commit 后停止治理写入。
- T02：重新读取合同与 exact head，运行完整 smoke、隔离构建与反例审议；由未参与实现的 Claude Code fresh 只读进程审查原则和合同符合性。本会话只写本 Issue 的证据/状态及审议索引，禁止接续 runtime 实施。
- 同范围发现若确需治理返修，使用单独受控 commit 并再次停止、fresh 审议；涉及改变已批准文案或范围的实质决策先升级，不静默更改。
- 负责人已批准本合同内 T01/T02；不按 ticket 或测试命令重复索要确认。

## 验证映射

| AC | 验证 |
|---|---|
| AC-1 | 全文字节 SHA-256、旧四部分前缀相等、来源和冻结 patch 反向检查 |
| AC-2 | diff 与六场景文本审议；明确不称为真实模型实验 |
| AC-3 | `usage-bundle.sh --verify --baseline-ref 9964f740ec6b4328714c1c5244da8ea7b6d9cc8a`；隔离 `--build` 后三端 `cmp`；历史与成员集合比较 |
| AC-4 | `git diff --check`、`aisoft check-change-documents --porcelain`、`AISOFT_USAGE_BASELINE_REF=9964f740ec6b4328714c1c5244da8ea7b6d9cc8a LC_ALL=C bash codex/tests/smoke.sh`、真实 Git scope/history 核验 |
| AC-5 | 治理 commit/停止记录；fresh Claude Code 的 exact-head 审议及既有六列表；判级投影读回；最终 PR 确认前停止 |

完整 smoke 已含 Codex/Claude 安装夹具、bundle 夹具与 baseline 不变性，不无故重复通过的定向测试。不新建镜像原则文字的形式测试，不实际安装或 adopt。

## 实际完成

T01 在 `6550228fc2c239f860bcd923638687f43648ee10` 提交后停止；T02 已完成完整 smoke、隔离导出、六场景文本审议及 Claude Code 两轮交叉审议，最终两轴 PASS。全分支空白检查发现提案 patch 上下文格式问题，已在 `b1c6cec3e12d99b75ac708ec88ee12c3741940c8` 改成等价零上下文格式并重跑相关检查，正文/bundle 未变。发现与处置、精确 head 与未执行项见 verification。

## 部署与回滚

无部署或全局安装。回滚按 spec；最终 push/PR 需确认点 2，合并由人执行。
