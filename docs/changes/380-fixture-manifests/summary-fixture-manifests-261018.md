---
issue: 380
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/380
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 测试改读自带夹具并退役 routine pilot 回滚工具，改动 broker installer、漂移检查与 smoke 登记，属于共享核心、安装与平台治理
risk_flags:
  - shared-core
  - rollback
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-fixture-manifests-261018.md
  spec: spec-fixture-manifests-261018.md
  plan: plan-fixture-manifests-261018.md
  verification: verification-fixture-manifests-261018.md
confidence: high
override_reason: ''
depends_on:
  - 377
status: pr-open
branch: change/380-fixture-manifests
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/382
created: 2026-10-18
updated: 2026-10-18
---

## 问题/需求总结

整改路线 R6b（ADR 0001 D3，路线表 A3、A4 残留）。负责人目标是平台对任何项目实例没有硬依赖，部署细节留在各项目。现状是约 18 个进 smoke 的测试直接读真实 `codex/config/gitea-governance.json` 与 `host-access-broker.json`，并断言其中已注册项目（主要是 NewEMaint，其次 LocalWMS、SFMDigitalBoard、HSDB）的条目：项目一退出或改声明，平台测试就变红，或者借生产数据当夹具的合同覆盖静默消失（`06` 踩坑 24）。`codex/tools/rollback-gitea-routine-pilot.sh` 写死 Issue 213 与 `newemaint-routine-merger`，只服务 NewEMaint 一个 pilot。负责人 2026-10-18 裁决 pilot 从平台退役：平台只留通用 schema 与夹具，pilot 具体配置去留与 live 回滚交给 NewEMaint 侧。

## 影响范围

新增 `codex/tests/fixtures/manifests/` 两份合成夹具；改读真实 manifest 的 Python 与 shell 测试；smoke（夹具守卫、回滚工具登记移除）；broker installer、漂移检查及其测试；回滚工具与测试移入 `archive/`；泄漏基线、`06`、整改路线。

## 初步方案与建议

见 mapped spec。夹具由当前真实 manifest 机械生成，应用项目统一改成合成名字并重算 pilot 封印摘要，测试改指夹具后断言随之改名，用例数与覆盖不变。回滚工具按 keychain-acl-audit 先例退役：installer 删除已装副本，漂移检查列为必须不存在。

## 风险

broker installer 改动要求负责人合并后在 Mac 重装 broker（需 sudo）；VM 侧安装面不变。重装后平台不再提供 pilot 的 PAT 撤销与账号删除工具，NewEMaint 侧若要撤掉 routine merger，需要自带回滚步骤；通用的 governance `rollback`（含 live 授权门）保留。测试大规模改名可能漏掉隐含依赖真实路径的用例，以全量 smoke 兜底。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 测试改读自带夹具并退役 routine pilot 回滚工具，改动 broker installer、漂移检查与 smoke 登记，属于共享核心、安装与平台治理
risk_flags:
  - shared-core
  - rollback
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- 改 broker installer 与已装工具集合、漂移检查与 smoke，属于共享核心与安装面，按 `AGENTS.md` 判级规则强制 complex。
- 已装副本被清除与漂移读回只能在本机重装后取证，声明 `verification`。

### 缺失的 acceptance criteria 或决策

- 无。pilot 去留由负责人 2026-10-18 裁决为退役。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC1、AC2 | smoke 夹具守卫；候选 manifest 删项目条目后重跑受影响测试 |
| AC3 | 改前改后逐文件用例数对照 |
| AC4 | `bash codex/tests/test-install-host-access-broker.sh`；`bash codex/tests/test-host-access-broker.sh`；漂移检查夹具测试 |
| AC5 | diff review；真实 manifest 字节不变 |
| AC6 | `bash codex/tests/smoke.sh`；`python3 -B codex/tests/check-project-leak.py` |

## 部署与回滚

无应用部署。合并后负责人在 Mac 重装 broker（`codex/install-host-access-broker.sh`，需 sudo），再用 `check-installed-drift.sh` 读回；本票不改技能源，两侧技能无需重装。回滚：revert 本 PR 后重装 broker 即恢复已装回滚工具。
