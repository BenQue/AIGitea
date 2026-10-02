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

## 执行结果

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

## Acceptance criteria 结果

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

## 遗留风险与未完成项

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
