---
issue: 402
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/402
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
  - shared-core
  - artifact
depends_on:
  - 391
  - 392
  - 395
status: pending
branch: change/402-usage-tool-entry
created: 2026-10-21
updated: 2026-10-21
---

# R11 验证记录

## 基线与范围

- 基线：`origin/main` = `86821cf`；实现中 R16（#397，PR 400）、#370（PR 401）与 R14（#403，PR 404）先后合并，用 merge commit `85ddf20`、`97b48d7`、`a03ab0f` 集成（R14 那次：先 `e3a3056` 把 03 暂时恢复成 main 的文本让 merge 无冲突，合并后 `84e7a2c` 按 R14 现行合同写法重新加回本票段落；推送闸门要求 merge 能无冲突重算，第 7 轮指出的冲突 merge `12e6d2b` 从未推送，已弃用），`origin/main` = `b2a154d`。发布包 1.7.0 已被 R16 占用，本票发 1.8.0（`compatibility: minor`）。
- 环境：macOS 本机（`/bin/bash` 3.2.57、Python 3、`sandbox-exec`）；已安装 broker（`/usr/local/libexec/aisoft/host-access-broker`）。
- 本记录负责证明的 acceptance criteria：AC-1 至 AC-8。会话 id `claude-r11-402-90529a4f`。

## 按 Txx 执行（superpowers `executing-plans`，内联、同一时刻一个写者）

| Ticket | commit | 证据 |
|---|---|---|
| 合同 | `8cf551f`、`acf8c29`、`18674ea`、`f170747` | 确认点 1：负责人 2026-10-21 03:40Z 回「确认，按推荐」，标签 `approved`（broker labels.set PASS） |
| T01 治理步骤 | `ee7943b` | 技能、使用合同、项目模板单独 commit 后停止，重读 `AGENTS.md`（未改）与已提交技能再动 runtime |
| T02 入口 | `7a060ef` | `codex/tools/aisoft`；project-check manifest 回退到 `/usr/local/share/aisoft` |
| T03–T04 发布包与采用 | `78853b3` | 48 个 `tool-provenance` 成员；`notes`/`compatibility`；`--adopt`；`agents-budget` |
| T05 测试 | `beca16f` | 见下表 |
| T06 文档 | `3bde56c` | `03`、`06` 指向 `aisoft`；路线图；E2E 表「采用记录」 |
| 合同更正 | `ed20282`、`7e2a2f8` | 试采用撞上 broker 推送闸门三条约束（spec §6）：治理文本先单独 commit，再改 runtime 并重发 1.8.0 |
| §7 CI checkout | `8248382`、`5b9aa4d`、`46b5866` | 负责人 2026-10-21 07:05Z 在 #370 线程回「并入 R11」（协调会话转达原话）：合同补 §7 与 AC-9 单独 commit；模板 `ci.yml` 作为治理步骤单独 commit；smoke 守卫与 1.8.0 重发在后 |
| 审查修复 | `976ed9a`、`1093a6d`、`6f0aca9`、`2a583e2`、`422905d` | Codex 三轮共 9 条发现；技能改动各自单独 commit 在前，运行时与测试在后，每次重发 1.8.0（未发布的候选记录撤回重发） |

## 验收证据

