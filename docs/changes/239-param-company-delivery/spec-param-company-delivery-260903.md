---
issue: 239
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/239
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - shared-core
  - external-contract
  - ci-change
depends_on:
  - 237
status: approved
branch: change/239-param-company-delivery
created: 2026-09-03
updated: 2026-09-03
---

# Spec · company-delivery runtime 参数化 compatibility 路径与 sync timer unit 名

## 目标与原因

按 2026-09-02 定案「平台只管流程管控与环境级指导，项目相关内容由项目自身决定；runtime 不得以常量绑定任何项目名」，
把 `codex/runtime/aisoft_company_delivery/` 的两处 pilot 绑定改成由调用方数据声明，然后删除平台仓的 pilot matrix
副本。Issue #239 正文是合同源，本文不扩张。行号以 `origin/main` = `2482584`（Merge PR #238，#237）为准。

## 术语

- **compatibility matrix**：项目仓保存并归属项目的 JSON（`contract_version` = `company-delivery-compatibility/v1`）。
  runtime 只读取两个字段：`contract_version` 与 `sync_timer_unit`；其余（拓扑、版本窗口、stage 进度、policy）
  是项目数据，runtime 不解释、不校验。
- **sync timer unit**：公司 `scm-ci` 主机上 GitHub 入站同步 timer 的 systemd 实例名，形如
  `aisoft-inbound-sync@<instance>.timer`（`sync/systemd/aisoft-inbound-sync@.timer` 的 `%i` 实例）。runtime pattern
  `SYNC_TIMER_UNIT = ^aisoft-inbound-sync@[A-Za-z0-9][A-Za-z0-9._-]{0,63}\.timer$`。
- **legacy handoff**：`operator_version` < `1.3.0` 的 `handoff-manifest.json`。只作历史 evidence 读取，
  `compatibility.sync_timer_unit` 可缺省；不原地补写。
- **当前 operator**：`company-delivery/VERSION` = `contract.OPERATOR_VERSION` = `1.3.0`。

## 接口与数据变更（逐项）

