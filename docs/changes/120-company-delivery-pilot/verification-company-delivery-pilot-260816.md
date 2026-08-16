---
issue: 120
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/120
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - schema-change
  - security
  - external-contract
  - shared-core
  - cross-module
  - ci-change
  - artifact
  - deployment
  - compatibility
  - rollback
  - platform-governance
depends_on:
  - 121
status: pending
branch: change/120-company-delivery-pilot
pr_url:
created: 2026-08-16
updated: 2026-08-16
---

# Verification：公司两 VM / NewEmaint operator workflow

## 环境与版本

- Baseline：`origin/main` = `718a14f1deb20062ae58ff8c7dd20b3377bd0214`。
- Candidate commit SHA：`NOT RUN`（implementation 尚未完成）。
- Operator bundle/version/checksum：`NOT RUN`。
- Local environment：Mac isolated worktree；fake/disposable filesystem/process fixtures only。
- Company `gitea-ci` / `appserver`、company Gitea/Runner/Registry、NewEmaint production：`NOT RUN`。

## 计划执行结果

| Command / check | Result | Evidence |
|---|---|---|
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=codex/runtime python3 -m unittest codex.runtime.tests.test_company_delivery -v` | PASS | `Ran 15 tests`、`OK`；T01–T03 focused contract/collector/bundle/security tests |
| `bash -n company-delivery/bin/*` | PASS | wrapper shell syntax |
| `shellcheck company-delivery/bin/*` | PASS | 当前环境可用，退出 `0` |
| strict JSON/schema/example parse | PASS | `company-delivery/**/*.json` 均通过 `jq empty`；四种 evidence outcome template 均通过 runtime validator |
| deterministic fake bundle build x2 | PASS | 同输入 archive name/SHA256 完全相同；解包后在 `umask 077` 下重新验证；Docker calls = 0 |
| tamper/wrong SHA/digest/arch/path/mode/Secret negatives | PASS | 全部在任何 target mutation 前 fail closed，且 Secret sentinel 不回显 |
| full runtime unittest discovery | NOT RUN | exact command/count 待实现后记录 |
| `bash codex/tests/smoke.sh` | NOT RUN | exact final-head output 待记录 |
| `git diff --check origin/main` | NOT RUN | candidate whitespace gate |
| no-secret/manual allowlist review | NOT RUN | 不回显任何命中值 |
| protected `main` / required CI / exact head status | NOT RUN | final push 后 typed broker readback |

## Ticket implementation evidence

### T01 — strict contract/model/CLI

- RED：`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=codex/runtime python3 -m unittest codex.runtime.tests.test_company_delivery -v`
  退出 `1`，同一 selector 在 import seam 明确失败：`ModuleNotFoundError: No module named 'aisoft_company_delivery'`。
- GREEN：同一命令退出 `0`，`Ran 6 tests`、`OK`；覆盖 strict documents、unknown field、短 SHA、unsafe path、
  mode/symlink、Secret sentinel、sanitized CLI 与 repository template/compatibility。
- `bash -n company-delivery/bin/aisoft-company-delivery`：PASS。
- `shellcheck company-delivery/bin/aisoft-company-delivery`：PASS（当前环境可用，退出 0）。
- `find company-delivery -type f -name '*.json' ... | xargs ... jq empty`：PASS。
- `git diff --check`：PASS。

### T02 — sanitized read-only inventory

- RED：`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=codex/runtime python3 -m unittest codex.runtime.tests.test_company_delivery.CompanyDeliveryCollectorTests -v`
  退出 `1`，同一 selector 在 collector seam 明确失败：
  `ModuleNotFoundError: No module named 'aisoft_company_delivery.collector'`。
- GREEN：同一命令退出 `0`，`Ran 4 tests`、`OK`；覆盖 `scm-ci`/`appserver-prod` 两 role、固定 read-only argv、
  `0600` 新文件与 `0700` parent、hostname/machine-id fingerprint、timer disabled/inactive、PostgreSQL version
  normalization，以及 probe Secret sentinel fail-closed/no-echo。
- `python3 -m compileall -q -f codex/runtime/aisoft_company_delivery`：PASS；只验证 Python syntax，随后删除本次生成的
  task-owned `__pycache__`，未改用户文件。
- `git diff --check`：PASS。

### T03 — deterministic handoff bundle

- RED：`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=codex/runtime python3 -m unittest codex.runtime.tests.test_company_delivery.CompanyDeliveryBundleTests -v`
  退出 `1`，同一 selector 在 bundle seam 明确失败：
  `ModuleNotFoundError: No module named 'aisoft_company_delivery.bundle'`。
- GREEN：同一命令退出 `0`，`Ran 5 tests`、`OK`；覆盖 clean exact source SHA、artifact-only
  `docker-release/v2`、repeat-build archive SHA equality、portable extraction、full `SHA256SUMS`、single-byte
  tamper、wrong release digest/merge SHA/architecture、unsafe file/parent symlink/mode、dirty source、短 SHA 与
  Secret-bearing release metadata fail-closed/no-echo。
- builder 输入和 payload 均来自 allowlisted tracked paths；archive 固定 mtime/uid/gid/order，sidecar 固定为
  `<archive-sha256>  <archive-name>`；验证结果明确 `docker_calls=0`、`target_facts=NOT_READ`。
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=codex/runtime python3 -m unittest codex.runtime.tests.test_company_delivery -v`：
  PASS，`Ran 15 tests`、`OK`。
- `bash -n company-delivery/bin/aisoft-company-delivery`、`shellcheck company-delivery/bin/aisoft-company-delivery`、
  `git diff --check`：PASS。