| AC | 结果 | 证据 |
|---|---|---|
| AC-1 | PASS | LocalWMS #335 worktree（当时 head `cd948ab`，采用内容随后按最终 1.8.0 重生成），`sandbox-exec` 拒读平台检出与本 worktree，`env -i HOME=<临时目录> PATH=/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin`：`aisoft version`（layout project，1.8.0）→ `change-name 335 adopt-usage-bundle` → `check-change-documents` gap=0 → `classify 335`（打印路由行）→ `classify --apply 335` updated → `classify --verify 335` **projected** → `complete --project localwms --range de829b9~1..de829b9` dry-run 计划（pinned 325），全部 exit 0 |
| AC-2 | PASS | `test-aisoft-entry.sh` 对导出的 `.claude/skills` 跑守卫：「维护层」小节外零命中；探针（会话步骤里写平台路径）被抓、维护层小节不报 |
| AC-3 | PASS（推送待确认点 2） | `--adopt` 对 HSDB #70（`6b2e9a4`）、LocalWMS #335（`e9a2ecc` 采用 + `43669b2` CI checkout）、SFM #184（`b30d519`）各跑一次（每次重发 1.8.0 后按最终版本重生成并 amend 本地未推送提交），`--project-status` 四项 PASS；源码 broker `GitRepository.scope` + `verify_history` 离线复现推送闸门 PASS（175/173/175 个 scope 路径，含 canonical 模板上下文）。PR 链接在确认点 2 之后写进 E2E 表 |
| AC-4 | PASS | `test-aisoft-entry.sh`：导出到空目录、沙箱拒读平台检出，十一个子命令逐个 `--help` 与真实调用（`classify --verify` 与 `complete` dry-run 用测试副本里的 mock broker 与合成 manifest，`project-check` 含 architecture-lock）；删掉 `aisoft_change_name.py` 后 `check-change-documents` 失败、`tool-provenance` GAP |
| AC-5 | PASS | `test-usage-bundle.sh` 20：改一个工具字节 → GAP；provenance 不符 → GAP；pin 1.0.0 → NOTE；`test-project-check.sh` 新增 tool-drift 用例 |
| AC-6 | PASS | `test-usage-bundle.sh` 19：缺 `--compatibility`/`--notes`、非法级别、空说明均拒绝；落后含 major → `platform-pin` GAP，minor/patch → NOTE；半声明的 release 被 `--verify` 拒绝；`--verify --baseline-ref origin/main` PASS |
| AC-7 | PASS | 模板「项目事实」1708 字节；`test-project-check.sh` 超 2 KB 用例报 `NOTE: agents-budget` 且计数不变 |
| AC-8 | PASS | `smoke.sh` 在 `c5bfff8` 从头到尾跑完 exit 0（680 个单测 OK，含 R14 文档守卫与 grep -Fq 棘轮）；`usage-bundle.sh --verify --baseline-ref origin/main` VERIFIED 1.8.0；`check-change-documents` gap=0；Codex 八轮只读审查，第 8 轮 PASS（`c5bfff8`），记录在项目库 `codex-review-402.md` |

| AC-9 | 部分（LocalWMS PR CI 待推送；第 5 轮修复见下） | 模板 `ci.yml` 无 `uses:`；smoke 守卫反向证明：模板副本加回 `uses: actions/checkout@v4` 后守卫命中（rc=0），原文件 rc=1。手写 checkout 步骤从模板原样抽出，在本地 `file://` 裸仓模拟复用工作区连跑两次：两次都检出 exact head（`de829b9`）、残留文件被清掉，extraheader 写入后可删除。HSDB、SFM workflow 读回 `uses:` 0 处，不改；LocalWMS 改用同一步骤（`43669b2`），#335 改判 maintenance / complex（`ci-change`）并读回 projected，Issue 评论记录范围变更。LocalWMS PR 的 CI 运行在推送后补记 |

## 交叉审查