| # | 位置 | 现状 | 变更 |
|---|---|---|---|
| R-01 | `contract.py:24` `OPERATOR_VERSION` | `"1.2.0"` | `"1.3.0"`；新增 `COMPATIBILITY_VERSION = "company-delivery-compatibility/v1"`、`SYNC_TIMER_UNIT` pattern |
| R-02 | `contract.py:46-53` `ROLE_UNIT_NAMES["scm-ci"]` | 含 `aisoft-inbound-sync@newemaint.timer` | 只含 `act_runner.service`、`docker.service`、`gitea.service`；timer 不再是固定名 |
| R-03 | `contract.py:291-322` `_load_inventory_v1` units 校验（v2/v3 复用） | `name` 必须在 `UNIT_NAMES` enum；expected units 为固定集合 | `name` 在 `UNIT_NAMES` 或匹配 `SYNC_TIMER_UNIT`；`scm-ci` 必须恰好一个 timer unit，`appserver-prod` 不得有；`timer_safe`（`:356`）按实际 timer 名判定；返回值结构不变 |
| R-04 | `contract.py:1379-1383` `load_handoff` `compatibility` | 精确 key `{matrix_path, matrix_sha256, required_roles}` | 允许 `sync_timer_unit`（匹配 `SYNC_TIMER_UNIT`）；`operator_version` ≥ `1.3.0` 时必填，legacy 可缺省；缺省且非 legacy → `INVALID_CONTRACT` |
| R-05 | `contract.py` 新增 `load_compatibility_matrix(path, *, require_protected=False)` | 无 | 有界 regular 非 symlink JSON object，`_reject_sensitive`，`contract_version` const、`sync_timer_unit` pattern；返回 dict |
| R-06 | `contract.py:1043-1126` `verify_gitea_transition` | 不读 timer | 读 handoff `compatibility.sync_timer_unit`（当前 operator 必填）与 scm inventory 的 timer unit（新增 `inventory_sync_timer_unit(inventory)` helper）；不一致 → `INVALID_CONTRACT` "transition sync timer unit does not match the verified handoff" |
| R-07 | `collector.py:86` `collect_inventory` | 无 timer 参数；`:184` 按 `ROLE_UNIT_NAMES` 采集；`:350` 按常量取 timer | 新增 keyword `sync_timer_unit`：`scm-ci` 必填且匹配 pattern，`appserver-prod` 传入即 `INVALID_ARGUMENT`；units = 固定 units + timer；`_collect_scm_inventory` 接收 timer 名。新增 `sync_timer_unit_from_handoff(path)`：`load_handoff(path, bundle_root=path.parent)`（完整 payload 校验）后返回字段，缺省 → `INVALID_CONTRACT` |
| R-08 | `bundle.py:33` `COMPATIBILITY_PATH` | 常量 | 删除；`build_bundle(..., compatibility_matrix)` 必填：absolute regular 非 symlink、mode ∈ {0600,0644,0755}、basename 匹配 `^[A-Za-z0-9][A-Za-z0-9._-]{0,127}\.json$`；经 R-05 校验后复制到 `operator/compatibility/<basename>`（与 tracked 文件同名 → `SOURCE_INVALID`）；handoff `compatibility` 写入 `matrix_path`、`matrix_sha256`、`required_roles`、`sync_timer_unit` |
| R-09 | `cli.py` | `build-bundle` 7 个参数；`collect-inventory --role/--output/--mode` | `build-bundle --compatibility-matrix <path>` 必填；`collect-inventory --handoff-manifest <path>`：`scm-ci` 必填（经 R-07 解析 timer），`appserver-prod` 传入即错误 |
| R-10 | `company-delivery/VERSION` | `1.2.0` | `1.3.0`（handoff manifest 新字段 + CLI 新参数 = 外部契约变化） |
| R-11 | `schema/inventory-v{1,2,3}.schema.json` unit `name` enum、v1 `:120` `contains` const | 含 pilot timer 名 | enum 只含 5 个固定 unit，`anyOf` 追加 `pattern`（同 `SYNC_TIMER_UNIT`）；v1 `contains` 改 `pattern`；#237 的 `$comment` 删除（标识符已不存在） |
| R-12 | `schema/handoff-v1.schema.json` `compatibility` | 3 个 property | 新增 `sync_timer_unit` property（pattern）；`required` 不变（legacy 仍可校验），顶层 `$comment` 说明 operator ≥ 1.3.0 必填由 runtime 判定 |
| R-13 | `schema/compatibility-v1.schema.json` | 无 | 新增：`contract_version` const、`sync_timer_unit` pattern、`additionalProperties: true`（项目数据） |
| R-14 | `templates/compatibility-matrix.example.json` | 无 | 新增项目中立示例（`example` 实例名、role 描述、policy 三个 BLOCKED 项）；不含任何项目名 |
| R-15 | `templates/handoff-manifest.example.json` | `operator_version` 1.2.0、`matrix_path` pilot 名 | `1.3.0`；`matrix_path` = `operator/compatibility/compatibility-matrix.example.json`；新增 `sync_timer_unit` |
| R-16 | `templates/gitea-transition.example.json`、`inventory.example.json`、`evidence.*.example.json` | operator/collector version `1.2.0` | `1.3.0`（transition 由 `OPERATOR_VERSION` const 绑定，其余保持示例一致） |
| R-17 | `README.md` `:5`、`:26-28`、`:45`、`:54`、`:65-72`；`runbook.md` `:5-8`、`:89`、`:92`、`:104`、`:108` | operator `1.2.0`；compatibility 指针段说明副本因 builder 绑定保留；build-bundle 无 matrix 参数；Stage 10 `collect-inventory` 无 handoff 参数 | 当前 operator `1.3.0`，`1.2.0` 并入历史版本列表；compatibility 段改为「matrix 归属项目仓，构建时由 `--compatibility-matrix` 传入，runtime 只读 `contract_version`/`sync_timer_unit`」；示例命令补 `--compatibility-matrix /approved/<project>/compatibility-matrix.json`；Stage 10 `scm-ci` 命令补 `--handoff-manifest <bundle>/handoff-manifest.json`（保留测试钉住短语 `collect-inventory --role scm-ci --mode preflight --output`） |
| R-18 | `codex/tests/integration/test-company-delivery-real-release.sh:179-196`、`:209` | `build-bundle` 无 matrix 参数；bundle 身份钉 `1.1.1`（陈旧，`--execute` 从未在 1.2.0 下运行） | 新增 `--compatibility-matrix` 脚本参数（`--execute` 必填、必须 absolute）并传给两次 build；身份钉改 `1.3.0`；默认调用仍 `NOT RUN` |
| R-19 | `codex/runtime/tests/test_company_delivery.py` | fixture 与断言含 pilot timer 名、pilot matrix 路径、`1.2.0`；方法名 `test_newemaint_never_reuses_…` | fixture timer 改 `aisoft-inbound-sync@example.timer`；bundle/runbook/template 测试改用 `templates/compatibility-matrix.example.json` 或临时 fixture matrix；版本断言 `1.3.0`；方法名去项目名；新增 R-03/R-04/R-06/R-07/R-08/R-09 的正反向测试与「runtime 包零项目名」断言 |
| R-20 | `company-delivery/compatibility/newemaint-company-pilot-v1.json`；`smoke.sh:499-512` 守卫 | 副本存在；守卫只读 README/runbook | **T05（软依赖 NewEmaint #75 closed）**：`git rm` 副本；守卫改为对整个 `"$ROOT/company-delivery"` 目录执行 #231 pattern，退出信息改「company-delivery 不得出现具体项目名（#239 AC-2）」 |

