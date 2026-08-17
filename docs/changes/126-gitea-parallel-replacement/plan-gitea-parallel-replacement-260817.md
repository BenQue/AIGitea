---
issue: 126
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/126
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
  - 120
  - 124
status: approved
branch: change/126-gitea-parallel-replacement
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/127
created: 2026-08-17
updated: 2026-08-17
---

# Implementation plan：greenfield systemd Gitea 并行替换

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | inventory v2 + transition v1 strict contracts、schemas、templates 与 RED/GREEN tests（AC-1、AC-3、AC-4） | - | pending |
| T02 | Docker legacy/candidate collision/resource 的 read-only collector vertical slice（AC-1、AC-2） | T01 | pending |
| T03 | transition binding、Stage 50 legacy pre/post invariant 与 CLI vertical slice（AC-3、AC-5） | T01、T02 | pending |
| T04 | compatibility、Stage 10–50 runbook、operator 1.1.0 和 authority docs 收口（AC-4、AC-6、AC-7、AC-8） | T03 | pending |
| T05 | full verification、deterministic bundle、security review 与 PR/CI handoff（AC-7、AC-9、AC-10、AC-11） | T04 | pending |

每个 ticket 先写同一 seam 的失败测试，再做最小实现、focused verification 与 `#126 Txx` 原子 commit。
任一实现要求读取 raw company data、增加 mutation command、改变 fixed target tuple 或让 Stage 10 实际运行，
必须停止并升级给人。

## T01 — Versioned contract 基座

- 将 runtime inventory contract 升级为 `company-delivery-inventory/v2`，保留 host/tool/unit strict validation，
  增加 `scm` role projection、preflight/post-install mode、legacy/candidate/resource fixed enums。
- 新增 `company-delivery-gitea-transition/v1` loader/schema/template，固定 decision、target identity、stage map、
  inventory/baseline/FQDN checksums 和 automation disabled states。
- 更新 inventory example/schema，增加 JSON parse/runtime parity tests；覆盖 unknown field、role/scm mismatch、
  wrong enum/path/port/version/checksum、greenfield skipped-stage fake PASS 与 controlled-upgrade prerequisite。
- 不修改 handoff/evidence v1；历史 1.0.1 bytes 不做 in-place rewrite。

## T02 — Safe coexistence collector

- `collect-inventory --role scm-ci` 强制 typed `--mode preflight|post-install` 与
  `--legacy-gitea-http-port <1..65535>`；`appserver-prod` 拒绝 SCM-only options。
- 固定 Docker probe：`docker ps --filter status=running --filter publish=<port> --format {{.ID}}`；只接受恰好
  一个 hex ID 并立即 fingerprint。zero/multiple/malformed/failure 分别投影为 fixed enum/reason，不保存原文。
- 固定 loopback `/api/v1/version` probe，只接受 bounded JSON 与 semver；注入 fake HTTP seam，测试不得访问
 真实 network。
- 对固定 3000/55432 做 loopback port state；对固定 binary/config/data/log/PG data path 做 no-name resource
  state；`lstat` symlink/permission/error 为 unsafe/unknown。
- preflight/post-install 的 PASS predicates 在写文件前闭合；Sensitive output、timeout、unexpected ID、resource
  collision 与 legacy unhealthy 都只产生 fixed pending codes。

## T03 — Transition/legacy invariant CLI

- 新增 `verify-gitea-transition --input --scm-inventory --appserver-inventory`，验证 protected regular files、
  SHA-256 binding、role/outcome/mode、fixed target tuple、legacy baseline 与 exact stage map。
- 新增 `verify-legacy-health --transition --post-inventory`；只接受 greenfield receipt + post-install scm-ci
  inventory，并比较 presence/health/version/baseline，返回 sanitized machine JSON。
- 正向用例固定 greenfield 00/10/20 PASS + 30/40/50 NOT RUN；负向覆盖 fake PASS、inventory tamper、wrong role、
  preflight collision、legacy drift/unhealthy、new unit state wrong、Secret sentinel/no-echo。
- CLI 不接受 URL、container name/ID、path、unit、candidate port、command、credential 或 mutation action。

## T04 — Runbook、compatibility 与 operator 版本

- compatibility matrix 增加 greenfield contract：exact upstream versions/checksums、identities、units、paths、
  loopback ports、disabled gates、legacy mutation denylist；revision bump。
