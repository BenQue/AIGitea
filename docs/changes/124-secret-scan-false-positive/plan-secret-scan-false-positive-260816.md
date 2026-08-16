---
issue: 124
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/124
change_type: security
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - security
  - shared-core
  - cross-module
  - external-contract
  - artifact
  - deployment
  - deployment-boundary
  - compatibility
  - rollback
depends_on: []
status: approved
branch: change/124-secret-scan-false-positive
pr_url:
created: 2026-08-16
updated: 2026-08-16
---

# Implementation plan：真实 release 的格式化 Secret 扫描

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | Compose/text scanner 端到端切片：严格 external-reference lexer、concrete-value/no-echo 结果与 fake bundle 正负测试（AC-2、AC-3、AC-6） | - | implemented `9b780e0` |
| T02 | image archive 端到端切片：复用 verified Docker/OCI graph、有界 config/layer/binary scan 与 archive 负向 fixtures（AC-4、AC-5、AC-6） | - | implemented `42087b2` |
| T03 | builder 集成切片：typed dispatcher、固定错误 code、清理/确定性、operator `1.0.1` 与文档兼容性（AC-3、AC-7） | T01、T02 | implemented `fa0596c` |
| T04 | exact `006d...` repo-external integration：material-aware scanner 修订、artifact-only → 双构建 → checksum equality → verify-handoff；不提交 412MB bytes（AC-1、AC-9、AC-10） | T03 | **BLOCKED / NEEDS_HUMAN_DECISION**；二级 role 为 `PACKAGE_METADATA`，通用修复后首次 real build 返回 `SENSITIVE_CONTENT`，按实际 credential signal 停止 |
| T05 | 全量回归、静态/安全审查、mapped verification 与唯一 PR 人工合并交接（AC-8） | T04 | **NOT RUN / blocked by T04** |

依赖图：`T01 ─┐`、`T02 ─┴→ T03 → T04 → T05`。T01/T02 是两个独立 frontier；任何 ticket 遇到
no-echo、scope、format 或真实 bytes 冲突都停止，不跳到下游。

本轮结果：二级 real diagnostic 固定为 `source_role=PACKAGE_METADATA`；通用 package scalar-map 正反
fixtures 与修复已完成，但 clean candidate 的首次完整 real build 返回 `SENSITIVE_CONTENT`。该结果按批准
合同属于实际 credential signal，故立即回到 `NEEDS_HUMAN_DECISION`；不得再运行第二/第三次尝试、诊断
命中内容或增加 release/image/path/digest 特判。T05、push、PR、CI 均未开始。

## Ticket details

### T01 — Compose/text scanner

1. 先在 `CompanyDeliveryBundleTests` 新增同一 seam 的 red tests：完整 `${NAME}` 与
   `${NAME:?required}` 通过；default/alternate/拼接/command substitution/concrete sentinel 失败；捕获
   exception 与 CLI stdout/stderr 证明 sentinel 不出现且输出清理。
2. 新建 stdlib-only scanner/tokenizer。parser 只识别 Spec 的精确外部引用，不用 optional brace regex、
   `.*` 或整段 `${...}` 替换；chunk boundary 必须可重放。
3. `compose.model.json` 调用既有 strict model/security validator；`compose.yaml` 走 token-aware scalar scan；
   operator/release 普通文本保留现有精确 placeholder，同时修正 concrete-literal 分类。
4. 以 fake release 从 `build-bundle` 入口跑 green，证明不是孤立 helper test。

### T02 — Format-aware image archive scanner

1. 将 `aisoft_release.transport` 已有 outer graph validation 提取成共享只读 verified result；现有
   `validate_offline_artifact` 行为和错误保持兼容，并用 `ReleaseTransportTests` 固定 graph parity。
2. scanner 不 extract：流式遍历全部 reachable Docker/OCI config、attestation 和 layers；支持
   uncompressed/gzip layer，锁定 inner path/type/duplicate 和 8 MiB JSON、200,000 entries、2 GiB member、
   8 GiB expanded-byte bounds。
3. 对 config Env、structured/runtime-config text、generic text 和 binary 应用 Spec 的分层规则；所有内容至少
   经过 high-confidence byte signature scan，未知/超限返回固定 `SENSITIVE_SCAN_BLOCKED`。
4. fixture matrix 包含 safe source/schema/doc/binary、config concrete Secret、layer config Secret、跨 chunk
   binary signature、unsafe/duplicate member、unsupported compression 和 resource bounds；只断言固定 code，
   不打印内层 path/value。
