---
issue: 423
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/423
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
branch: change/423-karpathy-principles
created: 2026-10-22
updated: 2026-10-22
status: pending
---

# Verification：共享工程原则

## 基线与范围

- 基线：fresh `origin/main` = `58b06590c1539ffdeb8af9e0d5a95b78090edb6b`。
- 上游研究 pin：`2c606141936f1eeef17fa3043a72095b4765b9c2`；已读 SKILL.md、CLAUDE.md、Cursor rule、EXAMPLES.md 与 plugin.json。
- 2026-10-22 用户确认 #423，补充纲领性定位和 Claude Code 独立审议。正文共四项工程原则，无具体开发步骤；runtime、CI/安装脚本、根 AGENTS.md 未修改。
- T01 首次治理提交：`f56d6687512cab6bec1a4d5e116ef6db7fe5c540`。提交后停止写入，由两个 fresh Claude Code 只读进程分别重读合同、审议 Standards 与 Spec；实现方未兼任独立审议方。
- 首轮发现按本 Issue 已批准范围返修，作为 T01 治理修订单独提交后再次停止写入，交 fresh Claude Code 复审；不涉及 runtime。

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| `git diff --check`；治理 patch reverse apply-check（`--unidiff-zero`）；`check-change-documents --porcelain` | PASS | T01 返修工作树；文档合同与 PR URL 两项 PASS |
| `usage-bundle.sh --verify --baseline-ref 58b06590c1539ffdeb8af9e0d5a95b78090edb6b` | PASS | 1.14.0；基线已发布的 14 条 release 记录逐条保留；仅重新生成本 Issue 尚未发布的 1.14.0 候选 |
| `usage-bundle.sh --build` + 三端字节/相对链接核对 | PASS | 修订后的隔离输出 `/private/tmp/aisoft-423-bundle-dwworfzn`；Claude/Codex/Cursor 参考文档字节相同，入口链接可解析；adapter 仅 Codex 落点 |
| `LC_ALL=C bash codex/tests/smoke.sh` | PASS | 首次 T01 head `f56d6687512cab6bec1a4d5e116ef6db7fe5c540`，exit 0；含 704 项 Python 主套件、安装/漂移/发布包夹具；末行 `Codex platform static smoke checks passed.`；日志 `/private/tmp/aisoft-423-smoke.log`。返修后完整回归待执行 |
| broker Issue 状态与判级 | PASS | #423 updated，approved + type/platform + complexity/complex；启动确认不含 PR 提交 |
| 上游排序示例的判别力复核 | PASS | 同分顺序不同的两个结果均通过其 score 断言，不能证明 tie-break 修复 |
| 六场景最终独立审议 | PENDING | 首轮能找到对应原则；F4 文字收紧后待新 head 复审 |
| required CI / 全局安装 / provider-session 效果 / 项目采用 / 部署 | NOT RUN | 未 push 或建 PR；后四项不在本次源码授权范围 |

修订后发布包 digest：`sha256:7c727eb4b5bf4efe94592976bf3248c8a04612566e303df8b2cf1d1475c02bf5`；原则 SHA-256：`4789d900d843e4884179e578e4f94db73b08966abab096ca1f80d33bd8d86ae4`。

## Acceptance criteria 结果

AC-1 的 source/local 分发检查 PASS。AC-2–AC-6 等待返修后的完整回归与独立审议；不得把文本原则、桌面场景或静态分发检查写成真实模型效果证明。

## 交叉审查

审议工具：本机 Claude Code `2.1.228`，全新 `-p` 进程，`--safe-mode --permission-mode plan`，只开放 Read/Grep/Glob，禁用 slash commands、Chrome 与 MCP，`--no-session-persistence`；未指定模型覆盖。首轮两个进程实际报告 `claude-opus-5[1m]`。审议方无 shell 或写入工具；运行验证由 Codex 执行并单列。

| 轮次 | 实现方 | 审查方 | exact head | 结论 | 发现与处置 |
|---|---|---|---|---|---|
| R1 Standards | Codex | Claude Code，只读 | `f56d6687512cab6bec1a4d5e116ef6db7fe5c540` | 原文 `VERDICT: PASS`，同时列 1 P2、4 P3；按实质发现处理，未据此宣布整批通过 | F3、F5–F8 已在本次返修处理，待新 head 复审；session `8ac14d65-839e-4eb0-ad5b-4db21403d2cf` |
| R1 Spec | Codex | Claude Code，只读 | `f56d6687512cab6bec1a4d5e116ef6db7fe5c540` | FAIL：1 P1、1 P2、1 P3；本轮合并结论 FAIL | F1、F2、F4 已在本次返修处理，待新 head 复审；session `4aa52035-1846-4761-b492-deb99f716c98` |

首轮原始结果保存在本次会话的 `/private/tmp/aisoft-423-{standards,spec}-review.json` 与同名 `.txt`。以下仓内清单保留每一项发现与处置，不依赖临时文件才能理解结论。

| 编号 | 来源/严重性 | 发现 | 处置与状态 |
|---|---|---|---|
| F1 | Spec / P1 | `git_scope` 仅在 summary，broker 只读 mapped spec，必然 `SCOPE_UNKNOWN` | 清单移入 spec，summary 只保留引用；待新 head 用真实 `GitRepository.scope()` 读取验证 |
| F2 | Spec / P2 | scope 漏列已授权的本 Issue 审议索引行 | 加入 `docs/governance/review-evidence-index.md`，共 13 个 exact 路径；不修改路线图/E2E |
| F3 | Standards / P2 | 风险匹配可能被理解为豁免既有验证硬门 | 原则明确项目已规定的必需验证仍须满足 |
| F4 | Spec / P3 | 澄清依赖操作时，未明确可继续独立工作 | 补明同时继续不依赖该决策的工作 |
| F5 | Standards / P3 | 纲领指导混入 usage 的流程不变量 | 移到独立的“编程思想指导”段，既有六节编号保持 |
| F6 | Standards / P3 | 审议入口位于确认点 1 尾部 | 移入已有确认点 2 段，不增阶段 |
| F7 | Standards / P3 | 08 入口混在 Matt pin/升级说明下 | 移到共享契约下，删除重复免责声明 |
| F8 | Standards / P3 | 三入口加载触发不同、边界声明重复 | 统一首次阅读/本会话已读且未变不重复；详细定位与边界仅保留 reference |

## 遗留风险与未完成项

T01 返修尚待新 head 完整回归、六场景与 Claude Code 复审。只有源码与隔离导出证据，尚未安装、生效到项目或交付 PR。
