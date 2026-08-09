---
issue: 67
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/67
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - authentication
  - security
  - external-contract
  - shared-core
  - platform-governance
depends_on:
  - 61
status: ready-for-review
branch: change/67
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/68
created: 2026-08-09
updated: 2026-08-09
---

# Git credential protocol compatibility verification

## 环境与版本

- Worktree: `/Users/benque/.codex/worktrees/e23a/AISoftPlatform`
- Branch: `change/67`
- Fresh protected-main baseline: `97445947fff79a4c2db6fa764feb21660e281556`
- Candidate implementation commit: `997f4e4f65045d23368c1eb6053e5d7e20b09e6f`
- Git: `git version 2.50.1 (Apple Git-155)`
- Installed helper: `/usr/local/libexec/aisoft/git-credential-aisoft-host`
- Issue: `#67`，open；initial lifecycle `spec-drafting`，contract resolver 通过后 labels 读回为
  `type/platform` + `complexity/complex` + `approved`

## 实时只读 baseline

| Check | Result | Evidence |
|---|---|---|
| protected `main` API + fresh anonymous fetch | PASS | 两条路径均为 `97445947fff79a4c2db6fa764feb21660e281556`；live branch `protected=true` |
| live required CI | NOT CONFIGURED | `enable_status_check=false`、`status_check_contexts=[]`；不能把本地 PASS 当 remote CI |
| live PR de-dup | PASS | repository `open_pr_counter=0`；PR #63 已人工合并，Issue #61 closed |
| `change/67` de-dup | PASS | 创建本地分支前匿名 `ls-remote --heads` 返回空 |
| Issue #66 isolation | PASS | #66 live state=open；本 Change 未读取或修改其 worktree/branch/Issue |
| repo-local binding | PASS | `credential.useHttpPath=true`、username=`aisoft-platform-agent`、fixed helper 路径精确 |
| live Git credential field-name probe | PASS | 依次为 `capability[]`、`capability[]`、`protocol`、`host`、`path`、`username`、`wwwauth[]`；未记录 values |
| merged helper dry-run replay | FAIL (EXPECTED DEFECT) | exit 128；`CREDENTIAL_PROTOCOL_INVALID: Git credential field is duplicated`；未进入 Keychain、未写远端 |

## Candidate verification

| Command / check | Result | Evidence |
|---|---|---|
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=codex/runtime python3 -m unittest codex.runtime.tests.test_host_access -v` | PASS | 23 tests；ordered multi-values、current shape、unknown arrays、CLI get/store/erase、scalar/malformed/target/identity negatives 全部通过 |
| `PYTHONDONTWRITEBYTECODE=1 bash codex/tests/test-host-access-broker.sh` | PASS | malformed/unknown/duplicate scalar 均在 credential store 前返回 exit 20；installer second-run byte-identical |
| full platform smoke 首轮 | FAIL | 新增 shell assertion 触发 ShellCheck `SC2251`；未误记为 runtime/test PASS，已改为显式 `if` 分支 |
| `PYTHONDONTWRITEBYTECODE=1 bash codex/tests/smoke.sh` 修正后与 exact candidate commit 重跑 | PASS | `997f4e4f65045d23368c1eb6053e5d7e20b09e6f` run 为 `Ran 280 tests in 9.816s`、`OK`，最终输出 `Codex platform static smoke checks passed.` |
| `bash -n` / ShellCheck 0.11.0 | PASS | 修改/相关 helper shell 语法有效且无 finding |
| strict JSON / document resolver / Secret scan / `git diff --check` | PASS | host manifest 可解析；四份语义文档 mapping 精确；高置信 credential/private-key pattern 无命中；无 whitespace error |

## Acceptance criteria 结果

- AC-1：PASS。四个 scalar strict allowlist、required fields、唯一性、malformed/NUL/oversized line 均有负向覆盖。
- AC-2：PASS。`key[]` values 以 tuple 保持顺序；current `capability[]`/`wwwauth[]` 与 future unknown arrays 解析后不参与 route。
- AC-3：PASS。wrong protocol/host/path/username 和 cross-project 均在 resolver 前失败；既有 route 代码未修改。
- AC-4：PASS。synthetic CLI success 只写 private captured pipe；store/erase 为空；真实 Secret 未进入 fixture 或输出。
- AC-5：PASS。23 个 focused tests 覆盖 spec matrix。
- AC-6：PASS。live probe 只保存七个字段名；shell negatives 验证 early fail。
- AC-7：PASS。首轮 ShellCheck finding 已修复，focused、shell、280-test smoke、syntax、ShellCheck、JSON、Secret、diff 全部重跑通过。
- AC-8：PASS。唯一 branch、原子 commits 与唯一 PR #68 已建立；live protection 未配置 required CI，
  final-head status 只读回查不写成 remote CI PASS。
- AC-9：NOT RUN。只允许人工 merge 后执行 exact merged-byte install/no-op/live Git canary。

## Bootstrap、PR 与 remote CI

- Standard fixed-helper push：`FAIL (EXPECTED DEFECT)`；installed helper 在 Keychain 前返回
  `CREDENTIAL_PROTOCOL_INVALID: Git credential field is duplicated`，远端分支仍不存在。
- Compatibility adapter：`PASS`；单条 `git -c` 仅把 helper 临时指向 committed repo-local candidate
  wrapper，仍使用 fixed manifest/service/account 和 strict identity/target check。未记录 protocol values、
  challenge 或 Secret，未把 token 写入 argv、文件、日志或 terminal。初始远端 head 匿名读回为
  `002ad63969b5d82c9e6bd4b5536f2e3829ed430e`。这只是 bootstrap，不是 post-merge fix evidence。
- Unique `Closes #67` PR：`PASS`；PR #68 初始读回为 `change/67@002ad639... -> main`、`open`、
  `merged=false`；本 handoff docs commit 会推进 final head，以后续匿名 read-back 为准。
- Final-head remote status contexts：`NOT RUN`；live protection 当前未配置 required CI，最终 push 后只读回查。
- PR merge：`NOT RUN`；只允许人工执行。

## Post-merge live gate

- Exact merged protected-main SHA/read-back：`NOT RUN`。
- 从 exact merged bytes 重装 broker/helper：`NOT RUN`。
- 第二次安装 no-op：`NOT RUN`。
- `aisoft-platform-agent` feature branch push/read-back：`NOT RUN`。
- rollback：`NOT RUN`；仅当上述 post-merge gate 获得独立执行条件后适用。

## 禁止项核对

- `ci-bot` credential/account/ACL：`NOT ACCESSED / NOT MODIFIED`。
- Gitea ACL/protected main/merge permission、account/PAT create/rotate：`NOT RUN`。
- Issue #66、NewEmaint 或其它项目：`NOT MODIFIED`。
- Docker、VM/service/timer/profile、database、deployment、migration、restart、prune：`NOT RUN`。
