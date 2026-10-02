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
status: approved
branch: change/287-profile-semantic-lock
created: 2026-10-02
updated: 2026-10-02
---

# #287：profile 说明编辑与机器合同哈希分离

## 目标与原因 / Problem Statement

平台 profile 中的说明被润色后，下游 declaration、catalog 与机器取值全没变化，已提交的 lock 却失效。当前 `profile_sha256` 是 strict JSON 解析后 canonical bytes 的哈希，不是原始磁盘字节：格式和 object key 排序本来就不会漂移；string/array 内容会。问题应在哈希合同边界解决。

## 方案比较与建议 / Solution

| 方向 | 散文编辑 | 机器变更漏 bump | 兼容代价 | 外部副作用 | 结论 |
|---|---|---|---|---|---|
| A：机器投影哈希 | 新格式稳定 | 仍检测 | 旧 V1 一次显式迁移 | 无 | 推荐 |
| B：全量哈希加广播 | 仍红，但通知 | 检测 | 每次散文需下游 commit | 需消费者名册、跨仓权限、幂等开票/投递与故障语义 | 本次不选 |
| C：version 替代 hash | 不 bump 则稳定 | 会漏检，须另建跨版本/基线 CI 规则 | version 已存在；仍需新 schema | 新增发布治理规则 | 不单独采用 |

采用 A，保留现有 version 和其 declaration 匹配校验。显式版本用于兼容声明与人类变更审阅；内容哈希仍负责检测漏 bump 的机器变化，不新增“版本相等则忽略 hash”的路径。

## User Stories

1. 作为 profile 维护者，我希望润色说明不触发新格式消费者重 lock。
2. 作为应用维护者，我希望 slot、状态和 transition 变动即使漏 bump 也被检测。
3. 作为运维审阅者，我希望 constraints 的备份、存储、并发等约束仍受哈希保护。
4. 作为现有 V1 消费者，我希望校验器继续严格检查原哈希，而不替我修改 lock。
5. 作为需要迁移的消费者，我希望升级工具后在自己 Change 内生成候选并审阅新 schema。
6. 作为审阅者，我希望未知 hash 算法、篡改 checksum、旧客户端读新 lock 均明确失败。
7. 作为 #288 的维护者，我希望以后加入的机器字段默认纳入投影，不被旧 allowlist 遗漏。
8. 作为平台维护者，我希望 reference evidence 不被批量重写，仍能重放 V1 边界。
9. 作为多环境消费者，我希望每一份 declaration/lock 独立校验，原环境边界不变。
10. 作为离线使用者，我希望同输入输出一致，无网络、时间戳或机器信息混入哈希。

## Implementation Decisions：接口、数据与兼容性

### 哈希覆盖范围

新 `profile-machine-v1` 投影只从通过 strict schema 校验的 profile 顶层去掉两个明确字段：`description` 与 `compatibility_rules`。其余字段按现有 canonical JSON 序列化，包含 `$schema`、`schema_version`、`profile_id`、`version`、`catalog_revision`、`status`、完整 `required_components`（含 allowed_states/transitions）、`delivery_contracts` 和完整 `constraints`。

哈希输入采用 envelope：`hash_contract` 的固定取值为 `profile-machine-v1`，`profile` 为上述投影，防止同一 digest 在算法域之间被误解。object key 按既有规则排序；array 不排序、不去重、不改变顺序语义。投影后任何字段、数组成员或约束值变化都改变 hash，未来获 schema 批准的机器字段自动入 hash。未知输入字段仍由 strict schema 拒绝。

`constraints` 虽是 string 值，承载部署、存储、备份/恢复等人类合同，不能当 decoration 删除。这次只承诺 `description`/`compatibility_rules` 的说明润色稳定，不能声称所有自然语言字段修改都稳定。实际规范变化须改相应机器字段/约束并经过平台 Change；不能只改被排除的散文来改变实施规则。本次不引入 NLP 判断语义或结构化迁移全部规则。

### V2 lock

新增独立 V2 lock schema；新生成 lock 默认 `schema_version: 2.0`，指向对应 schema，顶层新增必填 `profile_checksum_contract: profile-machine-v1`。保留 `source_checksums.profile_sha256` 字段名，其意义由版本与 marker 明确限定；catalog 与 declaration 保持全量 canonical 哈希。整体 `lock_sha256` 覆盖所有 lock 内容及 marker。其它 resolved component、exception、provenance 与验证硬门不变。

拒绝未知 version/marker、V1 中插入 V2 marker、V2 缺失 marker、额外字段和 checksum 篡改，诊断码可搜索。V2 坐实 marker 后不得 fallback 到 V1 哈希。旧客户端拒绝 V2 是显式升级边界，不能宣称旧程序兼容新输出。

### V1 reader 与迁移

`validate --lock` 依据传入 lock 自身的 schema_version 选择已知 reader/schema，不能由调用方选一个更宽算法。V1 用当前输入生成严格的原 V1 expected lock，保留原完整 profile hash 和 whole-lock 比对；V2 用 machine projection expected lock。无 lock 的 validate 和新 lock 生成采用 V2。内部 build seam 可显式计算已知版本供 reader/测试使用；不提供 ignore、自动降级或 CLI 强制使用 legacy writer 的开关。

V1 未记录机器投影或旧 profile 快照，所以不能从一个 opaque 旧 hash 证明改动只为散文。保持 V1 严格意味着历史 V1 散文变更依旧报 LOCK_DRIFT；这是一次性迁移边界，须用户在本合同确认时明确接受。AC-1 的“既有 lock”指已按 V2 生成并提交的 lock，不能把旧 V1 验收失败写成通过。

