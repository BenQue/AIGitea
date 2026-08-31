---
issue: 229
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/229
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - platform-governance
  - shared-core
  - external-contract
  - cross-module
depends_on: []
status: approved
branch: change/229-project-label-write-path
created: 2026-08-31
updated: 2026-08-31
---

# Implementation plan：project_extensions 的 typed 写面

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | manifest 侧前缀合同：validator 强制扩展前缀互不包含/相等；broker 侧前缀解析与唯一匹配 helper（含全部 fail-closed 判定），无新操作 | - | pending |
| T02 | `gitea.labels.extension.define`：仓库级定义，create-only，既有返回 `existing-preserved` 不 PATCH；操作表 31→32 | T01 | pending |
| T03 | `gitea.issue.labels.extension.set`：Issue 级附加，按匹配前缀单维单值替换，缺定义 `TARGET_MISMATCH` 指向 `extension.define`；操作表 32→33 | T02 | pending |
| T04 | 化石兼容与消费者一致性：NewEMaint 形态 fixture 端到端、`aisoft-project-check` 行为不变、installer provenance 与全量回归 | T03 | pending |

每个 ticket 都保持仓库全绿，可由 `$implement #229 Txx` 独立执行与验证。
选 vertical slice 而非 expand→migrate→contract：本变更是纯 additive，
既有 31 条操作与三条既有 label 操作的行为逐字不变，不存在需要跨批次保持红/绿的宽重构。

**T01 单独成票的理由**：D2 的「唯一匹配一个已声明前缀」依赖「前缀互不包含」这个不变量，
而该不变量当前**不存在**（`gitea-label-manifest.sh:120,139` 只检查扩展前缀与 canonical 命名空间的重叠）。
先把不变量与 fail-closed 判定立住，两条写操作才有可依赖的地基；否则 T02/T03 各自实现一遍前缀判定。

## Expected touch points

范围提示，不授权扩大 spec。

**T01**
- `codex/agent/gitea-label-manifest.sh`（`aisoft_label_manifest_validate`：新增扩展前缀互斥断言）
- `codex/runtime/aisoft_host_access/broker.py`（`_label_manifest()` 附近：扩展前缀解析 + 唯一匹配/拒绝 helper，复用 `_typed_text` 的边界与六位 hex 颜色校验）
- `codex/tests/test-gitea-label-manifest.sh`、`codex/runtime/tests/test_host_access.py`

**T02**
- `codex/runtime/aisoft_host_access/contract.py`（`EXPECTED_OPERATIONS` +1）
- `codex/config/host-access-broker.json`（操作表 +1）
- `codex/runtime/aisoft_host_access/broker.py`（`execute()` 签名与 `arguments` 字典、`_gitea()` 转发、dispatch、`_define_extension_label`）
- `codex/runtime/aisoft_host_access/cli.py`（`--label` / `--color` / `--description` 的 `add_argument` 与 `main()` 传参）
- `codex/runtime/aisoft_host_access/runner.py`（一个固定方法，**不**暴露通用 `execute/request`）
- `codex/runtime/tests/test_host_access.py`（操作表、fail-closed、create-only、`test_cli_exposes_only_typed_issue_and_pull_fields` 的三处 `assert_called_once_with`）
- `codex/tests/test-host-access-broker.sh`（`:16` `.operation_count` 与 `:21` `[.operations[].name] | length` → 32）

**T03**
- 同 T02 的操作表五处（+1，最终 33），外加
- `codex/runtime/aisoft_host_access/broker.py`（`_set_issue_extension_label`：以匹配前缀构造 `in_dimension`，`targets` 固定 singleton；复用 `_replace_issue_label_dimensions`）
- `broker.py:2096` 的 `TARGET_MISMATCH` 文案：扩展前缀的目标改为指向 `gitea.labels.extension.define`
- `codex/tests/test-host-access-broker.sh`（计数 → 33，新增两条操作的 route/mutating/arguments 断言，缺参/多参/非法前缀/无 delete 的 CLI 回归）

**T04**
- `codex/runtime/tests/test_host_access.py`（化石 fixture 端到端）
- `codex/tests/test-project-check.sh`、`codex/tests/test-sync-gitea-labels.sh`（既有行为不变的回归）
- `codex/tests/test-install-host-access-broker.sh`（installer 动态计数与 provenance）
- 必要时 onboarding / project-align 文档补一句 canonical 与 extension 的两套 metadata 所有权

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 定义 + 附加两步 | T02/T03：`PYTHONPATH=codex/runtime python3 -m unittest -v tests.test_host_access.HostAccessBrokerTests` |
| AC-2 fail-closed 负向用例 | T01–T03：同上 + `bash codex/tests/test-host-access-broker.sh` |
| AC-3 不动其它维度（#115 同型断言） | T03：`test_host_access.py` 新增断言，比对操作前后完整标签集 |
| AC-4 单维单值与 no-op 零 PUT | T03：四条 fixture（`area/old+priority/high`、`area/old+area/new`、`area/new`、未定义目标） |
| AC-5 化石不被 PATCH | T02/T04：`test_host_access.py` 化石 fixture 断言 color/description 逐字不变 |
| AC-6 三条既有 label 操作行为逐字不变 | T04：`PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests -t codex/runtime` |
| AC-7 扩展前缀互不重叠 | T01：`bash codex/tests/test-gitea-label-manifest.sh` |
| AC-8 操作表 31→33 与全部 guard 同步 | T02/T03/T04：`bash codex/tests/test-host-access-broker.sh`、`bash codex/tests/test-install-host-access-broker.sh` |
| AC-9 smoke 全绿 | T04：`bash codex/tests/smoke.sh` |
| AC-10 test_host_access 全绿含 CLI kwargs | T02–T04：`PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests -t codex/runtime -v` |
| AC-11 四问裁决 | spec D1–D4 的 diff review |
| AC-12 判级投影 | `codex/tools/apply-classification-labels.sh --verify 229` 读回 `projected` |

每个 ticket 收尾必跑：

```
bash codex/tests/smoke.sh
PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests -t codex/runtime
```

## 部署与回滚

**无部署影响。** 本变更只改源码与 manifest，不执行安装、不触碰任何运行中的服务。

新操作对直接调用 `/usr/local/libexec/aisoft/host-access-broker` 的调用方需要两台主机
（Mac 与 gitea-ci VM）重装 broker 才生效——**该重装不在本变更范围内**，是合并后的独立前置步骤，
Mac 侧只能由人执行。本变更不宣称任何部署或生产就绪。

回滚：纯 additive，`git revert` 单个 merge commit 完全撤销源码侧。
已由新操作在远端创建的扩展标签不随 revert 删除（typed surface 无 delete，既定合同），
它们退化为与 NewEMaint 现状同型的「化石」，不影响任何既有维度。
