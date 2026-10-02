# Docker migration rollback compatibility v1

> Issue #317 · 2026-10-02 已批准治理合同。T01 只应用本文件及 README；runtime、schema、
> 本地功能验收和 CI 尚未完成。后续 fresh run 重读本合同后才能实施 T02/T03。

本合同约束数据库迁移后的**旧镜像启动**，包括 phased `activate` 的自动回退、legacy
v1/v2 `deploy` 的自动回退、显式 `rollback`，以及显式回退失败后的原 current 恢复。
所有路径使用同一兼容判据；应用 consumer 不复制回退状态机。数据库不自动 restore。

## 数据库位置与容器位置

`current_release`、`previous_release` 记录容器发布位置，不表示数据库 schema 位置。
Migration 已成功但 activation 失败时，数据库仍处于迁移后位置；回切容器不得改写该事实。

目标写状态版本为 `docker-release-state/v3`。保留 v2 字段，增加严格的 `database_revision`：

| 字段 | 语义 |
|---|---|
| `status` | `known` / `untracked` / `uncertain` |
| `migration_identity` | 完整 SHA256 migration identity 或 null |
| `generation` | 非负整数；真实 migration 尝试前递增，容器回退不递减 |

- 空的新 state、合法 v1/v2 读升级：`untracked`、null、generation=0。读升级不写磁盘，
  不根据字典顺序、旧 release 或 completed receipt 猜测数据库当前位置。
- 真实 migration 调用前原子持久化 `uncertain`、candidate identity 和递增 generation；
  调用成功后写 `known`。失败或中断不能宣称 known，也不得自动重跑或恢复数据库。
- 无 migration 的 release 不改变数据库位置。已有 `completed` identity 的
  `migration-noop` 不改原 receipt.release_id，也不把旧 identity 写成当前数据库位置。
- #305 的规则保持：completed receipt 不要求 release_id 等于本次 release；正常 activation
  的 completed 判据不改回“每个 release 都重跑同一 migration”。
- 已有任一 started/failed migration 不能被兼容依据掩盖；独立现场处置前拒绝旧镜像启动。

## 判定顺序

旧 release 的 artifact、host-role、staging、本地 image identity 和 health 闸门保持。
兼容 gate 必须在该旧 release 的 transport prepare 与 container up 之前执行。

1. 数据库 uncertain，或 ledger 含未处置 started/failed：固定拒绝，不查询放行依据。
2. 数据库 known，数据库/candidate/rollback 三份 migration identity 完全相同且非 null，
   exact identity 的 receipt 已 completed：可证明没有偏离该迁移位置，允许回退。
3. 其它情况（不同 identity、null 或 untracked）：必须有下节的 exact 可信兼容依据。
4. 无依据、依据无效、过期或歧义：fail closed，旧 release 的 up 数为零。

两份 manifest 的 migration=null 不证明数据库未改变。曾完成 migration A 也不证明
数据库现在仍在 A；例如 C 已迁移但未激活，A/B 共用 A 时不得依据 A/B 的 identity 放行。
相同 identity 由其它 release 执行过是合法 no-op，receipt.release_id 只作审计。

## Operator 管理的依据

Target profile 的可选 `rollback_compatibility_file` 指向绝对路径，位于
release_root/state_root/env_file 外的 operator 配置区。无此字段表示没有显式依据；旧
profile 与 v1/v2 不可变 release bytes 无需重写。CLI 不增加任意路径、shell 或 boolean bypass。

兼容依据 envelope 版本为 `docker-migration-rollback-compatibility/v1`，由 target operator
独立安装。Producer 发布的布尔声明、同名 tag 或普通应用文件均不构成此信任来源。

读取要求：0400/0600 regular file、非 symlink、owner 与受保护 profile owner 相同或 root，
父目录不得 group/world writable；限量读取、strict JSON、拒绝重复/未知字段。
用 open/fstat 验证读到的同一文件，不能先检查路径再信任被替换的文件。

每条记录必须绑定以下全部事实：

