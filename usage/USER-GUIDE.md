# AISoft 平台 · 新用户使用手册

这一页讲清楚用平台开发一个新项目要准备什么、怎么开始。详细步骤不用记：打开你的 AI 工具，说一句
「带我上手 AISoft 平台」，它会按 [上手指南](../skills/aisoft-platform/references/getting-started.md) 一步一步带你走、每步帮你核对。

## 平台替你管什么

- **一张 Issue 一件事**：需求、缺陷、变更都先开 Issue，AI 按证据判级（small 或 complex），并给出路由卡：用什么档位的模型、走什么方法、怎么验证。
- **你只确认两次**：AI 写好合同后你回「确认」它才开工；本地验证做完后你回「开」它才提 PR。中间的实现、测试、修 CI 由 AI 自己完成。
- **合并只由人做**：PR 由你审核后合并。合并不等于部署，部署另行授权。
- **远端访问走 broker**：AI 不拿你的 token，一切 Gitea 与 Git 写操作都经本机安装的 host-access broker。

## 三种工具各要准备什么

| | Claude Code | Codex | Cursor |
|---|---|---|---|
| 登录 | 运行 `claude` 按提示登录 | 运行 `codex` 按提示登录 | 运行 `cursor-agent login` |
| 平台技能 | 项目里的 `.claude/skills/` | 项目里的 `.agents/skills/` | 项目里的 `.cursor/skills/` 与 `.cursor/rules/` |
| superpowers | Claude 官方市场安装 | Codex 官方市场安装 | 已随项目提供 |
| Matt 技能包 | 从平台 marketplace 安装插件 | 已随项目提供 | 已随项目提供 |

平台技能随项目一起来，不用往自己电脑的用户目录里装。

## 维护者要先做的三件事

这些需要管理员权限或改平台配置，如果你不是维护者，请找维护者完成：

1. 在你的 Mac 上安装 host-access broker。
2. 把新项目登记进平台（Gitea 仓库、project agent、required CI）。
3. 把平台使用发布包采用进项目，并选上你用的工具。

完成的标志：维护者告诉你接入验收已通过；之后你在项目目录里运行 `.aisoft/bin/aisoft project-check` 没有 `GAP:` 行，并让 AI 帮你读回一次外部技能包版本。

## 新项目先规划

完成登记与发布包采用后，如果项目还没有可维护实现，先显式启动 Matt `grill-me`，从已有想法或需求材料整理项目简报、
路线图和当前阶段。已有回答直接沿用：**当前阶段详细，下一阶段有轮廓，远期保留方向**。

| 所用工具 | 在项目会话中显式启动 |
|---|---|
| Claude Code | 指定插件技能：`请使用 mattpocock-skills:grill-me，按平台滚动阶段规划方法梳理这个新项目。` |
| Codex | 输入：`$grill-me 按平台滚动阶段规划方法梳理这个新项目，沿用已有材料。` |
| Cursor | 指定项目技能：`请使用项目 .cursor/skills/grill-me/SKILL.md，按平台滚动阶段规划方法梳理这个新项目。` |

规划入口登记在项目 AGENTS 的「项目规则」，建议为 `docs/planning/README.md`；小项目可把三份资料合成一个文件。
资料由规划 Issue 写入，多 Issue 阶段的实现会话只链接它；只有一张 Issue 时由该 Issue 兼任。
详细方法与最小模板见 [滚动阶段规划](../skills/aisoft-platform/references/greenfield-planning.md)。已有代码继续走项目对齐或增量 Issue。
尚未登记与采用时先整理本地笔记，再完成接入；规划资料不代替每张 Issue 的合同与两次确认。

## 第一张 Issue 怎么走

1. 把需求写成 Issue，写清怎么算做完。
2. 让 AI 判级（`$triage #N`），看它给的路由卡。
3. AI 给出合同，你回「确认」。
4. AI 实现、测试；做完给你一份 PR 候选，你回「开」。
5. 你审核并合并 PR。

之后每张 Issue 都是这五步。

## 想深入时读什么

- 项目里的 `.aisoft/platform-usage.md`：平台使用合同，流程规则以它为准。
- 平台仓 `03` 分册：Issue、判级、两个确认点与最终 PR 的完整规则。
- 平台仓 `08` 分册 §7.3：路由卡档位对应各工具的哪个模型。