| 轮 | head | 结论 | 发现 |
|---|---|---|---|
| 1 | `6daab1e` | FAIL | `--adopt` 跟随符号链接；`claim-worktree` 忽略 `--repo`；新版本可整项删除 tool-provenance；闭包测试缺成功路径；技能残留 `apply-classification-labels.sh` |
| 2 | `1093a6d` | FAIL | `--worktree=DIR` 被覆盖；子命令 `--help` 未覆盖；技能残留 `aisoft-loop` / `aisoft_loop.cli` |
| 3 | `2a583e2` | FAIL | `git_scope` 漏列 `skills/aisoft-matt-workflow/SKILL.md`（离线复现 SCOPE_DENIED） |
| 4 | `422905d` | PASS | 无；`git_scope` 与 diff 一致（25 条），源码推送闸门离线复现 PASS（19 个提交含 2 个 main 集成 merge） |
| 5 | `33453e6` | FAIL | 并入 §7 后：LocalWMS list-contract 闸门钉死旧 `fetch-depth`（`CHECKOUT_DEPTH_FACT_GONE`）；#335 summary 缺项目必需的「两份清单的影响」小节；复用旧浅克隆工作区时 fetch 不补历史（合并预览 `MERGE_PREVIEW_NO_MERGE_BASE`）；smoke 守卫漏行内 `uses`；改判证据不一致 |
| 6 | `7550616` | FAIL | 第 5 轮 5 条已修；新：unshallow 参数跨重试保留，上一轮已补全历史时重试会报错；LocalWMS workflow 注释与 summary 仍写 push 为 depth 1 |
| 7 | `0409ff2` | FAIL | 第 6 轮两条已修；新：R14 集成 merge `12e6d2b` 带人工解冲突，源码推送闸门重算 merge 报 `MERGE_CONFLICT`（已按上文重建，冲突 merge 弃用）；project-align 把模板闸门写成「核对内容」，实际只核对路径与文件类型（已更正） |
| 8 | `c5bfff8` | PASS | 无；四个分支源码推送闸门重算 PASS（平台 34 个提交含 3 个 main 集成 merge，无 `MERGE_CONFLICT`）；`backup-0409ff2` 与 `5484a73` 树相同 |

## 判级投影

`aisoft classify --verify` 读回 **projected**：#402（platform / complex）；HSDB #70、SFM #184（maintenance / small）；LocalWMS #335 按 §7 改判后为 maintenance / complex（`ci-change`）。

## 第 5 轮修复证据

- 模板与 LocalWMS 的 checkout 在 fetch 前对浅仓加 `--unshallow`：本地 `file://` 裸仓上先 `git clone --depth 1` 造出旧工作区，跑模板步骤后 `is-shallow-repository` 由 true 变 false、历史 621 个提交，再跑一次不变。
- smoke 守卫改为识别任意位置的 `uses` 键（块项、行内映射、带引号键），并内置四个探针：三种 `uses` 写法必须命中、普通步骤不得命中。
- LocalWMS（`253fec0`）：`list-contract-gate.mjs` 的全历史事实改钉 unshallow 判定，测试措辞同步；#335 summary 补「两份清单的影响」三问；`node scripts/ci/list-contract-gate.mjs` 绿；`node --test` 跑 list-contract、ci-merge-preview、ci-audit 三组 48 条全过，`fault-matrix-gate` 因本机未装 `typescript` 依赖起不来（改动前基线同样失败，NOT RUN，交给 PR CI）。

## 第 6 轮修复与 R14 交来的更正

- 模板与 LocalWMS 的 checkout 每轮 fetch 前重新判断浅仓（`04bdf65`、LocalWMS `ci.yml`）；LocalWMS workflow 注释、闸门注释与 summary 改为「两条路都取全历史」。
- R14 交接里归本票的两处技能更正（`726bd60`）：`aisoft-platform` 会话第 7 步改为「已推送分支用 merge commit 集成 main」；`project-align.md` 的 #360 过时句改为现行的模板 scope 例外说明。路线图 R14 行改「已完成」。

## 已知限制与遗留

- broker `git.push.change` 要求 small 也带映射 spec 的 `git_scope`，与「small 只有 summary」冲突；本票的采用 Issue 带只写 scope 的 spec，冲突本身交后续处理。
- `git_scope` 上限 256：带 Cursor 落点的采用约 355 个路径，用 Cursor 的项目（R15）要先解决上限或拆分。
- SFM 的 legacy change 目录（`0001-…` 等）在 `check-change-documents` 里是既有 GAP，归 R12；不影响 `--project-status`。
- `aisoft_loop.cli` 的 `get-issue`、`list-issues`、`apply-analysis` 未删（要 raw token，不进 `aisoft`），后续遗留项。
- 被工具包收录的平台文件以后改动都要发新版本。
- 平台仓自己的 `.gitea/workflows/ci.yml`（#370）同样没有处理复用的浅仓；不在本票范围，后续遗留项。

## 未运行

broker/技能重装（合并后）；三个项目的推送与 PR（确认点 2 之后）。
