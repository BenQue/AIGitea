# ADR-0002：官方 lifecycle 与 catalog state

- 状态：Accepted
- 日期：2026-08-02
- Next review：2026-11-02

版本/lifecycle 结论逐组件通过 Context7 的 upstream/official documentation 获取，再对
Ubuntu、Windows、PostgreSQL、SQLite、NGINX 和 release metadata 做官方页面 readback。
每条 component 保存 source URL、retrieved/review date 与兼容性证据。

官方未发布固定 EOL 时，`support_end`/`eol` 保持 `null`，并用季度 `review_by` 阻止陈旧结论；
绝不把平台复审日期伪装成 upstream support promise。Legacy Prisma 5 的 sunset 日期明确是
AISoftPlatform exception deadline。发现来源冲突时，以产品 lifecycle/source release metadata
为主，候选保持 `prohibited`，直到兼容测试与 soak 证据通过独立 Change。
