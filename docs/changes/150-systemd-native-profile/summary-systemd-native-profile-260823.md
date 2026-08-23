---
issue: 150
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/150
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 新增 architecture profile 与扩展 delivery_contract 枚举，属共享核心与外部交付合同变更，强制 complex
risk_flags:
  - shared-core
  - external-contract
  - deployment-boundary
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-systemd-native-profile-260823.md
  spec: spec-systemd-native-profile-260823.md
  plan: plan-systemd-native-profile-260823.md
  verification: verification-systemd-native-profile-260823.md
confidence: high
override_reason: ''
depends_on: []
status: approved
branch: change/150-systemd-native-profile
pr_url:
created: 2026-08-23
updated: 2026-08-23
---

## 问题/需求总结

LocalWMS 走到 project-align checklist 第 6 行（`.aisoft/architecture.json` + lock）时无法完成，卡在平台侧两处缺口：

1. **没有可用 profile。** `linux-node-postgres-v1@1.1.2` 的 `required_components` 强制包含 `orm.prisma.7`、`container.docker-engine.29`、`container.compose.5`、`proxy.nginx.1-30`、`framework.next.16`、`frontend.react.19` 和 `oci.node.24-bookworm-slim`；`small-embedded-sqlite-v1` 强制 `database.sqlite.3`；`windows-dotnet-postgres-v1` 无关。`validator.py` 对每个 profile slot 要求「preferred 或一个 allowlisted transition」二选一，缺一即 `PROFILE_COMPONENT_MISSING`，没有「本项目不适用」的逃生口。
2. **`delivery_contract` 枚举没有 systemd 原生取值。** 现有四个取值（`docker-release/v1`、`pm2-legacy`、`windows-iis/v1`、`embedded-sqlite/v1`）没有一个如实描述「systemd 直管、不经容器也不经 PM2」。

runbook §9 禁止目录名推测与虚报 component，所以项目侧无法绕开；缺口只能由平台补齐。

## 影响范围

- `architecture/profiles/`：新增第四个 active profile。
- `architecture/schemas/profile-v1.schema.json`、`architecture/schemas/project-architecture-v1.schema.json`：`delivery_contracts`/`delivery_contract` 枚举各加一个取值。
- `architecture/fixtures/valid/`：新增形如 LocalWMS 的候选声明，进入既有 glob 回归。
- `architecture/decisions/`：新增 ADR-0005，并在 ADR-0003 加交叉引用。
- `skill-for-codex/references/onboarding-runbook.md` §4/§9：新交付形态的适用条件与边界（skill-for-claude 由 install.sh 从同一份 references 复制，无第二份需要同步）。
- `codex/runtime/tests/test_architecture_schema.py`、`test_architecture_cli.py`：profile 计数与 byte-identical lock 回归。

不改 catalog（不为 PostgreSQL 17 背书）、不改 validator/lockfile 逻辑、不动既有三个 profile 与已接入项目的声明。

## 初步方案与建议

新增 `linux-node-systemd-postgres-v1@1.0.0`，只保留 `os.ubuntu.*`、`runtime.node.*`、`package.npm.*`、`database.postgresql.*`、`toolchain.typescript.*` 五个 slot，并沿用既有 profile 的 transition 写法；新增 delivery contract 取值 `systemd-native/v1`，其与 docker-release / pm2-legacy 的边界写进 ADR-0005 与 runbook §4.1。profile 是平台资产，slot 集合按平台既有写法裁定，不写死 LocalWMS 的取值。

## 风险

- **枚举扩展影响下游消费者。** `aisoft_release` 要求 release lock 的 `delivery_contract` 等于 docker-release 取值，systemd-native lock 天然进不了该路径——这是合同边界，需在文档里写清而不是留给读者推断。
- **profile 被误用成「宽松版 linux-node-postgres-v1」。** 缓解：ADR 与 runbook 明确适用条件，并用测试钉住被排除的 category。
- **既有声明回归。** 缓解：既有 fixtures/reference lock 交叉校验全部保留并通过。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 新增 architecture profile 与扩展 delivery_contract 枚举，属共享核心与外部交付合同变更，强制 complex
risk_flags:
  - shared-core
  - external-contract
  - deployment-boundary
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- `contract_effect: add`：新增 profile 与新增枚举取值都是对外部可消费合同的扩充，不是恢复既有行为。
- 共享核心：`architecture/schemas/*` 与 `architecture/profiles/*` 被所有接入项目的 `.aisoft/architecture.json` 与 `aisoft-project-check.sh` 消费。
- 交付合同/部署边界：`delivery_contract` 是 release 与部署路径的选择依据。
- 平台治理：改的是平台自身的合同分册与 ADR。

### 缺失的 acceptance criteria 或决策

- 无。Issue 正文已给出可测验收标准；PostgreSQL 17 明确不在范围内。
