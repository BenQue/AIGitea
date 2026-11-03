---
issue: 438
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/438
change_type: bugfix
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - agent-governance
  - ci-change
depends_on: []
branch: change/438-skill-frontmatter-yaml
created: 2026-11-03
updated: 2026-11-03
---

# 实施计划：技能 frontmatter 严格 YAML

## 全局约束与接口

- 检查器入口 `bash codex/tools/check-skill-frontmatter.sh [--root DIR]`，缺省为本仓；退出码 0 PASS、1 发现问题、2 无可用后端或用法错误。
- 环境变量 `AISOFT_YAML_BACKEND=python|ruby` 只用于测试强制后端；未设置时先 PyYAML 后 Ruby。
- 先写测试并看它红（TDD），再写检查器；最后才改 `SKILL.md`，以便在同一会话里观察守卫拦下旧字节。
- 停止条件：合同冲突、范围扩张、同一根因连续三次失败。

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 检查器 + 测试，拦下当前 main 的 `SKILL.md` | - | done |
| T02 | 修 `SKILL.md`、smoke 登记、发布 1.22.1，smoke 全绿 | T01 | done |
| T03 | 证据、交叉审查、证据索引行 | T02 | done |

## T01：检查器与测试

- **交付/范围**：`codex/tools/check-skill-frontmatter.{sh,py}`、`codex/tests/test-skill-frontmatter.sh`。
- **blocked_by**：无。
- **AC**：AC-2（反向部分）、AC-3。
- **接口/约束**：见全局约束；只读。
- **验证**：`bash codex/tests/test-skill-frontmatter.sh`；`bash codex/tools/check-skill-frontmatter.sh`（此时应红，点名 aisoft-platform）。
- **Expected**：测试绿；对仓库自身红且报 mapping values 错误。不覆盖 CI 主机上的 PyYAML 后端（本机无 PyYAML 时只跑 Ruby，PyYAML 后端由 CI 或 VM 实跑证明）。
- **停止条件**：两个后端在本机都不可用。

## T02：修复、登记与发版

- **交付/范围**：`skills/aisoft-platform/SKILL.md` 一处措辞；`codex/tests/smoke.sh` 5 处登记 + 对仓库执行检查器；`usage/bundle.json` 发布 1.22.1。
- **blocked_by**：T01。
- **AC**：AC-1、AC-2、AC-4、AC-5。
- **接口/约束**：`usage-bundle.sh --release 1.22.1 --today 2026-11-03 --compatibility patch --notes <一句话>`。
- **验证**：`bash codex/tests/smoke.sh`；`bash -n` 与 ShellCheck；VM 上用 PyYAML 后端跑检查器；删执行行的反向证明。
- **Expected**：smoke 全绿；两个后端都 PASS；删执行行后旧字节不再被拦。
- **停止条件**：smoke 红在与本批无关的闸门时先查陈旧 checkout，不改闸门。

## T03：证据与审查

- **交付/范围**：verification、证据索引行；Codex（Herdr 只读窗格，gpt-6-astra / high）对候选 head 交叉审查。
- **blocked_by**：T02。
- **AC**：AC-6。
- **验证**：审查结论 PASS，记录 40 位 head。
- **Expected**：FAIL 项修复后对新 head 重审。
- **停止条件**：审查连续三轮 FAIL 同一根因时升级给人。

## Expected touch points

- T01：`codex/tools/check-skill-frontmatter.sh`、`codex/tools/check-skill-frontmatter.py`、`codex/tests/test-skill-frontmatter.sh`
- T02：`skills/aisoft-platform/SKILL.md`、`codex/tests/smoke.sh`、`usage/bundle.json`
- T03：本目录 verification、`docs/governance/review-evidence-index.md`

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | 两个后端各跑检查器；`git diff origin/main -- skills/aisoft-platform/SKILL.md` |
| AC-2 | `bash codex/tools/check-skill-frontmatter.sh`；旧字节夹具 |
| AC-3 | `bash codex/tests/test-skill-frontmatter.sh` |
| AC-4 | `bash codex/tests/smoke.sh`；`grep -n` 计数；删执行行反向证明 |
| AC-5 | `bash codex/tools/usage-bundle.sh --verify --baseline-ref origin/main` |
| AC-6 | Codex 只读交叉审查 |

## 执行证据

<!-- execution-evidence:start -->
T01–T03 已完成；ticket_base `7bd38270`，candidate_head `95d22b71`，验证结果与审查记录见本 Issue 映射 verification。
<!-- execution-evidence:end -->

语义摘要仅排除图中的 Status 单元、updated 与这段成对标识的执行证据；原始全文摘要另存审计。

## 部署与回滚

无。平台仓不部署；回滚是 revert PR。
