# 04 · Agent 编排与定时任务

> gitea-ci VM 上 `coder` 用户名下的无人值守 agent。设计底线：**agent 只到「开 PR」为止**——ci-bot 无合并权、分支保护、CI 硬门、人工 review 四重兜底。

## 1. 运行环境（coder 用户）

| 组件 | 位置 / 值 |
|------|-----------|
| Claude Code CLI | `~/.npm-global/bin/claude`（v2.1.197，经 Verdaccio 安装） |
| superpowers 插件 | v6.1.1（brainstorm→spec→plan 工作流，交互会话用） |
| 工作克隆 | `~/work/rsdesign-new`（依赖已预热、测试库已迁移） |
| 环境文件 | `~/.agent.env`（600）：GITEA_URL/OWNER/REPO、GITEA_TOKEN（ci-bot PAT）、`CLAUDE_CODE_OAUTH_TOKEN`（订阅 token，一年期）、`CLAUDE_MODEL=sonnet`、PATH、PRISMA_ENGINES_MIRROR |
| git 身份 | ci-bot（credential store 存 ci-bot PAT，host 用 gitea-ci.orb.local:3000） |
| systemd | 用户级 `agent-poll.timer`（15 分钟，oneshot 防重叠执行）；`loginctl enable-linger coder` 已开 |

认证说明：订阅 OAuth token 对 **headless `claude -p` 完全有效**；交互模式首启要浏览器验证（这是把交互环节挪回 Mac 的原因之一）。换 token：重跑 `claude setup-token` 后更新 `.agent.env`。

## 2. 五个脚本（`~/agent/`）

| 脚本 | 触发 | 职责 | 状态 |
|------|------|------|------|
| `poll.sh` | timer 每 15min | 扫标签分发：`needs-analysis`→analyze；`approved`→implement | **implement 行已注释停用** |
| `analyze.sh <N>` | poll | 只读分析（`--allowedTools Read,Glob,Grep`）→ `docs/changes/N/00-summary.md` 推 `spec/N` → 🤖 评论 → 换标签 | ✅ 在用 |
| `spec-start.sh <N>` | 人工 | VM 内交互 spec 会话（superpowers 引导） | 备用（推荐在 Mac 做） |
| `spec-pr.sh <N>` | 人工 | 提交 docs → 开 docs-only spec PR（Refs #N）→ `spec-review` | ✅ 在用（Mac 写完文档后由会话代跑） |
| `implement.sh <N>` | poll（停用） | 读 main 上 spec/plan → bypassPermissions 实现 → **脚本独立跑 `npm test` 硬门** → 推 `change/N` → code PR（Closes #N） | 待命 |

安全要点（implement 的护栏，启用时生效）：
- 失败即评论转人工并**撤掉 approved 标签**，不会无限重试；
- 测试硬门在脚本里独立执行，不信任 agent 自述；
- prompt 强制「最小改动、schema 走迁移、不碰 .gitea/scripts/部署文件」（与 AGENTS.md 双保险）。

## 3. 恢复无人值守实现 / 换 Codex

```bash
# 恢复 Claude 版:去掉 poll.sh 中 approved 行的注释即可
# 换 Codex(2.6 Part H 接缝):implement.sh 中标注的一段,把 claude -p ... 换成:
codex exec "按 docs/changes/$N/01-spec.md 和 02-plan.md 实现 issue #$N,遵循 AGENTS.md,改动带测试,完成后 npm test。"
# 其余(分支、测试硬门、开 PR、换标签)完全复用——spec/plan 是 agent 无关的意图接口
```

## 4. 与仓库规范的关系

- agent 读仓库根 `AGENTS.md`（`CLAUDE.md` 仅一行 `@AGENTS.md` 导入，单一来源），内含：命令、硬性规范（带测试、迁移向后兼容、最小改动、禁碰部署文件）、分支/提交约定。
- 改 agent 行为的优先级：先改 `AGENTS.md`（对所有 agent 生效），再改脚本 prompt（只对该环节生效）。

## 5. 定时任务运维

```bash
# 状态 / 日志(coder 身份)
orb -m gitea-ci sudo -u coder bash -c 'XDG_RUNTIME_DIR=/run/user/$(id -u) systemctl --user list-timers | grep agent'
orb -m gitea-ci bash -c 'sudo journalctl _UID=$(id -u coder) --since "2h ago" | tail -30'
# 手动触发一轮
orb -m gitea-ci sudo -u coder bash -c 'source ~/.agent.env && ~/agent/poll.sh'
# 暂停/恢复
... systemctl --user stop agent-poll.timer / start agent-poll.timer
```

成本：poller 空转**不消耗** token（纯 curl）；只有带触发标签的 issue 才调用模型（sonnet，一次分析约几毛钱级）。

## 6. 已知边界

- VM 随 Mac 睡眠而停 → 轮询暂停，唤醒后 timer 自动补跑；「真常驻」等内网平移。
- 新 issue 需手动打 `needs-analysis` 才进入流水线（「免标签自动分析」在待办清单）。
- `sudo -u coder` + 通配符操作注意 🕳️ #12（glob 在调用方 shell 展开）——运维手册详述。
