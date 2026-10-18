---
issue: 380
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/380
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
  - 377
status: approved
branch: change/380-fixture-manifests
created: 2026-10-18
updated: 2026-10-18
git_scope:
  - docs/changes/380-fixture-manifests/summary-fixture-manifests-261018.md
  - docs/changes/380-fixture-manifests/spec-fixture-manifests-261018.md
  - docs/changes/380-fixture-manifests/plan-fixture-manifests-261018.md
  - docs/changes/380-fixture-manifests/verification-fixture-manifests-261018.md
  - codex/tests/fixtures/manifests/gitea-governance.json
  - codex/tests/fixtures/manifests/host-access-broker.json
  - codex/tests/fixtures/manifests/README.md
  - codex/runtime/tests/test_host_access.py
  - codex/runtime/tests/test_gitea_governance.py
  - codex/runtime/tests/test_routine_merge.py
  - codex/runtime/tests/test_dependency_integration.py
  - codex/runtime/tests/test_dependencies.py
  - codex/runtime/tests/test_credential_rotation.py
  - codex/runtime/tests/rotation_cli_fixture.py
  - codex/runtime/tests/test_change_control.py
  - codex/runtime/tests/test_deployment_lifecycle.py
  - codex/runtime/tests/test_vendored_change_templates.py
  - codex/runtime/tests/test_controller.py
  - codex/runtime/tests/test_main_integration.py
  - codex/tests/test-bootstrap-gitea-service-account.sh
  - codex/tests/test-rotate-gitea-service-account.sh
  - codex/tests/test-host-access-broker.sh
  - codex/tests/test-project-check.sh
  - codex/tests/test-mark-completed-issues.sh
  - codex/tests/test-agent-runtime.sh
  - codex/tests/test-install-host-access-broker.sh
  - codex/tests/fixtures/installed-drift/test-installed-drift.py
  - codex/tests/smoke.sh
  - codex/tools/rollback-gitea-routine-pilot.sh
  - codex/tests/test-rollback-gitea-routine-pilot.sh
  - archive/rollback-gitea-routine-pilot.sh
  - archive/test-rollback-gitea-routine-pilot.sh
  - archive/README.md
  - codex/tools/aisoft-project-check.sh
  - codex/install-host-access-broker.sh
  - codex/tools/check-installed-drift.py
  - codex/config/project-leak-baseline.json
  - 06-运维手册与踩坑集.md
  - docs/governance/remediation-roadmap.md
---

# #380 spec：测试改读自带夹具 manifest，routine pilot 回滚工具退役（R6b）

负责人于 2026-10-18 在项目线程“R6b”回复“确认”，批准本合同并启动实现。

## 目标与原因

ADR 0001 D3 只允许项目数据出现在 manifest 等登记位置；平台自身的测试却把真实 manifest 当夹具，断言其中具体项目的条目。这让平台对项目实例形成硬依赖：项目退出或改声明，平台测试变红，或合同覆盖静默消失（`06` 踩坑 24 的“测试夹具的坑”）。负责人 2026-10-18 裁决 routine pilot 从平台退役：平台只留通用 schema 与夹具，pilot 具体配置去留与 live 回滚交给 NewEMaint 侧。

## 已核对的事实（2026-10-18，确认前取证，`origin/main` `8fa4458`）

- 读真实 manifest 并含应用项目名的测试 18 个文件：`test_host_access.py`（236 处）、`test-bootstrap-gitea-service-account.sh`（70）、`test_gitea_governance.py`（61）、`test-rollback-gitea-routine-pilot.sh`（33）、`test_routine_merge.py`（31）、`test_dependency_integration.py`（20）、`test_credential_rotation.py`（19）、`test-host-access-broker.sh`（16）、`test-project-check.sh`（14）、`test_change_control.py`（10）、`test_dependencies.py`（7）、`test-mark-completed-issues.sh`（6）、`test-agent-runtime.sh`（4）、`test_deployment_lifecycle.py`、`test_controller.py`、`test_vendored_change_templates.py`、`rotation_cli_fixture.py`、`test_main_integration.py`。
- 通用 `routine_live_pilot` schema 在 #373 已改为 manifest 自洽校验（`aisoft_gitea_governance/contract.py`），governance CLI 的 live 授权门、broker 的 canary 限制、bootstrap 的 routine merger 分支都只读 manifest，不含项目名。
- `rollback-gitea-routine-pilot.sh` 写死 `issue=213` 与 `newemaint-routine-merger`，由 `install-host-access-broker.sh` 装到 `/usr/local/libexec/aisoft/`，漂移检查与 smoke 登记它；泄漏基线记 33 处。
- 已退役工具有先例：`keychain-acl-audit` 由 installer 删除已装副本，漂移检查列入 `absent`，`test-host-access-broker.sh` 断言删除。
- 真实 manifest 中 NewEMaint 的 `routine_live_pilot` 把 routine merger 限制在 canary Issue；删掉它而保留 `routine_auto_merge_enabled: true` 会放宽 live merger 权限。

