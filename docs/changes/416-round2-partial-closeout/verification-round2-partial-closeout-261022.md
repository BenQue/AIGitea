---
issue: 416
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/416
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
branch: change/416-round2-partial-closeout
created: 2026-10-22
updated: 2026-10-22
---

# Verification

## 基线与范围

- 基线：`0bcc3cd863afef3425e9dcdda5e1053a3b0ad097`（`origin/main`）。
- 代码候选 head：`127e6530`（T01 `3b7f0d84`、T02 `02f5dd8e`、T03 `096f09cf`、T04 `8f61b5a4`，其余为审查修复）。本记录之后的 commit 只写本文件与审查索引一行。
- 环境：macOS 本机（bash 3.2），`rg` 为真实 `/opt/homebrew/bin/rg`；VM 经 `/usr/local/bin/orb -m gitea-ci`。

## 执行结果

| 检查 | 结果 | 证据 |
|---|---|---|
| `python3 -B codex/tests/check-project-leak.py` | PASS | 项目名 4 文件 12 处（原 10 文件 41 处）；站点值 7 文件 29 处（原 10 文件 37 处）；基线文件与 ADR D3 例外表一致 |
| `python3 -m unittest tests.test_project_leak` | PASS | 11 tests OK |
| `bash codex/tests/test-bootstrap-gitea-service-account.sh` | PASS | 新增：无站点值时 BLOCKED、源码布局取 `site.credential_root_vm`、installed 布局回退 |
| `bash codex/tests/test-gitea-readonly.sh` | PASS | 新增：缺 `site.orbstack_machine` 报错、`$HOME/<machine>-credentials.txt` 默认值 |
| `bash codex/tests/test-platform-readiness.sh` | PASS | 新增：Linux 主机 exit 2 且不调 broker；`--repo /dev/null`、无 jq 仍 exit 2；`--render-readme` 在 Linux 照旧 |
| Mac：`aisoft-platform-readiness.sh --repo <主 checkout>` | PASS | 六节 PASS，`LIVE_VM_TIMERS PASS enabled=0 failing=0`，exit 0（在候选 worktree 上 `INSTALLED_*` 报 DRIFT items=1，是改了 `issue-session-flow` 而尚未重装的预期状态） |
| VM：`orb -m gitea-ci bash /mnt/mac/private/tmp/issue-416-round2-partial-closeout/codex/tools/aisoft-platform-readiness.sh` | PASS | `HOST ERROR host-mismatch os=Linux` 与指引两行，exit 2 |
| `bash codex/tools/check-installed-drift.sh --source-only` | PASS | `RESULT PASS` |
| `bash codex/tools/usage-bundle.sh --verify --baseline-ref origin/main` | PASS | `VERIFIED 1.12.0 sha256:7e62bc22…`，成员改动只有 `skills/issue-session-flow/SKILL.md` |
| `grep -c 'grep -Fq' codex/tests/smoke.sh` | 80 | 基线 89 → 80 |
| `codex/tools/aisoft check-change-documents --repo .` | PASS | gap=0 |
| `codex/tools/aisoft classify --verify 416` | projected | platform / complex |
| `bash codex/tests/smoke.sh` | 见下 | 见「smoke」 |
| `shellcheck`、`bash -n` | PASS | 改过的 7 个 shell 文件 |

### smoke

SMOKE_PLACEHOLDER

## Acceptance criteria 结果

