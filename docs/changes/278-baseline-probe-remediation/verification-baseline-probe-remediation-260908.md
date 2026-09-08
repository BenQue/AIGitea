---
issue: 278
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/278
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - schema
  - security
  - external-contract
  - shared-core
depends_on: []
status: pending
branch: change/278-baseline-probe-remediation
created: 2026-09-08
updated: 2026-09-08
---

# Verification · #278 baseline probe remediation

## 基线与范围

- 实现提交：T01 `52ff180`、T02 `dc676de`、T03 `848c51f`；最终 T04 文档提交的完整 head 由本地 candidate state 与 review bundle manifest 固定。
- 基线：`origin/main = 874e7169d9f8efbfe707114e71992e5d4333138f`。
- 环境：Mac 本地隔离 worktree `/private/tmp/issue-278-baseline-probe-remediation`；公司 installed/live 不可从开发机访问。
- 本记录负责证明：AC-1 至 AC-10 的 source/local compatibility、安全边界、bundle 可复核性及 installed/live 分层。

## 改动前一次性证据

| Observation | Result | Boundary |
|---|---|---|
| NewEMaint #79 v2 envelope offline verify | PASS（结构）/ BLOCKED_EXTERNAL（采用） | schema、checksum、pins 与 receipt 一致；不代表 current 事实满足 profile |
| Gitea service | PASS | `enabled + active`；仅说明 systemd 状态 |
| Gitea binary | 现场事实 PASS / collector BLOCKED | 实际输出使用小写 `gitea version 1.26.4 built with ...`；现 regex 只接受大写前缀 |
| PostgreSQL service | 现场事实 GAP / collector BLOCKED | `enabled-runtime + active`；现 schema 无法表达；不得提升为持久 enabled |
| Gitea listener/health/API | GAP / BLOCKED | 8888 无监听，两个固定 GET 均 `ConnectionRefusedError`；不扫描其它端口 |
| Runner unit | GAP | `not-found + inactive`；Runner activation 不在本 Issue |
| UFW | BLOCKED | 非特权调用 rc=1、stdout 为空；`false/0` 是空输出解析默认值，不是防火墙事实 |

