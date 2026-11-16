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

- Commit SHA：T01 治理提交 `3f4b6a6282bdd653fad18b54c9484cc2f1f45081`；ticket_base `443d8983f5b0c88c48c034b4f1286a651e3e0984`；change_base `c14a86d4ad0d1fd5938ab31343f8d72acd486a71`。
- 基线：`origin/main` = `c14a86d4ad0d1fd5938ab31343f8d72acd486a71`（2026-11-16 broker `git.fetch.main` 返回 PASS 后读取）。
- 环境：Mac 平台检出 `/Users/benque/MyDocs/AISoftPlatform`；change worktree `/private/tmp/issue-451-coordination-workspace`。
- 本记录负责证明的 acceptance criteria：AC-1 至 AC-8。T01 已执行到治理 STOP，完成判定与 T02 待 fresh run。
- 执行会话：Claude Code，会话元数据读回 model `claude-opus-5-5`、effort `medium`（路由为 max，偏离已记入 summary `override_reason`，待负责人裁决）。实际加载的 superpowers 插件路径为 7.0.2，平台 pin 为 7.0.0；`executing-plans` 由该插件提供，Txx 仍是唯一合同。

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
| `prepare-ticket 451 T01 --provider claude` | prepared | ticket_base `443d8983…`，起始状态为空，回执 `.superpowers/aisoft/451/T01.json` |
| T01 钉子先红：写入两个新用例后、应用补丁前运行 `python3 -m unittest tests.test_session_contract` | 按预期失败 | `Ran 15 tests`，`FAILED (failures=2)`，失败的是 `test_coordination_workspace_grants_no_access_and_stays_read_only` 与 `test_adoption_entry_points_follow_adr_0003`，原有 13 个通过 |
| T01 `git apply --check` 后应用冻结补丁 | 通过 | 补丁 SHA-256 `d2352ae8…a7c3` 与 spec 一致；应用前四份文件 SHA-256 等于 spec 基线值，应用后等于 spec 固定值 |
| T01 `git apply --reverse --check` | 通过 | 同一补丁可反向匹配 |
| T01 钉子转绿 | 通过 | `Ran 15 tests`，`OK` |
| T01 删短语反证 | 按预期失败后还原 | 临时删掉「不授予任何访问权」、「对其他项目缺省只读」各一次，`test_coordination_workspace…` 失败；删掉「它的项目目录不是第三种访问来源」，`test_adoption_entry_points…` 失败。每次还原后四份文件 SHA-256 回到固定值。「待建票」一条没有手工删，由用例内的 mutation 断言覆盖 |
| T01 `usage-bundle.sh --release 1.25.0 --today 2026-11-16 --compatibility minor` | 通过 | 发布前 broker `git.fetch.main` 读回 `origin/main` 仍为 `c14a86d4…`，最新版本 1.24.1；`RELEASED 1.25.0 sha256:8e0e15405bb6adac945943e7bc267bcd57c20659e8c25e6900e1b284421e43c8` |
| T01 `usage-bundle.sh --verify --baseline-ref c14a86d4…` | 通过 | `VERIFIED 1.25.0`，摘要同上；成员集合与基线相同，既有 31 个 release 前缀不变，只多 1 个 |
| T01 `python3 -B codex/tests/check-project-leak.py` | 通过 | `PASS: project-leak (4 baseline files, 12 hits; site 7 files, 29 hits)` |
| T01 `git diff --check` 与 `check-change-documents --porcelain` | 通过 | 无空白错误；`change-documents PASS`、`change-pr-url PASS` |
| T01 场景与反例审议 | 已做 | spec 七个场景逐条对到新小节的角色、远端写入、任务书、版本不一致、依赖、缺席与恢复、不授权各条，没有发现文字允许被排除的误读。这是作者自审，不是独立审查 |
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
