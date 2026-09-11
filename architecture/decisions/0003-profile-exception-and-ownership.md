# ADR-0003：Profile、例外与 #21/#22 所有权

- 状态：Accepted
- 日期：2026-08-02
- 补充：ADR-0005 增加第四个 profile `linux-node-systemd-postgres-v1` 与 delivery contract
  `systemd-native/v1`；本 ADR 的所有权与例外规则不变。
- 补充：ADR-0006 增加第五个 profile `linux-node-sqlite-v1`，并把 exception 的适用范围
  从 state transition 扩展到 as-built 版本偏差；owner/risk/expiry 规则与到期即失效不变。

三个 V1 profile 只声明兼容 component、边界和 delivery contract。#21 owns host role/
capability；#22 owns release manifest/deploy state；#23 owns catalog/profile/declaration/lock
validity。任何 profile 名称均不授予部署权限。

`sunset` component 需要 project migration Issue。临时偏离还必须声明短期 exception：ID、owner、
reason、risk、controls、created/expiry 与 migration Issue 缺一即失败，到期当日即无效。
`prohibited` 和 EOL 不能通过 exception 绕过。
