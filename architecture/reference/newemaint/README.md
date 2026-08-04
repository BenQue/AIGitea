# NewEmaint architecture references

本目录只保存 AISoftPlatform 对 NewEmaint authoritative remote main 的脱敏只读证据：

- `inventory.json`：在精确 commit 上观察到的 current facts；不含 Secret 或业务数据。
- `gap-report.md`：current、target 与外部 migration Gate 的差异。
- `target-candidate/`：project ID `newemaint-target-candidate` 的目标 declaration/lock；它不是
  current lock，也不是 migration、Docker release、部署或验收证据。

`current-transition/` 当前故意不存在。只有 NewEmaint 中每个实际 major migration 都有真实、
可读、独立的 HTTPS Issue，platform exception 与 Issue 一一绑定且未过期，并且所有 resolved
components 仍为 `supported`/`sunset` 而非 `prohibited`/EOL 时，才允许以 project ID
`newemaint` 生成 canonical current declaration/lock。

Issue #26 当前为 `BLOCKED_EXTERNAL`：未获授权创建 NewEmaint migration Issues，且官方支持
策略已将 Next.js 14 标为 unsupported。Transition 不能绕过 prohibited、EOL、digest、expiry、
source checksum 或 lock self-hash；target candidate 也不能复制成 current。
