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
status: approved
branch: change/120-company-delivery-pilot
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/123
created: 2026-08-16
updated: 2026-08-16
---

# Implementation plan：公司两 VM / NewEmaint operator workflow

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | strict schema/model/CLI 基座与 RED security/contract tests（AC-3、AC-4、AC-6） | - | completed |
| T02 | 两 role 脱敏 read-only inventory vertical slice（AC-1） | T01 | completed |
| T03 | deterministic builder、checksum/handoff/evidence validation vertical slice（AC-3、AC-4、AC-6） | T01 | completed |
| T04 | Stage 00–110 runbook、Gitea/backup/restore/inbound/Runner/Registry/fixed-target 合同（AC-2、AC-5、AC-7、AC-8） | T02、T03 | completed |
| T05 | README/07/12/13 拓扑收口、全量验证、bundle candidate、唯一 PR/CI handoff（AC-9、AC-10、AC-11、AC-12） | T04 | completed（PR #123；required CI `NOT CONFIGURED`；exact final-head Actions 状态由 broker 回读并写入 Issue） |

每个 `$implement #120 Txx` 只推进当前 frontier；同一 ticket 先写失败测试，再做最小实现、focused 验证、
原子 commit。发现 schema/安全/部署方向与 Spec 冲突时立即停止，不自行扩大合同。

## T01 — Contract model 与 fail-closed CLI

- 新增 `company-delivery/VERSION`、三个 strict JSON schema、compatibility matrix 与无 Secret example templates。
- 新增 stdlib-only `aisoft_company_delivery` runtime：strict JSON loader、unknown-field/type/pattern/enum/duplicate
  path 拒绝、SHA256、safe-relative-path、mode/no-symlink 与 Secret sentinel scanner。
- 新增固定 CLI/wrapper；不得接受 raw command、URL、credential path、service name、shell expression、任意
  target path 或 mutation action。
- RED matrix 至少覆盖：unknown field、short SHA、mutable digest、wrong role/arch、absolute/`..`/duplicate path、
  symlink、group/world writable、Secret sentinel 与 raw status 值。

## T02 — Inventory vertical slice

- 实现 `collect-inventory --role scm-ci|appserver-prod --output <new-file>`；output parent 必须已存在且安全，
  不覆盖 symlink/非 regular target，最终 mode `0600`。
- 固定 probe：OS ID/version、kernel/arch、CPU/memory/root free 数值、hostname/machine-id SHA256 fingerprint、
  allowlisted tool semver 与 role-specific systemd unit `enabled/active` 状态。
- 版本 probe 只保留 semver；systemd 只保留 enum；任何 raw output 不进入 JSON 或错误日志。
- fake PATH/systemctl fixtures 验证两个 role、命令缺失、无法解析、Secret-bearing stdout/stderr、失败退出码、
  no-network/no-mutation command allowlist。

## T03 — Handoff、bundle 与 evidence vertical slice

- 实现 inventory/handoff/evidence validators 与 fixed codes，校验 schema、scope/status、Secret、permissions、
  exact file bytes、release/compatibility identities。
- builder 只接受 repo root、exact source SHA、explicit release root、output directory、显式 UTC timestamp；先验证
  clean `HEAD==source_sha` 与 release artifact，再复制 allowlisted operator/sync/docker-release bytes。
- 生成排序 `SHA256SUMS`、handoff manifest、deterministic tar 与相邻 archive checksum；mtime/uid/gid/order 固定。
- fake `docker-release/v2` fixture 覆盖两次构建同 checksum、单 byte tamper、wrong digest/SHA/arch、不同 release
  bytes、Secret sentinel、unsafe mode/path。测试不得访问 Docker、network、target profile 或 Secret。

## T04 — 人工 runbook 与 live gates

- 写 Stage 00–110，每阶段固定：输入、human approval record、role/host、命令性质、预期输出、PASS 条件、
  BLOCKED 条件、stop point、rollback、evidence template；明确一次只批准一个阶段。
- Gitea Gate：inventory-driven side-by-side vs controlled upgrade；DB/config/keys/repositories/LFS/packages/
  attachments/external storage 完整 backup；隔离 restore 后做对象级对账，不能以 dump 可读替代。
