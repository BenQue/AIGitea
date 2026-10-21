---
issue: 409
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/409
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 项目检查器新增 LEGACY 级、architecture CLI 新增按 revision pin 的 catalog 快照与项目自带 profile 扩展点、使用发布包 lock 结构加可选键并发新版本，属于新增功能、共享核心、外部契约与发布制品
risk_flags:
  - shared-core
  - external-contract
  - artifact
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-catalog-pin-project-profile-261021.md
  spec: spec-catalog-pin-project-profile-261021.md
  plan: plan-catalog-pin-project-profile-261021.md
  verification: verification-catalog-pin-project-profile-261021.md
route:
  process: complex-production
  tier: frontier
  effort: max
  skills: grill-me, to-spec, to-tickets, executing-plans, verification-before-completion
  method: spec-plan
  verify: full+reverse-proof
  review: cross-provider
  confirm: 2
confidence: high
override_reason: ''
depends_on:
  - 402
status: analyzed
branch: change/409-catalog-pin-project-profile
pr_url:
created: 2026-10-21
updated: 2026-10-21
---

## 问题/需求总结

有历史的项目跑 `aisoft project-check` 无法全 PASS（R12）。2026-10-21 在真实检出上取的基线：

- NewEMaint：`change-documents` GAP 16 条（纯数字目录的 summary 缺 `required_docs`，`97-…` 缺 verification
  映射）；`architecture-lock` GAP，诊断 `PROJECT_CATALOG_MISMATCH`（lock pin 2026.08.3，平台 catalog 2026.09.0）。
- SFM：`change-documents` GAP 54 条（零填充目录名 `0001-…`、pre-#57 文档无 front matter）；`architecture-lock`
  GAP，诊断 `DOCKERFILE_DECLARATION_REQUIRED`（#288 新规则，catalog 并不落后）。
- HSDB：没有 `.aisoft/architecture.json`，技术栈（Node + React + Hono + Drizzle + PostgreSQL + PM2）没有平台
  profile 可选，ADR 0001 D5 要求「按技术栈登记的 profile 迁为项目自带」尚未有扩展点。
- 检查器的 `architecture-lock` GAP 只写「strict JSON 或 architecture lock 校验失败」，不带诊断码。

## 影响范围

- `codex/runtime/aisoft_loop/change_audit.py` 与 `cli.py`：LEGACY 登记。
- `codex/tools/usage-bundle.py`：usage lock 可选键 `legacy_changes_before`，读取与 `--adopt` 保留。
- `codex/runtime/aisoft_architecture/{cli,validator,lockfile}.py`：catalog 快照选择、pin 快照的 review 过期降级、
  多 profiles 目录。
- 新增 `architecture/catalog-releases/2026.08.3/`（git 历史原样快照）；`architecture/install.sh` 安装它。
- `codex/tools/aisoft-project-check.sh`：LEGACY 行、catalog 落后 NOTE、项目自带 profile、GAP 带诊断码。
- 文档：`architecture/README.md`、`usage/CONTRACT.md`、`docs/adr/0001-platform-boundary.md` D5。
- 发布包新版本（下一个空闲版本，当前为 1.9.0）。

## 初步方案与建议

见 spec。核心取舍：catalog 的 pin 用「已发布 revision 的不可变快照」实现，而不是放宽 revision 比较——
NewEMaint 实测对 2026.08.3 快照重建的 lock 与其已提交 lock 逐字段相等，说明快照就是真 pin。

## 风险

- usage lock 增加可选键是项目可见的合同变化：旧版项目内工具读到新键会报「格式不受支持」，因此只有采用
  新版本后才应写这个键（写进使用合同）。
- LEGACY 只按编号阈值登记，不能顺带吞掉新目录的问题；阈值以上的目录照旧 GAP。
- 快照必须与历史逐字节一致，否则 catalog_sha256 不再匹配；以 NewEMaint 真实 lock 做回归。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 项目检查器新增 LEGACY 级、architecture CLI 新增按 revision pin 的 catalog 快照与项目自带 profile 扩展点、使用发布包 lock 结构加可选键并发新版本，属于新增功能、共享核心、外部契约与发布制品
risk_flags:
  - shared-core
  - external-contract
  - artifact
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

- 新增行为：LEGACY 级、catalog 快照选择、项目自带 profile（`contract_effect: add`）。
- 外部契约：usage lock 结构与项目可见的检查结论；发布制品：发布包新成员与新版本。
- verification：验收要在 NewEMaint、SFM、HSDB 真实检出上运行，无法由 diff review 与 CI 重放。

### 缺失的 acceptance criteria 或决策

- SFM 与 NewEMaint 的 `DOCKERFILE_DECLARATION_REQUIRED` 是 #288 规则缺口，不是 catalog 落后；默认保持 GAP
  （带诊断码），在确认点 1 请负责人裁决。
