---
issue: 392
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/392
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 为 superpowers 建平台 vendor pin 作三端核对基准并从发布包导出到项目级落点，改动外部技能 pin、快照校验、发布包合同、版本核对与平台技能，属于共享核心与平台治理
risk_flags:
  - agent-governance
  - platform-governance
  - shared-core
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-superpowers-vendor-pin-261020.md
  spec: spec-superpowers-vendor-pin-261020.md
  plan: plan-superpowers-vendor-pin-261020.md
  verification: verification-superpowers-vendor-pin-261020.md
confidence: high
override_reason: ''
depends_on:
  - 389
status: approved
branch: change/392-superpowers-vendor-pin
pr_url:
created: 2026-10-20
updated: 2026-10-20
---

## 问题/需求总结

D6 裁决（2026-10-20）：Claude、Codex、Cursor 用同一套 Matt + superpowers，superpowers 像 Matt 一样 vendor pin 7.0.0，改掉 #355 的「superpowers 不自建 pin」。现状是 Claude 官方插件 7.0.0（`bb92a77`），Codex 的 `superpowers@openai-curated` 已启用但 marketplace 未注册所以 `NOT_LOADED`（缓存 5.1.3），Cursor 缓存 superpowers 6.1.1、Matt 1.2.0。三端版本不齐，Codex 侧事实上没有 superpowers。

## 影响范围

负责人在确认点 1 修正：Claude 与 Codex 的 superpowers 继续由官方 marketplace 同步，平台不安装，只核对；vendor 快照供项目级（Cursor）导出。

- 新增 vendor 快照 `codex/vendor/superpowers/v7.0.0/`（15 个技能，74 个文件，MIT）。
- 快照校验模块 `codex/runtime/aisoft_loop/matt_snapshot.py` 增加技能包参数。
- 发布包 `codex/tools/usage-bundle.py` 增加 vendor 成员，`--build` 导出 superpowers 到 `.cursor/skills/`、Matt 到 `.agents/skills/` 与 `.cursor/skills/`；`usage/bundle.json` 发 1.3.0。
- `codex/tools/check-external-skill-versions.py` 三端报 PIN 状态。
- 治理文件：`08` §5、`skills/aisoft-platform/SKILL.md`「外部技能包边界」、`README.md` 对应两句。

## 初步方案与建议

见 spec 的「方案与决策」。

## 风险

- 与 R10a 同改发布包版本，后合并者用 merge commit 集成 main 并发下一版。
- Codex 官方来源当前只给到 6.4.2（且现启用的 `openai-curated` 5.1.3 未加载），到 7.0.0 之前 Codex 端是 `PIN_DRIFT` / `PIN_NOT_INSTALLED`，这是如实报告，不由本票安装解决。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 为 superpowers 建平台 vendor pin 作三端核对基准并从发布包导出到项目级落点，改动外部技能 pin、快照校验、发布包合同、版本核对与平台技能，属于共享核心与平台治理
risk_flags:
  - agent-governance
  - platform-governance
  - shared-core
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- `contract_effect: change`：改掉 `08` §5 与 `aisoft-platform` 技能里「superpowers 不自建 pin」的现行合同（D6）。
- 强制 complex：外部技能 pin 与快照校验（共享核心）、发布包合同新增成员模式、平台技能（治理）。
- 需要 `verification`：三端读回与 Cursor/Codex fresh 会话实测属于 installed/live 层，diff review 与 CI 不能重放。

### 缺失的 acceptance criteria 或决策

- 无；spec 的四项设计决定在确认点 1 一并确认。
