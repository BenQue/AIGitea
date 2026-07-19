# 08 · Codex-first Development Loop 与 Claude Code 共存计划

> 版本：v3.0 通用 Codex runtime candidate ｜ 日期：2026-07-16 ｜ 状态：provider-neutral runtime、72 项 synthetic、每项目 profile 隔离、VM 临时安装和一个真实 complex pilot 已通过；AISoftPlatform 本身不部署，下一阶段为 Claude Code 通用 adapter parity。

## 1. 结论

平台只维护一套确定性外层：

```text
Issue / docs contract
  → provider-neutral Loop controller
      ├── Codex adapter（先实现和验证）
      └── Claude adapter（后接入）
  → deterministic verifier
  → Gitea PR / CI
  → 人工合并
  → artifact / deploy / health / rollback
```

Codex 和 Claude Code 只替换模型执行器，不各自复制标签状态机、Git/Gitea 操作、测试硬门或终态判断。项目差异只存在于显式 profile、仓库内合同与 versioned verifier 配置中；不得从 rsDesign 示例推断默认仓库。

## 2. 共享契约

- Issue 是主键；所有变更有 `00-summary.md`。
- small 可从明确 Issue 直接进入 Loop；complex 必须有 `01-spec.md` 和 `02-plan.md`。
- `approved` 启动 Loop，不授权合并或部署。
- 单一 `change/N` 分支承载文档、代码、测试和最终 PR。
- Loop 只能在合同范围内实现、自测、自修复和处理 CI feedback。
- `READY_FOR_REVIEW` 只是通知人 review；最终 PR 合并是唯一交付硬闸门。
- AI 可以参与非生产首次部署；生产只运行已验证脚本。

## 3. 配置与认证

- 仓库根 `AGENTS.md` 是共享规范源；Claude 用 `CLAUDE.md` 导入，Codex 原生读取。
- `~/.claude/`、`~/.codex/` 和 `~/.agents/skills/` 独立保存，不复制 token。
- provider 使用专用 `coder` 用户和最小权限 ci-bot，不拥有 `main` 合并权。
- 两个 provider 不在同一 working tree 同时写；controller 为每个 Issue 分配隔离 worktree 和锁。
- **⚠️ 上一条同样适用于「同一工具的多个交互式会话」**——规则的判据是 **working tree**，不是 provider。VM 侧由 controller 自动分配 worktree 已覆盖；**交互式路径（人在 Mac 克隆上同时开多个 Claude / Codex 会话，一 issue 一会话）没有任何分配者，是当前唯一裸露面**。共享 checkout 的 **HEAD 是全局可变状态**：A 会话 `git checkout` 会把 B 会话的 HEAD 一起带走，B 随后的 commit 落到 A 的分支上（2026-07-19 SFMDigitalBoard 实证，症状见 06 🕳️ 15）。
  **交互式路径纪律**：并行时非第一个会话必须自建 worktree（`git worktree add .claude/worktrees/<name> <branch>`，全程 `git -C <worktree>`）；任何 commit 前 `git branch --show-current` 必须等于目标分支。
- 生产机不安装或依赖 Claude/Codex 认证。

## 4. 现有 Codex 基础

已完成：

- Codex CLI、ChatGPT device auth、sandbox read-only/workspace-write smoke。
- `AGENTS.md`、VM 全局指导、四个阶段型 skills、复合 `aisoft-platform` skill。
- `provider-poll.sh` 的 Claude/Codex/none 路由和默认 `IMPLEMENT_PROVIDER=none`。
- 静态 smoke 与目标目录安装脚本。
- 五个阶段型 skills 和复合 skill 通过 `quick_validate.py`；Development Loop 普通失败返回 `CONTINUE`，缺 complex 合同并要求直改生产时返回 `NEEDS_HUMAN_DECISION`。

本地 candidate 已完成：

- provider-neutral Loop controller、state store、单 active Issue lock、deterministic verifier 和 Gitea adapter。
- analyzer 从 `spec/N` 迁移到 `change/N`，wrapper 确定性校验 classification 并独占标签 mutation。
- small/complex/unclear、explicit override、范围升级、同因三次、pending/failed CI feedback 和四种终态的 synthetic tests。
- 安装幂等、xtrace/argv token 防泄漏和 Claude implementation parity gate 的 mock 回归。
- `project-poll.sh`、每项目 state/worktree namespace、mode 400/600 profile 校验和禁用式 `aisoft-agent@.service/.timer` 模板。

