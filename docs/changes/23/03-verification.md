---
issue: 23
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/23
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - security
  - shared-core
  - ci-change
  - external-contract
  - compatibility
  - migration
  - platform-governance
depends_on: []
status: blocked-external
branch: change/23
pr_url:
created: 2026-08-02
updated: 2026-08-02
---

# Verification

## 环境与版本

- Source baseline：`origin/main@b806317cc87a58049719fff103af2c9d7c14ed56`
- Approved planning baseline：`change/23@9ad75b85971fc58e238572d6f8a406e2a0b5b0e8`
- Candidate branch：`change/23`，跟踪 `origin/change/23`；implementation commits
  `f4f76fc`、`d86e61e`，governance/verification commit `02c2749`
- Live Issue readback：open；labels `approved`、`complexity/complex`、`type/platform`；无评论
- Official lifecycle evidence：PASS，逐 component 使用 Context7 单概念查询并以官方/upstream
  source readback；记录见 `architecture/evidence/official-sources.md`
- Reference projects：NewEmaint authority
  `gitea/main@ecbdc674fde1f785cafdee92c6ee88c691104a34`；Windows/SQLite synthetic reference
- Server inventory：**BLOCKED_EXTERNAL**。OrbStack 当前 `Stopped`，`gitea-ci`/`prod-sim`
  read-only SSH 均拒绝授权；未启动 VM、未读取 Secret/业务数据、未修改服务器。SSH 首次连接只在
  Mac `known_hosts` 接受了 `prod-sim` host key。

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| planning contract parse + AC map | PASS | `load_contract` 通过；14 条 AC 全部映射 |
| catalog/schema/profile fixtures | PASS | 24 components、3 profiles；valid/invalid Schema/runtime fixtures 通过 |
| `PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests -p 'test_architecture_*.py' -v` | PASS | 26 tests；strict JSON、schema、semantic、lock、CLI、governance |
| validator/lock/CLI tests | PASS | unknown/duplicate/range/EOL/prohibited/sunset/expiry/digest/tamper/drift/source freshness/Secret 全覆盖 |
| installer repeatability | PASS | `bash codex/tests/test-architecture-install.sh` 两次 manifest byte/hash equality；不创建项目 declaration/lock |
| shell syntax / ShellCheck | PASS | `bash -n` 与 `shellcheck` 覆盖 CLI、installer、installer test |
| `bash codex/tests/smoke.sh` | PASS | 实现后重跑：131 Python tests 与全部 shell/static/sync/installer smoke 通过 |
| `git diff --check` | PASS | 无 whitespace error |
| official lifecycle source review | PASS | Context7 ledger、URL、retrieved/review date、冲突处理和 compatibility evidence 已提交 |
| NewEmaint/reference project dry-run | PASS | 3 个 declaration/lock 通过 cross-check；NewEmaint 收集后 `git status` clean |
| formal server exact inventory | BLOCKED_EXTERNAL | read-only SSH authorization unavailable；OS/CPU/runtime/DB/container/proxy exact values 保持 null，不推测 |
| branch push | PASS | fast-forward `origin/change/23` from `9ad75b8` to `02c2749`；无 force push |
| Gitea PR CI | NOT RUN | PR 尚未创建 |
| 项目 migration/test deployment/production | NOT RUN | 不在本 Change 范围 |

## Acceptance criteria 结果

- **AC-1 — PARTIAL / BLOCKED_EXTERNAL**：NewEmaint repository inventory、reference scope、
  dedup/source/owner/timestamp/confidence 已完成；正式服务器 exact metadata 因只读授权不可达未完成。
- **AC-2 — PASS**：strict JSON catalog、3 profiles、4 Schemas、ADRs、正反 fixtures 已建立。
- **AC-3 — PASS**：24 components 的 ID/state/exact pin/platform/lifecycle/source/provenance/
  compatibility 完整且 negative tests fail closed。
- **AC-4 — PASS（catalog candidate）**：仅使用官方/upstream evidence，Context7 单概念 ledger、
  source conflict 与 next review 已记录；应用级 integration 仍由各项目 Change 验证。
- **AC-5 — PASS**：OS/repository/package/runtime/framework/ORM/DB/container/proxy/frontend/CI
  action/OCI pin policy 完整；`latest`、range 和 mutable-only OCI 失败。
- **AC-6 — PASS**：project declaration 与 canonical lock 包含 resolved versions/digests/
  exception IDs/source checksums/lock SHA256；重复输出 byte-identical。
- **AC-7 — PASS**：required fail-closed routes 和脱敏 machine-readable diagnostics 通过。
- **AC-8 — PASS**：security/patch/minor/major cadence、Issue/CI/rollback/human merge gate 已固化。
- **AC-9 — PASS**：offline mirror/import、checksum、SBOM、provenance/digest contract 已固化；
  runtime 无网络，installer 不创建 updater/timer。
- **AC-10 — PASS**：Windows 同-major、Linux Node/Next/Prisma/PostgreSQL/OCI 与 SQLite
  single-instance/local-disk/WAL/backup/restore 约束均有正反验证。
- **AC-11 — PASS（dry-run only）**：NewEmaint candidate declaration/lock/gap 已生成；未修改应用
  lockfile、Dockerfile、schema、image、server 或 database，major Changes 明确拆分。
- **AC-12 — PASS**：profile 只暴露 delivery contract；#22 只消费 profile/revision/checksum，
  没有复制 release/deploy state machine。
- **AC-13 — PASS**：26 architecture tests、installer、ShellCheck、131-test full smoke 均通过。
- **AC-14 — PASS**：candidate/reference/CI/migration/test deployment/production 状态分开记录。

总体：implementation/local verification 通过；因 AC-1 server inventory 外部授权缺口，正式验收和
最终 PR 创建尚未达到批准计划的前置条件。

## 重复部署/执行

- lock generation 第一次/第二次 byte comparison：PASS（unit + CLI subprocess）
- installer 第一次/第二次：PASS（installed file manifest identical）
- validator offline rerun：PASS（test 将 proxy 指向不可达地址，runtime 无网络依赖）
- 无真实应用部署。

## 故意失败与回滚

- expired exception/EOL/mutable tag/tampered lock：PASS，均在外部 mutation 前返回非零。
- unknown/duplicate/unknown field/semver range/Secret marker：PASS，均 fail closed 且不回显值。
- official source conflict：PASS，Ubuntu Context7 extraction 冲突由 Canonical official readback
  解决；26.04 保持 `prohibited` 直到 point-release/soak Change。
- 项目文件 mutation 检查：PASS，NewEmaint `git status --porcelain` empty，authority SHA 未变。
- 回滚：本 Change 无部署/数据库 mutation；代码回滚为 revert PR。项目采用必须另有已验证回滚。

## 遗留风险与未完成项

- **BLOCKED_EXTERNAL**：需要在不启动/修改服务器且不读取 Secret/业务数据的前提下，提供
  `gitea-ci`/`prod-sim` 可用只读 inventory 身份或由授权人运行脱敏采集命令，才能完成 AC-1。
- 因批准计划要求“验收完成后”才创建最终 PR，本轮不会在 AC-1 未完成时创建 PR 或宣称 CI。
- Catalog candidate/CI 通过不等于项目升级、测试部署或 production 验收。
- #22 必须在 #23 交付后整合 lock contract，不能复制版本事实源。
