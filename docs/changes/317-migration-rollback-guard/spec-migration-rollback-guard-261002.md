---
issue: 317
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/317
change_type: bugfix
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - data-migration
  - external-contract
  - shared-core
  - rollback
  - security
  - platform-governance
depends_on: []
status: approved
branch: change/317-migration-rollback-guard
created: 2026-10-02
updated: 2026-10-02
---

# 数据库迁移后容器回退兼容合同

## Problem Statement

新 release 完成数据库迁移后，旧容器可能无法读取新 schema。当前 release runtime 在候选健康失败后自动启动 current_release；显式 rollback 仅检查 previous_release。容器标签、image digest、stage receipt、曾经完成的 migration receipt 均不证明旧镜像适用于数据库的当前位置。应用薄编排不能阻断 runtime 内部路径，必须在平台统一修复。

## Solution

旧镜像启动前执行同一个迁移兼容 gate。系统独立记录数据库迁移位置，保持失败后的真实位置；只有可证明相同位置或可信、精确且未过期的兼容依据才允许启动。未知状态 fail closed，不启动旧容器、不 restore 数据库。报错明确区分候选失败、兼容性拒绝与已允许但执行失败。

## User Stories

1. 作为发布操作员，我希望迁移后未知兼容性阻断旧镜像，以免错误回退损坏业务。
2. 作为应用维护者，我希望 phased activate 与 legacy deploy 使用相同 gate，避免绕过。
3. 作为操作员，我希望显式 rollback 也验证数据库当前位置，而不是只看容器 previous_release。
4. 作为操作员，我希望 rollback 失败后恢复原 current 容器也受同一 gate 保护。
5. 作为维护者，我希望相同 migration identity 的无新迁移 release 保持 migrate-noop 与正常 activation。
6. 作为操作员，我希望跨 identity 的已验证兼容可以通过 exact 依据受控放行。
7. 作为审计者，我希望依据绑定 target、release、migration 和不可变 bytes，无法跨环境重放。
8. 作为维护者，我希望旧 state 可读取而缺失事实明确 untracked，禁止伪造顺序。
9. 作为操作员，我希望失败不会把数据库位置回写成旧 release，也不会错误宣称旧容器 healthy。
10. 作为应用 consumer，我希望固定新的人工 merged SHA 后使用平台 API，不复制回退状态机。
11. 作为审计者，我希望 CLI 只输出安全的原因码，Docker stderr 和 Secret 不进入证据。
12. 作为平台维护者，我希望未获现场授权时通过既有 FakeDocker seam 验证零旧启动边界。

## Implementation Decisions

### 数据库位置与可信事实

新增 `docker-release-state/v3`，保留 v2 字段并增加 `database_revision`：严格对象，字段为 `status`（`known|untracked|uncertain`）、`migration_identity`（SHA256 identity 或 null）、`generation`（非负整数）。实际状态合法组合由 schema/parser 同时检查。generation 只在真实 migration 尝试前递增；不随容器成功/回退递减。

每次真实 migration 调用前原子写 `uncertain` 及 candidate migration identity、generation；成功写 `known`，失败/中断保持 uncertain。空的新状态为 untracked，不能从空 state 推断数据库未发生过迁移；无 migration 的 release 不改变数据库位置。`completed` 命中仍保持 #305 的 migration-noop 语义，不运行迁移、不重写原 receipt 的 release_id、不让旧 identity 覆盖数据库当前位置。activation 的原 completed receipt 判据保持，不能用回退安全控制恢复 #305 的错误门。

合法 v1/v2 state 只读升级为 v3/untracked，generation=0；保存时写 v3。不能根据字典顺序、receipt.release_id、current_release 或任意一个 completed record 猜当前数据库位置。旧 state 有多个已完成 identity 更不能宣称已知。迁移 outcomes 中任意 started/failed 不可由兼容依据掩盖或重跑；需独立现场处置。

### 兼容判据

