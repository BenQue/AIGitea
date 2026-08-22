---
issue: 142
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/142
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
depends_on: []
status: approved
branch: change/142-loop-pr-url-backfill
created: 2026-08-22
updated: 2026-08-22
---

# Verification

## 环境与版本

- Commit SHA: 见本分支最终 commit（基线 `36adb00`）
- Environment: Mac 交互开发 checkout，worktree `/private/tmp/issue-142-loop-pr-url-backfill`
- Python: 系统 `python3`（3.14），无新增依赖
- 未安装、未部署、未改动 broker；本变更不需要任何重装步骤

## 逐条验收

### AC-1 `pr_url` 写入位置唯一，且两个候选被逐条否决

spec §3 给出裁决（`aisoft-loop backfill-pr-url` 子命令）与两条否决论证：broker 内联（§3.2：broker 完全不写工作树；PR 建成而文件写失败没有可判读中间态）、新 broker typed 操作（§3.3：把无凭据的本地写入放进凭据边界，还要付 6 处枚举点 + 两台重装）。§3.5 额外声明本变更**不**消除那次额外的 commit + push，因为 PR 号只有在推送后才存在。

### AC-2 「哪些文档带 `pr_url`」有唯一答案

裁决：只有 summary。决定性论据是可从代码读出的事实——平台从非 summary 文档只读 `issue`/`branch`/`effective_complexity`/`created` 四个键（spec §2.1 表格），`pr_url` 没有任何消费者。

模板已同步：

```
$ git diff --stat templates/docs/changes/_template/
 templates/docs/changes/_template/plan.md         | 1 -
 templates/docs/changes/_template/spec.md         | 1 -
 templates/docs/changes/_template/verification.md | 1 -
```

`03-Issue-Spec-Plan与单闸门开发流程.md:71`、`skill-for-claude/SKILL.md` 第 3–4 步、`skill-for-codex/references/onboarding-runbook.md:144` 一并同步。

### AC-3 幂等：已有正确值时零 diff

`tests.test_documents.BackfillPrUrlTests.test_repeating_the_backfill_produces_no_diff` 逐字节比对 `read_bytes()`，第二次调用返回 `changed=False` 且文件字节完全不变（实现上根本没有触发写入）。

### AC-4 异值 fail-closed 且不写

`test_a_different_pr_url_is_refused_without_writing`：抛 `ContractError`，并断言文件字节未变。

### AC-5 URL 与 summary 不自洽时报错

`test_a_url_from_another_repository_is_refused`、`test_a_url_that_is_not_a_pull_request_is_refused`（覆盖 `/issues/58`、`/pulls/0`、`/pulls/58/files`、`not-a-url`）、`test_a_summary_without_gitea_url_is_refused`。校验完全离线：前缀由 summary 自己的 `gitea_url` 推导。

### AC-6 对每个 change 目录断言 `resolve-documents` 成功

平台仓自身（本分支）：

```
$ PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli check-change-documents --repo .
PASS: change-documents
PASS: change-pr-url
result: changes=66 pass=2 gap=0
```

首次运行时它并不是绿的——见下面 AC-9 的两条实测发现。

### AC-7 负向：删掉一份 spec 的 front matter，检查变红并指名道姓

真实运行（临时副本，未污染任何 checkout）：

```
$ PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli check-change-documents --repo <tmp>
GAP: change-documents — 138-broker-issue-comments-read/spec-broker-issue-comments-read-260822.md: document must start with YAML front matter
PASS: change-pr-url
result: changes=1 pass=1 gap=1
exit=1
```

变更号与文件名都在。这是 `_document_problems` 先逐文件解析、再退回结构性错误的直接效果——`resolve-documents` 自己给出的消息里没有文件名。

单测：`tests.test_change_audit.test_missing_front_matter_names_the_change_and_the_file`；
`aisoft-project-check.sh` 侧：`test-project-check.sh` 新增用例断言 `GAP: change-documents —` 同时包含目录名与文件名。

### AC-8 负向：`pr_url` 空而 PR 已存在

**在真实数据上命中了 Issue 描述的那个静默漏做**。`admin/LocalWMS`（本地 checkout，`4b2819bc3bf37fd1d96e52dacfc6fd8a5e4f3645`，九个 change 目录）：

```
$ PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli check-change-documents --repo /Users/benque/Projects/LocalWMS
PASS: change-documents
GAP: change-pr-url — 6-contract-errorcode-enum: summary-contract-errorcode-enum-260822.md: status 为 pr-open 但 pr_url 为空
result: changes=9 pass=1 gap=1
exit=1
```

变更 6 正是 Issue 正文点名的那一个（当时撞上 broker 推送死锁 #136 而只推了一次）。此前没有任何东西发现它，是人事后翻文档才看到的；现在一条离线命令就能指出来。

