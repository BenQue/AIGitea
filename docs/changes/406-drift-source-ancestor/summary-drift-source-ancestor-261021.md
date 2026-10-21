---
issue: 406
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/406
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 放宽漂移检查对安装源提交的绑定语义，属平台治理工具的检查合同变更
risk_flags:
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-drift-source-ancestor-261021.md
  spec: spec-drift-source-ancestor-261021.md
  plan: plan-drift-source-ancestor-261021.md
  verification: verification-drift-source-ancestor-261021.md
route:
  process: complex-production
  tier: frontier
  effort: max
  skills: to-spec, to-tickets, executing-plans, verification-before-completion
  method: spec-plan
  verify: full+reverse-proof
  review: cross-provider
  confirm: 2
confidence: high
override_reason: ''
depends_on:
  - 397
status: approved
branch: change/406-drift-source-ancestor
pr_url:
created: 2026-10-21
updated: 2026-10-21
---

## 问题/需求总结

`check-installed-drift.py` 的 `RotationSurface` 要求安装记录 `source_sha` 与当前检出 HEAD 完全相等，helper 构建凭证的 `source_commit` 也要求等于 HEAD。main 每前进一个提交（哪怕只改文档），broker 安装面都报 `rotation-source-binding` GAP，直到两台重装。改为：安装源提交是当前 HEAD 的祖先、且受管文件逐字节一致即 PASS。合同与验收见 spec。

## 影响范围

`codex/tools/check-installed-drift.py` 与 `codex/tests/fixtures/installed-drift/test-installed-drift.py`。轮换工具 `credential_rotation.py` 不动。

## 初步方案与建议

把 `source_identity` 里的只读 git 调用抽成模块级函数复用；`source_sha` 先按 SHA 格式校验再做 `merge-base --is-ancestor`；helper 凭证的 `source_commit` 改为对齐安装记录。

## 风险

放宽过度会让陈旧安装被判 PASS；缓解：逐字节比对与受管源码一致性闸门全部保留，夹具覆盖改轮换文件与非祖先两种 GAP，并做反向证明。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 放宽漂移检查对安装源提交的绑定语义，属平台治理工具的检查合同变更
risk_flags:
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

- type/platform 强制 complex；改变漂移检查 PASS/GAP 的判定合同（contract_effect=change）。
- 规则引擎 `Classification(...).route()` 实跑得 complex，required_docs 四份。
- 需要 Mac 与 VM 真实读回，验收证据不能由 diff review 与 CI 重放，故声明 verification。

### 缺失的 acceptance criteria 或决策

- 无。#316 待确认点已核实：轮换闸门只比对安装记录、命令参数与 grant 三处 `source_sha`（`credential_rotation.py` 的 `installation_receipt` 与 `validate_grant`），不读检出 HEAD，故只改漂移检查。
