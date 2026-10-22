---
issue: 420
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/420
change_type: docs
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
depends_on: []
status: pending
branch: change/420-onboarding-guide
created: 2026-10-22
updated: 2026-10-22
---

# 验证记录

## 基线与范围

- Commit SHA: 见下表各轮 exact head；最终候选 head 记在确认点 2 候选里
- 基线：`origin/main` = `c373f407ffc7a699be9495ce1be7b1adf995c370`
- 环境: Mac 本机，平台 change worktree `issue-420-onboarding-guide`；Claude Code 2.1.228、codex-cli 0.161.0、cursor-agent 2026.10.19
- 本记录负责证明的 acceptance criteria: AC-1 至 AC-6

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| 指南与手册引用的 15 个脚本、配置与文档路径逐个 `test -e` | PASS | 全部 `OK`，含 `codex/install-host-access-broker.sh`、`skill-for-claude/check-plugin-pin.sh`、`codex/tools/usage-bundle.sh` 等 |
| broker 操作名 `git.fetch.main`、`gitea.issue.create`、`host.onboarding.check` 在 manifest 或 contract 中存在 | PASS | `rg` 命中 `codex/config/host-access-broker.json` 与 `contract.py:282` |
| `aisoft` 用法输出含 `version`、`bundle status`、`project-check`、`change-name`、`claim-worktree`、`classify`、`open-pr`、`complete` | PASS | `codex/tools/aisoft` 无参数用法列表 |
| 指南引用的错误文本 `requested project is not explicitly managed`、`requested operation is not allowlisted`、`REQUEST_DENIED`、`TRANSPORT_ERROR` | PASS | 分别命中 `contract.py`、`contract.py:154`、`broker.py` |
| 登录核对命令 `claude auth status`、`codex login status`、`cursor-agent status` 在本机可运行 | PASS | 分别读到 `"loggedIn": true`、`Logged in using ChatGPT`、`Logged in as …` |
| 插件名 `superpowers@claude-plugins-official`、`mattpocock-skills@aisoft-platform` | PASS | 本机 Claude 已装插件记录中存在；marketplace 名取自 `.claude-plugin/marketplace.json` |
| `bash codex/tools/check-external-skill-versions.sh` | PASS | `RESULT PASS`；Codex superpowers `PIN_NOT_INSTALLED` 属 `KNOWN_EXTERNAL` |
| `bash codex/tools/usage-bundle.sh --verify --baseline-ref origin/main` | PASS | `VERIFIED 1.13.0` |
| `bash codex/tools/usage-bundle.sh --build <临时目录>` | PASS | `project/.claude/skills/`、`project/.agents/skills/`、`project/.cursor/skills/` 三处 `aisoft-platform/references/getting-started.md` 都在 |
| `bash codex/tests/smoke.sh`（最终修复后） | PASS | `Codex platform static smoke checks passed.`，exit 0 |
| 反向证明 1：往指南末尾追加站点主机名后跑 `check-project-leak.py` | FAIL（预期） | `getting-started.md: 1 site-value hits (baseline 0)`；`git checkout` 复原后 PASS |
| 反向证明 2：首版指南把平台仓工具路径写在非维护层小节 | FAIL（预期） | smoke 的 `test-aisoft-entry` 报 `exported skills name the platform tree outside a 维护层 section`，改为维护层小节后 PASS |
| 反向证明 3：SKILL.md 入口行写了某家工具名 | FAIL（预期） | smoke 报「单一来源技能正文不得出现某一家独有的工具名」，改为中性措辞后 PASS |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | PASS | 三种工具各一节，每步带核对命令与预期；引用逐条核对见上表前六行 |
| AC-2 | PASS | broker 安装、项目登记、发布包采用、平台技能安装在「维护者」或「维护层」小节；marketplace 注册与插件安装标为用户本人执行 |
| AC-3 | PASS | README 导航第一行链到 `usage/USER-GUIDE.md`；手册链到指南；SKILL.md 入口链到指南；相对路径均存在 |
| AC-4 | PASS | smoke 全绿；站点值反向证明变红 |
| AC-5 | PASS | `--verify` 与 `--build` 结果见上表 |
| AC-6 | 见下节 | 交叉审查各轮 |

## 交叉审查

仅平台仓 complex 变更保留本节（`03` §7「交叉审核」）；项目仓整节删除。每轮一行，`exact head` 写 40 位 SHA，
实现方与审查方不能是同一提供者。

| 轮次 | 实现方 | 审查方 | exact head | 结论 | 发现与处置 |
|---|---|---|---|---|---|
| 1 | Claude | Codex（gpt-6-astra，high，read-only） | `b228917818a2d5d831a6dcb08eed87aac941881b` | FAIL | 7 条：接入判据不足、TRANSPORT_ERROR 写操作不可盲重试、REQUEST_DENIED 归因过宽、版本读回不应可跳过、漂移核对未传同一 home、版本号不证明登录、verification 未填。前 6 条在 `6159fb3f` 修复，第 7 条随本记录补齐 |

## 遗留风险与未完成项

合格标准：每条 acceptance criterion 都有一条真实执行过的命令或一次真实观测支撑；
不得把 `NOT RUN` 改写为通过；不可达的环境与未执行项在此显式写明。
