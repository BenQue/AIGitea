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
updated: 2026-10-23
status: passed
---

# Verification：共享工程原则的审查思想

## 基线与范围

- fresh broker fetch 后基线 `origin/main` 为 `9964f740ec6b4328714c1c5244da8ea7b6d9cc8a`，收口前再次刷新，未前进。
- 单写者会话绑定 Issue #425、`change/425-review-principles` 与 `/private/tmp/issue-425-review-principles`。合同提交 `50806d20377b93c58341f93daef16cedaf2e6a76`；T01 治理提交及 R1/R2 正文审议 head 为 `6550228fc2c239f860bcd923638687f43648ee10`。
- 按负责人指定，R3 使用 Fable 5 / high，exact head 为 `cfc13a64cefe1b82864a1fb75729f8d362c65ebf`；这是包含 T02 证据的完整候选。R3 之后仅在本 Issue summary/plan/verification 和索引本行补记本次审议，原则正文与 bundle 未变。
- T01 提交后停止治理写入，由 fresh Claude Code 重读合同并只读审议。后续只有本 Issue 提案格式、文档证据及审议索引变化；原则正文与 bundle 均保持已审字节，不接续 runtime 实施。
- 全文 SHA-256：`07c78311875b6c99a68a131d8b1adaf5894d8faf1cb02902e9335bd19983f456`。bundle 1.15.0 digest：`sha256:c3e3ed4fb8c2c0f607fa4ec88e8056af4c8409fe889ec71364c3b5217a7b9401`。

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| 候选字节、原四部分及历史核对 | PASS | T01 工作树后提交为 `6550228fc2c239f860bcd923638687f43648ee10`，T02 再核对；Python `hashlib.sha256(Path(...).read_bytes())` 等于批准指纹；取基线原则中 `## 来源与适配` 前的字节，与新正文 `## 让审查发现真实问题` 前的字节比较相等；bundle `members` 相等且旧 15 条 `releases` 精确等于新历史前缀 |
| `usage-bundle.sh --release 1.15.0 --today 2026-10-22 --compatibility minor`（notes 见 bundle） | PASS | T01 实际 exit 0；生成上述 digest，只追加登记，不创建远端 Release/tag |
| `usage-bundle.sh --build` + 三端字节比较 | PASS | exact head `6550228fc2c239f860bcd923638687f43648ee10`；exit 0，隔离目录 `/private/tmp/aisoft-425-bundle-3t_5acav`；逐个比较 `project/{.agents,.claude,.cursor}/skills/aisoft-platform/references/engineering-principles.md` 的 `read_bytes()` 与源码相等；receipt `/private/tmp/aisoft-code-review-261022-xLBylI/425-build-result.json` |
| `AISOFT_USAGE_BASELINE_REF=9964f740ec6b4328714c1c5244da8ea7b6d9cc8a LC_ALL=C bash codex/tests/smoke.sh` | PASS | exact head `6550228fc2c239f860bcd923638687f43648ee10`，exit 0；含 12、46、704、1 项的 Python 套件及安装/分发/漂移夹具；末行 `Codex platform static smoke checks passed.`；日志 `/private/tmp/aisoft-code-review-261022-xLBylI/425-smoke.log`，SHA-256 `ad119772059048845679e246b3fd39457ae2a2f9f5dd0bbb9ff31581bcbc4bca` |
| `git diff --check 9964f740ec6b4328714c1c5244da8ea7b6d9cc8a HEAD` | FAIL → PASS | 首次全分支检查发现冻结 patch 的两个空白上下文行被当成 trailing whitespace；只将提案转换为零上下文格式并注明 `--unidiff-zero`，提交 `b1c6cec3e12d99b75ac708ec88ee12c3741940c8` 后同命令 exit 0；未改变批准正文或 bundle |
| `git apply --unidiff-zero --reverse --check docs/changes/425-review-principles/proposals/engineering-principles.patch` | PASS | exact head `b1c6cec3e12d99b75ac708ec88ee12c3741940c8`，exit 0，证明格式调整后的 patch 仍对应已批准的正文增量 |
| `aisoft check-change-documents --porcelain` | PASS | exact head `b1c6cec3e12d99b75ac708ec88ee12c3741940c8`，exit 0；`change-documents` 与 `change-pr-url` 均 PASS |
| `usage-bundle.sh --verify --baseline-ref 9964f740ec6b4328714c1c5244da8ea7b6d9cc8a` | PASS | exact head `b1c6cec3e12d99b75ac708ec88ee12c3741940c8`，exit 0，读回 1.15.0 与上述 digest；已审正文/bundle 字节未变 |
| 真实 `GitRepository.scope()` + `verify_history()` | PASS | `6550228fc2c239f860bcd923638687f43648ee10` 与 `b1c6cec3e12d99b75ac708ec88ee12c3741940c8` 均实际运行；已提交 scope 含八个合法路径，已变路径均在 scope，线性本地历史通过；当时审议索引尚待归档。纯本地验证，没有远端 tip 锚，不能代替 broker push 的授权/FF 检查 |
| broker Issue 判级与生命周期 | PASS | #425 `approved`；`classify --verify 425` 真实读回 `projected`，`type/platform` + `complexity/complex`；没有提前创建 PR |
| 六场景文本审议 | PASS | R1 逐项独立审议，R2 沿用；R3 Fable 5 / high 再逐项独立审议并全部支持，对应关系见下表，未做真实模型实验 |