### AC-9 在 LocalWMS 当前 `main` 上如实报告，不为变绿而调整判据

Issue 正文写「#5 与 #12 确实是坏的」，但 Issue 之后追加的评论说明它们已由 LocalWMS 侧 Issue #18 / PR #19 修复。本次实测与评论一致：`change-documents` 在 LocalWMS 上是 **PASS**，红的是 `change-pr-url`（变更 6）。判据没有为了迎合任何一方而调整——两条判据都按 spec §5 写死。

完整 `aisoft-project-check.sh` 在 LocalWMS 上的结果（其余 GAP 均为本变更之前就存在的对齐缺口）：

```
GAP: pointer-sections — 平台指针两节或 CLAUDE.md 与模板不一致
GAP: change-templates — docs/changes/_template 与平台模板不一致
PASS: change-documents
GAP: change-pr-url — 6-contract-errorcode-enum: … status 为 pr-open 但 pr_url 为空
GAP: architecture-lock — .aisoft/architecture.json 缺失
SKIP: labels-readback / ci-context — 未启用 --remote
GAP: delivery-profile — AGENTS.md 未声明明确交付形态
result: pass=1 gap=5 skip=2
```

#### 实现期的两条发现（都已写回 spec，不是绕开）

1. **`docs/changes/58/00-summary.md`**：巡检第一次跑在平台仓自身上时报出 `legacy summary must not declare documents mapping`——`resolve-documents 58` 今天在 `main` 上就是失败的。这正是本变更要拦的缺陷，恰好在平台仓自己。处置见 spec §7.1：删掉那五行冗余映射（与 `LEGACY_DOCUMENTS` 推断结果逐字相同，不丢信息）。
2. **`status: pr-open` 的顺序缺陷**：历史会话在首次推送时就写 `status: pr-open`，而 PR 尚不存在、`pr_url` 必然为空——若不处理，新闸门会让**每个变更的第一次 CI** 因自己的文档变红。裁决见 spec §4.1：首推写真实的前置状态，`backfill-pr-url` 把 `pr_url` 与 `status: pr-open` 一起写下。本变更自己的四份文档就是按新顺序写的（首推 `status: approved`）。

### AC-10 接入两处

- `codex/tools/aisoft-project-check.sh`：新增 `change-documents` 与 `change-pr-url`；用 tab 分隔的 `--porcelain` 读取，避免中文标点被当成字段分隔符；巡检自身崩溃（退出码 > 1 或零输出）报 GAP 而不是 skip——「检查没跑」绝不能读成「仓库没问题」。
- `codex/tests/smoke.sh`：对平台仓自身跑一次。交付闸门给别人之前先让自己过。

`test-project-check.sh` 新增 5 个用例（好目录 PASS / 坏 spec GAP / `pr-open` 空 `pr_url` GAP / 填好后 PASS / 无 `docs/changes` 时 SKIP），既有计数期望同步更新（`pass=6→8`、`pass=4→6`、`pass=5→7`）。

### AC-11 测试全绿

```
$ PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests
Ran 479 tests in 27.080s
OK

$ bash codex/tests/test-project-check.sh
project check tests passed (37 cases)

$ bash codex/tests/smoke.sh
Codex platform static smoke checks passed.   (exit 0)
```

说明：会话内的 `rg` 是 harness shim 函数，`smoke.sh` 的 `command -v rg` 查不到真实二进制会静默退 1；本次运行按既有规避法在 `PATH` 前置了一个可执行 `rg` shim。这是会话环境问题，与仓库无关。

## 模板改动的实际影响（实测，非估计）

对五个已接入 checkout 逐份 `cmp` 平台模板：

| 仓库 | 改动前 `change-templates` | 改动后 |
|---|---|---|
| NewEMaint | 一致 | **不一致（本变更导致）** |
| HSDB | 已不一致 | 不一致 |
| SFMDigitalBoard | 已不一致 | 不一致 |
| rsdesign-new | 已不一致 | 不一致 |
| LocalWMS | 已不一致 | 不一致 |

即：**本变更只让 NewEMaint 一个仓从 PASS 转 GAP**，其余四个在此之前就已经漂移。处置路径是既有的——各仓开自己的小 Issue/小 PR 同步三份模板文件；本变更不代任何目标仓提交。

## 未能进一步核实

- `backfill-pr-url` 对**本变更自己的 PR** 的端到端运行发生在本文件写成之后（PR 必须先存在）。运行结果与产生的 diff 会体现在本分支的回填 commit 里——那次 commit 本身就是这条能力的真实证据。
- 未在任何目标仓 CI 中运行本巡检；接入目标仓 CI 不在本变更范围内。

## 回滚

单个 commit，`git revert` 即可完全回退：新增的两个子命令与一个模块、两处接入、三份模板与三处文档文本改动。未安装任何东西，未改 broker，无需重装或重启。
