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
status: recorded
branch: change/416-round2-partial-closeout
created: 2026-10-22
updated: 2026-10-22
---

# Verification

## 基线与范围

- 基线：`0bcc3cd863afef3425e9dcdda5e1053a3b0ad097`（`origin/main`）。
- 代码候选 head：`82c0355e`（T01 `3b7f0d84`、T02 `02f5dd8e`、T03 `096f09cf`、T04 `8f61b5a4`，其余为审查修复）。本记录之后的 commit 只写本文件与审查索引一行。
- `codex/tools/gitea-pat-helper/README.md` 在 T01 改过又在审查第 1 轮撤回，最终 diff 为零，但 broker 逐提交核对 scope，所以它留在 spec 的 `git_scope` 里（首推曾因此 `SCOPE_DENIED`）。
- 环境：macOS 本机（bash 3.2），`rg` 为真实 `/opt/homebrew/bin/rg`；VM 经 `/usr/local/bin/orb -m gitea-ci`。

- PR 418 的 CI：首跑 run 2100 在 `1abd0ca4` 上红在 `test-bootstrap-gitea-service-account.sh`（Linux runner 上此前用例已留下 `$TMP/credentials`，无站点值用例的「未写入」断言误报）。在 `python:3.12-bookworm` 容器里复现，`a0dde5c1` 改为只检查该用例自己的凭据路径，只改测试；Linux 容器与 Mac 均通过。run 2101 在 `a0dde5c1` 上 success（200s）。这是交叉审查 PASS 之后唯一的非文档改动。

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

在审查快照上从头跑完，均 exit 0、`Codex platform static smoke checks passed.`：T04 `8f61b5a4`（runtime 单测 704 OK）、`127e6530`、`c4a800fb`、`a592ea57`、`bce9262c`、`4be80aa3`，以及最终 `e501d4d5`（代码候选 `82c0355e` 加 verification；runtime 单测 704 OK，漂移夹具 46 OK）。一次在快照 worktree 尚未检出完时启动的运行报文件不存在（exit 127），属操作失误，同一快照重跑通过。

## Acceptance criteria 结果

| AC | 结果 | 依据 |
|---|---|---|
| AC-1 | PASS | 路线图里 `#377 进行中` 与 `` `main` = `1db191e` `` 均无命中；R6、#370 行与审查索引一致；索引补 R9–R14、R16 与 #406 共 10 行，head 只取仓内与 PR 正文，查不到写「未记录」 |
| AC-2 | PASS | 清除项命中归零；ADR D3 例外表 9 个文件；`check-project-leak.py` 要求基线每个文件都在表内，且严格读表（ADR 全文出现围栏、HTML 注释或原始 HTML 块，或登记节出现正文、空行与一张前后空行的表以外的行、第二张表、标题重复，或表缺固定表头、分隔行、行格式不对，或 ADR 全文含空格、制表符、LF 以外的空白或控制字符，一律失败）；基线只减不增。处置表一处更改：helper README 由清除改为例外（构建输入树，改字节使 VM 报 `helper-build-input-differ`） |
| AC-3 | PASS | 见执行结果的 Mac 与 VM 两行；`06` §1、README、`issue-session-flow` 收尾节与退出条件 3 统一口径 |
| AC-4 | PASS | 9 条 `AGENTS.md` 整句钉子与 1 条残留整句钉子删除，改为 8 个章节 `require_heading`，保留 `` `Other` `` 选项值钉子；80 < 89，基线已调 |
| AC-5 | PASS | 路线图退出条件 4 收口句、「第二轮接受的例外」表（D6 2026-10-20、D9 2026-10-22）、#416 行 |
| AC-6 | PASS | 见「反向证明」 |
| AC-7 | PASS | 1.12.0 发布并 `--verify` 通过 |

### 反向证明

每项都是把被测源码换回修复前版本、跑同一测试：

- 例外登记核对：`check-project-leak.py` 换回基线版，`test_baseline_entry_must_be_registered_in_the_adr` FAIL；换回审查修复前的 `0e0659a0`、`6b03f01c`、`56adde62`、`127e6530`、`c4a800fb`、`93578db5`、`25a54f53`、`694b7bc6` 版，对应新增子用例 FAIL。
- bootstrap 默认根：脚本换回基线版，测试 exit 1；删掉 installed 回退项，测试 exit 1。
- gitea-readonly 默认文件：脚本换回基线版，测试 exit 1。
- readiness 主机拒绝：脚本换回基线版，测试 exit 1；换回 `02f5dd8e`（拒绝晚于 git/jq），测试 exit 1。
- 章节钉子：把 `## 治理文件` 改成 `## 治理` 的副本，章节循环 exit 1；把 `` `Other` `` 改成 `` `GitHub` `` 的副本，值钉子失败。

