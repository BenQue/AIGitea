---
issue: 223
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/223
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - ci-change
  - shared-core
  - platform-governance
depends_on: []
status: pr-open
branch: change/223-ci-merge-preview-gate
created: 2026-09-05
updated: 2026-09-05
---

# Verification：#223 合并预览检查器与过期绿闸门

## 基线与范围

- Commit SHA: `f9b2ca9`（PR head），分支 `change/223-ci-merge-preview-gate`
- 基线：`origin/main` = `724cf78`（两次 rebase 之后；开工时是 `07084de`，中途 #180 与 #182 先后合并进 main）
- 环境：Mac 本地 checkout `/private/tmp/issue-223-ci-merge-preview-gate`，Gitea `gitea-ci.orb.local:3000`
- 本记录负责证明的 acceptance criteria: AC-1 至 AC-11

声明 `verification` 的原因：`block_on_outdated_branch` 的**改动前**基线、跨 8 个仓库的
broker 回读、以及本 PR 上合并预览的一次性运行观测，required CI 都不重放。

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| `bash codex/tests/smoke.sh`（T01 后） | PASS | `Ran 660 tests ... OK` + `Codex platform static smoke checks passed.` |
| `bash codex/tests/smoke.sh`（T04 后，rebase 到 `87b3aa4`） | PASS | `Ran 668 tests ... OK` + `Codex platform static smoke checks passed.` |
| `bash codex/tests/test-project-check.sh` | PASS | `project check tests passed (50 cases)` |
| `bash -n templates/project/ci/merge-preview.sh` | PASS | 无输出 |
| `shellcheck templates/project/ci/merge-preview.sh` | PASS | 无输出 |
| `shellcheck codex/tools/aisoft-project-check.sh` | PASS | 无输出 |
| 检查器基线（改动前，本仓自检） | 记录 | `result: pass=3 gap=3 skip=2`；三条 GAP 是 pointer-sections / change-templates / architecture-lock，平台仓不是项目仓，属结构性 |
| 检查器（T04 后，本仓自检） | 记录 | `result: pass=4 gap=3 skip=3`；同样三条结构性 GAP，新增 `PASS: ci-merge-preview` |
| `ci-merge-preview` 跨仓实跑（本地 checkout） | 记录 | LocalWMS `PASS`；aisoft-platform（改动前）、NewEMaint、rsdesign-new、HSDB、SFMDigitalBoard 全部 `GAP`。与 Issue 正文的抽查表一致 |
| 假 PASS 回归（第一版判据） | 记录 | 第一版只找「某处有 `git` 也有 `merge`」，被 ShellCheck 清单里的 `git-credential-aisoft-host.sh` 与 `change-merge-range.sh` 凑成一次匹配，把改动前的本仓判成 `PASS: ci-merge-preview`。收紧为「`git` + 仅全局 flag + `merge` 子命令」并要求字面标记 `MERGE_PREVIEW` 后复判为 `GAP` |
| 合并预览脚本本地复现事故结构 | PASS | 构造 base=74、PR A 合入后 main=75、PR B 从旧 base 出发也写 75；PR B head 的树是 75，跑完预览得到合并 SHA `d4682b2`，父提交是 head 与 base 两个，工作区同时含两侧改动。项目自己的计数断言在合并前就能红 |
| 合并预览失败路径：真实冲突 | PASS | `MERGE_PREVIEW_CONFLICT`，打印冲突文件后 `git merge --abort`，`exit=1`，不回退到 head |
| 合并预览失败路径：head 与事件载荷不符 | PASS | `MERGE_PREVIEW_HEAD_MISMATCH`，`exit=1` |
| 合并预览路径：base 已是 head 祖先 | PASS | `MERGE_PREVIEW_ALREADY_UP_TO_DATE`，`exit=0`，明确说明合并结果与 head 逐字节相同 |
| `MERGE_PREVIEW_NO_MERGE_BASE` 分支 | NOT RUN | 本地用 `--depth=1` 克隆构造未能触发：脚本对 base ref 的显式 fetch 把历史补深到足以求出共同祖先，于是正常合并成功（`exit=0`）。该分支只有代码 review，没有实跑证据 |
| `block_on_outdated_branch` 改动前基线回读 | 记录 | 见下方交接项表，broker `gitea.protection.read`，2026-09-05 |
| 本 PR 的 `CI / verify (pull_request)` | PASS | PR #248，run 1041 / job 1041，`completed success`，56s，`workflow: ci.yml@refs/pull/248/head`。四步全绿：`actions/checkout@v4`、`Check out merge preview`、`Platform smoke suite`、`Merge preview evidence` |
| required context 字符串回读 | PASS | `gitea.commit.status.read --sha f9b2ca97…`：combined `success`，唯一 context `CI / verify (pull_request)`，与改动前逐字相同 |
| 合并预览在真实 runner 上的行为 | 记录 | 日志：`MERGE_PREVIEW_ALREADY_UP_TO_DATE: base 已是 head 的祖先`，`base main 当前尖端 = 724cf78…`，`已检出 SHA = f9b2ca97…`。刚 rebase 过，所以走的是「合并结果与 head 逐字节相同」那条分支；**真实三方合并那条路径在 runner 上没有被这次运行覆盖**，只有本地复现证据 |
| 末尾重印步骤的必要性 | 记录 | `gitea.actions.job.logs.read --job 1041` 返回 `[truncated: 99020 leading bytes omitted]`——`Check out merge preview` 那一步自己的输出取不回来。末尾 `Merge preview evidence` 步骤重印的那一份是唯一读得到的证据 |