真实环境已完成：

- 临时 HOME 两次安装清单一致；正式 VM 安装前建立回滚备份，timer 停止且 `IMPLEMENT_PROVIDER=none`。
- Issue #8 one-shot Loop 完成本地 `npm ci`、Prisma generate、unit tests、production build，并创建 PR #9。
- PR #9 CI 通过，controller 返回 `READY_FOR_REVIEW`；controller 未自动合并或部署。之后由人合并，既有应用流水线完成测试部署，两个健康入口返回 `ok`。
- 首次 VM 运行捕获 worktree 命令输出污染，中央提交 `bb0d5d5` 修复并增加 shell 回归后重装、重跑通过。
- 通用 profile candidate 在 VM 一次性 HOME 连续安装两次，结果为 35 files / 7 scripts；未生成 profile 或凭据，`systemd-analyze verify` 通过两个 template。输出中的 Mailpit `nobody` 警告来自既有外部 unit，与候选无关。

Claude adapter 已完成（Issue #1）：

- `claude-provider.sh`、`claude-analyzer.sh`、`analyze-claude.sh` 进入中央 source，`install-vm.sh` 一并安装；`provider-poll.sh` 不再引用未跟踪脚本。
- `cli.py` 按 `IMPLEMENT_PROVIDER` 显式选择 adapter，禁用与未知 provider 一律失败关闭，不静默回退 Codex。
- 17 项 parity 测试覆盖成功、verifier 反馈、CI 反馈、范围扩张、外部阻塞、同根因三次、总轮数上限、token 脱敏与无 merge/deploy，两个 provider 走同一 controller 得到同一终态。
- 两个 provider 的凭据独立：认证只经 `HOME` 生效，环境白名单只透传模型变量，凭据类变量有测试断言不透传。
- adapter 输出规整：Claude 会先输出散文再给 JSON，`claude-analyzer.sh`/`claude-provider.sh` 先经 `extract-json` 取最后一个 JSON 对象再交严格校验器；共享结果校验保持严格不放宽。真实 Claude analyzer 输出已复现验证。

仍未完成：真实 VM 上的 Claude 一次 real Issue pilot；`IMPLEMENT_PROVIDER` 默认仍为 `none`。

> **当前启用边界**：rsdesign-new Issue #8 的安装与 PR/CI 结果只作为一个 pilot evidence。现有 timer 仍 inactive、implementation none。其他仓库必须创建自己的 profile、verifier 和项目验收，不能继承 pilot 的启用结论。AISoftPlatform 没有应用部署目标，不需要为了完成中央 runtime 人为创建部署流水线。

## 5. Codex skills 映射

| Skill | v3 职责 |
|---|---|
| `gitea-analyze-change` | 只读分析 Issue，输出 evidence、风险、contract effect 和结构化 AI 判级字段 |
| `gitea-spec-plan` | 为 complex 变更收敛决策并写 spec/plan；不创建独立 spec PR |
| `gitea-development-loop` | 读取合同，在外层 controller 约束下持续实现、验证、自修复和升级 |
| `gitea-implement-change` | 兼容的一轮实现入口；不得冒充完整 Loop |
| `gitea-platform-ops` | 平台诊断、非生产首次部署、故障复现、脚本修复和回滚规划 |
| `aisoft-platform` | 平台路由、接入和完整安全边界 |

## 6. Loop controller 与 provider adapter

外层 controller 负责：

- 从 Issue、summary 和所需 spec/plan 重新计算合同有效性，不把 `approved` 当作充分证据。
- 调用唯一受控 wrapper 执行互斥的 type、complexity 和流程状态标签 mutation；provider 不得直接改标签。
- 创建/锁定 `change/N` worktree。
- 持久化当前任务、轮数、失败根因和终态。
- 调用 Codex 或 Claude adapter。
- 独立运行 verifier，不信任模型自述。
- 提交/推送 feature branch、创建最终 PR、读取 CI 状态。
- 把 CI 失败和范围内 review feedback 反馈给下一轮。
- 三次同根因失败、合同冲突或预算耗尽时升级给人。

Provider adapter 只负责：读取 controller 给出的合同和失败证据，在 worktree 内完成范围内修改并返回结构化结果。它不管理标签、合并、部署、凭据或生产状态。

## 7. Codex 验证矩阵

