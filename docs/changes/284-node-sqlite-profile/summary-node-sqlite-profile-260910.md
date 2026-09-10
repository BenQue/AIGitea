---
issue: 284
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/284
change_type: platform
requested_complexity: auto
assessed_complexity: complex
contract_effect: add
effective_complexity: complex
reason: 新增 architecture profile 并改动 catalog 与 validator 的共享校验语义，属共享核心与外部交付合同变更，强制 complex
risk_flags:
  - shared-core
  - external-contract
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-node-sqlite-profile-260910.md
  spec: spec-node-sqlite-profile-260910.md
  plan: plan-node-sqlite-profile-260910.md
  verification: verification-node-sqlite-profile-260910.md
confidence: high
override_reason: ''
depends_on: []
status: approved
branch: change/284-node-sqlite-profile
pr_url:
created: 2026-09-10
updated: 2026-09-10
---

## 问题/需求总结

SFMDigitalBoard 的 architecture-lock 声明会话在确认点 1 停下：catalog `2026.09.0` 的 4 个 profile
无一能如实描述该仓（SQLite + Next/React/Prisma + Node 22，两个环境两种交付形态）。平台侧需要
新增 profile，并裁决三处此前没有明确写下来的合同语义。

## 影响范围

- `architecture/profiles/`：新增一个 active profile。
- `architecture/catalog.json`、`architecture/schemas/`、`codex/runtime/aisoft_architecture/validator.py`：
  取决于裁决结果，可能改动 component 集合与共享校验语义。
- `architecture/fixtures/`、`codex/runtime/tests/test_architecture_*.py`：新增正/负 fixture 与断言。
- `architecture/README.md`、`architecture/decisions/`：写下裁决。
- 下游：`aisoft_release` 对 lock `delivery_contract` 的等值断言必须保持不变。

## 初步方案与建议

四点需求经证据核对后收敛为三处裁决加一个新 profile，详见 spec。四点不拆成独立 Issue：
SFMDigitalBoard 的阻塞同时命中全部四点，任何一点留到后续 Issue 都不能解除阻塞。

## 风险

- validator 语义是所有接入项目共用的共享核心，放宽任何一条都对全平台生效。
- 新增 catalog component 需要官方 provenance 证据，无法在离线环境凭记忆编造。
- `delivery_contract` 是 release 路径的选择依据，改成多值会削弱 ADR-0005 确立的互斥性。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
contract_effect: add
effective_complexity: complex
reason: 新增 architecture profile 并改动 catalog 与 validator 的共享校验语义，属共享核心与外部交付合同变更，强制 complex
risk_flags:
  - shared-core
  - external-contract
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- `AGENTS.md`：共享核心组件、外部契约与 Agent 或平台治理变更一律按 complex 处理。
- 新增 profile 是 `contract_effect=add`；ADR-0005 是同类先例，同样判 complex。
- `architecture/` 是平台事实源，改动对所有接入项目生效，不满足 small 的范围局部要求。
- `required_docs` 含 `verification`：验收要求同一输入连续两次 `lock` 产出 byte-identical
  结果，并要求记录内网 Gitea 的 http/https 可达性观测。两者都是运行期观测，diff review
  与 required CI 不能重放，按 `03` §3 欠一份验证记录。

### 缺失的 acceptance criteria 或决策

- 裁决 A：`delivery_contract` 单值与「一个仓库两种交付形态」的表达方式。
- 裁决 B：`PROJECT_VERSION_DRIFT` 精确相等比较的 pin 语义。
- 裁决 C：transition migration Issue 的绝对 HTTPS 要求，内网 Gitea 无 https 服务。
