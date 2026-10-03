数据库迁移完成后，activate、legacy deploy、显式 rollback 及失败恢复仍可能启动没有兼容依据的旧镜像。此变更记录 state v3 数据库位置，并让四类入口先经过统一 fail-closed gate：可证明相同位置时允许，否则必须提供绑定目标、release SHA、manifest hash、数据库状态和有效期的受保护 operator 依据；uncertain/未完成或失败 ledger 固定拒绝。

保留 v1/v2 只读兼容和同 identity no-op；严格验证 evidence owner、大小、JSON、路径及同 FD 内容，CLI 返回稳定安全错误。固定 source checker 仅扩展已批准的 exact paths/hash/mode，历史证据和拒绝边界保留。

验证：source `ed37445c9986fbff2aaac747ad41457da2a622ef`，base `16beee09aefe89b5bc80a31544c59d456190ea32`；默认 C.UTF-8/native Bash 3.2 完整 smoke exit0（1057 runtime、197 release、23 installed-drift 临时 fixture），26 boundary regression，Standards/Spec 0/0 findings。旧失败回执保留；最终候选相对该 source 仅增加本票文档与证据。required CI 为 `CI / verify (pull_request)`，PR CI 尚未运行。

合同与回执：
- [summary](docs/changes/317-migration-rollback-guard/summary-migration-rollback-guard-261002.md)
- [spec](docs/changes/317-migration-rollback-guard/spec-migration-rollback-guard-261002.md)
- [plan](docs/changes/317-migration-rollback-guard/plan-migration-rollback-guard-261002.md)
- [verification](docs/changes/317-migration-rollback-guard/verification-migration-rollback-guard-261002.md)

风险与回滚：state v3 不强行降级；采用 forward fix 或保留 guard 的源码 revert，禁止恢复旧数据库/state 绕过保护。真实 Docker/DB、安装、部署和应用消费验收 NOT RUN。NewEMaint #229 仅在本票人工合并后采用真实 merged SHA，当前 pin 未改。

Closes #317
