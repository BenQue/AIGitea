---
issue: 158
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/158
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - platform-governance
depends_on: []
status: pr-open
branch: change/158-issue-session-flow
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/159
created: 2026-08-23
updated: 2026-08-23
reason: 新增一份 Claude 侧 Agent 行为契约（会话编排技能）并改造技能安装工具的目标树语义，属 Agent/平台治理类别，强制 complex
required_docs:
  - summary
  - spec
  - plan
override_reason: ''
documents:
  summary: summary-issue-session-flow-260823.md
  spec: spec-issue-session-flow-260823.md
  plan: plan-issue-session-flow-260823.md
---

## 问题/需求总结

平台合同覆盖了 `Issue → triage → spec/plan → 单 PR → 人合并`，但**没有一句话描述会话本身**：
谁开会话、开在哪个项目、一个会话处理几个 Issue、PR 开完后怎么把球交回给人、人合并后谁收尾、
什么时候归档。结果是每次都靠临场记忆重演一遍，且总有环节漏掉。

根因不是记性问题，`03` §11「谁推进 `completed`」已经写明：

> controller 的 lifecycle 写入全在 Development Loop 内，而 Loop 在创建最终 PR 时就结束了，
> 没有任何组件处在能观察到「合并」的位置上。

`codex/tools/mark-completed-issues.sh`（#115）是既有的 merged-phase 执行者，但**没有任何契约规定谁在什么时候跑它**。
换句话说：平台把「合并之后」这一段留给了人，却没给人一份可执行的清单。

现场证据（2026-08-23 本机）：`git worktree list` 中 `issue-130-*`、`issue-139-*`、`issue-152-*`
三个已进入 PR 阶段的 change worktree 全部残留。

## 影响范围

改动集中在 Claude 侧技能源与其安装工具：

1. `skill-for-claude/` —— 目前是**单技能硬编码布局**：`SKILL.md` 直接躺在目录根，
   `install.sh` 把 `~/.claude/skills/aisoft-platform` 这个字面路径当作 exact managed tree 管理。
   新增第二个技能必须先把布局改成 `skill-for-claude/<skill-name>/SKILL.md`，
   `install.sh` 与 `check-drift.sh` 改成遍历。
2. 新增 `skill-for-claude/issue-session-flow/SKILL.md`。
3. `skill-for-claude/aisoft-platform/SKILL.md` 增加一行指向新技能的交叉引用（防止漏触发）。

不改动的：`AGENTS.md`、controller、CI、部署脚本、`skill-for-codex/`（Codex 是 headless VM，
没有会话生命周期这一层）、任何 broker 操作或 manifest。

## 初步方案与建议

技能主干**通用**，不绑定 AISoft：任何项目都适用「一 Issue 一会话 / 需要时开调度会话 /
PR 后停在合并闸门 / 合并后收尾 / 归档」。平台特有的部分（broker typed 操作、
`mark-completed-issues.sh`、`change/N-slug` 元组、`host-access-broker.json` 的 `mac_checkout`）
以**适配层**形式出现：项目接入平台就用平台工具，没接入就用通用等价物。

三个角色：

| 角色 | 开在哪 | 职责 |
|---|---|---|
| 调度会话 | 这批 Issue 的相关项目 | 拆分/派单/跟踪/收口，**不实现任何 Issue** |
| Issue 会话 | 该 Issue 的目标项目 checkout | 一个 Issue 从头到尾，止于 PR，人合并后收尾并归档 |

调度会话只在三种情形下开：大阶段任务需要拆成多个 Issue、一次新生成了多个 Issue、
要处理多个已有 Issue。单个 Issue 直接开 Issue 会话。

派单用 `spawn_task({title, prompt, tldr, cwd})`：它生成**待点击的卡片**而不是直接开会话，
这恰好守住「AI 不擅自扩张工作量」的边界。`cwd` 从 `host-access-broker.json` 的
`projects[].mac_checkout` 查，查不到或为 `null` 就停下来问人，不拼路径。

## 风险

- **合并 ≠ 生效**：技能装在 `~/.claude/skills/`，且技能列表在**会话启动时**加载。
  合并后必须显式跑 `bash skill-for-claude/install.sh`，且只有**新开的会话**才看得到。
  这条限制本身与「一 Issue 一会话」自洽，但必须在交接项里写清楚，否则会误判为「装了没用」。
- **install.sh 的 prune 语义**：它会删掉目标目录下一切不在预期清单内的文件。
  改成多技能遍历时若把「预期清单」算错，会误删用户手工放在 `~/.claude/skills/` 下的其它技能。
  因此目标树必须严格限定为「本仓库声明的技能目录」，而不是整个 `~/.claude/skills/`。
- **两个技能的 description 重叠**：`aisoft-platform` 的触发词已含「Issue → PR 流程」。
  若新技能 description 与之高度重合，模型可能只命中其中一个。缓解手段是交叉引用（AC-2）
  而不是靠措辞去抢触发。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 新增一份 Claude 侧 Agent 行为契约（会话编排技能）并改造技能安装工具的目标树语义，属 Agent/平台治理类别，强制 complex
risk_flags:
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
confidence: high
override_reason: ''
```

### 判级证据

- `AGENTS.md`：「新增功能、功能性更改、……以及 Agent 或平台治理变更一律按 complex 处理」。
  本变更新增的正是一份规定 Agent 如何编排会话的行为契约。
- `contract_effect: add`：此前不存在任何会话生命周期契约，这是新增治理面，不是恢复或
  维持既有产品合同，因此不满足 small 的候选条件。
- `AGENTS.md` 还要求「只有 complex 变更映射的 `spec` 明确授权时，才能修改 …… Agent 行为」——
  本 spec 即该授权，且改动只落在技能**源**上，安装是合并后的独立步骤，
  满足「治理文件先由受控步骤应用并停止，后续 fresh run 重新读取后才实施 runtime」。
- `required_docs` 不含 `verification`：与 #87、#99 两个技能类变更一致。本变更没有应用部署，
  终态应为 `completed`；`mark-completed-issues.sh` 正是据此字段判定，写错会让它跳过本 Issue。

### 缺失的 acceptance criteria 或决策

无。Issue #158 已给出 7 条可测验收标准；技能通用性、调度会话所在项目、收尾清单范围
三个设计决策已由人在会话中明确裁定（通用、开在相关项目、按 7 步收尾）。