自动相同位置放行必须同时满足：database_revision=known；数据库 identity 与候选及回退 release 的 manifest migration identity 三者相同且非 null；对应 migration receipt=completed；不存在未处置的 started/failed。相同 identity 可由不同 release 实际执行，不要求 receipt.release_id 等于本次 release。仅两份 manifest 都 migration=null 不能证明数据库位置，必须使用下述可信依据。正常 initial deploy 无旧容器，失败报告 candidate failure；不虚构 rollback success。

其余情况（不同 identity、null、untracked）只允许 exact 兼容依据。uncertain 或 migration started/failed 固定拒绝，即使存在依据也不得 bypass。依据不是 artifact producer 的声明或 `--allow-rollback`；producer 不得自行生成现场授权。

### Operator 管理的兼容依据

目标 profile 可选新增 `rollback_compatibility_file`：绝对路径，位于 release_root/state_root/env_file 外的受保护 operator 配置区。未声明表示没有显式依据。旧 profile 与 v1/v2 manifest 无需重写。Runtime 不接受 CLI shell、路径 override、布尔 bypass；fixed action gate argv 与授权边界保持。

依据 envelope 为 `docker-migration-rollback-compatibility/v1`，由管理该 target profile 的 operator 独立安装；0400/0600、非 symlink regular file、owner 与受保护 profile owner 相同或 root，父目录不得允许 group/world 写；读取限量、严格 JSON、拒绝重复/未知字段，open/fstat 验证同一文件，避免路径替换。不得在本票 provisioning live 依据。

每条记录严格绑定：profile_id、environment、expected_hostname、compose_project、source_repository；candidate_release、rollback_release 两个 full SHA；两份原始 release manifest SHA256；candidate_migration_identity、rollback_migration_identity；database_migration_identity；数据库 revision 与完整 migrations ledger 的 canonical fingerprint；verified_at、expires_at（UTC RFC3339，verified_at <= now < expires_at）；safe evidence_id 与 result=`compatible`。canonical fingerprint 对 profile namespace、database_revision 和全部 migration records 计算，不包含 last_result、current/previous 容器指针或 Secret，因此同一 migration 状态可供自动回退和显式回退使用，迁移一旦变化立即过期。

known 位置时 observed database identity 必须相等；untracked 时 operator 的观测是唯一外部可信事实，必须绑定 exact 未跟踪状态 fingerprint，runtime 不据此改写成 known、不缓存永久批准。数据库离线变更/restore 后 operator 必须撤销旧依据并重新验证；profile 定义的数据库身份与外置 env 由 operator 管理，runtime 不读取连接串生成可公开 hash。绑定 target 不构成对带外数据库修改的探测保证。

记录含非兼容 result、未来时间、过期、identity/checksum/fingerprint/target 任一不符，或存在多个匹配记录，一律拒绝，不把 invalid evidence 降级成无文件 fallback。缺失依据拒绝为稳定原因。被拒记录内容、路径、连接串、Docker 输出不回显。

### 所有旧容器启动与失败语义

统一覆盖 activate 自动回退、v1/v2 legacy deploy 自动回退、显式 rollback、以及显式 rollback 失败后恢复先前 current 的路径。旧 release 的 artifact/host/staging/本地 image 精确校验继续成立，不能以兼容依据代替任何旧闸门。检查 compatibility 必须发生在旧 release transport.prepare/up 之前。read-only 验证可以执行；不确定兼容性旧容器启动数必须为零。

候选启动失败且无可回退 release：候选失败；有可回退 release但 gate 拒绝：`ROLLBACK_BLOCKED`；gate 允许、旧容器启动或健康失败：`ROLLBACK_FAILED`；gate 允许且旧容器恢复健康：仍返回候选激活失败，不把发布标为成功。CLI 保持非零失败出口，分别给出安全 code/message；state.last_result 写相应阶段结果。current_release 仅在真实成功后变更，失败时保留记录但不将指针当健康证据，status 继续读取 exact runtime health。绝不自动执行 migration down、database restore 或把 migration position 改回旧 identity。

### 治理文件授权与 fresh-run 边界

本 spec 获合同启动确认后，明确授权独立 T01 只修改 release 治理合同文档及本 Issue 语义文档，并停止。范围仅为 Docker release README、新的 versioned migration-rollback contract 说明；不修改本次遵循的 AGENTS.md、CLAUDE.md、provider/controller、CI、broker、installer 或 host permissions。

