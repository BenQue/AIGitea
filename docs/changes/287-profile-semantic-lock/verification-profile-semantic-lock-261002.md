---
issue: 287
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/287
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - shared-core
  - schema-change
  - external-contract
  - platform-governance
depends_on: []
status: pending
branch: change/287-profile-semantic-lock
created: 2026-10-02
updated: 2026-10-02
---

# #287 Verification

## 基线与范围

- authoritative `origin/main`：`5c2cd726c9aeaee9d17541d8feb049e33881bbac`，2026-10-02 broker fresh fetch；共享 checkout 当时相同。
- Worktree：`/private/tmp/issue-287-profile-semantic-lock`；branch：`change/287-profile-semantic-lock`；owner：`01a0fc7c-027e-70a3-8871-beb484e4a8d8`，claim created。
- 历史 profile 对象：`6121838e05f1daefea5a8bb0679b4f906243432b` 和 `97b09a7a7db4ce079cb6779ba47df4a1d6b55919`，git show 可读。
- 机制复现使用 main 的 `node-sqlite-native-project.json` fixture，不是 SFM 历史 declaration；不能声称复现 Issue 的整个 lock_sha256。profile 两个 sha256 精确一致。
- 固定 today：2026-09-05；仅用于离线重放，未用此日期替代真实 live readiness。

## 合同起草阶段执行结果（历史记录）

| Command / check | Result | Evidence |
|---|---|---|
| broker #287 issue/comments read | PASS | open/needs-analysis；一条历史延后调度评论；未有已批准合同 |
| broker #288 issue read | PASS | Dockerfile digest fail-open 的独立机制；没有实现它 |
| broker git.fetch.main | PASS | 项目与 remote 绑定读回，以上 SHA |
| broker host.onboarding.check | PASS | main 禁止 direct/force push；required `CI / verify (pull_request)`；routine disabled |
| broker gitea.pulls.read open | PASS | 当时列表为空，无 #287 重复 PR |
| historical profile diff | PASS | compatibility_rules 最后一项 1增1删，version/机器投影不变 |
| V1 old-profile lock vs new prose profile | EXPECTED FAIL | LOCK_DRIFT；profile hash 6eb2458f…→7ed962a2…；catalog/declaration hash 不变 |
| valid delivery removal without bump | EXPECTED FAIL | LOCK_DRIFT，version 保持 1.0.0，机器投影改变 |
| candidate projection comparison | PASS | 去掉 description/compatibility_rules 后两历史 profile 投影相等；只是实验，非 runtime 已实现 |
| baseline architecture unittest discover | PASS | 57 tests，1.089s，OK；pattern test_architecture*.py |
| formal classification --apply then separate --verify 287 | PASS | type/platform + complexity/complex；result=projected |
| broker lifecycle projection/readback | PASS | spec-drafting；未 approved |
| actual-Issue draft contract loader | PASS | allowed_lifecycle spec-drafting；8 AC、4 mapped docs；未启动 |
| semantic document check | PASS | changes=145 pass=2 gap=0 |
| triage Agent Brief posted via installed broker | PASS | comment 11976；本地合同未 push，Issue 中明确待确认 |
| implementation acceptance | NOT RUN | 合同待启动确认 |
| full smoke / required CI | NOT RUN | 仅合同阶段，未 PR |
| installed / live consumer / SFM acceptance | NOT RUN | 未安装、未修改或校验 SFM；不声称旧 inventory 仍真 |

完整离线机制 receipt 见本目录 `baseline-profile-probe.json`。

## 合同起草阶段 Acceptance criteria（历史记录）

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | NOT RUN | V2 未实现；基线失败已保留 |
| AC-2 | NOT RUN | V2 未实现；合法漏 bump 基线失败已保留 |
| AC-3 | NOT RUN | 双 reader 未实现 |
| AC-4 | NOT RUN | 显式临时候选格式迁移未实现 |
| AC-5 | NOT RUN | 57 基线通过不能冒充改动后回归 |
| AC-6 | NOT RUN | full smoke 与实现验证未执行 |
| AC-7 | NOT RUN | 具体文档治理步骤 T01 待确认 |
| AC-8 | PASS（合同阶段） | 仅独立 worktree 合同草稿，无 runtime/其它仓/live mutation |

## 合同起草阶段风险与未完成项（历史记录）

- 旧 V1 必须保留严格失败；用户需确认一次显式迁移边界，不能假装新 reader 能恢复旧 profile 投影。
- 现有 broker 无 typed Matt triage projector；不通过直接 API/extension fallback 绕过。type/complexity 与 lifecycle 投影分别采用既有正式工具。
- baseline revision 的 lifecycle/source 校验不会保证当前 2026-10-02 所有 catalog entry 可用；本次实验固定日期不作当前部署证据。
- 所有实现、source 发布、CI、安装与实际消费者迁移尚未完成，Issue 不关闭、会话不归档。

