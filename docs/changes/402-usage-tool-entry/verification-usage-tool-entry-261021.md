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

- 基线：`origin/main` = `86821cf`；实现中 R16（#397，PR 400）与 #370（PR 401）先后合并，用 merge commit `85ddf20`、`97b48d7` 集成，`origin/main` = `fdf93c1`。发布包 1.7.0 已被 R16 占用，本票发 1.8.0（`compatibility: minor`）。
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
| 审查修复 | `976ed9a`、`1093a6d`、`6f0aca9`、`2a583e2`、`422905d` | Codex 三轮共 9 条发现；技能改动各自单独 commit 在前，运行时与测试在后，每次重发 1.8.0（未发布的候选记录撤回重发） |

## 验收证据

| AC | 结果 | 证据 |
|---|---|---|
| AC-1 | PASS | LocalWMS #335 worktree（当时 head `cd948ab`，采用内容随后按最终 1.8.0 重生成），`sandbox-exec` 拒读平台检出与本 worktree，`env -i HOME=<临时目录> PATH=/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin`：`aisoft version`（layout project，1.8.0）→ `change-name 335 adopt-usage-bundle` → `check-change-documents` gap=0 → `classify 335`（打印路由行）→ `classify --apply 335` updated → `classify --verify 335` **projected** → `complete --project localwms --range de829b9~1..de829b9` dry-run 计划（pinned 325），全部 exit 0 |
| AC-2 | PASS | `test-aisoft-entry.sh` 对导出的 `.claude/skills` 跑守卫：「维护层」小节外零命中；探针（会话步骤里写平台路径）被抓、维护层小节不报 |
| AC-3 | PASS（推送待确认点 2） | `--adopt` 对 HSDB #70（`838b863`，173 个改动路径）、LocalWMS #335（`7fbc4d9`，170）、SFM #184（`6796407`，173）各跑一次（审查修复后按最终 1.8.0 重生成并 amend 本地未推送提交），`--project-status` 四项 PASS；源码 broker `GitRepository.scope` + `verify_history` 离线复现推送闸门 PASS（175/172/175 个 scope 路径，含 canonical 模板上下文）。PR 链接在确认点 2 之后写进 E2E 表 |
| AC-4 | PASS | `test-aisoft-entry.sh`：导出到空目录、沙箱拒读平台检出，十一个子命令逐个 `--help` 与真实调用（`classify --verify` 与 `complete` dry-run 用测试副本里的 mock broker 与合成 manifest，`project-check` 含 architecture-lock）；删掉 `aisoft_change_name.py` 后 `check-change-documents` 失败、`tool-provenance` GAP |
| AC-5 | PASS | `test-usage-bundle.sh` 20：改一个工具字节 → GAP；provenance 不符 → GAP；pin 1.0.0 → NOTE；`test-project-check.sh` 新增 tool-drift 用例 |
| AC-6 | PASS | `test-usage-bundle.sh` 19：缺 `--compatibility`/`--notes`、非法级别、空说明均拒绝；落后含 major → `platform-pin` GAP，minor/patch → NOTE；半声明的 release 被 `--verify` 拒绝；`--verify --baseline-ref origin/main` PASS |
| AC-7 | PASS | 模板「项目事实」1708 字节；`test-project-check.sh` 超 2 KB 用例报 `NOTE: agents-budget` 且计数不变 |
| AC-8 | PASS | `smoke.sh` 在本记录所在 head 复跑见下节；`usage-bundle.sh --verify --baseline-ref origin/main` VERIFIED 1.8.0；`check-change-documents` gap=0；Codex 四轮只读审查，第 4 轮 PASS（`422905d`），记录在项目库 `codex-review-402.md` |

## 交叉审查

| 轮 | head | 结论 | 发现 |
|---|---|---|---|
| 1 | `6daab1e` | FAIL | `--adopt` 跟随符号链接；`claim-worktree` 忽略 `--repo`；新版本可整项删除 tool-provenance；闭包测试缺成功路径；技能残留 `apply-classification-labels.sh` |
| 2 | `1093a6d` | FAIL | `--worktree=DIR` 被覆盖；子命令 `--help` 未覆盖；技能残留 `aisoft-loop` / `aisoft_loop.cli` |
| 3 | `2a583e2` | FAIL | `git_scope` 漏列 `skills/aisoft-matt-workflow/SKILL.md`（离线复现 SCOPE_DENIED） |
| 4 | `422905d` | PASS | 无；`git_scope` 与 diff 一致（25 条），源码推送闸门离线复现 PASS（19 个提交含 2 个 main 集成 merge） |

## 判级投影

`aisoft classify --verify` 读回 **projected**：#402（platform / complex），HSDB #70、LocalWMS #335、SFM #184（maintenance / small）。

## 已知限制与遗留

- broker `git.push.change` 要求 small 也带映射 spec 的 `git_scope`，与「small 只有 summary」冲突；本票的采用 Issue 带只写 scope 的 spec，冲突本身交后续处理。
- `git_scope` 上限 256：带 Cursor 落点的采用约 355 个路径，用 Cursor 的项目（R15）要先解决上限或拆分。
- SFM 的 legacy change 目录（`0001-…` 等）在 `check-change-documents` 里是既有 GAP，归 R12；不影响 `--project-status`。
- `aisoft_loop.cli` 的 `get-issue`、`list-issues`、`apply-analysis` 未删（要 raw token，不进 `aisoft`），后续遗留项。
- 被工具包收录的平台文件以后改动都要发新版本。

## 未运行

broker/技能重装（合并后）；三个项目的推送与 PR（确认点 2 之后）。
