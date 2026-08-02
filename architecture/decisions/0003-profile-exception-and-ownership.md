# ADR-0003：Profile、例外与 #21/#22 所有权

- 状态：Accepted
- 日期：2026-08-02

三个 V1 profile 只声明兼容 component、边界和 delivery contract。#21 owns host role/
capability；#22 owns release manifest/deploy state；#23 owns catalog/profile/declaration/lock
validity。任何 profile 名称均不授予部署权限。

`sunset` component 需要 project migration Issue。临时偏离还必须声明短期 exception：ID、owner、
reason、risk、controls、created/expiry 与 migration Issue 缺一即失败，到期当日即无效。
`prohibited` 和 EOL 不能通过 exception 绕过。