## 交叉审查

审查方 Codex（`codex exec -s read-only -m gpt-6-astra -c model_reasoning_effort="high"`），实现方 Claude。每轮在 detached 快照 worktree 上审查；exact head 是被审查的快照，代码候选之后的 commit 只改本文件。

| 轮次 | 实现方 | 审查方 | exact head | 结论 | 发现与处置 |
|---|---|---|---|---|---|
| T01-1 | Claude | Codex | `3b7f0d841bed2065237db455f7d0cc4cc7e55227` | FAIL | P2 例外表解析读进表外行；P3 installed 回退无测试 → `0e0659a0`；自查发现 helper README 是构建输入，改为例外 |
| T01-2 | Claude | Codex | `0e0659a042e9c3c976b5d498596ab6aa100f0f59` | FAIL | P2 围栏内同名标题、四反引号围栏 → `6b03f01c` |
| T01-3 | Claude | Codex | `6b03f01c4ca1cddfd1c963119119600eeaca122c` | FAIL | P2 注释与缩进行里的表；P3 #380 守卫整文件豁免 → `56adde62`（严格读表；窄守卫） |
| T02-1 | Claude | Codex | `02f5dd8ed1f06c0996ec76e685c8b8078e3fd74f` | FAIL | P2 拒绝晚于 git/jq；P3 合同写 BLOCKED → `fb01792d` |
| T02-2 / T03-1 | Claude | Codex | `fb01792d7e39c81575cbfaad8be4abf46072cf4b` | T02 PASS；T03 FAIL | P2 删掉了 `Other` 选项值；P3 残留 `生产环境只运行` → `8f61b5a4` |
| 全量-1 | Claude | Codex | `8f61b5a4ee43535c080509b44d898a8d6cea0ca2` | FAIL | P2 标题前打开的注释或围栏包住整张表 → `127e6530`；T04 十行索引、D9 行数与 1.12.0 核对无误 |
| 全量-2 | Claude | Codex | `127e65309352539b9109b8c59f93322602ca6abd` | FAIL | P2 反引号 info string、NBSP 闭合行骗过 CommonMark 近似 → `c4a800fb`：ADR 全文禁止围栏、注释与原始 HTML，不再解析 |
| 全量-3 | Claude | Codex | `c4a800fb6c54f192f5b153134a01d558002e4e6f` | FAIL | P2 删掉分隔行的非表格仍被登记；P3 verification 候选 head 过期 → `93578db5`：固定表头、分隔行与两列行格式 |
| 全量-4 | Claude | Codex | `a592ea570c192e8b4b2ed4d56c98d9397e0675d7` | FAIL | P2 分隔行里的 NBSP 让表变成段落仍被登记；P3 本表未用 `03` §7 固定表头与 40 位 SHA → `25a54f53`：登记节只允许 ASCII 空格与制表符；本表改格式 |
| 全量-5 | Claude | Codex | `bce9262cc65bafb3104a6156bd1a00488a571490` | FAIL | P2 `splitlines()` 把 U+2028、VT 当换行，非表格仍被登记 → `694b7bc6`：ADR 只按 LF 切行，全文除空格、制表符、LF 外的空白与控制字符一律拒绝 |
| 全量-6 | Claude | Codex | `4be80aa34aaa17fab71f6f713175d03dbd98262d` | FAIL | P2 带前导空格的 ATX 标题与 Setext 标题能把表划到下一节，D3 仍被当成已登记 → `82c0355e`：登记节改为允许清单（正文、空行、一张前后空行的表），其余行一律拒绝 |
| 全量-7 | Claude | Codex | `e501d4d5bb08af29d4272baed7a5c92caeed4ec5` | PASS | 无 P1/P2/P3；8 个旧绕过变体当前版全部拒绝，另 10 个块语法变体被拒，删除登记行正确失败 |

## 遗留风险与未完成项

- 合并后需负责人重装：Mac 与 VM 两台 broker（`bootstrap-gitea-service-account.sh` 随它安装），Mac 技能；之后读回两台 drift 与 Mac readiness。重装 NOT RUN（会话无 sudo）。
- 例外表与基线互相核对，例外表本身由人维护；新增例外仍走 complex Issue。
- PAT 真实轮换（#417）与当前版本 E2E（admin/NewEMaint#324）不在本批。