| AC | 结果 | 依据 |
|---|---|---|
| AC-1 | PASS | 路线图里 `#377 进行中` 与 `` `main` = `1db191e` `` 均无命中；R6、#370 行与审查索引一致；索引补 R9–R14、R16 与 #406 共 10 行，head 只取仓内与 PR 正文，查不到写「未记录」 |
| AC-2 | PASS | 清除项命中归零；ADR D3 例外表 9 个文件；`check-project-leak.py` 要求基线每个文件都在表内，且严格读表（ADR 全文出现围栏、HTML 注释或原始 HTML 块，或登记节有缩进行、第二张表、标题重复，一律失败）；基线只减不增。处置表一处更改：helper README 由清除改为例外（构建输入树，改字节使 VM 报 `helper-build-input-differ`） |
| AC-3 | PASS | 见执行结果的 Mac 与 VM 两行；`06` §1、README、`issue-session-flow` 收尾节与退出条件 3 统一口径 |
| AC-4 | PASS | 9 条 `AGENTS.md` 整句钉子与 1 条残留整句钉子删除，改为 8 个章节 `require_heading`，保留 `` `Other` `` 选项值钉子；80 < 89，基线已调 |
| AC-5 | PASS | 路线图退出条件 4 收口句、「第二轮接受的例外」表（D6 2026-10-20、D9 2026-10-22）、#416 行 |
| AC-6 | PASS | 见「反向证明」 |
| AC-7 | PASS | 1.12.0 发布并 `--verify` 通过 |

### 反向证明

每项都是把被测源码换回修复前版本、跑同一测试：

- 例外登记核对：`check-project-leak.py` 换回基线版，`test_baseline_entry_must_be_registered_in_the_adr` FAIL；换回审查修复前的 `0e0659a0`、`6b03f01c`、`56adde62`、`127e6530` 版，对应新增子用例 FAIL。
- bootstrap 默认根：脚本换回基线版，测试 exit 1；删掉 installed 回退项，测试 exit 1。
- gitea-readonly 默认文件：脚本换回基线版，测试 exit 1。
- readiness 主机拒绝：脚本换回基线版，测试 exit 1；换回 `02f5dd8e`（拒绝晚于 git/jq），测试 exit 1。
- 章节钉子：把 `## 治理文件` 改成 `## 治理` 的副本，章节循环 exit 1；把 `` `Other` `` 改成 `` `GitHub` `` 的副本，值钉子失败。

## 交叉审查

审查方 Codex（`codex exec -s read-only -m gpt-6-astra -c model_reasoning_effort="high"`），实现方 Claude。每轮在 detached 快照 worktree 上审查。

| 轮 | 范围 / head | 结论 | 发现与处置 |
|---|---|---|---|
| T01-1 | `6b585e89..3b7f0d84` | FAIL | P2 例外表解析读进表外行；P3 installed 回退无测试 → `0e0659a0`；同时自查发现 helper README 是构建输入，改为例外 |
| T01-2 | `0e0659a0` | FAIL | P2 围栏内同名标题、四反引号围栏 → `6b03f01c` |
| T01-3 | `6b03f01c` | FAIL | P2 注释与缩进行里的表；P3 #380 守卫整文件豁免 → `56adde62`（严格读表；窄守卫） |
| T02-1 | `02f5dd8e` | FAIL | P2 拒绝晚于 git/jq；P3 合同写 BLOCKED → `fb01792d` |
| T02-2 / T03-1 | `fb01792d` | T02 PASS；T03 FAIL | P2 删掉了 `Other` 选项值；P3 残留 `生产环境只运行` → `8f61b5a4` |
| 全量-1 | `8f61b5a4` | FAIL | P2 标题前打开的注释或围栏包住整张表 → `127e6530`；T04 十行索引、D9 行数与 1.12.0 核对无误 |
| 全量-2 | `127e6530` | REVIEW2_PLACEHOLDER | |

## 遗留风险与未完成项

- 合并后需负责人重装：Mac 与 VM 两台 broker（`bootstrap-gitea-service-account.sh` 随它安装），Mac 技能；之后读回两台 drift 与 Mac readiness。重装 NOT RUN（会话无 sudo）。
- 例外表与基线互相核对，例外表本身由人维护；新增例外仍走 complex Issue。
- PAT 真实轮换（#417）与当前版本 E2E（admin/NewEMaint#324）不在本批。