- SCM Gate：GitHub one-shot reconcile、company Gitea bootstrap/protection/required CI、Runner/Registry 正负验证；
  timer/Actions auto deploy/production gate 保持 disabled/inactive。
- Release Gate：`scm-ci` 仅 artifact-only；`appserver-prod` 先 read-only target readiness，未来 production action
  只经 fixed gate。公司要求重建但无隔离 test 时固定 BLOCKED。
- evidence 回流仅含 schema-approved 脱敏 JSON、checksums 与引用；禁止日志原文、Secret、host address。

## T05 — 权威文档、验证与交付

- README、07、12-Linux、13 明确此 pilot 为“两台公司 VM + 本地 DockerLab”，三 role capability 不变；清理
  “公司必须有 appserver-test VM”“公司侧内网重建不同 bytes 后沿用本地测试证明”等冲突文本。
- 把新增 wrapper 加入 `codex/tests/smoke.sh` 的 `bash -n`、ShellCheck 与 JSON parse；runtime tests 由现有
  unittest discovery 自动纳入。
- 从 exact candidate head + fake release 生成两次可重复 bundle evidence；真实 NewEmaint release/company
  actions 保持 NOT RUN。执行 full smoke、diff/check、no-secret review 与双轴 code review。
- 每个 ticket 原子提交后只用 typed broker push exact branch；最终创建唯一 PR，PR body 恰一行
  `Closes #120`，读取 protected main、required CI 与 exact head status，停在人工 merge gate。

## Expected touch points

- **T01–T03**：`company-delivery/{VERSION,README.md,bin/,schema/,templates/,compatibility/}`、
  `codex/runtime/aisoft_company_delivery/`、`codex/runtime/tests/test_company_delivery.py`。
- **T04**：`company-delivery/runbook.md` 及模板/fixtures；只引用、不修改 `sync/` 与 `docker-release/` runtime。
- **T05**：`README.md`、`07-内网与生产平移路线.md`、
  `12-Linux-GitHub-Gitea-双服务器自动部署方案.md`、`13-项目结果迁移与内网切换实施手册.md`、
  `codex/tests/smoke.sh` 与本 Change 四份 mapped docs。
- 禁止触碰：`AGENTS.md`、credential/profile live files、Gitea/Runner live config、NewEmaint repo、公司主机。

## 数据库迁移

无。本 Change 不连接或修改任何 PostgreSQL/Gitea DB。runbook 中 backup、isolated restore、application
migration 与 database restore 都是未来独立批准阶段，当前 verification 固定 `NOT RUN`。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | focused collector unittest；fake PATH/probe allowlist；schema/mode/no-secret assertions |
| AC-2 | Stage 00–110 completeness parser + human review，逐 stage 验证 prerequisites/stop/evidence/rollback |
| AC-3 | focused bundle unittest；two-build checksum equality；tamper/short SHA/wrong digest/arch/path negatives |
| AC-4 | strict schema/template validation；evidence status/scope/section matrix |
| AC-5 | runbook decision table + backup coverage + isolated restore acceptance review |
| AC-6 | fake artifact-only validator call-count/forbidden-input tests；rebuild-without-isolated-test BLOCKED case |
| AC-7 | runbook positive/negative matrix；static assertion timer/auto deploy remain disabled/inactive |
| AC-8 | fixed action/target/full SHA review against existing `aisoft_release.gate` contract；no generic runner surface |
| AC-9 | `rg` conflict scan + four-document topology review |
| AC-10 | focused unittest；`bash -n company-delivery/bin/*`; ShellCheck if available；full runtime suite；`bash codex/tests/smoke.sh`; `git diff --check origin/main` |
| AC-11 | broker branch/PR/head/body/protection/status readback；no merge operation |
| AC-12 | mapped verification environment matrix，company/live rows all `NOT RUN` |

## 部署与回滚

本 Change 无部署。Stage 00 的 fake/local bundle verification 可重复两次；这不是部署。真实 Gitea/Runner/
Registry、backup/restore、AppServer、database、Nginx、test/prod deployment 与 service/timer action 全部
`NOT RUN`。

source 回滚为单 PR revert。若未来公司人按 runbook 执行，必须只回滚当前批准 stage：Gitea upgrade 回到
isolated-restore 已证明的 snapshot；application 回到 previous release；database restore 仍需新的人工决定。
