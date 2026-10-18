---
issue: 383
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/383
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - shared-core
  - rollback
  - platform-governance
depends_on:
  - 380
status: approved
branch: change/383-reference-impl-exit
created: 2026-10-19
updated: 2026-10-19
git_scope:
  - docs/changes/383-reference-impl-exit/summary-reference-impl-exit-261019.md
  - docs/changes/383-reference-impl-exit/spec-reference-impl-exit-261019.md
  - docs/changes/383-reference-impl-exit/plan-reference-impl-exit-261019.md
  - docs/changes/383-reference-impl-exit/verification-reference-impl-exit-261019.md
  - archive/reference-implementations-exit-261019.md
  - archive/README.md
  - AGENTS.md
  - README.md
  - 02-CI与自动部署流水线.md
  - 06-运维手册与踩坑集.md
  - 07-内网与生产平移路线.md
  - 12-Linux-GitHub-Gitea-双服务器自动部署方案.md
  - 13-项目结果迁移与内网切换实施手册.md
  - 14-Windows部署与迁移验收清单.md
  - platform-bootstrap/README.md
  - platform-bootstrap/runbook.md
  - skills/aisoft-platform/references/onboarding-runbook.md
  - usage/bundle.json
  - architecture/evidence/inventory.json
  - codex/runtime/tests/test_architecture_governance.py
  - codex/tests/smoke.sh
  - codex/tests/test-installer-source-guard.sh
  - codex/tests/fixtures/installed-drift/test-installed-drift.py
  - codex/tools/check-installed-drift.py
  - codex/config/project-leak-baseline.json
  - docs/governance/remediation-roadmap.md
  - architecture/reference/newemaint/README.md
  - architecture/reference/newemaint/gap-report.md
  - architecture/reference/newemaint/inventory.json
  - architecture/reference/newemaint/target-candidate/Dockerfile
  - architecture/reference/newemaint/target-candidate/architecture.json
  - architecture/reference/newemaint/target-candidate/architecture.lock.json
  - codex/runtime/aisoft_company_baseline.py
  - codex/runtime/aisoft_company_baseline_diagnostics_v1.py
  - codex/runtime/aisoft_company_baseline_diagnostics_v2.py
  - codex/runtime/aisoft_company_baseline_v2.py
  - codex/runtime/aisoft_company_delivery/__init__.py
  - codex/runtime/aisoft_company_delivery/bundle.py
  - codex/runtime/aisoft_company_delivery/cli.py
  - codex/runtime/aisoft_company_delivery/collector.py
  - codex/runtime/aisoft_company_delivery/contract.py
  - codex/runtime/aisoft_company_delivery/secret_scan.py
  - codex/runtime/aisoft_release/__init__.py
  - codex/runtime/aisoft_release/cli.py
  - codex/runtime/aisoft_release/compatibility.py
  - codex/runtime/aisoft_release/compose.py
  - codex/runtime/aisoft_release/contract.py
  - codex/runtime/aisoft_release/docker.py
  - codex/runtime/aisoft_release/errors.py
  - codex/runtime/aisoft_release/gate.py
  - codex/runtime/aisoft_release/rollback_compatibility.py
  - codex/runtime/aisoft_release/runner.py
  - codex/runtime/aisoft_release/security.py
  - codex/runtime/aisoft_release/state.py
  - codex/runtime/aisoft_release/transport.py
  - codex/runtime/tests/release_test_support.py
  - codex/runtime/tests/test_company_baseline.py
  - codex/runtime/tests/test_company_baseline_diagnostics_v1.py
  - codex/runtime/tests/test_company_baseline_diagnostics_v2.py
  - codex/runtime/tests/test_company_baseline_v2.py
  - codex/runtime/tests/test_company_delivery.py
  - codex/runtime/tests/test_release_architecture_integration.py
  - codex/runtime/tests/test_release_capability.py
  - codex/runtime/tests/test_release_cli.py
  - codex/runtime/tests/test_release_contract.py
  - codex/runtime/tests/test_release_docker28_compatibility.py
  - codex/runtime/tests/test_release_evidence_boundary.py
  - codex/runtime/tests/test_release_gate.py
  - codex/runtime/tests/test_release_phases.py
  - codex/runtime/tests/test_release_rollback_compatibility.py
  - codex/runtime/tests/test_release_runner.py
  - codex/runtime/tests/test_release_safety.py
  - codex/runtime/tests/test_release_transport.py
  - codex/tests/check-release-evidence-boundary.py
  - codex/tests/fixtures/docker-image-store-e2e/Dockerfile
  - codex/tests/fixtures/docker-image-store-e2e/server.go
  - codex/tests/fixtures/docker-release-v2-lifecycle/docker-wrapper.sh
  - codex/tests/fixtures/docker-release-v2-lifecycle/migrate.sh
  - codex/tests/fixtures/docker-release/compose-config-valid.json
  - codex/tests/fixtures/docker-release/newemaint-v2-images.json
  - codex/tests/fixtures/docker28-classic/docker-wrapper.py
  - codex/tests/fixtures/docker28-classic/identity.txt
  - codex/tests/fixtures/docker28-classic/install-daemon.sh
  - codex/tests/fixtures/docker28-classic/lifecycle-operation.py
  - codex/tests/fixtures/docker28-classic/lifecycle.py
  - codex/tests/fixtures/docker28-classic/migrate.sh
  - codex/tests/fixtures/docker28-classic/postgres-image-proof.json
  - codex/tests/fixtures/docker28-classic/python-image-proof.json
  - codex/tests/fixtures/docker28-classic/software-lock.json
  - codex/tests/fixtures/docker28-classic/web.py
  - codex/tests/integration/docker-release-v2-lifecycle-driver.py
  - codex/tests/integration/docker28-classic-driver.py
  - codex/tests/integration/provision-docker28-classic-lab.sh
  - codex/tests/integration/test-company-delivery-real-release.sh
  - codex/tests/integration/test-docker-image-store-e2e.sh
  - codex/tests/integration/test-docker-release-v2-lifecycle-e2e.sh
  - codex/tests/integration/test-docker28-classic-e2e.sh
  - codex/tests/test-company-delivery-real-release-harness.sh
  - codex/tests/test-docker-image-store-e2e-harness.sh
  - codex/tests/test-docker-release-install.sh
  - codex/tests/test-docker-release-v2-lifecycle-e2e-harness.sh
  - codex/tests/test-docker28-classic-e2e-harness.sh
  - company-delivery/README.md
  - company-delivery/VERSION
  - company-delivery/baseline/DIAGNOSTICS-V2.md
  - company-delivery/baseline/DIAGNOSTICS.md
  - company-delivery/baseline/README.md
  - company-delivery/baseline/blocked-envelope.example.json
  - company-delivery/baseline/diagnostics-v1.schema.json
  - company-delivery/baseline/diagnostics-v2.schema.json
  - company-delivery/baseline/inventory-v1.schema.json
  - company-delivery/baseline/inventory-v2.schema.json
  - company-delivery/baseline/operator-record.example.json
  - company-delivery/baseline/prepare-diagnostics-bundle.py
  - company-delivery/baseline/prepare-diagnostics-v2-bundle.py
  - company-delivery/baseline/profile-v1.schema.json
  - company-delivery/bin/aisoft-company-delivery
  - company-delivery/runbook.md
  - company-delivery/schema/compatibility-v1.schema.json
  - company-delivery/schema/evidence-v1.schema.json
  - company-delivery/schema/gitea-transition-v1.schema.json
  - company-delivery/schema/gitea-transition-v2.schema.json
  - company-delivery/schema/handoff-v1.schema.json
  - company-delivery/schema/inventory-v1.schema.json
  - company-delivery/schema/inventory-v2.schema.json
  - company-delivery/schema/inventory-v3.schema.json
  - company-delivery/templates/compatibility-matrix.example.json
  - company-delivery/templates/evidence.blocked.example.json
  - company-delivery/templates/evidence.fail.example.json
  - company-delivery/templates/evidence.not-run.example.json
  - company-delivery/templates/evidence.pass.example.json
  - company-delivery/templates/gitea-transition.example.json
  - company-delivery/templates/handoff-manifest.example.json
  - company-delivery/templates/inventory.example.json
  - docker-release/README.md
  - docker-release/bin/aisoft-docker-release
  - docker-release/bin/aisoft-docker-release-gate
  - docker-release/compatibility/image-stores-v1.json
  - docker-release/contracts/migration-rollback-v1.md
  - docker-release/examples/rollback-compatibility-v1.example.json
  - docker-release/install.sh
  - docker-release/schema/command-gate-v1.schema.json
  - docker-release/schema/image-store-compatibility-v1.schema.json
  - docker-release/schema/offline-inventory-v1.schema.json
  - docker-release/schema/offline-inventory-v2.schema.json
  - docker-release/schema/release-manifest-v1.schema.json
  - docker-release/schema/release-manifest-v2.schema.json
  - docker-release/schema/rollback-compatibility-v1.schema.json
  - docker-release/schema/state-v2.schema.json
  - docker-release/schema/state-v3.schema.json
  - docker-release/schema/target-profile-v1.schema.json
  - docker-release/templates/action-grant.example.json
  - docker-release/templates/target-profile.example.json
