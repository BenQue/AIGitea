---
issue: 373
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/373
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - external-contract
  - security
  - shared-core
  - platform-governance
depends_on:
  - 371
status: approved
branch: change/373-broker-deproject
created: 2026-10-18
updated: 2026-10-18
git_scope:
  - docs/changes/373-broker-deproject/summary-broker-deproject-261018.md
  - docs/changes/373-broker-deproject/spec-broker-deproject-261018.md
  - docs/changes/373-broker-deproject/plan-broker-deproject-261018.md
  - 06-运维手册与踩坑集.md
  - codex/config/host-access-broker.json
  - codex/config/project-leak-baseline.json
  - codex/runtime/aisoft_host_access/application_preflight.py
  - codex/runtime/aisoft_host_access/broker.py
  - codex/runtime/aisoft_host_access/cli.py
  - codex/runtime/aisoft_host_access/contract.py
  - codex/runtime/aisoft_host_access/runner.py
  - codex/runtime/aisoft_gitea_governance/contract.py
  - codex/runtime/tests/test_application_preflight.py
  - codex/runtime/tests/test_gitea_governance.py
  - codex/runtime/tests/test_host_access.py
  - codex/tests/test-host-access-broker.sh
  - codex/tools/application-target-preflight.py
  - archive/application-target-preflight.py
  - templates/project/ci/ci.yml
  - docs/governance/remediation-roadmap.md
  - docs/adr/0001-platform-boundary.md
---

# #373 spec：broker 与 governance 去项目化（R4）

负责人于 2026-10-18 在项目线程“R4 broker 与治理去项目化”回复“确认”，批准本合同并启动实现。

## 目标与原因

ADR 0001 D3 规定项目专属值只能出现在 manifest、fixture、`docs/changes/`、`archive/`、`06` 踩坑表与 ADR/治理背景段落。K1/K2 代码里仍写死项目常量，任何项目变动都要改平台代码。本票让代码只校验 manifest 的结构与自洽，项目数据只留在 manifest。

## 负责人裁决（2026-10-18，项目线程）

- **routine pilot 保留。** 退役需要在两个 PR 之间做一次现场回滚（移除 merger 协作者、删账号），超出本票。`rollback-gitea-routine-pilot.sh` 原样保留并留在泄漏基线，pilot 真正退役时再归档。
- **AppServer 预检接口退役。** 它按 #340 实现只返回固定拒绝、零次目标执行；采集器从未被 installer 安装；LocalWMS main（`de829b9`）不调用它，原消费方 LocalWMS#333 已改走 DockerLab。这偏离 ADR D5 原文“只保留采集引擎”，同步修改 D5 该行。

## Acceptance criteria

- [ ] AC1 预检接口退役：manifest 删除 `application.target.preflight.read` 与顶层 `application_targets`；`EXPECTED_OPERATIONS`、`application-preflight` identity route、`AccessContract.application_target`、broker dispatch、runner 方法、cli 的预检参数净化、`application_preflight.py` 与其测试全部删除；采集器 `git mv` 到 `archive/application-target-preflight.py`。源码 runtime `validate` 对当前 manifest 返回 38 个操作；manifest 若仍带 `application_targets` 键则按未知键拒绝。
- [ ] AC2 合同自洽化，当前 manifest 下行为不变：
  - governance：pilot 至多一个；非目标摘要以 pilot 仓自身名称排除计算；删除 pilot 仓名、project id、四个 Issue 号与两个 SHA 的代码常量（值留在 manifest，结构校验与 `required_contexts`、rollout Issue 互异等现有自洽校验保留）；公开仓库白名单只校验与 manifest 中公开仓库逐项有序一致，删除具名集合。
  - host-access：VM profile 仓库集合不再要求等于具名集合；`timer_unit` 只能为 null 或 `aisoft-agent@<该 profile 名>.timer`；pilot project id 与 host-access project id 一致的现有校验保留。
  - 补拒绝用例：两个 pilot、pilot 改仓后摘要不符、timer 与 profile 名不一致、公开白名单与 manifest 不一致、残留 `application_targets`。
- [ ] AC3 注释去项目名（`aisoft_gitea_governance/contract.py`、`aisoft_host_access/contract.py`、`broker.py` 中的项目轶事改为通用表述或 Issue 号）；`templates/project/ci/ci.yml` 注释中已归档的“02 §2”改为指向 governance manifest 的 `status_check_contexts`；`06` 的 #340 单票合同段落替换为两行退役说明并指向本票。泄漏基线用 `--write-baseline` 收紧，只降不升。
- [ ] AC4 macOS 本机全量 `bash codex/tests/smoke.sh` 全绿；PR required CI 绿。
- [ ] AC5 Codex 对最终 diff 做一次独立审查（ADR D6），结论记入 PR 候选说明。

## 接口、数据与兼容性影响

- broker 操作表 39 → 38。删除操作对既有调用方是破坏性变更；本仓与 LocalWMS main 均无调用方。其余操作的参数集合与行为不变。
- `host-access-broker.json` 删除顶层 `application_targets`；`gitea-governance.json` 不改字节，pilot 封印摘要不需要重算。
- 合并前安装层不变；合并后两台需重装，并手工删除已安装的 `application_preflight.py`（installer 只装不删），否则漂移检查会报多余文件。

## 风险与回滚约束

- 合同加载写错会让全部 broker 调用 fail closed：以源码 runtime `validate`、单测和全量 smoke 验证，合并后先 VM 重装读回，再请负责人装 Mac。
- 放宽具名集合后，项目集合、timer 与公开白名单只受 manifest 约束；manifest 改动仍须走受保护 `main` 的 PR 与重装，封印摘要仍拦截非目标仓的悄悄变更。
- 回滚：revert 本 PR 后两台重装；归档的采集器从 `archive/` 原样恢复。

## 非目标

- docker-release 合同字节、architecture lock、routine merger 行为、`rollback-gitea-routine-pilot.sh`、`bootstrap-gitea-service-account.sh`。
- summary 模板依赖边注释（改模板会触发下游 6 仓重新同步，推迟到 R6 发布包）。
- #358 architecture profile 扩展点（R4 合并后在其自身 Issue 重新 triage）。
- 平台自身的 Issue 号常量（如 #35、#208），它们不是项目数据。

## 未决问题

无。
