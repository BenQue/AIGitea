# NewEmaint architecture references

本目录只保存 AISoftPlatform 对 NewEmaint authoritative remote main 的脱敏只读证据：

- `inventory.json`：在精确 commit 上观察到的 current facts；不含 Secret 或业务数据。
- `gap-report.md`：current facts、preferred target 与后续应用 Gate 的差异。
- `target-candidate/`：project ID `newemaint-target-candidate` 的目标 declaration/lock；它不是
  current lock，也不是 migration、Docker release、部署或验收证据。

Issue #26 采用 target-only 验收，`current-transition/` 故意不存在。NewEmaint
[#52](http://gitea-ci.orb.local:3000/admin/NewEMaint/issues/52) 是唯一 umbrella migration
tracking Issue，逐项列出全部 preferred components 和应用/数据库/制品/环境 Gate；无需为每个
component 再创建 Issue。

一个 Issue 不等于一个 exception 或一次性部署。若未来仍需合法 transition，每个 component
仍必须有自己的 owner、risk、controls、expiry 和 exception；多个 exception 可引用同一个明确
覆盖这些 components 的 umbrella Issue。`prohibited`/EOL component 无论是否有 Issue 都不能
进入 lock。NewEmaint 完成实际迁移后，只能根据真实 supported/preferred release bytes 生成
project ID `newemaint` 的 current lock，不能复制 `target-candidate`。

创建 #52 只建立治理跟踪，不授权 package/image/schema/server/database/Secret mutation、部署、
生产操作或合并。NewEmaint consumer/build/migration/deployment 在本 Change 中全部 `NOT RUN`。
