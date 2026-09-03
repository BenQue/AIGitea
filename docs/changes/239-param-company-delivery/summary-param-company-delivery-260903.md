---
issue: 239
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/239
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 把 aisoft_company_delivery runtime 以常量绑定的两处 pilot 项目标识符（bundle.py COMPATIBILITY_PATH 与 contract.py/collector.py 的 sync timer unit 名）改为由调用方传入的 compatibility matrix 与 handoff manifest 字段声明；handoff manifest 新增 compatibility.sync_timer_unit、build-bundle/collect-inventory 新增参数属 operator bundle 外部契约，operator VERSION 1.2.0→1.3.0；inventory/handoff schema 与 smoke.sh 守卫同步。命中共享核心、外部契约与 CI 守卫强制规则，effective complexity=complex；change_control=production 需 spec+plan。删除平台仓 pilot matrix 副本软依赖 NewEmaint #75 关闭，拆为 plan 最后一个 ticket
risk_flags:
  - shared-core
  - external-contract
  - ci-change
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-param-company-delivery-260903.md
  spec: spec-param-company-delivery-260903.md
  plan: plan-param-company-delivery-260903.md
  verification: verification-param-company-delivery-260903.md
confidence: high
override_reason: ''
depends_on:
  - 237
status: pr-open
branch: change/239-param-company-delivery
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/240
created: 2026-09-03
updated: 2026-09-03
---

## 问题/需求总结

#237（merge `2482584`）把 `company-delivery/` 判定为去项目名的公司两 VM 离线 handoff operator 参考实现，但
`codex/runtime/aisoft_company_delivery/` 仍以常量绑定 pilot 项目名，平台仓因此保留 5 处 JSON 项目专属标识符
（`grep -rci NewEmaint company-delivery/` = 9，含 `$comment` 标注）：

1. `bundle.py:33` `COMPATIBILITY_PATH = "operator/compatibility/newemaint-company-pilot-v1.json"`，对应
   `company-delivery/compatibility/newemaint-company-pilot-v1.json`（pilot matrix，归属由 NewEmaint 仓 #75 承接）
   与 `templates/handoff-manifest.example.json` 的 `matrix_path`。
2. `contract.py:49/357`、`collector.py:350` 绑定 sync timer unit 名 `aisoft-inbound-sync@newemaint.timer`，对应
   `schema/inventory-v{1,2,3}.schema.json` 的 enum/const。

本 Issue 把这两个绑定参数化（由 compatibility matrix 与 handoff manifest 字段声明），随后删除平台仓 pilot matrix
副本并把 `smoke.sh` 项目名守卫扩展到整个 `company-delivery/`。Issue 正文「验收标准」「非目标」是唯一合同。

## 影响范围

- runtime：`codex/runtime/aisoft_company_delivery/{contract,collector,bundle,cli}.py`。
- operator bundle 外部契约：`company-delivery/VERSION`（1.2.0→1.3.0）、`schema/inventory-v{1,2,3}.schema.json`、
  `schema/handoff-v1.schema.json`、新增 `schema/compatibility-v1.schema.json` 与
  `templates/compatibility-matrix.example.json`、`templates/*.example.json` 的 operator/collector version、
  `README.md`/`runbook.md` 中 build-bundle 与 Stage 10 collect-inventory 命令。
- 测试与守卫：`codex/runtime/tests/test_company_delivery.py`（fixture 去项目名 + 参数化路径覆盖）、
  `codex/tests/integration/test-company-delivery-real-release.sh`（`build-bundle` 调用补 `--compatibility-matrix`）、
  `codex/tests/smoke.sh`（守卫扩展到整个 `company-delivery/`，随删除副本一起落地）。
- 删除：`company-delivery/compatibility/newemaint-company-pilot-v1.json`（软依赖 NewEmaint #75 关闭，见 plan T05）。
- 不动：`docker-release/`（#65 冻结）、`architecture/`、broker、标签 manifest、`AGENTS.md`、两侧技能源；不改
  NewEmaint 仓、不做任何公司环境部署。

## 初步方案与建议

