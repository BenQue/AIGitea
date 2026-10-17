---
issue: 368
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/368
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - ci
  - agent-governance
depends_on:
  - 366
status: analyzed
branch: change/368-project-leak-guard
created: 2026-10-17
updated: 2026-10-17
git_scope:
  - docs/changes/368-project-leak-guard/summary-project-leak-guard-261017.md
  - docs/changes/368-project-leak-guard/spec-project-leak-guard-261017.md
  - docs/changes/368-project-leak-guard/plan-project-leak-guard-261017.md
  - codex/tests/check-project-leak.py
  - codex/config/project-leak-baseline.json
  - codex/runtime/tests/test_project_leak.py
  - codex/tests/smoke.sh
  - docs/governance/remediation-roadmap.md
---

## 目标

把 ADR 0001 D3 变成机器检查：项目名在白名单之外的出现次数只能减少，不能增加。

## 决定

- **项目名来源**：`gitea-governance.json` 中分类为 `internal-application` 的仓库名，加上 `host-access-broker.json` 中这些仓库对应的 `project_id` 与 `vm_profile.name`；再加基线文件里的 `retired` 列表（已退出项目，如 rsdesign）。`public-test` 仓库（myapp、smoke-test）名字是通用词，误报太多，不纳入。平台仓自身不纳入。检查器代码不写任何项目名。
- **匹配**：大小写不敏感的子串匹配，只扫 Git 跟踪的文本文件。
- **白名单（ADR D3）**：`codex/config/`、路径中含 `tests/` 或 `fixtures/` 段的文件、`*_test.go`、`docs/changes/`、`archive/`、`06-运维手册与踩坑集.md`、`docs/adr/`、`docs/governance/`、`codex/vendor/`。
- **棘轮**：基线 `codex/config/project-leak-baseline.json` 记 `{路径: 次数}`。基线外文件有命中，或命中超过基线，退出码 1 并列出文件与次数；命中减少只打印提示。`--write-baseline` 按当前仓库重写基线，供清理批次收紧基线时使用。
- **接入**：smoke 在 release evidence boundary 检查旁增加一行 `python3 -B codex/tests/check-project-leak.py`；单测放 `codex/runtime/tests/test_project_leak.py`，由现有 discover 自动执行。

## 验收标准

- AC1：在非白名单文件新增一个项目名，检查器失败并指出文件与次数；删掉后通过（单测覆盖，本机再手工演示一次）。
- AC2：基线与当前仓库一致时 smoke 全绿。
- AC3：检查器里没有项目名字面量；单测用临时 manifest 证明新增项目无需改代码。
- AC4：macOS 本机 smoke 全绿，PR CI 绿。

## 边界

- `git_scope` 为全部范围；不清理现存命中，不改 runtime 产品代码、broker、CI workflow、installer。
