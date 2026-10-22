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
status: passed
---

# Verification：共享工程原则

## 基线与范围

- 基线：broker fresh fetch 后 `origin/main` = `58b06590c1539ffdeb8af9e0d5a95b78090edb6b`，未前进。
- 最终治理源码与审议 head：`c87b66bb811add3f2556afac17d5531cb65d1b42`。其后只回填本 Issue 的 summary/spec/plan/verification 与审议索引；原则正文、三个技能、使用合同、08、发布包和治理 patch 的字节均不再改变。
- 上游研究 pin：`2c606141936f1eeef17fa3043a72095b4765b9c2`；已读 SKILL.md、CLAUDE.md、Cursor rule、EXAMPLES.md 与 plugin.json。只自行表述思想，无第三方正文 vendor 或新技能包。
- 2026-10-22 负责人确认 #423，补充纲领性定位和 Claude Code 独立审议。正文只有四项工程原则，无具体开发步骤；runtime、CI/安装脚本、根 AGENTS.md 未修改。
- T01 三次线性提交分别为 `f56d6687512cab6bec1a4d5e116ef6db7fe5c540`、`8988259faf2421e5c43f8761ff129373a936638b`、`c87b66bb811add3f2556afac17d5531cb65d1b42`。每次治理提交后停止写入，由 fresh Claude Code 只读进程重读合同并审议；没有继续 runtime 实施。

## 执行结果

除完整 smoke 两行及另有说明的事实外，下表检查针对 `c87b66bb811add3f2556afac17d5531cb65d1b42` 的工作树；所有测试的退出码均实际读取。

| Command / check | Result | Evidence |
|---|---|---|
| `git diff --check 58b06590...HEAD`；治理 patch reverse apply-check（`--unidiff-zero`）；`check-change-documents --porcelain` | PASS | exact head `c87b66bb811add3f2556afac17d5531cb65d1b42`；文档合同与 PR URL 两项 PASS |
| `usage-bundle.sh --verify --baseline-ref 58b06590c1539ffdeb8af9e0d5a95b78090edb6b` | PASS | exact head `c87b66bb811add3f2556afac17d5531cb65d1b42`；1.14.0 与成员字节一致，基线已发布的 14 条 release 记录完整保留；只重生成本 Issue 未发布的 1.14.0 候选 |
| `usage-bundle.sh --build` + 三端字节/相对链接核对 | PASS | exact head `c87b66bb811add3f2556afac17d5531cb65d1b42`；隔离输出 `/private/tmp/aisoft-423-bundle-16p3v4m1`；Claude/Codex/Cursor 正文同字节，入口链接可解析；adapter 仅 Codex 落点 |
| `LC_ALL=C bash codex/tests/smoke.sh`（首次） | PASS | head `f56d6687512cab6bec1a4d5e116ef6db7fe5c540`，exit 0，含 704 项 Python 主套件及安装/漂移/发布包夹具；末行 `Codex platform static smoke checks passed.`；日志 `/private/tmp/aisoft-423-smoke.log` |
| `LC_ALL=C bash codex/tests/smoke.sh`（R2） | PASS | head `8988259faf2421e5c43f8761ff129373a936638b`，exit 0，704 项 Python 主套件通过，同一末行；日志 `/private/tmp/aisoft-423-r2-smoke.log` |
| `LC_ALL=C bash codex/tests/test-install-skills.sh` | PASS | exact head `c87b66bb811add3f2556afac17d5531cb65d1b42`，exit 0；`/private/tmp/aisoft-423-final-codex-skills.log` 末行 `install-skills tests passed` |
| `LC_ALL=C bash codex/tests/test-install-claude-skills.sh` | PASS | exact head `c87b66bb811add3f2556afac17d5531cb65d1b42`，exit 0；`/private/tmp/aisoft-423-final-claude-skills.log` 末行 `claude skill install tests passed` |
| `LC_ALL=C bash codex/tests/test-usage-bundle.sh` | PASS | exact head `c87b66bb811add3f2556afac17d5531cb65d1b42`，exit 0；`/private/tmp/aisoft-423-final-usage-bundle.log` 末行 `test-usage-bundle: PASS` |
| `GitRepository.scope()` + `verify_history()` | PASS | mapped spec 实际读取；13 个路径与完整 diff 精确相等，三个线性提交逐条在 scope 内；没有调用 push |
| broker Issue 状态、判级、main | PASS | #423 approved；fresh `classify --verify 423` = `projected`，type/platform + complexity/complex；fresh `git.fetch.main` 后仍为上述基线 |
| 上游排序示例的判别力复核 | PASS | 研究阶段实际运行：同分顺序不同的两个结果均通过其 score 断言，不能证明 tie-break 修复 |
| 六场景独立文本推演 | PASS | R3 Claude Code Spec 审议将六场景逐项映射到正文，未发现缺失或越界；不是实际模型行为实验 |
| required CI / 全局安装 / provider-session 效果 / 项目采用 / 部署 | NOT RUN | 未 push 或建 PR；后四项不在本次源码授权范围 |

R2 后的变动只有入口/段落位置、重复文字、未采用的路线图条件授权及候选 digest。原则正文与所有 runtime/test/installer 均未改变，因此运行直接受影响的三项既有夹具、文档与导出检查；不把旧 head 的 full smoke 冒充最终 head 的实跑。

发布包 digest：`sha256:d15d8aebb605668c4c2b22347750271f41f259865b720872a6a79c7c73d62ab5`；原则 SHA-256：`4789d900d843e4884179e578e4f94db73b08966abab096ca1f80d33bd8d86ae4`。

## Acceptance criteria 结果

