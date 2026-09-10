# ADR-0006：embedded SQLite 前端 profile、按环境拆声明与 as-built 版本例外

- 状态：Accepted
- 日期：2026-09-10
- 关联：Issue [#284](http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/284)，补充 ADR-0002、ADR-0003、ADR-0004、ADR-0005

catalog `2026.09.0` 的 4 个 profile 无一能如实描述「embedded SQLite 加前端框架、
运行在上一个 Node LTS 上、同一个仓库两个环境两种交付形态」的应用。补齐这个形态的过程
暴露出三条此前只存在于实现里、没有写成合同的语义。本 ADR 记录四条裁决及其边界。

## 一、新增 profile `linux-node-sqlite-v1@1.0.0`

slot 为 `os`/`runtime`/`package-manager`/`database`/`framework`/`frontend`/`orm`/`toolchain`
八项。它与既有 profile 的边界是刻意的：

- `small-embedded-sqlite-v1` 只有四个 slot，没有前端框架、ORM 与 toolchain slot，
  因此表达不了带前端的应用；它继续服务纯后台的单实例 SQLite 应用。
- `linux-node-postgres-v1` 的 database slot 只接受 client-server 数据库，
  并强制 proxy、container-engine、container-compose 与 OCI slot。
- `linux-node-systemd-postgres-v1` 明确排除前端框架 slot。

本 profile 不含 proxy、container-engine、container-compose 与 OCI slot。它继承
embedded 数据库的全部约束：单写者、本地文件系统、无高可用声明。profile 的 slot 集合
是平台资产，不复制任何单个项目的取值。

## 二、`delivery_contract` 保持单值，按环境拆声明

一个 profile 的 `delivery_contracts` 可以列出多个取值；一份 declaration 仍然只取其中
一个。同一个仓库的多个环境如果交付归属不同，就各写一份 declaration 与一份 lock，
而不是把它们合并进一份。

不把字段改成数组的理由是它解决不了真正的问题：交付归属不同的两个环境，通常 OS、
CPU 架构与基镜像也不同，单个 `components` 数组本来就装不下两者。改成数组只会让一份
lock 同时宣称两种按 ADR-0005 互斥的交付归属，却仍然只能记录一套 component。

下游边界不变：release 运行时仍要求 lock 的 `delivery_contract` 精确等于容器交付取值，
因此只有对应环境的那一份 lock 能进入 release 路径。带容器交付取值的 declaration 必须
额外声明 catalog 中按 digest 固定的基镜像 component；本 profile 没有 OCI slot，
是因为原生交付的两个取值没有基镜像。

## 三、as-built 版本例外

`PROJECT_VERSION_DRIFT` 的精确相等比较保持为默认，不 opt-in 的声明行为逐字不变。
component 可以显式声明 `as_built: true`，如实记录部署中真正运行的构建，条件是：

- 必须有且只有一个有效 exception，字段与到期规则与 transition exception 完全相同：
  owner、reason、risk、controls、created_at、expires_at 与 migration Issue，
  有效期不超过创建日起 180 天，也不超过 component 的 `migrate_by`；
- 声明版本必须与 catalog pin 同 major 且不相等。相等时直接报错，强制清理不再需要的例外；
- major 为 `0` 时 minor 也必须相等，因为该区间的破坏性变更由 minor 承载；
- 按 digest 固定的 OCI component 一律拒绝 as-built，ADR-0004 的不可变身份不受影响。

lock 在 `resolved_components` 中记录**声明的真实构建**，而不是把 catalog pin 回显一遍。
回显 pin 的 lock 描述的是平台的期望，不是运行中的字节。偏差由记录的构建加上同一条目上的
`exception_id`/`exception_expires_at` 承载：lock 自带 `catalog_revision`，读者据此就能确定
pin 与真实构建的差别，因此不需要在 lock 中再加一个标记字段。

resolved component 的 `source_url` 仍然是 catalog component 对 **pinned** 构建的 provenance，
不是对 as-built 构建的 provenance；后者由应用仓自己的 lock 文件固定，并由该仓的 Change 治理。

不给 lock 增加新字段是刻意的。release 运行时按精确 key 集合校验 lock 的每个 resolved
component，而该运行时目前处于 Issue #65 的证据闸门冻结中；新增一个它不认识的 key 会让所有
带 as-built 偏差的项目无法进入 release 路径。扩大该闸门的豁免清单属于 #65 的授权边界，
不在本 Change 范围内。

as-built 不是第四种永久状态，也不是免检通道。`prohibited`、EOL、digest、expiry、
checksum 与 lock drift 的 fail-closed 行为全部不变；例外到期当日即无效。

## 四、migration Issue 放宽为绝对 http 或 https

transition 与 sunset component 的 migration Issue 由「绝对 HTTPS」改为「绝对 http 或
https」。其余检查不变：必须有 host、不得带凭据、不得带 query 或 fragment、路径必须形如
`/.../issues/N`，相对路径与 `#N` 简写在 transition 校验中仍被拒绝。

理由是该字段是审计引用，validator 从不解引用它；而平台自己的 tracker 只在 http 端口
提供服务。保留 https-only 不会提高任何安全性，只会让 governed transition 路径对本平台
的每个项目都不可用，实际后果是逼出一个语法合规但根本不解析的 URL——这正是合同禁止的虚报。

## 五、不新增 `os` category 取值

Issue 提出补两个 `os` 取值，评估后都不加：

- 容器基镜像的 OS 已经由 `oci-image` 类目连同 runtime 一起表达并按 digest 固定。
  再建一个 `os` component 会让同一事实有两处建模，且第二处无法按 digest 固定。
  应用侧的真实缺口是用可变 tag 而不是 digest，那是 ADR-0004 刻意的 fail closed。
- 另一个候选取值是 interim release，标准支持期已于 2026-07-01 结束。如实入库后
  任何声明它的项目都会在 `COMPONENT_EOL` 上 fail closed，加它不产生任何可用路径。
  正确处置是把该主机迁到受支持的 LTS，而不是给已 EOL 的 OS 开一条通道；
  as-built 例外也不适用，跨 major 被明确拒绝。
