# 04 · Matt 编排与自动化迁出说明

> 现行合同（#391，[ADR 0002](docs/adr/0002-deterministic-development-flow.md)）。VM 上的 Development Loop（analyzer 轮询、controller、provider adapter、verifier、state）与 routine 自动合并已退出平台 `main`；每条 Issue 由 Mac 上的交互会话（或协调者派单的线程）按两个确认点做到唯一最终 PR，人合并。删除清单、最后所在 commit 与重建形状见 [迁出说明](archive/automation-engine-exit-261020.md)；本分册旧版正文在该 commit 的 Git 历史里。

## 1. 设计原则

- Matt `triage → to-spec → to-tickets → implement` 保持原始技能语义，通过 Gitea tracker adapter 对齐平台阶段。
- Issue、summary 与路由要求的 spec/plan 是会话不可擅自改写的执行合同；`approved` 只授权开始实现。
- 会话按 frontier `Txx` 在 exact `change/N-short-description` 创建本地原子 commit；push、PR 与判级投影走 broker，确认点 2 之前不推送。
- Claude Code 与 Codex 对等，共用同一合同；平台仓 complex 由未参与实现的一方只读交叉审查。
- 最终 PR 只由人合并；生产部署不由任何会话执行。

### 仓库初始化

仓库初始化先完成 AISoftPlatform onboarding，并用 `$aisoft-matt-workflow` 校验 Issue、权限、受保护 `main`、required CI、文档和部署边界；随后调用 `$setup-matt-pocock-skills`，tracker 选择 `Other`，直接使用 `templates/docs/agents/` 下的 `issue-tracker.md`、`triage-labels.md` 与 `domain.md`，不得另建一套 Gitea 模板。

### Matt v1.3.1 源码适配（#352）

保持上述确定性流程。完整快照中的 `implement-spec` 默认不启用其写入编排；
`pr` 提供 Summary/Evidence/Merge Danger 内容，提交仍在确认点 2 之后经 broker 进行；
`retro` 仅由人明确选择 Matt 来源后运行，输出待审候选，不自动改规则或持续自调用。
新项目采用 [GLOSSARY.md](GLOSSARY.md)；旧 CONTEXT 文档按 [domain 合同](docs/agents/domain.md) 保留业务规则与引用。
每个 ticket 按自身 AC 验证，全部完成后再做整个 spec 的完整性检查；已有合同决策不重复询问。

## 2. 判级输出

判级由 `$triage` 与平台判级规则（`codex/runtime/aisoft_loop/classification.py` 的强制 complex 规则）完成，结果写进映射 summary 的 front matter 与 `## AI 判级` 块：

```yaml
change_type: bugfix # bugfix | feature | docs | test | refactor | maintenance | platform | security | reliability | data
requested_complexity: auto # auto | small | complex
assessed_complexity: small # small | complex | needs-human-decision
effective_complexity: small # small | complex；needs-human-decision 时省略
contract_effect: restore # restore | unchanged | add | change | unclear
reason: 恢复已经明确的既有行为
risk_flags: []
required_docs:
  - summary
document_slug: restore-login-flow
confidence: high # high | medium | low
override_reason:
```

会话（或任何判级工具）必须按强制风险规则和显式标签优先级复核结果，再执行互斥标签变更：

- 明确 small：只保留一个 `type/*` 和 `complexity/small`；合同完整时写入 `approved`，否则进入 `awaiting-triage`。
- 明确 complex：只保留一个 `type/*` 和 `complexity/complex`；production 进入 `spec-drafting`，
  spec/plan 合同完整后才可写入 `approved`；development 由 Issue 正文提供可测验收标准，
  不生成 spec/plan，合同完整后可写入 `approved`。
- `assessed_complexity: needs-human-decision`、`contract_effect: unclear`、低置信度冲突或风险边界不明：移除两个 complexity 标签，保持 `awaiting-triage`。
- Issue 显式要求 `complexity/complex` 时不得降级；显式 `complexity/small` 触发强制复杂规则时必须覆盖为 complex，并在 summary 和 Issue 评论记录 `override_reason`。

判级投影由 `codex/tools/apply-classification-labels.sh` 从 summary 读取并经 broker 写入，合并前读回 `projected`（见 `03`）。

## 3. 迁出的自动化引擎

| 原组件 | 状态 | 去向 |
|---|---|---|
| analyzer 轮询（VM 定时器 + analyzer 脚本） | 已删除（#391） | 判级在会话里完成；阶段 2 可在 Mac 上用只读 `codex exec` / `claude -p` 跑候选（ADR 0002 D3） |
| Loop controller、provider adapter、verifier、state | 已删除（#391） | 会话按两个确认点执行；重建只在 Mac 上，产出止于 PR 候选 |
| routine 自动合并 | 已删除（#391） | 合并永远是人（ADR 0002 D4） |
| VM profile 与 `install-vm` 安装面 | 已删除（#391） | VM 只保留 broker 安装面；旧单元与状态由负责人清理 |

无人值守的实现（阶段 3）只有满足 ADR 0002「重开条件」三条后才可以开 Issue 讨论，且只对 `small-direct` 开放。
