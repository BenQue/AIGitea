---
issue: 451
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/451
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
status: pending
branch: change/451-coordination-workspace
created: 2026-11-16
updated: 2026-11-16
---

# Verification：跨项目协调工作区的平台最小适配

## 基线与范围

- Commit SHA：尚无实现提交。合同准备阶段的候选只存在于冻结补丁。
- 基线：`origin/main` = `c14a86d4ad0d1fd5938ab31343f8d72acd486a71`（2026-11-16 broker `git.fetch.main` 返回 PASS 后读取）。
- 环境：Mac 平台检出 `/Users/benque/MyDocs/AISoftPlatform`；change worktree `/private/tmp/issue-451-coordination-workspace`。
- 本记录负责证明的 acceptance criteria：AC-1 至 AC-8。当前全部未执行。

## 准备阶段记录（不是实施验收）

| 检查 | 结果 | 证据 |
|---|---|---|
| #451 最新状态读回 | 已读 | 2026-11-16 23:26（北京时间）broker `gitea.issue.read --number 451`：open，标签仅 `needs-analysis`，comments 0，`updated_at` 2026-11-15T17:45:15+08:00 |
| 既有分支、worktree 与 owner | 无 | `git worktree list` 与 `git branch -a` 没有 #451 条目；本会话 `claim-worktree` 返回 `result: created` |
| 方案与审核材料 | 已读 | 方案 v2.1 SHA-256 `5f306c6a6a75c29e13845cde0d14f625509a6b9c894c5cf93e7e93c295ea8573`；校准附录 `18ff6a2656f49810a1e3155ab112ee3fde52c6d5c4b1aa3a12d70c7046346c7b`；R2 报告 `d1d189f56f6885f2ebb71c4c0fbb9488a3b04726d88497fd61788ed7f0258c8a`。后两份留在仓库外，未重新启动历史审核 |
| 冻结补丁可应用 | 通过 | 相对基线 `git apply --check` 成功；补丁 SHA-256 `d2352ae89d3c4709c394f693ca821d7ba3c4d2b6de60d4edcbea9c3451b1a7c3` |
| 候选对现有钉子的影响 | 通过 | 候选临时写入 worktree 时 `python3 -m unittest tests.test_session_contract` 13 个用例通过，smoke 对 `issue-session-flow` 的四个标题钉子仍命中；随后 `git checkout -- skills` 还原，基线 SHA-256 复核一致 |
| 技能来源 | 已记录 | Claude Code 会话没有 `to-spec`、`to-tickets` 的可调用入口（上游声明 `disable-model-invocation`）。本会话直接读取平台检出 `codex/vendor/mattpocock/v1.3.1/skills/engineering/` 下的两份 SKILL.md，产物按平台适配写进映射 spec 与 plan。Claude 侧 Matt 插件的实际版本未读回 |
| `admin/AISoftHome` 是否存在 | NOT RUN | 没有 typed 路由；匿名 404 不构成证据。留给建仓前由有权人员核对 |

### 一次性副本预演

为了在确认点 1 之前发现范围外的钉子，本会话在 scratchpad 里从 `origin/main` 建了一个 detached 副本，应用冻结补丁并用现有工具登记 1.25.0，然后跑完整 smoke。副本没有提交、没有推送，用后移除；它不在 change worktree 里，不是 T01 的应用，也不算本票的执行证据。

| 预演步骤 | 结果 |
|---|---|
| 副本上应用冻结补丁 | 干净应用，改动只有四份技能文件 |
| `usage-bundle.sh --release 1.25.0 --today 2026-11-16 --compatibility minor` | `RELEASED 1.25.0 sha256:8e0e15405bb6adac945943e7bc267bcd57c20659e8c25e6900e1b284421e43c8`，只多出 `usage/bundle.json` |
| `usage-bundle.sh --verify --baseline-ref c14a86d4…` | `VERIFIED 1.25.0`，摘要同上 |
| `AISOFT_USAGE_BASELINE_REF=c14a86d4… LC_ALL=C bash codex/tests/smoke.sh` | 退出码 0，末行 `Codex platform static smoke checks passed.` |

预演没有包含 T01 的合同钉子，也没有本目录的文档，所以它只说明四份技能文件加发布登记不会撞到范围外的钉子。正式的 T01、T02 验证仍是 NOT RUN。实施时的发布摘要会因实施日期与当时的 `main` 而不同，不以预演的摘要为准。

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| T01 钉子先红 | NOT RUN | 待执行 |
| T01 应用冻结补丁与全文 SHA-256 | NOT RUN | 待执行 |
| T01 钉子转绿与删短语反证 | NOT RUN | 待执行 |
| T01 `usage-bundle.sh --release` 与 `--verify` | NOT RUN | 待执行 |
| T02 完整 smoke | NOT RUN | 待执行 |
| T02 隔离 build 三端字节比对 | NOT RUN | 待执行 |
| T02 `classify --apply` 与 `--verify` | NOT RUN | 待执行 |
| required CI `CI / verify (pull_request)` | NOT RUN | PR 之后才有 |
| Mac 技能重装与漂移读回 | NOT RUN | 合并后由负责人执行，不在本票授权内 |
| 任何 provider 会话实际加载新文字 | NOT RUN | 本次未取得证据 |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | NOT RUN | 待执行 |
| AC-2 | NOT RUN | 待执行 |
| AC-3 | NOT RUN | 待执行 |
| AC-4 | NOT RUN | 待执行 |
| AC-5 | NOT RUN | 待执行 |
| AC-6 | NOT RUN | 待执行 |
| AC-7 | NOT RUN | 待执行 |
| AC-8 | NOT RUN | 待执行 |

## 交叉审查

此前的方案审核（Claude Opus 5.5，R1、R2 与校准附录，结论 APPROVE_WITH_CHANGES）审的是上一版方案，方案 v2.1 之后没有新的独立审核。它不是本票实现的交叉审查。

| 轮次 | 实现方 | 审查方 | exact head | 结论 | 发现与处置 |
|---|---|---|---|---|---|
| 1 | Claude | Codex（Herdr，GPT-6-Astra high，实际值待记录） | 待填写 | NOT RUN | 待填写 |

## 遗留风险与未完成项

- 本票合并只改变源码合同。Home 仓库的建立、采用、保护、CI、canary 与三项试点全部未执行，归 Home 自己的 Issue。
- 正式跨仓依赖的 installed/live 验收仍未完成，本票不改变这一点。
- 路由 effort 为 max，本会话的实际强度未能自证，实施前由负责人确认或裁决。