| 绑定维度 | 字段/内容 |
|---|---|
| Target namespace | profile_id、environment、expected_hostname、compose_project、source_repository |
| 发布身份 | candidate_release、rollback_release，均为完整 40 位 lowercase SHA |
| 不可变内容 | 两份原始 release manifest 的 SHA256 |
| 迁移身份 | candidate_migration_identity、rollback_migration_identity、database_migration_identity |
| 当前数据库状态 | database_revision 与完整 migration ledger 的 canonical fingerprint |
| 有效期与验证 | verified_at、expires_at：UTC RFC3339；verified_at <= now < expires_at |
| 结果与审计 | result=compatible、安全 evidence_id；不含 Secret、自由命令或原始日志 |

数据库 fingerprint 固定 target profile namespace、database_revision、全部 migration records，
不包含 last_result、容器 current/previous 指针或 Secret。因此 migration 变化立即使旧记录
失配；容器切换不能错误地改变数据库依据。Known 时依据的数据库 identity 必须匹配已知位置。
Untracked 时 operator 观测是唯一外部可信事实，必须绑定 exact untracked fingerprint；
不能据此把 state 永久改成 known，也不缓存长期放行。

拒绝：任一 target/release/migration/checksum/fingerprint 不匹配、未来 verified_at、已过期、
非兼容 result、多条匹配记录、无效权限/路径或损坏 JSON。Invalid evidence 不可降级成
“没有文件，继续 fallback”。拒绝原因稳定、脱敏，不回显依据内容、路径、连接串或 Docker 输出。

本机制不检测带外数据库操作。Operator 更换数据库、离线修改或 restore 后必须撤销旧依据
并重新验证；不能通过恢复旧 deployment state 制造兼容事实。独立现场处置不在 #317 授权内。

## 失败与状态输出

| 结果 | CLI/状态要求 |
|---|---|
| 候选失败，无可回退 release | 失败且非零退出；不宣称恢复了旧容器 |
| 兼容 gate 拒绝 | `ROLLBACK_BLOCKED`；旧 up=0；保留迁移后数据库位置 |
| Gate 允许，旧容器启动或健康失败 | `ROLLBACK_FAILED`；不可宣称已 restored |
| Gate 允许，旧容器已恢复健康 | 仍报告候选激活失败；不把本次发布标成功 |

上表所有失败结果均以非零退出，并输出安全 code/message；旧容器恢复成功也不把候选发布
失败改为零退出。不回显子进程 stdout/stderr 或上述敏感上下文。

`last_result` 记录真实阶段结果。容器指针只在真实成功后更新；失败时保留的指针不是
健康证明，status 仍需 exact release/image/service/health 读回。显式回退失败后若尝试恢复
原 current，也执行同一 gate 与 image/health 闸门。不运行 migration down/database restore。

## Consumer、降级与证据边界

- Consumer 使用平台原有 CLI/API 和 profile；不能复制状态机，也不能以应用薄编排绕过内部回退。
- 本票人工 merge 后由 NewEMaint #229 的独立会话更新 exact merged SHA pin，并做应用集成验证。
  T01 本地 commit、开放 PR、绿 CI 均不是可采用的 merged pin，更不是现场部署证明。
- State v3 写入后旧 runtime 不识别。源码回退必须保留此 guard 或 forward fix；不得恢复旧 state
  或直接降级到会无条件启动旧镜像的 runtime。
- 本票不 provision profile/依据/grant/Secret，不安装、不部署、不操作真实数据库。
  FakeDocker/source/local、PR CI、installed/live 与业务验收分别记录，未运行均为 NOT RUN。

## 实施停止点

T01 只修改本治理合同、Docker release README 与 #317 映射语义文档，验证范围后本地提交并停止。
下一条 fresh run 必须重读 AGENTS/README、本合同、已批准 spec/plan 和单写者 claim，才能在
同一 branch/worktree 实施 runtime/schema/test。最终 PR 提交仍需独立 exact manual 确认。
