---
issue: 377
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/377
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 新增项目使用层合同、版本化使用发布包与 project-check 按版本核对，改动模板与验证矩阵，属于平台治理与共享核心
risk_flags:
  - platform-governance
  - shared-core
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-usage-bundle-261018.md
  spec: spec-usage-bundle-261018.md
  plan: plan-usage-bundle-261018.md
  verification: verification-usage-bundle-261018.md
confidence: high
override_reason: ''
depends_on: []
status: approved
branch: change/377-usage-bundle
pr_url:
created: 2026-10-18
updated: 2026-10-18
---

## 问题/需求总结

整改路线 R6（ADR 0001 D1、D2、D4、D6、D7）。负责人 2026-10-18 决定提前开工，目标是平台去项目实例化：项目实例与平台之间不再有直接硬性依赖，部署细节留在各项目，平台只保留流程与解决方案模式。现状是项目跟着平台 live main 走：指针写本机平台仓路径，vendored change 模板与平台最新版逐字节比较，平台一改所有项目同时变红；项目无法声明自己用的是哪一版平台合同。本票交付独立的平台使用合同、版本化使用发布包与项目 pin，project-check 改为按 pin 的版本核对，`08` 验证矩阵拆成两层，并清掉 R4 推迟的 summary 模板依赖边注释。

## 影响范围

新增 `usage/`（使用合同与发布包声明）、`codex/tools/usage-bundle.sh` 与其 Python 实现、回归测试；改 `codex/tools/aisoft-project-check.sh` 与其测试、`templates/project/AGENTS.md` 指针、summary 模板、`08` §7、project-align 参考文档、两侧平台技能的 project-align 指引、change 模板 digest、smoke 登记与整改路线。

## 初步方案与建议

见 mapped spec。发布包不新增 broker 操作、不用 Gitea Release：版本就是 `usage/bundle.json` 里只追加的历史表，每个版本记逐文件 sha256；项目在 `.aisoft/platform-usage.lock.json` pin 版本与摘要。

## 风险

模板与指针改动后，已接入项目的 `pointer-sections` 在采用新版本前报 GAP，这是预期的使用层采用工作，由各项目自己的 Issue 处理；平台 CI 不受影响。技能源改动让本机已装技能漂移，合并后由负责人重装。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 新增项目使用层合同、版本化使用发布包与 project-check 按版本核对，改动模板与验证矩阵，属于平台治理与共享核心
risk_flags:
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

- 新增功能（发布包工具、project-check 检查项）并改变下发给项目的模板与合同，按 `AGENTS.md` 判级规则强制 complex。
- 对接入项目的影响（NewEMaint、LocalWMS 当前 main 的读回）只能在本机取证，required CI 无法重放，所以声明 `verification`。

### 缺失的 acceptance criteria 或决策

- 无。负责人 2026-10-18 确认合同；R6 之后剩余的 NewEMaint 耦合按建议另开 R6b 批次。
