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

# Verification：真实 release 的格式化 Secret 扫描

## 环境与版本

- Planning baseline：freshly fetched `origin/main` =
  `7950d119ab5c949d914de172dac8606369483cd4`（#120 / PR #123 merge source）。
- Worktree：`/private/tmp/issue-124-secret-scan-false-positive`。
- Branch：`change/124-secret-scan-false-positive`；本轮新增 commits 为 `0d6e113`、`28bd268`、
  `b822ba2`、`28e4be4`（前序 T01–T04 历史保持不变）；当前无 push 或 PR。
- Exact external release：`006d0c43cafebff058889e3338d1e8bdcc8b661c`；约 412MB bytes 不在仓库中。
- 当前阶段：`APPROVED / T04 FIXED-REASON DIAGNOSTIC`。此前 structure-aware 实现正确 fail closed；人工现
  批准七个无参数 JSON-context reason code、synthetic no-echo tests 与一次 exact-release 脱敏诊断。该批准不
  允许输出任何内部内容或放宽安全语义；诊断不能可靠证明通用修复时必须再次停止。

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| broker Issue #124 read-back | PASS | Issue open、0 comments；标签精确为 `approved`、`complexity/complex`、`triage/enhancement`、`triage/ready-for-agent`、`type/security`；未创建重复 Issue |
| broker `git.fetch.main` + base pin | PASS | planning 时 `origin/main` 与 worktree base/HEAD 均为 `7950d119ab5c949d914de172dac8606369483cd4`；当前 commits 均后继该 base |
| readable tuple validation | PASS | `change-name 124 secret-scan-false-positive` 输出 exact branch；建立单一 worktree/branch/docs tuple |
| analyzer schema/render | PASS | validated analyzer 输出 `type/security`、forced complex、`spec-drafting`、四份 semantic documents mapping |
| current scanner static root-cause review | PASS | `_scan_bundle_payloads` 对所有 payload 做 Latin-1 raw-byte regex；`_mask_source_placeholders` 不识别 strict `:?required`；`images.tar` 未按 graph/layer 解析 |
| existing `docker-release/v2` seams review | PASS | strict Compose external-reference validator与 Docker/OCI path/member/digest/reachability gate 可复用；未查询外部工具文档 |
| mapped document resolver | PASS | `resolve-documents 124 --repo .` 精确返回四个 semantic basename，全部同 slug/date |
| planning diff whitespace | PASS | 对四个 untracked Markdown 分别执行 `git diff --no-index --check /dev/null <file>`，均无 whitespace diagnostic |
| T01 exact red | PASS | exact 2-test selector exit 1；`${PASSWORD:?required}` 在旧 scanner 下固定失败，不含 concrete 值 |
| T01 exact green | PASS | 同一 selector exit 0；`Ran 2 tests ... OK` |
| T02 exact red | PASS | exact ReleaseTransport + ArchiveScanner selector exit 1；缺 graph seam/bounds/blocked behavior |
| T02 exact green | PASS | 同一 selector exit 0；`Ran 25 tests ... OK` |
| T03 version/no-echo red → green | PASS | 同一 2-test selector先因 `1.0.0 != 1.0.1` exit 1，再 `Ran 2 tests ... OK` |
| fake bundle/archive suite | PASS | Bundle + ArchiveScanner `Ran 17 tests ... OK`；Docker 0、target facts NOT_READ |
| real harness default/guard | PASS | default 明确 `NOT RUN`；参数、clean tree、external root、双 temp output 与 cleanup 静态/负向检查通过 |
| real `006d...` integration harness | BLOCKED | clean `0bc3c1d...` candidate 上 artifact-only PASS；首次 build 固定 `SENSITIVE_CONTENT`；第二次 build/双 verify 未运行；临时输出 cleanup PASS |
| permitted top-level category replay | PASS / BLOCKED | `compose.model.json=PASS`、`compose.yaml=PASS`、`images.tar=SENSITIVE_CONTENT`；未输出值、片段、offset 或 inner path |
| T04 content-classifier red → green | PASS | safe source/JSONC 与 literal/duplicate/ambiguous negatives 先 RED，后 ArchiveScanner 7/7、Bundle 11/11 PASS；commit `bd35270` |
| T04 material-aware exact red → green | PASS（fake） | 同一 3-test selector 先 `FAILED (errors=3)`，后 `Ran 3 tests ... OK`；完整 PEM/known token/JWT/high-entropy/runtime 拒绝，source/example 通过，ambiguity blocked |
| T04 focused regression | PASS（fake） | ArchiveScanner + Bundle + ReleaseTransport `Ran 39 tests ... OK`；`git diff --check` PASS |
| real `006d...` post-decision replay | BLOCKED | clean `9abdb25...` artifact-only PASS；首次 build 对 `images.tar` 固定 `SENSITIVE_CONTENT`；第二次 build/双 verify 未运行；cleanup PASS |
| revised contract docs | PASS | `0d6e113` 记录完整 PEM/known token/JWT/credential URL/Authorization、source example 与 ambiguity 边界；未加入 path/digest/release allowlist |
| revised structure-aware red → green | PASS（fake） | exact selector 先 `FAILED`，后 4 tests PASS；最新 ArchiveScanner + Bundle + ReleaseTransport `Ran 39 tests ... OK`；commits `28bd268`、`28e4be4` |
| input immutability harness guard | PASS（fake/static） | `b822ba2` 增加 build 前后全输入指纹比较及 post-build artifact revalidation；默认 `NOT RUN`、guard test 与 `bash -n` PASS |
| real replay attempt 1 | BLOCKED | clean `b822ba2...`：artifact-only boundary PASS；首次 build 固定 `SENSITIVE_SCAN_BLOCKED`；第二次 build/双 verify 未运行；cleanup PASS |
| sanitized classifier replay | BLOCKED | 仅记录 `top_level=images.tar`、`classifier=JSON_CONTEXT` 与固定 code；未记录 inner path、value、snippet 或 offset；cleanup PASS |
| real replay attempt 3 / threshold | BLOCKED | clean `28e4be4...`：首次 build 再次固定 `SENSITIVE_SCAN_BLOCKED`；第二次 build/双 verify 未运行；cleanup PASS；触发同因三次人工升级门 |
| post-failure artifact revalidation | PASS | exact release 再次 `ok=true`、`contract_version=docker-release/v2`、`docker_calls=0`、`target_facts=NOT_READ`；临时输出计数 0，candidate tree clean |
| fixed-reason diagnostic approval | APPROVED / NOT RUN | reason allowlist 固定为七个无参数常量；实现、synthetic tests 与唯一一次 real diagnostic 尚待执行 |
| company/live checks | NOT RUN | 未连接公司内网，未访问两台公司 VM，未部署或读取 Secret/DB/target facts |