## 正式 projector 的执行路径

本轮首次 dry-run 使用源 checkout 工具，其 same-directory-first 分支会选择源 broker wrapper。为严格遵循本会话“安装路径 broker”约束，后续将官方 projector 与两个依赖按字节不变复制到 `/private/tmp/287-classification-tools/`，不放 sibling broker，并通过其既有 fallback 使用 `/usr/local/libexec/aisoft/host-access-broker`。先重新 dry-run，再 apply 与 verify。没有改动任何工具、manifests 或操作表；没有 fallback 身份/直接 API。

verify 输出的既有 detail 含 “merged summary” 字样；本 summary 实际是未提交的本地草稿。真实可证明的是当前 labels 与本地映射 summary 的判级相符，不能称为已合并的合同。

## T01：已批准的独立文档合同步骤

- 用户在本聊天回复“确认”，批准本 spec 与 T01/T02/T03。原文件 hashes 与实际授权边界记录在 `contract-start-approval.json`。
- 重新读取 worktree AGENTS/README、03/04、spec/plan、Issue 完整评论；broker fresh fetch main 仍为 5c2cd726c9aeaee9d17541d8feb049e33881bbac；owner marker 与当前 CODEX_THREAD_ID 精确一致。
- broker 将 lifecycle 从 spec-drafting 置为 approved，再用实际 Issue 调用默认 approved contract loader：8 AC，frontier T01；receipt 见 `approved-contract-validation.json`。
- 修改 architecture README 并新增 ADR-0007：说明投影、完整 constraints、双格式 reader、V1 显式迁移、人工通知/重 lock、自动广播 NOT IMPLEMENTED、旧 release reader 边界与回滚。
- `aisoft_release.contract` 的 existing reader 以 strict keys、schema 与 schema_version 检查 V1；本轮只读，不修改或为 V2 授予 release 能力。
- 本轮没有 shell/script/runtime/schema/profile/catalog/reference 改动。完整 smoke/CI/安装/release/SFM 现场 NOT RUN；本步骤的文档检查通过不能继承为 T02/T03 验收。
- T01 完成后停止，fresh run 必须重读治理合同再实现 T02/T03，不新增启动确认。

### T01 审查与提交 receipt

- 初次 T01 原子提交：`4bbd840055f19c72f67d51bc4089e7db514bc13c`，9 个文件，仅 architecture 两份文档和本 Change 的 7 份合同/证据。
- Standards 独立只读审查发现 1 项 P2：plan 缺明确 AC→Txx 分配（03 分册要求）。已补 Ticket 列，区分 T01 文档应用、T02 功能与 T03 全量/一致性复核，不改变 spec 范围或验收标准。
- Spec 独立只读审查：0 actionable findings；V1/V2/constraints/广播/release 边界均匹配已批准合同。T02/T03 未实现不算 T01 遗漏。
- 提交后 exact #287 classification `--verify`：projected；semantic document check：changes=145 pass=2 gap=0；worktree 与共享 main 都 clean。
- 本次文档步骤完成后停在 fresh run 边界；后续 T02/T03 已授权，无需重复确认启动。

## T02 fresh run：V2 writer 与严格双 reader

- 起点 `c793118a81c0f6d20a1b52c3fbd0330c07e4e8a5`；broker fresh main 仍 `5c2cd726c9aeaee9d17541d8feb049e33881bbac`；真实 approved contract frontier T02，owner 匹配。fresh read hashes 见 evidence/t02-fresh-read.json。
- 先增加 highest seam 回归：7 tests 中 failures=2/errors=2，核心失败为历史 prose 输出不等和默认 writer 仍 1.0；保留 evidence/t02-red.log。不是把现有测试删掉制造红。
- runtime 现在默认 V2，带 profile-machine-v1 domain/marker；V1 expected build 显式保持原算法，仅已知版本可解析，CLI 按 lock 自身版本校验。原 V1 schema/reference/profile/catalog 未改。
- architecture targeted tests：70 tests / 2.392s / OK，见 evidence/t02-architecture-green.log；覆盖新 CLI 显式临时候选迁移、原 lock 无写入、未知版本/marker 混用/篡改、合法 slot移除/transition状态/constraints/delivery 漂移，version 不变仍红。
- release integration：5 tests / 0.042s / OK。既有 V1 round-trip 仍精确匹配原 reference；新 V2 architecture 校验成功但旧 release reader 因新增 marker 严格拒绝。release runtime 未改，不宣称 release V2 可用。
- 新增 release regression 首次运行出现测试插入位置导致 NameError；恢复原 catalog_revision 断言到原 V1 test 后修复，未删断言，5项完整通过。
- T02 完成，T03 full smoke/审查/最终候选尚未执行；CI/安装/live/SFM均 NOT RUN。

## T03：最终本地验收

