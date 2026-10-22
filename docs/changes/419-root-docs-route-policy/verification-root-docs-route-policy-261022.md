---
issue: 419
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/419
change_type: docs
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - agent-governance
depends_on: []
status: passed
branch: change/419-root-docs-route-policy
created: 2026-10-22
updated: 2026-10-22
---

# 验证记录

## 基线与范围

- Commit SHA: 代码候选 `be291a6197b44d800b9fe07f3862666bc5994d8f`（之后只有本记录、spec `git_scope` 与审查索引的记录型提交）
- 基线：`origin/main` = `c373f407ffc7a699be9495ce1be7b1adf995c370`
- 环境: Mac 平台检出的 change worktree `/private/tmp/issue-419-root-docs-route-policy`，`rg` 为 `/opt/homebrew/bin/rg`
- 本记录负责证明的 acceptance criteria: AC-1 至 AC-7

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| `bash codex/tests/smoke.sh`（head `5027814a`） | PASS | 退出码 0，末行 `Codex platform static smoke checks passed.`，用时 6 分 52 秒 |
| `bash codex/tests/smoke.sh`（head `be291a61`） | PASS | 退出码 0，末行同上 |
| `bash codex/tests/smoke.sh`（head `011f285d`） | PASS | 退出码 0，末行同上 |
| `grep -c 'references/route-policy.md' AGENTS.md` | PASS | `1` |
| `grep -c executing-plans AGENTS.md` | PASS | `1` |
| `wc -c < AGENTS.md` | PASS | `5024`（≤ 5120） |
| 反向证明：`sed` 去掉 AGENTS.md 的路由表链接后 `grep -Fq 'references/route-policy.md'` | 变红 | 退出码 `1`；工作树未改动 |
| `grep -n route-policy.md README.md` | PASS | 命中第 132 行（§4）与第 154 行（§5 导航） |
| `head -1 08-*.md` 对照 README 第 149 行 | PASS | 都是「Matt 编排与双工具共存」 |
| `git diff --stat origin/main -- skills usage templates` | PASS | 空输出 |
| `aisoft check-change-documents` | PASS | `changes=193 pass=2 gap=0` |
| `aisoft classify 419` | PASS | 路由行 `complex-production · frontier/max · spec-plan · verify full+reverse-proof · review cross-provider` |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | PASS | AGENTS.md 第 25 行指向路由表并区分 `executing-plans` 与 `$implement #N Txx`，大需求先 `grill-me`，small 可按合同跳过 spec/plan；smoke 钉住的字面量全部保留；5024 B |
| AC-2 | PASS | README 第 132、154 行 |
| AC-3 | PASS | README 第 149 行与 08 一级标题一致 |
| AC-4 | PASS | §8 Matt 行只列 Codex 会话实际调用 Matt 技能与 Claude 侧 `retro`；Codex 模型回合依据 `08` §7.1「模型回合是否跑通由交叉审查记录证明」，未新增完成声明 |
| AC-5 | PASS | smoke 的 README 日期版本检查通过；三个目录无 diff，`usage/bundle.json` 未变 |
| AC-6 | PASS | 三次 smoke 退出码 0；反向证明变红 |
| AC-7 | PASS | 见下节；审查索引与路线图各一行 |

## 交叉审查

| 轮次 | 实现方 | 审查方 | exact head | 结论 | 发现与处置 |
|---|---|---|---|---|---|
| 1 | Claude | Codex（`codex exec -s read-only -m gpt-6-astra`，high） | `5027814a9aebff35a08d3e4554612e466bfb3a14` | FAIL | 1 条 P2：AGENTS.md「small 跳过 spec/plan」把条件豁免写成无条件；改为「small 可按合同跳过 spec/plan」（`be291a61`） |
| 2 | Claude | Codex（同上） | `be291a6197b44d800b9fe07f3862666bc5994d8f` | FAIL | 第 1 轮 P2 确认已修，内容无其它发现；1 条 P2：本记录与审查索引仍是占位；本次提交补齐 |
| 3 | Claude | Codex（同上） | `011f285db1debecea5621a6307f73b157f32f5e6` | PASS | 无发现；`git_scope` 精确覆盖 8 个变更文件，反向证明只读复现（原文 0，去链接 1） |

## 遗留风险与未完成项

范围 B（`skills/aisoft-platform/SKILL.md`、`usage/CONTRACT.md`、`templates/project/AGENTS.md`、`docs/agents/issue-tracker.md` 里同一句 `$implement` 主路径）不在本批，需另开 Issue 并发版。