5. 从 fake `build-bundle` 入口证明 safe archive PASS、敏感/不可扫描 archive fail closed 且清理输出。

### T03 — Builder integration、版本和确定性

1. 用 typed payload dispatcher 替换 `_scan_bundle_payloads` 的 raw Latin-1 whole-file path；scanner 必须在
   handoff manifest/archive 发布前完成，失败路径沿用完整 cleanup。
2. 保持 `SENSITIVE_CONTENT`，新增 `SENSITIVE_SCAN_BLOCKED`；CLI 只输出固定安全消息。验证
   `docker_calls=0`、`target_facts=NOT_READ`，不得引入 subprocess/Docker/target read。
3. `company-delivery/VERSION` bump 为 `1.0.1`，同步 README/runbook/templates/tests；handoff V1 和六文件
   bytes/checksum contract 不变。
4. 同一 fake input/UTC/source 构建两次并比较 archive SHA；执行 `verify-handoff`、single-byte tamper 与
   legacy security negatives。

### T04 — Exact real-release integration regression

1. 先实现 `JSON_RESOURCE_LIMIT`、`JSON_PARSE_UNSAFE`、`JSON_SOURCE_ASSIGNMENT_AMBIGUOUS`、
   `JSON_RUNTIME_ENV_INVALID`、`JSON_SOURCE_SENSITIVE_AMBIGUOUS`、`JSON_GENERIC_SENSITIVE_AMBIGUOUS` 和
   `JSON_REASON_UNAVAILABLE` 七个无参数 reason code；synthetic fixtures 必须证明普通 CLI 不输出 reason、显式
   diagnostic 只输出 fixed code/top-level/classifier/reason，且所有输入 sentinel 都不出现。
2. 对 exact release 只运行一次固定枚举诊断；不得输出 inner path、key/path、值、片段、长度、offset、hash、
   计数或异常。只有 reason 证明可在既有结构感知语义内作通用修复时才继续；否则立即停止。
3. 当一级 reason 为 `JSON_SOURCE_SENSITIVE_AMBIGUOUS` 时，再实现 `SCHEMA`、`SOURCE_MAP`、
   `PACKAGE_METADATA`、`I18N`、`EXAMPLE`、`OTHER` 六个 fixed source role；冲突/未知必须 `OTHER`。为每个
   role 建立成对 no-echo fixture，证明普通 CLI 不输出 role，再只运行一次二级 real diagnostic。
4. 只有二级 role 支持 Spec 已批准的通用结构规则时，才继续同一 exact selector 的 structure-aware
   red/green：完整且匹配的 PEM material、known token/JWT、
   含真实 userinfo 的 credential URL、完整具体 Authorization block 与 runtime-config concrete credential 必须
   拒绝；source/doc/schema/test-fixture 中的示例、regex、不完整 header 不得误报；context 不明确时固定
   `SENSITIVE_SCAN_BLOCKED`。不得增加 path/digest/release allowlist。
5. 新增显式 `--execute`、默认只报 `NOT RUN` 的 integration harness；只接受 absolute repo-external
   release root、固定 release ID `006d0c43cafebff058889e3338d1e8bdcc8b661c`、clean candidate repository 与
   两个新 mode `0700` 临时输出目录。harness 不访问网络、Docker 或 target profile。
6. 先调用现有 `verify-artifact`，断言 `ok=true`、`contract_version=docker-release/v2`、
   `docker_calls=0`、`target_facts=NOT_READ`，并依赖 release manifest/inventory 验证六文件 exact checksum。
7. 固定同一 `created-at`，顺序构建两次；断言两份 archive SHA256 相等、两份 `verify-handoff` PASS、source
   SHA 为 candidate full HEAD、release ID 精确匹配。只输出 fixed status/identity/checksum，不输出扫描内容。
8. 无论成功或失败都删除两个临时 bundle/output；以 `git status --short` 和 size/path guard 证明 412MB
   bytes 未进入 index/worktree。真实失败继续记录 Stage 00 `BLOCKED`，不得修改 release bytes 或添加豁免。

### T05 — 收口与人工 merge gate

1. 重跑 focused tests、company-delivery suite、release transport/contract suite、完整 runtime suite、smoke、
   JSON parse、shell syntax、ShellCheck（可用时）、diff/no-secret 和 code review。