| Command / check | Result | Evidence |
|---|---|---|
| historical V2 CLI prose / valid machine change | PASS | evidence/t03-cli-receipt.json；前后生成 byte-identical，既有 lock 对新说明 exit 0；合法 delivery 变更且 version 未变 exit 2 / LOCK_DRIFT，原文件不变 |
| protected scope bytes | PASS | evidence/t03-protected-bytes.json；31 文件与 base 字节相同，包括 AGENTS、catalog、V1 schema、全部 profiles/reference 和 release runtime |
| smoke / sandbox | SANDBOX_PATH_BLOCKED | evidence/t03-smoke-sandbox-blocked.log；临时 registry fixture 的 127.0.0.1 bind 被拒绝，非服务故障 |
| smoke / host default locale | FAIL（既有 locale 兼容问题） | evidence/t03-smoke-host-default-locale.log；registry 关闭后预期 exit 1，实际 0；#278 verification 已记录 Bash 3.2 + C.UTF-8 中文标点进入变量名的问题 |
| registry fixture / host C locale | PASS | evidence/t03-registry-c-locale.log；LC_ALL=C，仅修正执行环境，source 与断言未改 |
| full smoke / host C locale | PASS | evidence/t03-smoke-host-c-locale.log；LC_ALL=C bash codex/tests/smoke.sh exit 0；完整 runtime 992 tests / 87.172s / OK；static smoke checks passed；另含 source conformance 162 tests 与 harness mock，不能视为 live E2E |
| semantic documents / diff whitespace | PASS | evidence/t03-document-check.log：changes=145 pass=2 gap=0；git diff --check exit 0 |
| broker fresh main | PASS | evidence/t03-main-fetch.json；origin/main 仍 5c2cd726c9aeaee9d17541d8feb049e33881bbac，无需 rebase |
| exact Issue classification verify | PASS | evidence/t03-classification.json：issue=287 / projected / platform / complex；detail 的 merged summary 措辞不改变本地合同未合并的事实 |
| independent Spec / Standards review | PASS | 两轴只读 review 未发现 runtime 问题；README/ADR 旧状态 P2 已修并复核关闭；最终 receipt 的“未改测试”已明确限定为 smoke 重试之间；没有重写已批准的哈希合同 |
| push / PR / required remote CI / merge | NOT RUN | manual 最终 PR 提交确认尚未取得；本地测试不替代 required CI |
| installed / live / SFM / release V2 / deploy | NOT RUN | 不安装或触碰下游；release 仍 V1-only；自动跨仓广播 NOT IMPLEMENTED |

失败与成功执行的命令、log hash 和条件见 evidence/t03-smoke-receipt.json。此次未修改 shell、CI、broker、installer、controller、AGENTS 或 skills；smoke 自身包含既有静态检查与临时 fixture installer 测试，它们不等于实际工具安装。

### 最终 Acceptance criteria（source / local）

| AC | 结论 | 证据与边界 |
|---|---|---|
| AC-1 | PASS | historical before/after fixtures、ProfileChecksumTests 和 CLI；description/compatibility_rules 独立编辑及历史说明差异保持 V2 byte-identical |
| AC-2 | PASS | 合法 delivery/status/constraints/slot 移除及顺序/transition allowed states 改动精确 LOCK_DRIFT，version 不 bump；非法 component/allowed_states/transition/unknown 字段先在 schema/semantic 失败 |
| AC-3 | PASS | 全部既有 V1 reference 严格校验且字节不变；精确历史完整 profile hashes 保留；旧 V1 prose drift 继续失败；未知版本/marker/混用/缺失/额外字段/篡改只读拒绝 |
| AC-4 | PASS | CLI 显式临时候选 V1→V2、重复生成与 validate，原 V1 bytes 不变；离线测试禁止 socket，无迁移其它仓 |
| AC-5 | PASS | 70 architecture targeted 与完整 992 runtime 回归；catalog/declaration 原算法、version/exception/EOL/prohibited/provenance/digest 硬门保留；5 release integration tests 保留 V1 精确 round-trip 并拒绝 V2 |
| AC-6 | PASS（host C locale） | 全部现有 fixture/reference cross-check 与完整 smoke 通过；诊断不回显输入测试通过。默认 locale 独立失败仍保留，不称为通过 |
| AC-7 | PASS | README/ADR 与实现复核一致，字段边界、V1/V2、显式一次迁移、constraints、人工 relock 与自动广播 NOT IMPLEMENTED 均明确 |
| AC-8 | PASS | 独立 owner worktree；31 protected files 与 base 相同；无 #288、其它仓写入或真实 installer/service/protection/credential/deploy 操作 |

T01 受控文档步骤独立完成后停止；fresh run 的 T02/T03 均完成。最终候选停在 AWAITING_PR_CONFIRMATION / manual；批准启动不代表批准 PR、合并或部署。后续 exact head 与交互候选状态在会话回执中钉住，避免把文档 commit 的自身 SHA 循环写进内容。