以上为用户经独立授权从公司现场回传的脱敏结果；本 Issue 不保存 host hash、内部地址、配置、规则、日志或 Secret，也不把它们重解释为平台 source PASS。

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| broker open-Issue duplicate check | PASS | 创建前 `count=0` |
| broker create/read/labels/comments for #278 | PASS | Issue #278 open；`needs-analysis`；正文回读一致；comments=[] |
| broker `git.fetch.main` | PASS | project=`aisoft-platform`；`origin/main=874e716…` |
| analyzer result validation/render | PASS | `platform / complex / change / manual`；slug=`baseline-probe-remediation`；required summary/spec/plan/verification |
| 合同/启动确认 | PASS | 用户明确批准 exact #278 / branch / spec / plan；Issue/comments 重新读回无冲突 |
| classification/lifecycle projection | PASS | typed `gitea.issue.labels.classify` 与 `.set` 分别投影，再回读 `approved / complexity/complex / type/platform` |
| T01 compatibility tests | PASS | baseline v1+v2：62 tests；2.0.0/2.0.1、严格前缀、runtime enablement、异常 rc |
| targeted tests run 1 | PASS | 79 tests，3.824s；`/private/tmp/issue-278-validation/targeted-1.log` |
| targeted tests run 2 | PASS | 79 tests，3.821s；`/private/tmp/issue-278-validation/targeted-2.log` |
| full runtime unittest discover | PASS | 813 tests，86.609s；`/private/tmp/issue-278-validation/runtime-full.log` |
| smoke sandbox | SANDBOX_PATH_BLOCKED | registry-preflight fixture 绑定 127.0.0.1 临时端口被 PermissionError 拒绝；`/private/tmp/issue-278-validation/smoke.log` |
| smoke host / default locale | FAIL（既有环境兼容） | Bash 3.2 + C.UTF-8 将中文标点并入 REGISTRY 变量名；registry fixture 负向失败；`smoke-host.log` / `registry-trace.log` |
| registry fixture / C locale | PASS | `LC_ALL=C bash codex/tests/test-registry-preflight.sh`；断言/source 未改；`registry-c-locale.log` |
| smoke host / C locale | PASS | `LC_ALL=C bash codex/tests/smoke.sh` exit 0；813 tests，82.177s；static smoke checks passed；`/private/tmp/issue-278-validation/smoke-host-c.log`；不等同默认 locale PASS |
| semantic documents | PASS | 128 changes；change-documents 与 change-pr-url，gap=0 |
| git diff --check | PASS | 实现与文档无 whitespace error |
| v1 exact bytes | PASS | collector SHA-256 `3561d2f1fc607cdee1ba4688489645db1b2142cf57cc4d99433c35b1f33a7a88`；schema SHA-256 `98663edac823c465600a8d0b01ab71778144a7372e146728a5702310ec39b8c6`；与 base bytes 相同 |
| diagnostic review bundle | PASS（local） | NewEMaint #79 现有 canonical profile；T03 exact commit 预审 build/verify 均 PASS，6 files，0700/0600；`/private/tmp/issue-278-validation/review-bundle` |
| final bundle handoff | 独立 exact-head 回执 | T04 提交后在 `/private/tmp/newemaint-79-02` materialize；该包 manifest 与 `/private/tmp/issue-278-validation/final-bundle-receipt.json` 为最终 source/digest/build/verify 事实源，不在文档内自引用提交 SHA |
| installed / company live | NOT RUN | 无安装、拷贝、公司诊断执行或现场 mutation |
| push / PR / remote CI / merge | NOT RUN | 固定 AWAITING_PR_CONFIRMATION / manual |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | PASS（source/local） | 2.0.0/2.0.1 保留原始 collector pins 离线 verify；v1 两文件 byte-equality |
| AC-2 | PASS（source/local） | 严格大小写前缀成功 fixture；错误产品名、多行、非数值、超范围版本拒绝 |
| AC-3 | PASS（source/local） | enabled-runtime + active = GAP；未知状态与异常返回码 BLOCKED |
| AC-4 | PASS（source/local） | 独立 envelope/closed schema；全部 pins、两个不同 v4 UUID、freshness、checksum、receipt 篡改负例 |
| AC-5 | PASS（source/local） | exact property argv；enum/数值上限/重复或额外 property 负例；PID 只返回 yes/no |
| AC-6 | PASS（source/local） | 固定 app.ini 路径；symlink、目录、FIFO、0666、超限、格式错误拒绝；只输出四个 yes/no |
| AC-7 | PASS（source/local） | UFW active/inactive、规则数归一化；权限/空输出/缺失元数据/未知格式 BLOCKED/null |
| AC-8 | PASS（source/local） | AST 固定命令/文件/API 审查；subprocess stdin/stderr/env/4 秒 timeout/kill/超限测试；stdout/stderr/schema/manifest Secret sentinel 零回显 |
| AC-9 | PASS（source/local） | disposable Git fixture；exact commit materialization；source/object/hash/profile/schema/mode/file-set drift 拒绝；NewEMaint profile 本地 build/verify |
| AC-10 | PASS（source/local） | targeted 连续两次 79/79、full runtime 813/813；host `LC_ALL=C` smoke exit 0；默认 locale 失败保留；所有现场操作 NOT RUN |

## 遗留风险与未完成项

- #278 已获合同/启动确认；最终 PR 提交仍等待绑定 exact Issue/branch/manual policy 的第二确认。
- 不修改或追溯改写 NewEMaint #79 的旧 envelope；平台 merge 后必须由项目仓另行 repin、重新授权并使用新 UUID。
- Gitea 8888、PostgreSQL persistent enablement、Runner 与 UFW owner review 是现场整改/审核事项，不由本 source PR 执行。
- 公司诊断、安装、service/UFW/Runner/database mutation、PR merge 全部 NOT RUN。


## 执行边界与回滚

所有 host 观察测试均为注入 fixture 或本地临时文件/子进程，未连接公司服务器。builder 使用 NewEMaint 已有 profile 的只读副本，未更新 #79 platform pin、PR #81、服务、防火墙、Runner 或数据库。source 回滚为最终 PR revert；现场没有本 Issue 引入的状态。

首次 sandbox broker read 为 `TRANSPORT_ERROR`，相同 typed 操作在获准 host 执行上下文成功；首次把 classification 参数混入 lifecycle 操作被 `ARGUMENT_MISMATCH` 拒绝（零写入），核对 contract 后改用两个独立 typed operation 并成功回读。Bash 3.2 locale 失败由既有脚本失败提示中的无花括号变量后接中文标点触发，以测试进程 `LC_ALL=C` 独立复验通过；未扩大 #278 去修改该既有 CI 脚本。Git 本地 index.lock 的 sandbox 阻止通过授权的 exact worktree 本地提交解决；未绕过 broker、扩大权限或安装工具。

最终 candidate state 保存在本地独立 project namespace `/private/tmp/issue-278-validation/state/projects/aisoft-platform/issues/278.json`，stage 固定 `awaiting_pr_confirmation`。这是当前交互任务的本地交接状态，不代表 VM timer/controller 被启用。