### T04 — staged manual runbook 与 live gates

- RED：`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=codex/runtime python3 -m unittest codex.runtime.tests.test_company_delivery.CompanyDeliveryRunbookTests -v`
  退出 `1`；`company-delivery/runbook.md` 与 PASS/FAIL/BLOCKED templates 尚不存在，NOT RUN template 也缺少
  non-live example 标记。
- GREEN：同一命令退出 `0`，`Ran 3 tests`、`OK`；精确解析 Stage `00,10,...,110`，逐 stage 验证前置、
  单阶段人工批准、role、允许动作、预期输出、PASS/FAIL/BLOCKED、停止点、evidence 和回滚边界。
- 静态 fail-closed assertions 覆盖：两台公司 VM、本地 `appserver-test`、Gitea side-by-side/controlled
  upgrade、完整 backup 对象、isolated restore 对账、`pg_restore --list` 不等于 PASS、one-shot inbound、
  protected main/required CI、Runner/Registry 正负验收、首次验收三个自动化入口 disabled/inactive、
  artifact-only zero-target boundary、fixed action/target/full SHA，以及“内网重建但无隔离测试环境”固定
  `BLOCKED`。
- `evidence.pass|fail|blocked|not-run.example.json`：均通过 strict runtime validator；每个都明确为 structure
  example，不是 live evidence。
- focused full module：PASS，`Ran 18 tests`、`OK`；全部 `company-delivery/**/*.json` 通过 `jq empty`；
  `git diff --check`：PASS。

## Acceptance criteria 结果

| AC | Result | Evidence |
|---|---|---|
| AC-1 | PASS（local fake） | 两 role collector、固定只读 argv、脱敏、mode 与 fail-closed tests 已通过；公司 inventory 仍 `NOT RUN` |
| AC-2 | PASS（contract） | Stage 00–110 completeness parser 证明每阶段包含批准、停止、evidence 与回滚合同 |
| AC-3 | PASS（local fake） | 两次相同输入产生相同 archive SHA；tamper/wrong SHA/digest/arch/path/mode 全部 fail closed |
| AC-4 | PASS（local） | strict inventory/handoff/evidence contracts、templates、full `SHA256SUMS` 与 payload identity 已验证 |
| AC-5 | PASS（contract） | side-by-side/controlled-upgrade decision table、完整 backup coverage、isolated restore object reconciliation 已固定；live drill `NOT RUN` |
| AC-6 | PASS（contract/local fake） | artifact-only zero-target tests 与不同 bytes/rebuild-without-isolation `BLOCKED` 已固定；真实 NewEmaint/company verification `NOT RUN` |
| AC-7 | PASS（contract） | one-shot/bootstrap/protection/CI/Runner/Registry 正负矩阵与 disabled/inactive 初验边界已固定；company checks `NOT RUN` |
| AC-8 | PASS（contract） | fixed action/`newemaint-prod`/full SHA、普通 Runner 禁权和 app rollback/DB restore 分离已固定；production `NOT RUN` |
| AC-9 | NOT RUN | topology docs update/review pending |
| AC-10 | NOT RUN | focused/full validation pending |
| AC-11 | NOT RUN | unique PR/final-head readback pending；merge human-only |
| AC-12 | PASS（当前边界） | 未连接公司内网，未执行任何 company/live/deploy mutation |

## 重复部署

- Local deterministic bundle build 第一次：`NOT RUN`。
- Local deterministic bundle build 第二次：`NOT RUN`。
- 公司 test/prod 第一次部署：`NOT RUN`。
- 公司 test/prod 同 SHA 第二次：`NOT RUN`。

bundle build/verify 是制品准备，不是 deployment，不得写成公司环境 PASS。

## 故意失败与回滚

- Fake/local checksum tamper、wrong full SHA/digest/architecture、unsafe path/mode、Secret sentinel：`NOT RUN`。
- Company Gitea install/upgrade failure：`NOT RUN`；未来只按已批准 stage 的 snapshot/side-by-side 回滚。
- NewEmaint application rollback：`NOT RUN`。
- PostgreSQL isolated restore drill / production restore：`NOT RUN`；本 Change 不执行数据库操作。

## Company/live 状态矩阵

| Scope | Result | 边界 |
|---|---|---|
| 两台公司 VM inventory | NOT RUN | collector 仅在未来由人运行 |
| 公司 Gitea side-by-side / controlled upgrade | NOT RUN | 未连接、未安装、未升级 |
| backup / isolated restore drill | NOT RUN | 未读取或修改数据 |
| GitHub inbound one-shot / company bootstrap | NOT RUN | 未访问公司网络 |
| company protected main / required CI | NOT RUN | 仅本地 Gitea protection 已读回，不可外推 |
| company act_runner / Registry/cache | NOT RUN | 未安装、未验证 |
| exact NewEmaint `docker-release/v2` handoff | NOT RUN | 真实 release bytes 未作为输入 |
| company artifact-only verification | NOT RUN | 不以 fake/local tests 替代 |
| appserver target readiness / Nginx / PostgreSQL | NOT RUN | 未连接 production target |
| migration / activation / health / rollback / restore | NOT RUN | 未部署；future human-only stage |
| sync timer / Actions auto deploy / production gate enable | NOT RUN | 必须保持 disabled/inactive，未来另批 |

## 遗留风险与未完成项

在 implementation、review、final-head push 与 PR/CI readback 完成前，本文件除明确的当前范围边界外不记录
PASS。不得把 source、merged PR、local fake tests、zero-context aggregate status 或 DockerLab 历史结果改写为
公司 Gitea、Runner/Registry、AppServer、数据库或 production 成功。