## Acceptance criteria

- [ ] **AC-1 runtime 参数化**（Issue 第 1 条）：`grep -rci newemaint codex/runtime/aisoft_company_delivery/` 每个文件 = 0；
  `grep -n COMPATIBILITY_PATH codex/runtime/aisoft_company_delivery/*.py` 为空；单测证明：R-03（scm-ci 缺 timer /
  两个 timer / 名字不匹配 pattern / appserver 带 timer 均 `INVALID_CONTRACT`，任意合法实例名 PASS）、R-04（≥1.3.0 缺
  `sync_timer_unit` 拒绝，legacy 1.2.0 缺省可读）、R-06（timer 与 handoff 不一致拒绝）、R-07（collector 按传入名采集，
  appserver 传入拒绝）、R-08（builder 把传入 matrix 复制到 `operator/compatibility/<basename>` 且 handoff 含
  `sync_timer_unit`；错 `contract_version`/缺字段/相对路径/同名冲突拒绝）、R-09（`--handoff-manifest` 解析 timer）。
- [ ] **AC-2 副本删除与守卫扩展**（Issue 第 2 条，T05）：`test -e company-delivery/compatibility/newemaint-company-pilot-v1.json`
  失败；`grep -rci NewEmaint company-delivery/ | grep -v ':0$'` 为空；守卫块对整个 `company-delivery/` 执行，反向证明：
  向副本树任一 JSON/Markdown 追加 `参照 NewEMaint` 后单独执行守卫块 rc=1，真实树 rc=0。**T05 之前**：副本计数 1，
  其余文件 0；verification 如实记录中间状态。
- [ ] **AC-3 VERSION 与 legacy**（Issue 第 3 条）：`cat company-delivery/VERSION` = `1.3.0` 且等于 `OPERATOR_VERSION`；
  bundle 测试 archive 名以 `aisoft-company-delivery-1.3.0-` 开头；legacy 1.2.0 handoff fixture（无 `sync_timer_unit`）
  经 `load_handoff` 可读但 `verify_gitea_transition` 以 `CHECKSUM_MISMATCH`（operator 不匹配）拒绝；仓库内不新增任何
  1.2.0 handoff 补写。
- [ ] **AC-4 测试与守卫**（Issue 第 4 条）：`bash codex/tests/smoke.sh` rc=0；`grep -n -i newemaint
  codex/runtime/tests/test_company_delivery.py` 只剩 #237 的否定断言 `assertNotIn("NewEmaint 公司交付 runbook", …)`（fixture、
  正向断言与方法名均为 0）；`grep -ci newemaint company-delivery/templates/compatibility-matrix.example.json`
  = 0；`bash -n` + `shellcheck -S warning` 对 `smoke.sh` 与 integration 脚本通过；`test-company-delivery-real-release-harness.sh`
  PASS；integration `--execute` 记 NOT RUN。