迁移流程：先更新消费者所调用的平台 CLI/schema 到已合并的 #287 版本，在应用自身 Issue/Change 内复核当前 profile/catalog/declaration，再显式生成 V2 候选到临时输出，审阅 diff、校验并提交该应用的 lock。陈旧 V1 可以报 drift，不能当迁移已证明安全；重新生成只是候选，是否接受当前合同由应用 review 决定。只迁移每个实际环境对应 lock；不复制 target lock 为 current。平台 reference 和应用旧 lock 不批量改写。禁止安装全局 runtime、跨仓 commit/开票、live signal 或部署。

### 真实合同变更与广播边界

新 V2 纯说明编辑无需重 lock/广播；机器/constraints/catalog/declaration 变化仍失败，由应用在自己的 Change 中审阅影响、更新声明或例外后 relock。README 给出明确人工通知与应用接收步骤，包括平台变更 Issue/PR、profile ID、旧/新 checksum contract 与 version、受影响声明/环境、required action 与 NOT RUN 边界。

B 的确定性广播需要可信消费者名册、逐环境 lock 路径、受控跨仓 writer、幂等键、重试/失败 receipt 及撤销语义；本次不声称已有自动发现或广播能力，不把“现在仅一家”当当前 verified inventory。可以后续独立设计，但本 Issue 不创建派生 Issue。

### #288 兼容性

#288 的 Dockerfile 实际 digest 对照独立于 profile 哈希，可新增受控 evidence/校验规则；新机器字段不会被本投影排除。不实现 Dockerfile parser、不改 delivery enforcement。若双方修改同一 CLI/schema，由各自 writer 从最新 authoritative main rebase，并重跑现有与新增测试；不能代改对方 worktree。#288 不是本 Issue 硬依赖。

## Acceptance criteria

- [ ] AC-1：历史 6121838→97b09a7 两个 profile 的说明变动，在同 catalog/declaration/固定 today 下生成的 V2 lock byte-identical；用前者生成的已存在 V2 lock 对后者 `validate --lock` 返回成功。单独修改 description、compatibility_rules 亦同。
- [ ] AC-2：slot/component、allowed_states、transition、delivery_contracts、status、constraints 任一机器/约束变动，既有 V2 lock 失败。若输入仍合法，精确为 LOCK_DRIFT；若变更破坏结构/策略，先报相应 schema/semantic 诊断，不能假装已走到 lock 比对。至少一个合法 delivery 变动在 version 未 bump 时精确 LOCK_DRIFT。
- [ ] AC-3：原 V1 reference lock 在新 reader 上仍严格通过；V1 散文漂移仍失败；tampered lock、未知版本、marker 混用、缺 marker、unknown field 均非零退出，且不产生 lock 写入。
- [ ] AC-4：一次显式 V1→V2 临时候选生成后可验证且重复生成 byte-identical；原 lock bytes 不变。无自动迁移、无跨仓写、无网络调用。
- [ ] AC-5：catalog/declaration 哈希保持原算法；version mismatch、expired exception、prohibited/EOL、source freshness、digest 硬门不回退；机器变更不会被 version 相等绕过。
- [ ] AC-6：现有 fixtures、reference cross-check、architecture targeted tests 与 `bash codex/tests/smoke.sh` 通过；故意失败诊断不回显敏感输入。
- [ ] AC-7：architecture README/ADR 明确全部覆盖/排除字段、V1/V2 reader、一次迁移、constraints 保守边界、人工 relock 与自动广播 NOT IMPLEMENTED。文档与代码一致。
- [ ] AC-8：共享 main、平台 reference locks、catalog、profiles 与所有下游仓文件不被本次批量修改；#288 无顺手实现；无 installer/service/protection/credential/deploy 操作。

## Testing Decisions

最高行为 seam 为现有 architecture CLI 的 lock→validate 闭环，辅以现有 build_lock/validate_lock 测试 seam。历史两个 profile 用保留的 before/after fixture（注明来自 Git 对象）复现。有效与无效机器输入探针分别断言；不以“任意失败”替代有效输入上的 LOCK_DRIFT。CLI 集成检查 legacy reader、new writer、unknown marker、临时迁移、无写入副作用。固定 today 只用于可重放测试，真实 CI 继续当天 UTC。

先 T01 单独应用 architecture 文档合同并停止，fresh run 重新读取后 T02 实现。T01 不改正在遵循的 AGENTS.md、skills、controller、broker、CI 或 installer。本 spec 明确只授权 architecture README/新 ADR 为治理合同触点；其它治理文件不在授权内。

## 风险与回滚约束

未发布 source 可 revert 本 Issue 本地 commit。合并后可以用新 Change revert，但一旦有下游接受 V2，旧 reader 会拒绝 V2，须保持双 reader 的已发布 CLI/schema或由应用独立 Change 审阅生成 V1 兼容候选；不能为回滚自动重写下游。无 DB/数据迁移、无安装部署。任何 runtime 回滚前核对实际消费者格式，未读回不能声称兼容。

## 非目标 / Out of Scope

不修改 catalog component/version、profile 取值、V1 reference evidence、现有下游 lock；不实现 #288；不构建消费者 registry/自动广播/跨仓票据；不升级 LM/工具/全局 skills/CI；不改 AGENTS/controller/broker；不合并或部署。

## 未决问题

无技术未决问题。用户已确认 A、V1 一次性迁移边界、测试 seam 与 ticket 粒度，允许启动 T01。实现 AC 随真实验收记录，T01 不代表 runtime 已实现。