---

# #383 spec：参考实现迁出平台（R8）

## 目标与原因

ADR 0001 D1/D5/D7：平台只交付流程、技能、外部技能 pin 与 K1–K5 内核。`docker-release`、`aisoft_release`、`company-delivery`、`aisoft_company_*` 与 `architecture/reference/newemaint` 是按某个项目实例化的参考实现，带着证据闸门、E2E harness 和一个 installer 留在 smoke 硬门里。迁出后平台对任一项目只剩 manifest 注册数据，项目对平台只剩发布包 pin。

## 已核对的事实（2026-10-18/19，平台 `origin/main` `a395f7a`，R7 合并后在 `80a38dc` 复核，NewEMaint `gitea/main` `db8b5bed`）

1. NewEMaint 两个发布 workflow 按平台 `e1290d2` checkout 27 个发布文件；main 删除不影响取法（脱钩通知 §2）。
2. NewEMaint company-scm 的 collector、diagnostics 与 baseline schema 按 `source_commit` `1164318` 与 SHA-256 钉住。
3. NewEMaint 测试只断言自身仓里没有 `architecture/reference/newemaint/architecture.lock.json`，不读平台该目录。
4. 未 pin：NewEMaint `docs/DEPLOYMENT.md` 与 `ops/aisoft/company-delivery/README.md` 按平台 `src/branch/main/company-delivery/` 引用 runbook、schema 与 CLI；CLI（`aisoft_company_delivery/bundle.py`、`secret_scan.py`）import `aisoft_release` 并把同检出的 `docker-release/` 与 `aisoft_release` 打进 operator 包。公司路线当前全部 NOT RUN。
5. 互为夹具：release 单测、v2 lifecycle 与 image-store harness 读 `architecture/reference/newemaint/target-candidate/`；`check-release-evidence-boundary.py` 钉 docker-release 字节与该 lock。
6. `docker-release/install.sh` 是 8 个 installer 之一；DockerLab 有已安装副本（`/opt/aisoft-docker-release`、`/usr/local/bin/aisoft-docker-release`、`aisoft-docker-release-gate`），gitea-ci 与 AppServer 没有。NewEMaint 公司 host executor 由自己的 field kit 按 pin 安装。
7. `codex/tools/aisoft-project-check.sh` 把 `docker-release/v2` 当作交付形态关键字识别项目 AGENTS.md；architecture schema/validator 把 `docker-release/v1` 当 delivery contract 名称，NewEMaint lock 使用它。二者是通用词汇，不依赖被删目录。