| AC | Result | Evidence |
|---|---|---|
| AC-1 | PASS | 一份 reference、三技能入口与使用合同；隔离导出三端字节、链接及 manifest 落点核对 |
| AC-2 | PASS | 重要假设与按影响澄清；低风险自主，不依赖决策的工作继续；R3 文本审议与场景 S1–S3 |
| AC-3 | PASS | 当前需求、必要防护、聚焦且完整修复；R3 文本审议与 S4–S6 |
| AC-4 | PASS | 可验证目标、判别力、风险匹配和必需验证并存；无固定测试顺序或新硬门 |
| AC-5 | PASS | 文档/技能/发布包检查、两次真实 full smoke 与最终文案定向回归；六场景文本推演通过 |
| AC-6 | PASS | 固定思想来源，已发布历史不变；治理独立提交后停止；Claude Code fresh、只读、另一提供者审议通过 |

六场景均为文本层审议：S1 已批准一行文案 → 不复问/不造形式测试；S2 lock 可查版本 → 自主查证；S3 敏感导出歧义 → 先澄清、独立工作继续；S4 单一计算 → 现有模式而非预建框架；S5 空输入错误 → 可靠复现、完整修复、无夹带；S6 外部输入/权限失败 → 保留防护、负例有判别力。

## 交叉审查

审议工具：本机 Claude Code `2.1.228`，全新 `-p` 进程，`--safe-mode --permission-mode plan`，只开放 Read/Grep/Glob，禁用 slash commands、Chrome 与 MCP，`--no-session-persistence`；未指定模型覆盖。首轮两个进程实际报告 `claude-opus-5[1m]`。审议方无 shell 或写入工具；运行验证由 Codex 执行并单列。

| 轮次 | 实现方 | 审查方 | exact head | 结论 | 发现与处置 |
|---|---|---|---|---|---|
| R1 Standards | Codex | Claude Code，只读 | `f56d6687512cab6bec1a4d5e116ef6db7fe5c540` | 原文 `VERDICT: PASS`，同时列 1 P2、4 P3；按实质发现处理，未据此宣布整批通过 | F3、F5–F8 已修订，R3 复核通过；session `8ac14d65-839e-4eb0-ad5b-4db21403d2cf` |
| R1 Spec | Codex | Claude Code，只读 | `f56d6687512cab6bec1a4d5e116ef6db7fe5c540` | FAIL：1 P1、1 P2、1 P3；本轮合并结论 FAIL | F1、F2、F4 已修订，R3 复核通过；session `4aa52035-1846-4761-b492-deb99f716c98` |
| R2 Standards | Codex | Claude Code，只读 | `8988259faf2421e5c43f8761ff129373a936638b` | PASS，3 项不阻断的 P3 | F3/F5/F7/F8 fixed，F6 residual；新增 F10/F11，均作同范围文字修订，R3 复核通过；session `14428bb9-ff1e-4e8f-9e66-81f5351b382a` |
| R2 Spec | Codex | Claude Code，只读 | `8988259faf2421e5c43f8761ff129373a936638b` | FAIL，1 P2、1 P3；本轮合并结论 FAIL | F1/F2/F4 fixed；新增 F9，另指出 F6；均已修订，R3 复核通过；session `09a3cab3-0ea2-480b-9e7d-2e6f8bd1a6f3` |
| R3 Standards | Codex | Claude Code，只读 | `c87b66bb811add3f2556afac17d5531cb65d1b42` | PASS；本轴既有发现无 residual | F3/F5–F8/F10/F11 fixed；新增 F13/F14 两项不阻断文风建议，处置见下；session `cf398513-e795-44ed-ab6e-1a8ce75e6833` |
| R3 Spec | Codex | Claude Code，只读 | `c87b66bb811add3f2556afac17d5531cb65d1b42` | PASS；本轮合并结论 PASS | F1/F2/F4/F9 fixed，六场景文本推演符合合同；F12 建议在归档中补 exact head，已补；session `a1c88e06-be28-4c64-860a-fc906081cf92` |

首轮原始结果保存在本次会话的 `/private/tmp/aisoft-423-{standards,spec}-review.json` 与同名 `.txt`；R2 为 `/private/tmp/aisoft-423-r2-{standards,spec}-review.json` 与 `.txt`；R3 为 `/private/tmp/aisoft-423-r3-{standards,spec}-review.json` 与 `.txt`。以下仓内清单保留每一项发现与处置，不依赖临时文件才能理解结论。

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
| F12 | R3 Spec / P3，不阻断 | 部分通过记录未绑定精确提交号 | 本次 T02 归档将各项 source/local 检查标明为 `c87b66bb811add3f2556afac17d5531cb65d1b42`，完整 smoke 保留真实的旧 head；已修复 |
| F13 | R3 Standards / P3，不阻断 | 08、使用合同、发布 notes 与正文的概括用词不同 | 未采纳统一改写建议：标题概括与边界说明用途不同，均指向单一正文，未形成第二份要求清单；保留既有简短导航，不为同义措辞重开源码修订 |
| F14 | R3 Standards / P3，不阻断 | 英文 adapter 链接跳到中文正文，建议加语言标注 | 未采纳：本次按负责人要求交付中文思想正文，平台共享合同以中文为主；沿用 adapter 既有英文结构，无新增本地化要求 |

F1–F11 已经 R3 独立复核；F12 是审议明确留给归档步骤的证据补齐，已处理。F13/F14 为建议，审议原文明确“不阻断”，不作为未解决的合同缺陷。

## 遗留风险与未完成项

源码、隔离分发与独立文本审议完成，当前为 `AWAITING_PR_CONFIRMATION`。#423 保持 `approved`，summary 的 `pr_url` 留空；没有 push 或 PR，required CI 尚未运行。
全局安装、真实 provider-session 效果、项目采用、部署均未执行，不能从本记录推断这些层面的生效。F13/F14 是记录保留的非阻断文风建议。
