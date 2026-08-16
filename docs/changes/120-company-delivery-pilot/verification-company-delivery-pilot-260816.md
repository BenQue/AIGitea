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
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=codex/runtime python3 -m unittest codex.runtime.tests.test_company_delivery -v` | NOT RUN | focused contract/collector/bundle/security tests |
| `bash -n company-delivery/bin/*` | NOT RUN | shell syntax |
| `shellcheck company-delivery/bin/*` | NOT RUN | 仅环境可用时运行 |
| strict JSON/schema/example parse | NOT RUN | `company-delivery/**/*.json` |
| deterministic fake bundle build x2 | NOT RUN | exact archive SHA equality；不访问 Docker/network |
| tamper/wrong SHA/digest/arch/path/mode/Secret negatives | NOT RUN | 全部应在 mutation 前 fail closed |
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

## Acceptance criteria 结果

| AC | Result | Evidence |
|---|---|---|
| AC-1 | NOT RUN | implementation/focused tests pending |
| AC-2 | NOT RUN | runbook review pending |
| AC-3 | NOT RUN | deterministic bundle tests pending |
| AC-4 | NOT RUN | schema/template validation pending |
| AC-5 | NOT RUN | Gitea decision/backup/restore contract review pending |
| AC-6 | NOT RUN | exact-byte negatives pending；真实 NewEmaint artifact 不在本仓 |
| AC-7 | NOT RUN | inbound/SCM contract review pending；company live checks remain NOT RUN |
| AC-8 | NOT RUN | fixed target contract review pending；production remains NOT RUN |
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