- 将 Stage 10 改为 inventory v2；Stage 20 加 `greenfield-parallel-replacement`；Stage 30/40 对 greenfield 明确
  NOT RUN；Stage 50 使用 alternate prerequisites 与 pre/post health gate，controlled upgrade 仍走 backup/restore。
- 更新 `company-delivery/README.md`、平台 README、07、12-Linux、13：新实例先并行承载新仓库，legacy migration/
  phase-out 独立 Change，当前 company Stage 10+ NOT RUN。
- `company-delivery/VERSION` bump `1.1.0`；更新 version assertions 和 integration harness basename contract。
- 文档不得出现真实公司 hostname/IP/FQDN/port/config；只使用 `scm-ci`、`appserver-prod` 和 fixed candidate tuple。

## T05 — Verification 与交付

- focused module、full unittest discovery、`bash codex/tests/smoke.sh`、JSON parse、wrapper `bash -n`、ShellCheck
 （可用时）、`git diff --check origin/main`、no-secret scan 全部执行并记录真实结果。
- 用 local fake release 从 exact clean candidate commit 构建两次 1.1.0 bundle，要求 archive checksum 相同；
  解包后验证 handoff，证明 transition schema/template 在 payload manifest 内；tamper 必须 fail closed。
- 做 Standards/Spec 双轴 review；发现问题用 focused regression 修复，不把 local fake 结果写成 company PASS。
- typed broker 推送 exact branch，创建唯一 PR；PR body 恰一行 `Closes #126`；回读 PR head/body/state、protected
  main、required CI 和 Actions exact head，停止在人工 merge gate。

## Expected touch points

- **T01–T03**：`codex/runtime/aisoft_company_delivery/{contract,collector,cli}.py`、
  `codex/runtime/tests/test_company_delivery.py`、`company-delivery/schema/`、`company-delivery/templates/`。
- **T04**：`company-delivery/{VERSION,README.md,runbook.md}`、
  `company-delivery/compatibility/newemaint-company-pilot-v1.json`、`README.md`、
  `07-内网与生产平移路线.md`、`12-Linux-GitHub-Gitea-双服务器自动部署方案.md`、
  `13-项目结果迁移与内网切换实施手册.md`、real-release harness version assertion。
- **T05**：本 Change 的 summary/spec/plan/verification；只生成 repo-external disposable bundle evidence，不提交
  archive。
- 禁止触碰：公司主机、credential/profile、live Gitea/DB/service、NewEmaint repository/release、protected main。

## 数据库迁移

无。source 只描述未来独立 PostgreSQL cluster/database/role contract；T01–T05 不连接、创建、读取、备份、
恢复或删除任何真实数据库。Stage 50 database mutation 仍是未来新的人工批准。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | inventory v2 parser/collector focused tests；role/scm/mode completeness matrix |
| AC-2 | fake Runner/HTTP/port/path probes；fixed argv assertions；malformed/multiple/secret/no-echo negatives |
| AC-3 | transition schema/runtime parity；two inventory checksum binding；exact stage-map negatives |
| AC-4 | compatibility constants vs runtime/docs static assertions；official checksum source review |
| AC-5 | `verify-legacy-health` baseline equality positives + presence/version/health/fingerprint drift negatives |
| AC-6 | runbook/static assertions for SSH/Runner/timer/Actions/gate/DNS/TLS/import disabled or NOT RUN |
| AC-7 | operator version/bundle payload assertions；two-build repeatability；tamper/no-secret checks |
| AC-8 | Stage 10–50 completeness parser + human review of greenfield/upgrade fork and rollback allowlist |
| AC-9 | focused/full unittest、smoke、JSON、bash、ShellCheck、diff、dual-axis review |
| AC-10 | broker branch/PR/head/body/protection/status readback；no merge operation |
| AC-11 | verification matrix and source scan prove every company/live stage remains NOT RUN |

## 部署与回滚

本 Change 不部署。local fake bundle build/verify 重复两次只是 portable artifact 验证。公司 Stage 10、20、30、
40、50，Gitea/PostgreSQL install、service enable/start、health、repo bootstrap、DNS/TLS 和 production 全部
`NOT RUN`。

source rollback 为单 PR revert。未来 Stage 50 的运行/回滚不由本 PR 执行；其唯一 rollback allowlist 是停止并
隔离新 units/namespace，legacy Docker Gitea 不得被触碰。数据库删除/restore 和 legacy phase-out 始终需要
新的人工决定。
