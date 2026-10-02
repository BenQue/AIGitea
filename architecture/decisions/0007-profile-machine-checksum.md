# ADR-0007：profile 说明字段与机器合同 checksum 分离

- 状态：Accepted（2026-10-02 用户确认合同；V2 runtime 源码已实现并本地验证，安装与实际消费者验收 NOT RUN）
- 日期：2026-10-02
- 关联：Issue [#287](http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/287)，补充 ADR-0001 与 ADR-0006

## 原因与证据

历史 `6121838` → `97b09a7` 仅改 profile 的一条 `compatibility_rules` 说明。全量 canonical
profile checksum 从 `6eb2458f…` 变为 `7ed962a2…`，机器字段与 version 不变，既有 V1 lock
却报 `LOCK_DRIFT`。这要求明确哈希合同边界，而不能让消费者反复为说明改动重 lock。

hash 是解析后 canonical JSON 的函数，不是 commit identity，也不是未经解析的磁盘字节。
ADR-0001 的 strict JSON、离线 stdlib-only、未知字段拒绝和 canonical serialization 保持。

## 决定一：内容 hash 保留，采用明确机器投影

选择 #287 方向 A。profile 顶层仅排除 `description` 和 `compatibility_rules`，其它完整
字段全部保留。投影置于 `hash_contract: profile-machine-v1` 与 `profile` 两字段的
envelope 后按既有 canonical 规则求 hash。数组不做额外排序或去重。

身份/version/catalog revision/status、slot/component、allowed_states/transitions、
delivery_contracts、constraints 与未来 schema 批准的机器字段都受保护。特别是 constraints
的存储、单写者、备份与恢复等要求虽以字符串承载，仍是合同；措辞变化保守触发漂移。
不能只修改被排除的散文来引入新实施规则；规范变化必须体现在机器字段或受保护约束。

## 决定二：格式与算法不可混用

新增 V2 lock 格式 `schema_version: 2.0`，使用独立 schema 与必填顶层
`profile_checksum_contract: profile-machine-v1`。保留 source_checksums 字段名；其中
profile_sha256 的意义由该明确格式/marker 决定，catalog/declaration 仍全量求 hash。
whole-lock checksum 包括格式与 marker。

新 writer 默认 V2；reader 由实际 lock 的版本选择完整已知校验路径，不能由调用方选择
更宽算法。V1 用旧完整 profile hash 与严格 whole-lock expected 比较；V2 使用上述投影。
未知版本/marker、格式混用、缺 marker、额外字段和篡改均拒绝；没有 silent fallback。

## 决定三：旧 V1 严格保持，显式迁移一次

V1 缺少旧机器投影，不能从 opaque hash 反推出说明与机器变化，因此 V1 的说明漂移继续
失败；不得偷换 checksum 含义。新格式稳定性只适用于已生成并采用的 V2 lock。

下游在自己的 Issue/Change 中核对工具/reader 格式兼容性、当前输入与环境，显式生成临时
候选、审阅差异、校验与 required CI 后提交。平台不重写旧 reference 或下游 lock，
target/current 与按环境拆声明的边界保持。旧 V1-only release reader 对 V2 的拒绝是
升级边界；architecture V2 校验成功不证明 release 路径可用。

## 决定四：version 不能替代内容检测，广播仍为独立能力

profile version 原已存在，继续与 declaration 精确匹配。机器变化漏 bump 时，内容 hash
仍改变；合法输入报 LOCK_DRIFT，非法输入可先报 schema/semantic 错误。方向 C 单凭 version
会放过漏 bump，故不采用，也不在本 Change 新增跨版本基线发布 CI 规则。

方向 B 保持所有说明编辑都破坏下游，还需可信消费者名册、跨仓权限、幂等事件/票据、重试与
失败 receipt，超出本次选择。V2 纯说明无需 relock；真实机器变化走 README 的人工通知与
项目自身 Change。自动消费者发现、跨仓开票与 needs-relock 信号 **NOT IMPLEMENTED**。

## 风险、回滚与实施边界

维护者通知应带平台 Issue/PR、profile ID、旧/新 version/checksum contract、环境及
required action；消费者 inventory 未读回不得宣称完整。安装、release、CI 与部署分别验收。

若有 V2 消费者，回滚应保留双 reader 或由应用独立 Change 审阅 V1 候选；不自动重写其它仓。
所有 EOL、prohibited、digest、exception/expiry、provenance 与 checksum 硬门保持。

#288 的 Dockerfile evidence 是独立机制，本 ADR 不实现它；未来获 schema 批准的机器字段
默认入投影。T01 已独立应用文档合同并停止，后续 fresh run 重读后实施 T02/T03。当前源码
具备默认 V2 writer 与严格双 reader；release reader 仍仅支持 V1。该实现不修改 AGENTS、
skills、controller、broker、CI、installer、profile/catalog 取值或 live 状态。