后续 fresh run 必须重新读取本仓库 AGENTS/README、T01 发布合同、本 spec/plan 和 worktree claim 后才实施 T02/T03 runtime/schema/tests。合同启动确认同时授权仅对 #317 进行判级/lifecycle/triage 投影和发布合同 brief（均经 project-scoped broker 可用 typed surface）；不更改其它 Issue。2026-10-02 用户直接回复“批准”后，首次拒绝的 live classification 写入可依精确授权重新执行；不存在的 triage typed 操作报告 GAP，不绕过 broker。批准 T01 不提供 merge/安装/部署权限。所有来源最终进入本 Issue 唯一 manual PR。

### 固定证据闸门修订（2026-10-02 第二次直接批准）

用户在审阅 `evidence/governance-amendment-proposal.md` 后直接回复“批准”，绑定
`#317` / `change/317-migration-rollback-guard` / `manual`。完整授权记录见
`evidence/governance-amendment-approval.json`；原送审草案保留为历史证据，当前授权以本节为准。
既有数据库兼容行为与 AC-01–10 不变；只补充当前 source 的精确证据闸门范围。

明确将 `codex/tests/check-release-evidence-boundary.py` 和
`codex/runtime/tests/test_release_evidence_boundary.py` 加入本票 allowlist。除此以外不增加治理
实现文件；不改 smoke.sh、CI workflows、AGENTS/CLAUDE、Controller/provider/broker、installer、
权限、现场配置或应用仓。本票仍只有一个最终 manual PR。

- `BASELINE`、`SCOPES`、`CONTENT_EXEMPT`、`RUNNER_BEFORE`、`RUNNER_AFTER`、
  `EVIDENCE_SHA256` 及原 historical regression snapshot 完全保持；历史 evidence bytes 不变。
- Existing-source pin allowed set 只增加 `codex/runtime/aisoft_release/contract.py`、
  `codex/runtime/aisoft_release/errors.py`、`codex/runtime/aisoft_release/state.py` 与
  `docker-release/schema/target-profile-v1.schema.json`；runner hash 推进为实际当前 bytes，
  transport/matrix 原有 hash 保持。新增 allowed paths 均使用上述完整 repository-relative path。
- 独立固定 `CURRENT_ADDITIONS` 只允许5个新增对象：
  `codex/runtime/aisoft_release/rollback_compatibility.py`、
  `docker-release/schema/state-v3.schema.json`、
  `docker-release/schema/rollback-compatibility-v1.schema.json`、
  `docker-release/contracts/migration-rollback-v1.md`、
  `docker-release/examples/rollback-compatibility-v1.example.json`。
  每项固定 mode `100644` 和经过审查的真实 SHA256；expected file set 为历史集合与这5项之和。
- Baseline 与新增对象都逐项验证 disk/index exact bytes 和 mode；未知、缺失、改名、symlink、
  mode/hash drift、额外 byte 一律 fail closed。不能使用 glob/目录/content 豁免或 CLI override。
  正常 checker run 不自动重算“被认可”的 hash。合同文档或 review 修复导致 bytes 变化时，
  必须先记录、审查真实新 SHA256，再更新固定 pin。
- Historical 与完整 current release regression 都须真实执行，前后再验 source identity；
  保留树外 bytecode isolation，历史真实 evidence 不能成为当前 real-E2E PASS。
  `current_real_e2e`、`installed`、`company_live` 继续 `NOT_RUN`；本票不运行真实 Docker/DB。

T04 是独立、只修改治理合同与本票记录的步骤：应用本节及 plan/versioned contract 后本地
提交并停止，检查器、tests、pins 和 runtime 在 T04 不改。后续 fresh run 重读 AGENTS/README、
#320 最新共享合同、本 spec/plan/versioned contract 与单写者 claim，才实施 T05 的两个精确文件。
T05 完成 targeted boundary regression、完整 checker/release suite/smoke 和两轴 review 后，
T03 才能结项并请求唯一最终 PR 提交确认。本次修订批准不授权 push/PR/merge/安装/部署。