## 拆法（负责人裁决）

默认：本 Issue 一次做完全部迁出并完成本地验证；确认点 2（提交 PR）等 NewEMaint 回告脱钩通知第 4 步，或负责人另行裁决。原定“docker-release 先删、company-delivery 后删”不可行（事实 4、5）。

## Acceptance criteria

1. git_scope 中被删的 127 个文件从 main 删除；`archive/reference-implementations-exit-261019.md` 按目录列出路径、最后所在平台 commit（本 PR 的 merge base）、NewEMaint pin 的 commit（`e1290d2`、`1164318`）与去向；`archive/README.md` 登记它。不把被删树复制进 `archive/`。
2. smoke 不再执行或登记被删文件：去掉证据闸门、docker-release 安装测试、image-store、docker28-classic、v2 lifecycle、company-delivery real-release 各段，shellcheck 名单、docker-release 与 company-delivery 的 Secret/项目名守卫与 compatibility 矩阵断言；runtime 单测 discover 自然不再包含被删测试。
3. installer 集合由 8 减为 7：`check-installed-drift.py` 删掉 docker-release surface 与 `aisoft_release`、docker-release 的 scope 根；`test-installer-source-guard.sh` 与漂移夹具同步；文档中的 installer 计数同步（ADR 0001 作为决策记录不改）。已安装副本不由平台删除，verification 写明 DockerLab 现状与处置建议。
4. architecture 只留 K4 通用部分：`architecture/evidence/inventory.json` 去掉指向 `reference/newemaint` 的条目，`test_architecture_governance.py` 删除读该目录的用例；`docker-release/v1` 名称与 project-check 的 `docker-release/v2` 关键字保留（事实 7）。
5. 活文档去掉对被删路径的链接：README、`02`、`06`、`07`、`12`–`14`、`platform-bootstrap/`、onboarding runbook、`AGENTS.md` 目录行；需要时指向迁出说明。06 踩坑表的历史行只改断链，不改事故叙述。
6. 治理文件按路线规则 5：`AGENTS.md` 与 onboarding runbook 的修改作为第一个 commit 单独提交，提交后停止，fresh 重读再做其余改动。onboarding runbook 是使用层发布包成员，同 PR 用 `usage-bundle.sh --release` 发下一个版本 1.2.0（R7 已于 2026-10-18 合并并发布 1.1.0）。
7. 泄漏基线收紧：被删路径的基线条目移除，`project-leak` 守卫读回基线外零新增。
8. 全仓 `git grep` 对 `docker-release/`（目录路径形式）、`company-delivery/`、`aisoft_release`、`aisoft_company`、`reference/newemaint` 只命中 `docs/changes/`、`archive/`、`docs/adr/`、`docs/governance/`、06 踩坑表与事实 7 的通用词汇。
9. macOS 全量 `bash codex/tests/smoke.sh` 通过，`bash -n` 与 ShellCheck 覆盖改过的 shell；Codex 经 Herdr 只读独立审查通过。
10. 合并后：两侧技能 installer 重装并读回漂移 CLEAN；需要 sudo 的重装由负责人执行，未执行如实记 NOT RUN。

## 接口、数据与兼容性影响

- 删除 CLI：`aisoft-docker-release`、`aisoft-docker-release-gate`、`aisoft-company-delivery`、`python3 -m aisoft_release.cli`。平台内无其他消费者（已 grep）。
- NewEMaint 的 pin 取法不变；`e1290d2`、`1164318` 在平台历史中永久可取，平台不 force-push、不改写历史。
- governance manifest 不改；NewEMaint 注册与 routine pilot 声明不动。

## 风险与回滚约束

- 风险：在 NewEMaint 第 4 步之前合并会断公司路线文档与 CLI 来源。控制：确认点 2 等回告。
- 风险：删掉 smoke 段后计数类断言漂移。控制：每个 commit 跑全量 smoke。
- 回滚：`git revert` 本 PR 的 merge commit 即恢复全部文件与 smoke 段；无数据或 live 状态变更。

## 非目标

- 不动 NewEMaint 仓库、任何主机上的已安装文件、governance manifest、live Gitea 状态。
- 不动 `12`–`15` 参考文档的正文结构（只修断链），不改 ADR 0001。
- 不实现任何替代的发布或交付能力。

## 未决问题

- 无。负责人 2026-10-18 确认合同与默认拆法。