- [ ] **AC-5 与 NewEmaint #75 衔接**（Issue 第 5 条）：verification 写明平台侧读取路径——builder 由调用方传入项目仓
  matrix 绝对路径；collector 从已验证 handoff 读 timer；transition 交叉校验；删除副本前读回 #75 state。
- [ ] **AC-6 非目标守卫**：`git diff --stat origin/main...HEAD -- docker-release/ architecture/ codex/config codex/tools
  AGENTS.md skill-for-codex skill-for-claude codex/skills codex/runtime/aisoft_loop codex/runtime/aisoft_release` 为空；
  `git diff --stat origin/main...HEAD` 只含平台仓路径。

## 接口、数据与兼容性影响

- **handoff manifest（外部契约）**：`compatibility.sync_timer_unit` 新增；当前 operator 必填，legacy 只读。
  `HANDOFF_VERSION` 保持 `company-delivery-handoff/v1`（key 集合按 `operator_version` 分档，与 inventory v1/v2/v3
  「旧版只读」的既有模式一致，不新增 handoff/v2）。
- **CLI（外部契约）**：`build-bundle` 与 `collect-inventory --role scm-ci` 各新增一个必填参数；旧调用形态失败并返回
  argparse 错误（rc=2），不会静默沿用旧常量。
- **inventory 合同**：timer unit 由 enum 改 pattern；既有 1.2.0 evidence（`aisoft-inbound-sync@newemaint.timer`）
  仍匹配 pattern，历史 evidence 读取不受影响。
- **bundle 字节**：`operator/compatibility/` 内容随调用方 matrix 而变；同一组输入（含同一 matrix 字节）重复构建仍
  byte-identical（R-08 复制走既有 `_copy_new_file`，archive 走确定性 tar）。
- **sync/**：不改；timer 实例名只是 `%i` 的具体取值。
- **schema 文件**：runtime 不读 schema（自有 validator），schema 只作文档与外部校验；`$comment` 是 JSON Schema 标准键。
- **`03` §3 verification 判据**：grep 计数、守卫反向证明、NewEmaint #75 state 读回、integration NOT RUN 都是一次性
  证据，声明 `verification`。

## 风险与回滚约束

- 回滚 = revert 本 Issue 的唯一 PR；无数据迁移、无部署。
- 本 spec 是修改 `codex/tests/smoke.sh`、integration 脚本与 `test_company_delivery.py` 的授权，范围以 R-18～R-20 为限；
  不改 `AGENTS.md`、两侧技能源、`codex/skills/`。
- `collect-inventory --handoff-manifest` 走完整 payload 校验（含 release archive 哈希）：一次性 operator 动作，fail-closed
  优先于速度。

## 非目标

- 不改 `docker-release/`（#65 冻结）、`architecture/`、broker、标签 manifest、`codex/runtime/aisoft_loop`、
  `codex/runtime/aisoft_release`。
- 不做任何公司环境或 NewEmaint 部署；不改 NewEmaint 仓；不运行 integration `--execute`。
- 不清理 `README.md:23`、`13:60` 等根文档中「operator 1.2.0」历史叙述（状态句与参考记录，#233 F 组判定保留）。
- 不新增 handoff/v2、inventory/v4 合同版本。

## 未决问题

无。以下 4 项解读已于 2026-09-03 确认点 1 由人认可：

1. timer unit 来源：collector CLI 读**已验证 handoff manifest**（`--handoff-manifest`），不提供裸 `--sync-timer-unit`
   CLI 参数（Python API 仍显式接收 `sync_timer_unit` 供测试与 CLI 内部使用）。
2. handoff 合同版本：保持 `company-delivery-handoff/v1`，`sync_timer_unit` 按 `operator_version` ≥ 1.3.0 必填。
3. matrix 在 bundle 内的路径：`operator/compatibility/<调用方文件 basename>`，不固定文件名。
4. integration 脚本 `:209` 陈旧的 `1.1.1` 身份钉随 R-18 一并改为 `1.3.0`（同文件已触碰、不改外部行为、`--execute`
   本就 NOT RUN）。
