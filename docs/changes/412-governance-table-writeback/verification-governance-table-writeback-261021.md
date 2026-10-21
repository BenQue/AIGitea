---
issue: 412
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/412
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
status: recorded
branch: change/412-governance-table-writeback
created: 2026-10-21
updated: 2026-10-21
---

# 治理表回写验证记录

## 基线与范围

- Commit SHA: 实现 head `07915940f0dd137218717db4faff7005c5e81a41`（T02）；本记录的提交在其后，只改本文件
- 基线：`origin/main` = `1db191ebf83f7393baa4001d9e85d40ad7f93b40`（broker `git.fetch.main` 后读回）
- 环境: Mac 平台检出，Claude 会话；各项目 checkout 只做 broker fetch 与临时 detached worktree，读完即删
- 本记录负责证明的 acceptance criteria: AC-1 至 AC-6

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| broker `gitea.pulls.read --state closed`（aisoft-platform） | PASS | PR 390 `0192a8e`、393 `149e469`、394 `08be6f4`、398 `43db3d0`、399 `86821cf`、400 `fb9d8c5`、401 `fdf93c1`、404 `b2a154d`、405 `38ddc92`、407 `cee4294`、410 `f169b12`、411 `1db191e`，均 `merged=true` |
| 各合并 commit 上 `usage/bundle.json` 的最后一个 release | PASS | 149e469 1.3.0、08be6f4 1.4.0、43db3d0 1.5.0、86821cf 1.6.0、fb9d8c5 1.7.0、38ddc92 1.8.0、f169b12 1.9.0、1db191e 1.10.0；0192a8e、fdf93c1、b2a154d、cee4294 不改 `usage/` |
| broker `gitea.pull.read`（newemaint 322、hsdb 71、sfm-digital-board 185 与 187、localwms 336） | PASS | NewEMaint 322 `dfe04df` 2026-10-21；HSDB 71 `673cadb`；SFM 185 `799bf12`、187 `3bb6b78`；LocalWMS 336 `6e143fe`；均 `merged=true` |
| 各项目 main 合并 SHA 的 detached worktree 里 `.aisoft/bin/aisoft bundle status` | PASS | HSDB `673cadb`、SFM `3bb6b78`、LocalWMS `6e143fe` 各四项 PASS：platform-pin、tool-provenance、pointer-sections、change-templates，均为 1.8.0 |
| 同上 `.aisoft/bin/aisoft check-change-documents` | 见证据 | HSDB `changes=33 gap=0`；LocalWMS `changes=161 gap=0`；SFM `changes=78 gap=1`，GAP 全部是旧编号目录与无 front matter 的旧四文档（R12 LEGACY 范围，本批不处理） |
| LocalWMS `grep -n uses: .gitea/workflows/*` | PASS | 无输出 |
| 反向证明：把 03 的 `### 治理表回写（平台仓）` 改成 `### 治理表回写` 后跑 smoke | FAIL（预期） | `exit=1`，`缺少小节标题：治理表回写（平台仓）`；随后恢复原文件 |
| `bash codex/tests/smoke.sh`（head `0791594`，干净工作树，`rg` 为 `/opt/homebrew/bin/rg`） | PASS | `exit=0`，`Codex platform static smoke checks passed.`，耗时约 7 分钟 |
| `wc -c AGENTS.md` | PASS | 4767 → 4853 字节，≤ 5 KB |
| `grep -c 'grep -Fq' codex/tests/smoke.sh`（本分支与 `origin/main`） | PASS | 89 与 89，棘轮基线不变 |
| `aisoft check-change-documents` | PASS | `changes=190 pass=2 gap=0` |
| `aisoft classify --verify 412` | PASS | `projected`，platform / complex |
| `git diff --stat origin/main...HEAD` | PASS | 只含 `03`、`AGENTS.md`、`codex/tests/smoke.sh`、两张治理表与本 change 目录 |

NewEMaint PR 322 正文：AC-5 的隔离比对被无关容器的重启循环误判为 FAIL，负责人以回执判过并记录例外；生产恢复仍 NOT RUN。

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | PASS | 路线图第二轮 11 行均按上表 PR 读回写成 `已完成（#N，PR M，SHA[，发布包 X]）`；R16 行带衍生 #406；新增本批 #412 行；推荐顺序下加现状说明 |
| AC-2 | PASS | 验收记录新增 NewEMaint #313 行：PR 322、`dfe04df`、NewEMaint main pin 1.2.0，AC-5 例外与生产 NOT RUN 照 PR 正文与其 verification 写 |
| AC-3 | PASS | 四行采用记录的读回换成各项目 main 合并 SHA 上的 `bundle status` 结果；LocalWMS 写无 `uses:`；SFM 文档检查 gap=1 如实写 |
| AC-4 | PASS | `03` §7 新增小节与来历 #412 行；AGENTS.md 一行指针（4853 字节）；两张表「用法」行指向 `03` §7 |
| AC-5 | PASS | 反向证明 FAIL（预期），恢复后全量 smoke PASS，`grep -Fq` 计数 89 不变 |
| AC-6 | PASS | diff stat 见上；技能、runtime、broker、模板、`usage/` 无改动 |

## 交叉审查

| 轮次 | 实现方 | 审查方 | exact head | 结论 | 发现与处置 |
|---|---|---|---|---|---|
| 1 | Claude | Codex（`codex exec -s read-only -m gpt-6-astra`，reasoning ultra） | `f308d3459709cbacfcb6958f0f7f3bea57072903` | FAIL | 2 条 P2：①spec 回滚段与 summary 风险段的冲突处理写法（merge commit、rebase）与 `03` §1「main 整合与发布」不一致，改为引用该节、冲突先停下；②E2E #313 行把数据哈希写成「与备份和源库一致」，NewEMaint verification 只证明恢复库与备份哈希一致，源库比的是表集合、行数、结构、枚举与迁移，已分开写 |
| 2 | Claude | Codex（`codex exec -s read-only -m gpt-6-astra`，reasoning high，负责人澄清单批审查用 high） | `c0f2814f59a1c856c82b2e2b1ca1d06e6294c609` | PASS | 无发现；两条 P2 已核对修复，全 diff 复审无新增问题 |

## 遗留风险与未完成项

- 规则落在文档，执行仍靠会话；收尾读回 `origin/main` 是唯一确定性核对。