## Acceptance criteria

- [ ] AC1 合成夹具：新增 `codex/tests/fixtures/manifests/gitea-governance.json` 与 `host-access-broker.json`，由当前真实 manifest 机械生成，应用项目改为合成名字（NewEMaint→AlphaApp、LocalWMS→BetaApp、SFMDigitalBoard→GammaBoard、HSDB→DeltaDB，以及各自的 project id、agent、merger、profile 与 checkout 路径），pilot 封印摘要按夹具重算；平台与 public-test 项目保持原样。附 README 说明来源、改名表与“夹具是冻结数据，不随真实 manifest 同步”。
- [ ] AC2 测试改读夹具：上列测试改为读夹具 manifest，断言中的项目名同步改为合成名字；改完后这些文件不再出现已注册应用项目名。smoke 新增守卫：`codex/runtime/tests/` 与 `codex/tests/` 下除允许清单（安装、校验真实 manifest 可加载、泄漏守卫自身）外，不得引用 `codex/config/gitea-governance.json` 或 `host-access-broker.json`。
- [ ] AC3 覆盖不减：逐文件用例数（Python `Ran N tests`、shell 断言计数）改前改后相等；routine pilot 通用 schema（封印、canary 限制、live 授权门）、routine merger、凭据轮换、依赖读取、bootstrap 用例全部保留。另在候选副本上删掉真实 manifest 的一个应用项目条目，证明改后的测试不受影响（记入 verification）。
- [ ] AC4 回滚工具退役：`rollback-gitea-routine-pilot.sh` 与其测试移入 `archive/`（按 `application-target-preflight.py` 先例在 `archive/README.md` 登记：来源 #213、退役原因、项目侧撤掉 routine merger 时的参考）；`install-host-access-broker.sh` 不再安装并删除已装副本与 `.previous`；漂移检查把它列入 `absent`；`test-install-host-access-broker.sh`、`test-host-access-broker.sh` 与漂移夹具测试同步；smoke 五处登记移除；泄漏基线删掉该条目。
- [ ] AC5 保留不变：真实 `gitea-governance.json` 与 `host-access-broker.json` 字节不变（NewEMaint 的 pilot 声明是 D3 允许的登记数据，改它会改变 live merger 行为，属 NewEMaint 侧决定）；通用 schema、governance CLI、broker、bootstrap 与 rotate 工具不改。
- [ ] AC6 文档：`06` 中提到 pilot 回滚工具处改为指向归档与 NewEMaint 侧；整改路线 R6b 行写本票状态。
- [ ] AC7 macOS 全量 `bash codex/tests/smoke.sh` 通过；`python3 -B codex/tests/check-project-leak.py` 只减不增；`usage-bundle.sh --verify` 通过（本票不改发布包成员）。

## 实现中的调整（确认后，确认点 2 一并复核）

- `aisoft-project-check.sh` 原先把治理 manifest 路径写死为本仓 `codex/config/gitea-governance.json`，测试无法换成夹具。按 `aisoft_loop/cli.py` 与 `aisoft-project-target.sh` 已有的 `AISOFT_GOVERNANCE_MANIFEST` 约定增加同名覆盖，缺省行为不变；`test-project-check.sh` 设置它指向夹具。这是一个只读诊断工具的读路径，不放宽任何写闸门。
- broker 入口 `host-access-broker.sh` 固定读本仓或已装 manifest、刻意不接受覆盖，因此 `test-host-access-broker.sh` 中经入口的拒绝用例改用平台自有的 `smoke-test` 测试仓，不再借用应用项目。

## 接口、数据与兼容性影响

已装工具集合少一个 `rollback-gitea-routine-pilot`。重装后平台不再提供 pilot 的 PAT 撤销与账号删除；通用 governance `rollback`（带 `AISOFT_ROUTINE_LIVE_MODE` 授权门，回滚分支保护与 collaborator）与 `rotate-gitea-service-account` 保留。runtime、manifest、broker 操作表不变，VM 安装面不变。

## 风险与回滚约束

merger 账号、PAT、collaborator 的 live 状态不动；NewEMaint 侧决定撤掉 routine merger 时，应在自己的 Issue 里做（可参考归档脚本），平台侧随后再改 manifest。回滚：revert 本 PR 后在 Mac 重装 broker，已装工具恢复。测试改名漏网以全量 smoke 与守卫兜底。

## 非目标

- 不改 NewEMaint 仓库与 live Gitea 状态。
- 不动 R8 范围：`docker-release/`、`aisoft_release`、`aisoft_company_*`、`company-delivery/`、`architecture/reference/newemaint` 及其 release/architecture 测试与 docker-release 夹具。
- 不改 `codex/tools/gitea-pat-helper/` 的 Go 测试：它的源文件摘要进入已装 PAT helper 的 provenance，改动会迫使 helper 重建，留给后续批次。
- 不改 `credential_rotation.py` 的源模式路径映射（运行时从仓库读真实 manifest 是它的职责）。

## 未决问题

无。
