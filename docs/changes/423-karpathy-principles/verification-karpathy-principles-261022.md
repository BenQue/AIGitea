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
| `usage-bundle.sh --build` + 三端字节/相对链接核对 | PASS | 最终文字修订的隔离输出 `/private/tmp/aisoft-423-bundle-olspm6hk`；Claude/Codex/Cursor 参考文档字节相同，入口链接可解析；adapter 仅 Codex 落点 |
| `LC_ALL=C bash codex/tests/smoke.sh` | PASS | 首次 T01 head `f56d6687512cab6bec1a4d5e116ef6db7fe5c540`，exit 0；含 704 项 Python 主套件、安装/漂移/发布包夹具；末行 `Codex platform static smoke checks passed.`；日志 `/private/tmp/aisoft-423-smoke.log`。R2 head `8988259faf2421e5c43f8761ff129373a936638b` 再跑完整 smoke，exit 0、704 项 Python 主套件通过，同一末行；日志 `/private/tmp/aisoft-423-r2-smoke.log` |
| broker Issue 状态与判级 | PASS | #423 approved；R2 fresh `classify --verify 423` = `projected`，type/platform + complexity/complex；启动确认不含 PR 提交 |
| `GitRepository.scope()` + `verify_history()` | PASS | R2 head 实际读取 mapped spec，13 个路径与完整 diff 精确相等，两次线性提交逐条在 scope 内；没有调用 push |
| R2 之后的文档与分发定向回归 | PENDING | 仅移动已有入口/段落、删重复文字、收紧路线图条件授权及同步候选 digest；原则正文与所有 runtime/test/installer 不变，待提交后执行现有三项安装/发布包夹具及文档/导出检查 |
| 上游排序示例的判别力复核 | PASS | 同分顺序不同的两个结果均通过其 score 断言，不能证明 tie-break 修复 |
| 六场景最终独立审议 | PENDING | 首轮能找到对应原则；F4 文字收紧后待新 head 复审 |
| required CI / 全局安装 / provider-session 效果 / 项目采用 / 部署 | NOT RUN | 未 push 或建 PR；后四项不在本次源码授权范围 |

修订后发布包 digest：`sha256:d15d8aebb605668c4c2b22347750271f41f259865b720872a6a79c7c73d62ab5`；原则 SHA-256：`4789d900d843e4884179e578e4f94db73b08966abab096ca1f80d33bd8d86ae4`。

## Acceptance criteria 结果

AC-1 的 source/local 分发检查 PASS；完整 smoke 在 R2 head PASS。AC-2–AC-6 等待最后一轮文字修订的定向回归与独立审议；不得把文本原则、桌面场景或静态分发检查写成真实模型效果证明。

## 交叉审查

审议工具：本机 Claude Code `2.1.228`，全新 `-p` 进程，`--safe-mode --permission-mode plan`，只开放 Read/Grep/Glob，禁用 slash commands、Chrome 与 MCP，`--no-session-persistence`；未指定模型覆盖。首轮两个进程实际报告 `claude-opus-5[1m]`。审议方无 shell 或写入工具；运行验证由 Codex 执行并单列。

| 轮次 | 实现方 | 审查方 | exact head | 结论 | 发现与处置 |
|---|---|---|---|---|---|
| R1 Standards | Codex | Claude Code，只读 | `f56d6687512cab6bec1a4d5e116ef6db7fe5c540` | 原文 `VERDICT: PASS`，同时列 1 P2、4 P3；按实质发现处理，未据此宣布整批通过 | F3、F5–F8 已在本次返修处理，待新 head 复审；session `8ac14d65-839e-4eb0-ad5b-4db21403d2cf` |
| R1 Spec | Codex | Claude Code，只读 | `f56d6687512cab6bec1a4d5e116ef6db7fe5c540` | FAIL：1 P1、1 P2、1 P3；本轮合并结论 FAIL | F1、F2、F4 已在本次返修处理，待新 head 复审；session `4aa52035-1846-4761-b492-deb99f716c98` |
| R2 Standards | Codex | Claude Code，只读 | `8988259faf2421e5c43f8761ff129373a936638b` | PASS，3 项不阻断的 P3 | F3/F5/F7/F8 fixed，F6 residual；新增 F10/F11，均作同范围文字修订；session `14428bb9-ff1e-4e8f-9e66-81f5351b382a` |
| R2 Spec | Codex | Claude Code，只读 | `8988259faf2421e5c43f8761ff129373a936638b` | FAIL，1 P2、1 P3；本轮合并结论 FAIL | F1/F2/F4 fixed；新增 F9，另指出 F6；均在本次修订处理；session `09a3cab3-0ea2-480b-9e7d-2e6f8bd1a6f3` |

首轮原始结果保存在本次会话的 `/private/tmp/aisoft-423-{standards,spec}-review.json` 与同名 `.txt`；R2 为 `/private/tmp/aisoft-423-r2-{standards,spec}-review.json` 与 `.txt`。以下仓内清单保留每一项发现与处置，不依赖临时文件才能理解结论。

| 编号 | 来源/严重性 | 发现 | 处置与状态 |
|---|---|---|---|
| F1 | Spec / P1 | `git_scope` 仅在 summary，broker 只读 mapped spec，必然 `SCOPE_UNKNOWN` | 清单移入 spec，summary 只保留引用；R2 head 用真实 `GitRepository.scope()` 读取及逐提交范围验证 PASS |
| F2 | Spec / P2 | scope 漏列已授权的本 Issue 审议索引行 | 加入 `docs/governance/review-evidence-index.md`，共 13 个 exact 路径；不修改路线图/E2E |
| F3 | Standards / P2 | 风险匹配可能被理解为豁免既有验证硬门 | 原则明确项目已规定的必需验证仍须满足 |
| F4 | Spec / P3 | 澄清依赖操作时，未明确可继续独立工作 | 补明同时继续不依赖该决策的工作 |
| F5 | Standards / P3 | 纲领指导混入 usage 的流程不变量 | 移到独立的“编程思想指导”段，既有六节编号保持 |
| F6 | Standards / P3 | 审议入口位于确认点 1 尾部 | R1 曾移入确认点 2；R2 指出仍属跨阶段指引，本次移至流程前独立的“共享工程原则”通用说明 |
| F7 | Standards / P3 | 08 入口混在 Matt pin/升级说明下 | 移到共享契约下，删除重复免责声明 |
| F8 | Standards / P3 | 三入口加载触发不同、边界声明重复 | 统一首次阅读/本会话已读且未变不重复；详细定位与边界仅保留 reference |
| F9 | R2 Spec / P2 | spec/plan 的条件路线图授权与实际 13 项清单不一致 | 删除条件授权并明确本批不登记路线图，不扩大清单 |
| F10 | R2 Standards / P3 | 08 原则段重复分发证据 caveat | 删除半句，实际验证边界保留在本记录 |
| F11 | R2 Standards / P3 | usage 的无号 H2 打断编号章节 | 原则说明改为末尾 §7；既有 §1–§6 引用不变 |

## 遗留风险与未完成项

R2 后的纯文字修订尚待提交后的定向分发/文档回归、六场景与 Claude Code 复审；完整 smoke 已在 R2 head 通过，不把旧 head 的运行结果写成新 head 实跑。只有源码与隔离导出证据，尚未安装、生效到项目或交付 PR。
