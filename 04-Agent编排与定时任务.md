# 04 · AI 自动分析与 Development Loop 编排

> v3 目标契约（2026-07-14）。当前 VM 只有自动分析与停用的 one-shot 实现脚本；本册定义待实现的 provider-neutral Loop，不把规划写成已上线能力。

## 1. 设计原则

- Analyzer 与 Development Loop 分离。
- `needs-analysis` 触发分析，`approved` 触发 Loop。
- Issue/spec/plan 是不可由 Loop 擅自改写的执行合同。
- 外层 controller 管状态、锁、Git/Gitea、验证和终态；模型只做范围内分析与修改。
- Codex 与 Claude Code 只作为 provider adapter，共用同一 controller 和 verifier。
- 只有人可以合并最终 PR。
- 生产部署不由 analyzer、Loop 或 provider 执行。

## 2. 当前运行基线

| 组件 | 当前状态 | v3 处理 |
|---|---|---|
| `provider-poll.sh` | 已安装，默认 Claude analysis / implementation none | 暂不修改，Codex 验证阶段另行设计 controller |
| Claude `analyze.sh` | 可按 `needs-analysis` 运行 | 后续改为 `change/N` 和结构化 AI 判级 |
| `analyze-codex.sh` | 已落库，尚未真实 Issue 冒烟 | 后续随 Codex controller 实施修改 |
| Claude/Codex one-shot implement | 保留但停用 | 不直接恢复；由 Loop 取代 |
| systemd timer | 15 分钟单 poller | 文档阶段不改 |

> **兼容性暂停（Issue #8）**：当前 VM wrapper 仍是 v2；`analyze-codex.sh` 仍校验 `spec/N` 和旧 summary 标题，尚不理解本册的 v3 字段与标签路由。Issue #8 的 runtime wrapper/controller 修改通过自动化测试和真实验证前，不得运行 `codex/install-vm.sh` 覆盖当前 VM 安装，也不得把以下目标合同写成已上线。

## 3. 目标组件

```text
provider-poll / controlled trigger
  → loop-controller
      ├── contract loader
      ├── worktree + issue lock
      ├── Codex adapter（先验证）
      ├── Claude adapter（Codex 验证后）
      ├── deterministic verifier
      ├── Gitea Issue/PR/CI adapter
      └── local state store
```

第一版只允许一个 active Issue，使用独立 worktree，避免并发写同一工作树。不得为 Claude 和 Codex 各复制一套状态机。

## 4. Analyzer

Analyzer：

1. 读取 Issue、`AGENTS.md`、仓库和相关测试。
2. 只读分析产品代码，识别主要 type、产品合同影响、风险和有效复杂度，输出固定结构；模型不得直接修改 Issue 标签。
3. 外层 wrapper 校验结构化输出，在 `change/N` 写 `00-summary.md`、提交、推送和评论，并独占所有标签 mutation。
4. 不实现代码、不创建最终 PR、不启动部署。

所有 Issue 都经过 analyzer；是否需要 spec/plan 由有效复杂度决定。Analyzer 至少输出：

```yaml
change_type: bugfix # bugfix | feature | docs | test | refactor | maintenance | platform
requested_complexity: auto # auto | small | complex
assessed_complexity: small # small | complex | needs-human-decision
effective_complexity: small # small | complex；needs-human-decision 时省略
contract_effect: restore # restore | unchanged | add | change | unclear
reason: 恢复已经明确的既有行为
risk_flags: []
required_docs:
  - 00-summary.md
confidence: high # high | medium | low
override_reason:
```

Wrapper 必须按强制风险规则和显式标签优先级复核结果，再执行互斥标签变更：

- 明确 small：只保留一个 `type/*` 和 `complexity/small`；合同完整时写入 `approved`，否则进入 `awaiting-triage`。
- 明确 complex：只保留一个 `type/*` 和 `complexity/complex`，进入 `spec-drafting`；spec/plan 合同完整后才可写入 `approved`。
- `assessed_complexity: needs-human-decision`、`contract_effect: unclear`、低置信度冲突或风险边界不明：移除两个 complexity 标签，保持 `awaiting-triage`。
- Issue 显式要求 `complexity/complex` 时不得降级；显式 `complexity/small` 触发强制复杂规则时必须覆盖为 complex，并在 summary 和 Issue 评论记录 `override_reason`。