命令与输出照实抄。

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | 达成 | `check_ci_merge_preview` 只读文件，无写操作；三种结论各有用例，`test-project-check.sh` 50 cases 绿 |
| AC-2 | 达成 | 对 `/Users/benque/Projects/LocalWMS`（`origin/main` 已含 Issue #193 的修复）实跑得 `PASS: ci-merge-preview`。用例侧以 `templates/project/ci/` 的实际文件做 fixture，同形态 |
| AC-3 | 达成 | 改动前的本仓 `ci.yml` 与用例 `merge-preview-head` 均得 `GAP: ci-merge-preview — .gitea/workflows/ci.yml …`，文案含 workflow 文件名 |
| AC-4 | 达成 | 无 workflow 目录、push-only、pull_request 无 checkout 三种情形各有用例，均 `SKIP` 并带原因 |
| AC-5 | 达成 | `check_outdated_branch` 由 manifest 的 `classification` 推导范围；`false`、缺 key、`public-test`、不在 manifest 四种情形各有用例 |
| AC-6 | 达成 | 未启用 `--remote`、HTTP 403、读取失败三条路径各有断言，语义与既有 `ci-context` 一致 |
| AC-7 | 达成 | `templates/project/ci/ci.yml` 与 `merge-preview.sh` 已交付；失败路径三条实跑见上表；`bash -n` 与 `shellcheck` 均绿并进入 smoke 清单 |
| AC-8 | 达成 | `.gitea/workflows/ci.yml` 的 `name: CI`、`verify:`、`on: pull_request` 三处逐字未变；run 1041 四步全绿；commit status 回读唯一 context 仍是 `CI / verify (pull_request)`，combined `success` |
| AC-9 | 达成 | `06-运维手册与踩坑集.md` 踩坑 22，含两个缺口的机理、分工与串行化代价的处置 |
| AC-10 | 达成 | `Ran 668 tests ... OK` + `Codex platform static smoke checks passed.` |
| AC-11 | 达成 | 见下方交接项表，逐仓写明未执行 |

## 需要人在 Gitea 界面执行的交接项（未执行）

broker 没有 `protection.set`，本次变更**没有**修改任何仓库的分支保护。下表是
2026-09-05 用 broker `gitea.protection.read` 逐仓回读的**改动前**真实值。
除 SFMDigitalBoard 外，全部需要人在 Gitea 的 `main` 分支保护里勾上
`block_on_outdated_branch`。

| 仓库 | classification | 改动前 `block_on_outdated_branch` | required contexts | 需要人操作 |
|---|---|---|---|---|
| aisoft-platform | public-platform | `false` | `CI / verify (pull_request)` | **是** — NOT RUN |
| HSDB | internal-application | `false` | `CI / test (pull_request)` | **是** — NOT RUN |
| LocalWMS | internal-application | `false` | `CI / test (pull_request)` | **是** — NOT RUN |
| NewEMaint | internal-application | `false` | `CI / verify (pull_request)` | **是** — NOT RUN |
| rsdesign-new | internal-application | `false` | `CI / test (pull_request)` | **是** — NOT RUN |
| SapTableMigrate | internal-application | `false` | 无 | **是** — NOT RUN |
| WMPDA | internal-application | `false` | 无 | **是** — NOT RUN |
| SFMDigitalBoard | internal-application | `true` | `CI / verify (pull_request)` | 否，已满足 |

SapTableMigrate 与 WMPDA 没有 required contexts，打开该开关只会强制 rebase，
不会带来一次 CI 重跑——它们仍在裁定范围内，但收益比其余仓小。

打开之后可用 `codex/tools/aisoft-project-check.sh --repo <checkout> --remote`
读回 `PASS: ci-outdated-branch` 确认。

## 遗留风险与未完成项

- **7 个仓库的分支保护尚未打开**，缺口②在人执行上表之前不闭合。合并本 PR 只是让
  它可被机器读回，不等于它已生效。
- **`MERGE_PREVIEW_NO_MERGE_BASE` 分支没有实跑证据**，只有代码 review。
- **合并预览的真实三方合并路径在本平台 runner 上没有被这次运行覆盖**：PR head 刚
  rebase 过，base 已是 head 的祖先，脚本走的是 `MERGE_PREVIEW_ALREADY_UP_TO_DATE`。
  runner 上已证明的是脚本能跑、能取到 base 尖端、能给出可复验的 SHA；三方合并与
  冲突退出只有本地证据。下一次 base 在 PR 开着时前进，就会自然覆盖到。
- 本次变更**不改任何项目仓文件**。既有项目的 `ci-merge-preview` GAP 需要各自开 Issue 修，
  平台不代改。
- 不声明任何部署、外部验收或生产就绪。