完整 smoke 的实跑 head 如上；其后只有 proposal 表示格式与归档文档变化，定向重跑全分支空白、patch、文档及 bundle 检查，不把旧 head 的 full smoke 冒充最终归档 head 实跑。

## Acceptance criteria 结果

| AC | Result | Evidence |
|---|---|---|
| AC-1 | PASS | 批准指纹、原有引言/四部分字节比较、冻结 patch 与来源读回 |
| AC-2 | PASS | R1 正文/机制通过，R2 两轴 PASS；R3 Fable 5 / high 两轴 PASS，无新增发现；无新增流程、门禁或工具要求，03/08、根 Agent 文件、技能入口均未改 |
| AC-3 | PASS | 1.15.0 仅追加历史，成员集合不变；三端隔离导出与源码同字节；无真实 HOME 安装或项目 adopt |
| AC-4 | PASS | 完整 smoke、定向校验、真实 scope/history 与六场景文本判断；不宣称模型效果/UAT |
| AC-5 | PASS | T01 独立 commit 后停止，fresh Claude Code R1/R2 审议及负责人指定 Fable 5 / high 的 R3 独立审议；本次只交付 source/local 候选，停在最终 PR 确认前 |

| 场景 | 文本判断 |
|---|---|
| 偏好与项目规范 | 新节第 1 条区分真实缺陷与个人偏好，同时要求遵守既有项目标准 |
| 多个 AI 一致 | 第 2 条要求触发条件、影响和证据；模型一致不能替代证据及人的责任 |
| 小改动高影响 | 第 3 条按潜在损害、影响范围与可逆性判断，拒绝仅按行数免审 |
| 复审与新证据 | 第 4 条聚焦修复及影响，不重复旧问题；不能为收敛忽略新的可靠证据 |
| 同类问题超出范围 | 第 4 条限于本次涉及的问题，范围外另行记录，既有完整修复原则仍适用 |
| 遗漏与误报 | 第 5 条按既有合同考虑更早验证，兼顾缺陷后果与人的处理成本 |

拒绝新增统一门禁或固定仪式的约束来自保留的引言及既有必需验证条文；它们管辖全文。新节应连同全文理解，不能抽掉前提后推断获得流程变更权限。

## 来源核验与实施前审议

