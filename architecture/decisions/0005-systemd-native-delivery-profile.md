# ADR-0005：systemd 原生 Node 服务 profile 与 `systemd-native/v1`

- 状态：Accepted
- 日期：2026-08-23
- 关联：Issue [#150](http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/150)，补充 ADR-0003

V1 的三个 profile 都无法表达「Linux + Node 服务、systemd 直管、无容器、无前端框架、
查询层不限定 Prisma」这一形态：`linux-node-postgres-v1` 强制 Prisma/Docker/Compose/nginx/
Next/React/OCI slot，`small-embedded-sqlite-v1` 强制 SQLite，`windows-dotnet-postgres-v1`
无关。`required_components` 没有「本项目不适用」的逃生口，这是刻意的 fail-closed 设计，
因此缺口只能由新 profile 补齐，不能由 exception 或省略绕开。

本 ADR 增加第四个 active profile `linux-node-systemd-postgres-v1@1.0.0`，只保留
`os`/`runtime`/`package-manager`/`database`/`toolchain` 五个 slot，并新增 delivery contract
取值 `systemd-native/v1`。profile 只声明兼容 component、边界与 delivery contract，
不授予任何部署能力——这一点与 ADR-0003 完全一致。

`systemd-native/v1` 与既有取值的边界：

- 与 `docker-release/v1`（及 `docker-release/v2` 消费者）互斥。release manifest 运行时
  要求 lock 的 `delivery_contract` 等于 docker-release 取值，因此 systemd-native lock
  天然无法进入 Docker release/transport/offline bundle 路径，不需要额外开关。
- 与 `pm2-legacy` 互斥。`pm2-legacy` 描述既有 PM2 应用在独立迁移验收前的 delivery
  ownership；`systemd-native/v1` 表达的是「systemd 直接管理应用进程，中间没有 process
  manager」，两者不能同时成立。
- 与 `windows-iis/v1`、`embedded-sqlite/v1` 无交集。

profile 的 slot 集合是平台资产，不复制任何单个项目的取值。项目可以在 declaration 中
额外声明其它 catalog component；不在 catalog 中的查询层或框架仍由应用仓 lock 文件固定，
并按平台合同在应用自己的 Change 中治理。