2. 将 exact red/green command、最小安全输出、真实 integration fixed result、candidate commit 与全部
   `NOT RUN`/`BLOCKED` 写入 mapped verification；不写入 412MB bytes、临时路径或命中值。
3. Controller 仅在合同 `approved` 后校验 exact tuple/allowlist/commit，再 fast-forward push 并创建或更新
   唯一 PR；PR body 恰有一行 `Closes #124`。跟踪 exact final head required CI，AI 不 merge、不 deploy。

## Expected touch points

- **T01**：`codex/runtime/aisoft_company_delivery/secret_scan.py`（new）、
  `codex/runtime/aisoft_company_delivery/bundle.py`、`codex/runtime/tests/test_company_delivery.py`。
- **T02**：`codex/runtime/aisoft_release/transport.py`、可选只读 internal dataclass/module、
  `codex/runtime/tests/test_release_transport.py`、`codex/runtime/tests/release_test_support.py`、
  `codex/runtime/tests/test_company_delivery.py`。不得改变 stable release CLI 或 Docker mutation path。
- **T03**：`company-delivery/VERSION`、`company-delivery/README.md`、`company-delivery/runbook.md`、必要的
  versioned templates，以及 T01/T02 runtime/tests。不得修改 handoff/evidence/inventory schema version。
- **T04**：`codex/tests/integration/test-company-delivery-real-release.sh`（new）及其纯 fake preflight test；
  real release root/output 只在 repo 外临时存在。
- **T05**：`docs/changes/124-secret-scan-false-positive/` 四份 mapped 文档；远端只允许唯一 change branch/PR。

若实现证明需要触碰 NewEmaint repository、release bytes、credential/profile、company host、数据库、部署、
Gitea live config 或当前治理文件，立即标记 `NEEDS_HUMAN_DECISION`，不得把它当作 ticket 内偏差。

## 数据库迁移

无。不得运行 PostgreSQL migration、restore 或读取业务数据库。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | 经单独执行授权后：`bash codex/tests/integration/test-company-delivery-real-release.sh --execute --repository-root <clean-candidate> --release-root <repo-external-parent> --release-id 006d0c43cafebff058889e3338d1e8bdcc8b661c`；断言 artifact-only zero-target、双构建同 SHA 与双 verify-handoff |
| AC-2 | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=codex/runtime python3 -m unittest codex.runtime.tests.test_company_delivery.CompanyDeliveryBundleTests.test_compose_external_reference_grammar codex.runtime.tests.test_company_delivery.CompanyDeliveryBundleTests.test_compose_default_and_command_substitution_fail_closed` |
| AC-3 | 同一 focused suite 的 sentinel/no-echo/cleanup tests；CLI subprocess 只断言 fixed code/message 与 sentinel absence |
| AC-4 | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=codex/runtime python3 -m unittest codex.runtime.tests.test_release_transport.ReleaseTransportTests codex.runtime.tests.test_company_delivery.CompanyDeliveryArchiveScannerTests.test_verified_graph_is_scanned_without_docker` |
| AC-5 | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=codex/runtime python3 -m unittest codex.runtime.tests.test_company_delivery.CompanyDeliveryArchiveScannerTests` |
| AC-6 | T01/T02 safe fixtures + review：不存在 release SHA/image digest/path/extension/whole-binary skip allowlist |
| AC-7 | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=codex/runtime python3 -m unittest codex.runtime.tests.test_company_delivery.CompanyDeliveryBundleTests`；fake repeat-build checksum、verify-handoff、version/schema assertions |
| AC-8 | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests -p 'test_*.py'`；`bash codex/tests/smoke.sh`；`bash -n`/ShellCheck；JSON parse；`git diff --check origin/main`；人工 scope/no-secret review |

新 test selector 名是 plan contract；TDD red 必须先以完全相同 selector 失败，再在 green 后记录 exit code 与
最小输出。real harness 未得到单独执行授权或缺少 external bytes 时必须写 `NOT RUN`，不能用 fake fixture
替代 AC-1。

## 部署与回滚

本 Change 不部署。T04 仅在本机从 repo-external exact bytes 生成并删除临时 handoff，用于 Stage 00 local
preparation regression；它不是 test/prod deployment。

source 回滚为单 PR revert；operator `1.0.0` bundle 保持不可变。任何 scanner/real fixture 失败都删除临时
输出并把 Stage 00 保持 `BLOCKED`；公司 Stage 10–110、服务/timer、数据库和 production 始终 `NOT RUN`。