- compatibility matrix 由调用方在 `build-bundle --compatibility-matrix <absolute-path>` 传入（项目仓保存、归属项目），
  builder 只读其 `contract_version` 与 `sync_timer_unit`，把文件复制到 bundle `operator/compatibility/<basename>` 并把
  `matrix_path`/`matrix_sha256`/`sync_timer_unit` 写入 handoff manifest。
- sync timer unit 名在 inventory 合同里改为 pattern `aisoft-inbound-sync@<instance>.timer`（scm-ci 恰好一个），collector
  从已验证的 handoff manifest 读取（`collect-inventory --handoff-manifest`），`verify-gitea-transition` 交叉校验 scm
  inventory 的 timer unit 与 handoff 声明一致。
- operator `VERSION` bump 到 `1.3.0`；`< 1.3.0` 的 handoff 只作历史 evidence 读取（`sync_timer_unit` 可缺省），
  transition 仍只接受当前 operator 版本。
- 删除 pilot 副本与守卫扩展放 plan 最后一个 ticket，读回 NewEmaint #75 closed 后再执行。

## 风险

- `collect-inventory`/`build-bundle` 新增必填参数：旧调用形态（runbook Stage 00/10 命令、integration 脚本）必须同步。
- `test_company_delivery.py` 与 `smoke.sh` 钉住 runbook/README 短语，改文档前先 rg 测试目录。
- integration 脚本 `--execute` 路径本 Issue 不运行（无 exact release bytes），只能靠 harness 静态守卫与 `bash -n`。
- NewEmaint #75 在本会话开始时仍 open：删除副本前必须再次读回 state。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 把 aisoft_company_delivery runtime 以常量绑定的两处 pilot 项目标识符（bundle.py COMPATIBILITY_PATH 与 contract.py/collector.py 的 sync timer unit 名）改为由调用方传入的 compatibility matrix 与 handoff manifest 字段声明；handoff manifest 新增 compatibility.sync_timer_unit、build-bundle/collect-inventory 新增参数属 operator bundle 外部契约，operator VERSION 1.2.0→1.3.0；inventory/handoff schema 与 smoke.sh 守卫同步。命中共享核心、外部契约与 CI 守卫强制规则，effective complexity=complex；change_control=production 需 spec+plan。删除平台仓 pilot matrix 副本软依赖 NewEmaint #75 关闭，拆为 plan 最后一个 ticket
risk_flags:
  - shared-core
  - external-contract
  - ci-change
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- Issue 正文自述 complex / production，要求 spec + plan。
- `grep -rn -i newemaint codex/runtime/aisoft_company_delivery/` = 4 处（`bundle.py:33`、`contract.py:49/357`、
  `collector.py:350`）；`grep -rci NewEmaint company-delivery/ | grep -v ':0$'` 合计 9（D-04 1、D-06 3、D-07 2、
  D-08 2、D-13 1，与 Issue 正文一致）。
- `bundle.py` 把 `company-delivery/` 整体复制为 bundle `operator/`，handoff manifest 由 `load_handoff` 严格校验
  key 集合：新增字段即外部契约变化，命中 `external-contract`；runtime 包被 `test_company_delivery.py`（76 tests）
  与 `smoke.sh` 守护，命中 `shared-core` + `ci-change`。
- broker `gitea.issue.read --project newemaint --number 75`：state `open`（2026-09-03 会话开始时），删除副本软依赖
  未满足，按调度指令拆为最后一个 ticket。
- 依赖 #237（`2482584`）已在 `origin/main` 历史中。

### 缺失的 acceptance criteria 或决策

- 无缺失验收标准。需在确认点 1 认可的 4 项解读见 spec「未决问题」。

`## AI 判级` YAML 使用 analyzer 的唯一字段集合和顺序。
`required_docs` 使用语义角色：`small` 和 unresolved 只包含 `summary`；
`complex` 必须依次包含 `summary`、`spec`、`plan`；当本次变更的验收证据不能由
diff review 与 required CI 复现时，再追加 `verification`（判据见 `03` §3
「何时声明 `verification`」）。追加它表示这次变更**欠一份验证记录**，不表示
这次变更要部署——部署与迁移必然需要它，但不是只有它们需要。`documents`
把每个角色映射到同目录的 `<role>-<short-slug>-<YYMMDD>.md`；所有角色共用
2–4 词短 slug。