共享 runtime 按顺序执行，前一层通过后再进入下一层；随后每个项目 profile 执行自己的接入子集：

1. **Skills 静态验证**：front matter、openai.yaml、触发描述、禁止危险参数。
2. **合成 Issue**：先用下表五类 classifier case 验证判级、互斥标签和路由，再验证缺文档拒绝与四种终态。
3. **真实集成 pilot**：至少一个项目完成 `approved → Loop → tests → PR → READY_FOR_REVIEW`；当前为 rsdesign-new complex Issue #8，不能成为硬编码默认值。
4. **项目 profile 验收**：目标项目分别验证 real small/complex、verifier、CI feedback 和权限；失败不影响其他 profile。
5. **自修复**：故意制造普通测试失败，确认不立即找人。
6. **升级**：合同冲突、缺凭据、三次同因失败和预算上限。
7. **CI feedback**：本地通过、CI 失败、修复、重新提交。
8. **非生产首次部署（仅应用项目）**：两次正常执行和一次故意失败回滚；文档/source 仓库标记 not applicable。
9. **生产负向边界**：Codex 无权部署生产，只能准备经非生产验证的修复 PR。

验证结果写入对应 `docs/changes/N/03-verification.md`，真实命令与未通过项分开记录。

合成 classifier case 必须覆盖：

| Case | Issue 输入 | 预期结构化结果 | Wrapper 最终路由 |
|---|---|---|---|
| bugfix/small | 恢复已经明确的既有行为，无强制风险 | `contract_effect: restore`、`assessed_complexity: small`、`effective_complexity: small` | `type/bugfix + complexity/small`；合同完整时 `approved` |
| feature/complex | 新增产品功能，即使代码改动很少 | `contract_effect: add`、`assessed_complexity: complex`、`effective_complexity: complex` | `type/feature + complexity/complex + spec-drafting` |
| explicit-small override | Issue 请求 `complexity/small`，但内容是功能性更改或命中其他强制风险 | `requested_complexity: small`、`assessed_complexity: complex`、`effective_complexity: complex`，并记录 `override_reason` | 覆盖错误请求，写 `complexity/complex + spec-drafting` |
| explicit-complex preservation | Issue 明确请求 `complexity/complex`，即使内容原本是 small 候选 | `requested_complexity: complex`、`effective_complexity: complex` | 保留 `complexity/complex`，不得自动降级 |
| unclear/awaiting-triage | 信息不足、内容冲突或风险边界不明 | `contract_effect: unclear`、`assessed_complexity: needs-human-decision`，省略 `effective_complexity` | `awaiting-triage`，不保留任何 complexity 标签 |

这些是 Issue #8 runtime 实现前必须新增并先看到失败的 classifier 合同测试；本次文档更新不代表 VM wrapper 已支持这些 case。

## 8. Claude Code 接入条件

只有共享 Codex runtime、profile 隔离和至少一个 real integration pilot 完成后才更新 Claude Code 运行路径：

1. 盘点 VM 真实 `analyze.sh`、`implement.sh`、`poll.sh` 和 Superpowers 配置。
2. 实现 Claude adapter，复用同一 controller、verifier、状态和终态。
3. 更新 Claude skills/commands，但不复制 Codex skill 内容形成第二套合同。
4. 使用 Codex 的同一组合成用例和通用 project-profile fixture 做 parity；rsDesign 数据、端口和部署脚本不进入 adapter。
5. 两个 provider 都通过后再决定长期默认值和降级策略。

## 9. 部署边界

Codex/Claude 可以在开发/测试环境协助设计和执行首次部署，把成功操作固化为 workflow 和脚本，并验证重复执行、失败停止和回滚。

生产环境只接收不可变制品并运行固定脚本。生产失败后先由脚本停止/回滚；AI 读取脱敏证据，在非生产环境复现、修复、验证并准备 PR。不得让模型在生产机临场生成或执行命令。

## 10. 回滚

- 在 Loop 验证完成前保持 `IMPLEMENT_PROVIDER=none`。
- 试点失败时停止新 controller，保留 analyzer，回到 Mac 人机交互开发。
- Codex 不可用时不自动切换 Claude 执行同一 active Issue；先结束或转移状态，再显式选择 provider。
- 不删除现有 Claude/Codex 认证、旧脚本或 skills，直到两个 provider 完成 parity 验证并另行批准清理。
- CI、制品和生产部署不依赖 Loop，因此 Loop 回滚不影响交付平台。