- 核验者 Codex 于 2026-10-22 使用 `web.open` 直接读取 [用户给定文章](https://claude.dev/blog/solving-code-review-at-anthropic/)，返回 URL 与给定 URL 一致；标题 *How the Claude Code team does code review*，作者 Addy Osmani、Morgan Westlee Lunt、Qing Wang，页面 PUBLISHED 为 Oct 15, 2026。链接 slug 与显示标题不同，不构成错误。R2 的 Claude 没有访问网络，页面事实来自实现方读回。
- 实施前真实 Claude Code `2.1.228` / `claude-opus-5[1m]` 首轮 session `af145fb3-e671-4928-9d10-be38b34c2f62`，原始文件 `/private/tmp/aisoft-code-review-261022-xLBylI/claude-principles-review.json`：要求收紧同类问题范围与复审边界、核验来源，建议明确按既有合同转化验证。
- 以上要求已落实，定稿 session `64febeec-2d8b-4d17-8e36-7b944ee46afe`，原始文件 `/private/tmp/aisoft-code-review-261022-xLBylI/claude-principles-final.json`，结论 `VERDICT: ACCEPT`。原文确认两项必改均满足、建议已采纳、无新增必改项，文案可定稿。
- 实施前讨论没有 git head，因候选尚在临时文件中；以本记录的全文 SHA-256 绑定最终批准稿，之后 T01 实际字节核对一致。这些讨论不替代下列 exact-head 审查。

## 交叉审查

实现方 Codex；R1/R2 的另一提供者为本机真实 Claude Code `2.1.228`，未参与实现，实际主模型 `claude-opus-5[1m]`。R1 使用 fresh `--safe-mode --permission-mode plan`，仅 Read/Grep/Glob，禁用 skills/Chrome/MCP/会话持久化；R2 fresh、所有工具关闭，仅对所给原文与 R1 争议作限定复议。R1/R2 没有模型覆盖，没有 shell 或写入能力。
R1 独立读取合同、正文、入口、bundle 及相关校验源码；R2 不重新读取 repo/bundle/git，不重开 R1 已通过项。两轮均未独立运行测试或访问网络；执行证据由 Codex 实测，不能称为 Claude 复现。

负责人随后指定“claude code 进行评议的模型应该选择 Fable 5 high”。R3 为全新 Claude Code `2.1.308` 只读进程，显式 `--model claude-fable-5 --effort high`，并在该进程设置 `CLAUDE_CODE_EFFORT_LEVEL=high`；不改全局配置。命令、版本、输入指纹与 exit 0 记录于 `425-r3-fable-invocation.json`。流式 `system/init.model` 及全部 assistant 消息的实际模型均为 `claude-fable-5`；流中没有独立的 effort 字段，high 的依据是明确调用参数与同值进程环境，不以模型自述作为执行证明。平台路由 `route.effort: max` 保持原合同，审议调用参数独立记录。
R3 仅开放 Read/Grep/Glob，实际使用工具也只有这三种；重读相关合同、正文、入口、bundle 与证据，重新判断六场景并复核 F1–F3。R3 没有运行命令、读取 Git 对象或访问网络，测试/指纹/提交历史证据仍由 Codex 实测，不代表 Fable 复现。

| 轮次 | 实现方 | 审查方 | exact head | 结论 | 发现与处置 |
|---|---|---|---|---|---|
| R1 Standards + Spec | Codex | Claude Code，fresh，只读 | `6550228fc2c239f860bcd923638687f43648ee10` | Standards PASS；Spec FAIL | F1 导航摘要缺新增项，判 P2 阻断；F2/F3 为非阻断归档建议；session `e4351c19-9c6f-4624-a7b9-bdc7311c65a1` |
| R2 限定复议 | Codex | Claude Code，fresh，文本只读 | `6550228fc2c239f860bcd923638687f43648ee10` | Standards PASS；Spec PASS；总体 `VERDICT: PASS` | F1 的排除/矛盾/索引失效判定撤回，降为 P3 可改善项；F2/F3 证据补齐，要求本次归档；session `2bc99890-f442-4e82-bef1-d6b079a9bdef` |
| R3 用户指定模型复审 | Codex | Claude Code 2.1.308，Fable 5 / high，fresh，只读 | `cfc13a64cefe1b82864a1fb75729f8d362c65ebf` | Standards PASS；Spec PASS；`VERDICT: PASS` | F1 维持非阻断处置，F2/F3 已结清；六场景全部支持；新发现无；session `e0123a90-e370-4314-bfb3-78dec952b7c2` |

原始结果：`/private/tmp/aisoft-code-review-261022-xLBylI/425-claude-review.json` 与 `425-claude-r2.json`，同目录有 Markdown 正文及输入。R3 同目录原始流为 `425-r3-fable.stream.jsonl`，结果为 `425-r3-fable-result.json` / `425-r3-fable.md`，调用 receipt 为 `425-r3-fable-invocation.json`，实际模型核对为 `425-r3-fable-meta.json`；原始流 SHA-256 `19523aab6ae3b754b1514343d6da6297d4a7dc4145613b77a7c2df5f369bd226`。下面保留完整处置含义，不依赖临时文件才能理解。

| 编号 | R1 发现 | 复议证据与处置 |
|---|---|---|
| F1 | 08 与 usage §7 未列新增审查思想，被视为索引失效 | 08 的“四项”限定 Karpathy 来源，“正文只有一份”指副本而非思想来源；08/§7 均明确适用于审查，没有排他表述。三个技能引导读完整 reference，摘要不参与路由或章节过滤，新正文已正确分发。R2 撤回阻断、认可源码保持且无需扩范围；概括更全面的建议记为后续候选，本批不修改这两份文件，也未新建后续 Issue |
| F2 | 文章出处缺可核验记录 | 本节已落访问方式/日期、URL、标题、作者、发布日期；Claude 只核内部一致性，不冒充亲自浏览。页面未来可能变化，届时按既有合同维护引用，本轮无来源错误证据 |
| F3 | 实施前 ACCEPT 缺出处 | 本节已落两轮 session、版本/模型、原始文件、结论、无 git head 原因与全文指纹绑定；已结清 |

Codex 同意 R2 的事实判断与处置。R3 Fable 5 / high 独立确认：正文仍为纲领性指导、八路径 scope 与候选一致、版本历史仅追加；F1 没有排他或索引失效证据，维持非阻断建议，F2/F3 的记录已结清；新发现（F4 起）无。Codex 核对其依据与现有原文/执行证据相符，同意 R3 结论，以 R3 作为当前审议依据；一致来自证据，不以模型数量决定正确性。

## 遗留风险与未完成项

R3 无阻断缺陷及新增发现；F1 的导航概括完善只保留建议，不自动扩本批范围。2026-10-23 负责人明确确认提交 #425 的唯一最终 PR、CI 全绿后停在待人工合并，确认点 2 已通过。发布前 fresh fetch 的 main 仍为本记录基线，完整 PR 列表未发现同分支 PR；live protection 的 required context 为 `CI / verify (pull_request)`。
本表保留 source/local 的真实证据。PR 地址以 summary 的 `pr_url` 为准；每次推送均核对 `pushed_head`，最终 required CI 以该 PR 的当前 exact head 和 Actions/status 读回独立留证于 PR/Issue，不以本地 PASS 替代。全绿后停在 `READY_FOR_REVIEW`。全局安装、真实 provider-session 效果、项目采用、合并与部署均 NOT RUN，发布授权不传递这些权限。