## Exact release 证据

| Layer | Result | Boundary |
|---|---|---|
| DockerLab 原位六文件 ↔ 本机临时副本 SHA256 | PASS（用户提供） | 只记录逐项一致结论，不记录命中值 |
| artifact-only verifier | PASS（用户提供） | `ok=true`、`contract_version=docker-release/v2`、`docker_calls=0`、`target_facts=NOT_READ` |
| baseline `build-bundle` | BLOCKED（用户提供） | artifact verification 后固定 `SENSITIVE_CONTENT`；输出目录已清理 |
| candidate `build-bundle` | BLOCKED（本次重放） | clean `28e4be4...` artifact-only PASS；`images.tar` 固定 `SENSITIVE_SCAN_BLOCKED`；没有读取、记录或猜测命中值 |
| Stage 00 local preparation | BLOCKED | 尚无 exact handoff bundle |
| company Stage 10–110 | NOT RUN | 必须等待 Stage 00 PASS 及后续逐阶段人工批准 |

## Acceptance criteria 结果

| AC | Result | 当前证据 / 下一 gate |
|---|---|---|
| AC-1 | BLOCKED / resumed | clean `28e4be4...` 首次 build 按获批安全合同 fail closed；现仅获准先执行固定枚举诊断，双构建/checksum equality/双 verify 仍未运行 |
| AC-2 | PASS | exact T01 red/green 覆盖 strict references 与 default/alternate/拼接/command substitution |
| AC-3 | PASS（fake） | sentinel、fixed code、CLI no-echo 与完整 output cleanup 通过 |
| AC-4 | PASS（fake） | canonical verified graph result驱动 config/metadata/layer/binary streaming；Docker 0 |
| AC-5 | PASS（fake） | config Env、layer config、cross-chunk binary、unsafe/duplicate/compression/resource bounds 均覆盖 |
| AC-6 | PASS（fake/review） | schema/source/doc/binary safe fixtures 通过；未增加 release/image/path/binary allowlist |
| AC-7 | PASS（fake） | operator `1.0.1`、handoff V1、repeat build 与 verify-handoff 兼容通过 |
| AC-8 | PARTIAL | focused/fake/diff、harness guard 与 T04 cleanup 已通过；full runtime、smoke、ShellCheck、review、CI 因 AC-1 阻塞未执行 |
| AC-9 | NOT RUN | 七个 fixed reason 的 synthetic no-echo tests 与唯一一次 real diagnostic 尚待执行 |

## 重复部署

- 第一次部署：`NOT RUN`；本 Change 不授权部署。
- 第二次部署：`NOT RUN`；T04 的双 bundle build 是本地确定性制品验证，不是部署。

## 故意失败与回滚

- 基线真实 fail-closed：`BLOCKED`，`SENSITIVE_CONTENT` 且输出已清理；只记录允许的三个顶层类别，未记录值。
- implementation red/green 与 archive negative fixtures：`PASS`；所有断言只使用 fixed code/message。
- source revert：`NOT RUN`；fake 与真实 T04 临时 output cleanup 均为 `PASS`。
- 数据恢复验证：`NOT RUN`；无数据库动作且不在授权内。

## Company/live 状态矩阵

| Scope | Result | 边界 |
|---|---|---|
| 公司 `gitea-ci` / `scm-ci` inventory 与 Stage 10+ | NOT RUN | 开发机不可访问公司内网；只可未来由人运行 |
| 公司 Gitea/Runner/Registry/cache | NOT RUN | 未安装、未配置、未验证 |
| 公司 `appserver` / `appserver-prod` | NOT RUN | 未读取 target profile、Secret、Nginx/PostgreSQL 或 host facts |
| service/timer/Actions production gate | NOT RUN | 必须保持 disabled/inactive，启用需未来独立批准 |
| database migration/restore、test/prod deploy | NOT RUN | 明确不授权 |

## 遗留风险与未完成项

- 当前 implementation/fake tests 不能写成真实 Stage 00 或公司执行 PASS。
- real fixture 在第二版 structure-aware 合同下曾达到同因三次 `SENSITIVE_SCAN_BLOCKED` 阈值；人工现只
  恢复一次固定枚举 JSON-context 诊断。若 reason 为 unavailable、仍属 ambiguity、表明真实 credential，或
  修复需要扩大现有语义，必须立即回到 `NEEDS_HUMAN_DECISION`。
- 任何需要读取命中值、增加 release/image/path broad allowlist、重建 release 或访问公司环境的方案都超出
  Spec，必须停止并请求新的人工决策。
- 最终 PR、required CI、merge 与公司部署均未发生；human merge 仍是未来唯一代码交付硬闸门。