## 5. Loop 启动条件

每次收到启动信号时，controller 都必须从 Issue、有效评论、summary 和所需 spec/plan 重新计算合同有效性，不能把现有 `approved` 当作充分证据。启动前必须满足：

- Issue 为 open 且带 `approved`。
- `change/N` 和 `00-summary.md` 存在。
- 恰有一个由当前证据支持的 `complexity/small` 或 `complexity/complex` 标签，且 type、复杂度和强制风险规则无冲突。
- `complexity/small` 时 Issue 有可测验收标准，summary 字段完整，且没有强制复杂风险。
- `complexity/complex` 时 `01-spec.md` 和 `02-plan.md` 完整、验收映射明确且无未决问题。
- 没有另一个 active Issue 占用第一版 controller。

任一条件不满足时 controller 必须拒绝启动、由 wrapper 修正到 `awaiting-triage` 或 `spec-drafting`，并输出 `NEEDS_HUMAN_DECISION` 或 `BLOCKED_EXTERNAL`；不得猜测合同，也不得因 `approved` 已存在而跳过复核。

## 6. 每轮执行

```text
加载合同和持久化状态
  → 选择下一个未完成 plan task
  → provider 在隔离 worktree 实现最小改动
  → verifier 独立运行要求的命令
  → 通过：记录进度并进入下一项
  → 失败：归因并把真实输出反馈给下一轮
  → 判断完成、继续或升级
```

普通 lint、类型、测试、构建和范围内 review 失败不能立即转人工。禁止通过删除测试、弱化断言、隐藏错误或改验收标准制造假绿。

## 7. Verifier

按项目和合同选择：format/lint/typecheck、目标单测、集成测试、迁移验证、完整测试、构建、浏览器/API acceptance、diff review 和 PR CI。

Verifier 必须由外层脚本独立运行，不信任模型自述。每条 acceptance criterion 至少映射一个真实验证命令或人工最终 review 项。

## 8. 重试和升级

- 同一根因最多连续尝试三次。
- 时间、token、总轮数在 controller 专项设计中配置。
- 需求冲突、范围扩张、破坏性迁移、安全/权限决策、缺凭据/外部服务、验证不可靠或预算耗尽时停止。
- 升级输出必须包含：已完成、失败验证、根因、已尝试、需要人决定的问题和选项影响。

## 9. 终态

| 终态 | 条件 |
|---|---|
| `READY_FOR_REVIEW` | 合同满足，本地 verifier 和 PR CI 通过，最终 PR 等待人合并 |
| `NEEDS_HUMAN_DECISION` | 需要需求、架构、安全、范围或破坏性操作决定 |
| `BLOCKED_EXTERNAL` | 缺凭据、服务、网络或外部协调 |
| `FAILED_LIMIT` | 达到重试、时间、token 或总轮数限制 |

只有 `READY_FOR_REVIEW` 可以通知人进行最终 review；任何终态都不授权自动合并。

## 10. Codex-first 验证顺序

1. 静态验证 skills、metadata、sandbox 和禁止参数。
2. 合成 Issue 验证合同读取与终态。
3. 真实 small Issue 验证自修复到 PR。
4. 真实 complex Issue 验证 spec/plan 要求。
5. 验证 CI failure feedback。
6. 验证升级条件和三次同因失败。
7. 在开发/测试环境验证首次部署和回滚。
8. 全部通过后再接 Claude adapter，并用同一矩阵做 parity 验证。

## 11. 安全与回滚

- controller 使用专用 `coder` 用户和最小权限 ci-bot。
- 不打印 `.agent.env`、auth、Git credentials 或应用环境变量。
- 第一阶段保持 `IMPLEMENT_PROVIDER=none`；文档更新不启用 Loop。
- Loop 试点失败时停止 controller，保留 analyzer，开发回到 Mac 人机交互，不影响 CI 和生产部署。