## Testing Decisions

使用既有 public `ReleaseRuntime` + FakeDocker + 临时 state/profile/release fixture 的最高测试 seam，不模拟内部 gate 的成功返回。每个拒绝场景检查旧 SHA 的 up 数为零、零恢复、state 保留数据库位置与真实 last_result；每个允许场景同时检查 image/release/service/health 硬门。旧测试中默认不同 migration identity 的健康失败/回退成功用例不能继续作为“安全”正例，应补 exact compatibility fixture 或显式选择 shares_migration_with；保留不同 identity 的无依据负例。

## Acceptance criteria

- [ ] AC-01：activate 的不同 identity、无依据健康失败旧 up=0，返回 ROLLBACK_BLOCKED，不虚报已恢复。
- [ ] AC-02：legacy deploy（v1/v2）与显式 rollback 同样 fail closed，恢复 current 的路径也执行同一检查。
- [ ] AC-03：错目标、错任一 release/migration/checksum、过期/未来/重复/损坏/不安全权限/路径的依据均拒绝，旧 up=0。
- [ ] AC-04：正确 exact operator 兼容依据可放行跨 identity，原 staging/local image/health 硬门保持；旧启动失败为 ROLLBACK_FAILED。
- [ ] AC-05：已知同 identity、不同 release receipt 保持 migration-noop、正常 activation 和兼容回退；原 receipt.release_id 不改写。
- [ ] AC-06：migration uncertain/failed、候选迁移完成激活失败、C 已迁移但未激活、A/B同 identity但 DB 已到 C，以及无 migration 的 release，均按数据库真实位置判定；不能用候选身份掩盖 C。
- [ ] AC-07：v1/v2 state/profile/manifest 读兼容，缺位置为 untracked，不自动猜测；依赖 operator exact 依据的路径无永久提升。
- [ ] AC-08：同 SHA健康 no-op、锁、原子 state、原 staging/image/Compose/host-role/security gates 保持，无绕过；所有路径零自动数据库恢复。
- [ ] AC-09：CLI 安全 code 区分候选失败、回退阻止、回退执行失败，非零出口和 state 状态可读回，fixture Secret 不出现在 stdout/stderr/evidence。
- [ ] AC-10：consumer 说明给出 optional profile/evidence/state 升级、失败处理和人工 merged SHA pin 规则；本票不改 NewEMaint pin。
- [ ] AC-11：固定 source checker 只认可新增4个 existing-pin allowed paths 与5个 exact additions；historical baseline/scope/exemptions/evidence及transport/matrix原hash保持。
- [ ] AC-12：新增对象的 exact disk/index bytes/mode 正例通过；extra byte、staged-only drift、删除/改名/symlink/mode、unknown addition/untracked extra、非法hash/mode或历史evidence加入pin均拒绝。
- [ ] AC-13：historical/current regressions、前后source identity与bytecode isolation保持，完整 checker/release suite/smoke实际通过；current_real_e2e/installed/company_live仍NOT_RUN。

## Out of Scope

不修改 NewEMaint #229、不更新应用 pin、不安装 runtime/skills/兼容依据、不创建目标 grant/Secret、不 workflow dispatch、不操作真实 Docker/数据库/生产、不 merge/直推 main/force、不更改既有不可变 release bytes、不提供数据库兼容性自动探测、签名 PKI 或通用部署编排。

## 风险与回滚约束

state v3 写入后旧 runtime 不识别，不能直接降级到不含安全 gate 的旧平台；发生源码回退时保留本 guard 或采用 forward fix。v1/v2 原始 state 的受保护备份只能作审计，数据库发生迁移后不得通过恢复旧 state 制造安全证明。生产事故操作仍走消费项目的独立确定性脚本/授权。

## 未决问题

无未决实现方向。第一次直接“批准”确认数据库位置/可信依据/schema与T01/fresh-run合同；
第二次直接“批准”明确授权本节的两文件证据治理修订与T04停止/T05 fresh-run步骤。
保留2026-09-21的平台先行决定。任何其它范围扩张或信任来源改变仍须停止升级。
