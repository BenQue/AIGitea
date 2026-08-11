# AI Issue 判级与标签实施计划

> **归档资料：** 本文件记录 2026-07 的一次性实施过程，不是当前执行计划。当前合同见
> [README](../README.md)、[03](../03-Issue-Spec-Plan与单闸门开发流程.md) 与
> [04](../04-Agent编排与定时任务.md)；正文命令、路径和状态不得直接重放。
>
> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **历史说明：** 本计划记录 2026-07-15 的初始 16-label 实施，因此正文保留当时的
> “七个流程状态”与验证数字。Issue #19 后续新增 `completed`，当前 canonical taxonomy
> 为 17 个标签、八个流程状态；不要把后来的合同倒写成当时已存在。

**Goal:** 将已经批准的“变更类型标签 → AI 复杂度判级 → 自动路由”合同同步到 AISoftPlatform 文档、模板、Codex skills、Gitea 标签和 `rsdesign-new` Issue #8 试点合同。

**Architecture:** `type/*` 描述 Issue 的主要变更类型，AI 根据产品合同影响和强制风险规则生成唯一有效的 `complexity/*`，现有七个标签继续只表达流程状态。中央平台仓库保存规范、模板和 skills；Gitea 保存实际标签与 Issue 审计；`rsdesign-new` 的 `change/8` 只承载试点项目合同和后续验证，不在本计划中启用或安装 Development Loop runtime。

**Tech Stack:** Markdown、YAML front matter、Codex skills、Bash、`jq`、Gitea REST API、Git worktree。

## Global Constraints

- 所有 Issue 都必须有 `00-summary.md`；只有有效复杂度为 `complex` 的 Issue 强制要求 `01-spec.md` 和 `02-plan.md`。
- `type/feature` 和 `type/platform` 强制为 `complex`；`type/bugfix`、`type/docs`、`type/test`、`type/refactor` 只是 `small` 候选。
- schema、数据迁移、共享 API、认证授权、安全、CI/部署、Agent 规则、跨模块核心逻辑和破坏性变更强制为 `complex`。
- Issue 明确要求 `complexity/complex` 时不得自动降级；Issue 要求 `complexity/small` 时仍必须通过 AI 安全校验。
- AI 无法安全判级时不得写入 `complexity/*`，Issue 保持 `awaiting-triage`。
- Development Loop 只能从 `small` 单向升级到 `complex`；不得在运行中自动降级。
- 最终 PR 合并仍是唯一交付硬闸门；本计划不授权自动合并或生产部署。
- 不打印或提交 token、`.env`、`auth.json`、Git credentials 或 Gitea credentials。
- 不运行 `codex/install-vm.sh`，不覆盖 VM 当前 v2 analyzer，不启用 `IMPLEMENT_PROVIDER`，不更新 Claude Code runtime。
- 每个任务只提交列出的文件；现有 `.DS_Store`、`.playwright-cli/`、其他工作树和无关修改保持不动。

## Approved Execution Order Adjustment

执行前预检确认 `worktrees/` 尚未被 Git 忽略，而且试点模板依赖中央模板。经用户批准，实际执行顺序调整为：

```text
Task 0 → Task 3 → Task 1 → Task 2 → Task 4 → Task 5 → Task 6
```

Task 0 先完成 worktree 安全准备；Task 3 先形成 canonical templates；Task 1 随后直接复制最终模板，不产生二次同步提交。其他任务内容和验收标准不变。

---

### Task 0: Ignore project-local worktrees before creating the pilot worktree

**Files:**
- Create: `.gitignore`

**Interfaces:**
- Consumes: the approved project-local worktree root `worktrees/`.
- Produces: a Git-ignored worktree root required by `superpowers:using-git-worktrees` before Task 1.

- [x] **Step 1: Verify the safety check currently fails**

```bash
git check-ignore -q worktrees
```

Expected: exit status 1 because `worktrees/` is not currently ignored.

- [x] **Step 2: Add the exact ignore rule**

Create `.gitignore` with:

```gitignore
/worktrees/
```

Do not add rules for `.DS_Store`, `.playwright-cli/` or any unrelated path in this task.

- [x] **Step 3: Verify and commit the safety preparation**

```bash
git check-ignore -v worktrees
git diff --check -- .gitignore
git add .gitignore
git commit -m 'chore: ignore local worktrees'
```

Expected: `git check-ignore -v` reports `.gitignore` and `/worktrees/`; the commit contains only `.gitignore`.

---

## File and State Map

### AISoftPlatform authoritative contract

- Modify: `AGENTS.md` — 根级判级、保护文件和 Loop 升级规则。
- Modify: `README.md` — 用户可见的自动判级流程与三层标签模型。
- Modify: `01-基础设施-VM-Gitea-Runner.md` — Gitea 标签集合与职责。
- Modify: `03-Issue-Spec-Plan与单闸门开发流程.md` — 判级算法、标签优先级和双路径。
- Modify: `04-Agent编排与定时任务.md` — analyzer 输出、自动路由和 Loop 启动校验。
- Modify: `08-Codex双工具共存与实施.md` — Codex-first 验证矩阵和安装暂停边界。
- Modify: `09-v3平台简化与Loop-Engineering文档改造规划.md` — 实施状态和完成证据。
- Modify: `codex/tests/smoke.sh` — 新合同的静态回归检查。

### Canonical templates and skills

- Modify: `templates/docs/changes/_template/00-summary.md`
- Modify: `templates/docs/changes/_template/01-spec.md`
- Modify: `templates/docs/changes/_template/02-plan.md`
- Modify: `templates/docs/changes/_template/03-verification.md`
- Modify: `skill-for-codex/SKILL.md`
- Modify: `skill-for-codex/references/onboarding-runbook.md`
- Modify: `codex/global-AGENTS.md`
- Modify: `codex/skills/gitea-analyze-change/SKILL.md`
- Modify: `codex/skills/gitea-analyze-change/agents/openai.yaml`
- Modify: `codex/skills/gitea-spec-plan/SKILL.md`
- Modify: `codex/skills/gitea-development-loop/SKILL.md`
- Modify: `codex/skills/gitea-implement-change/SKILL.md`

### Repeatable Gitea label provisioning

- Create: `codex/config/gitea-labels.json` — 16 个规范标签的名称、颜色和描述。
- Create: `codex/tools/sync-gitea-labels.sh` — 只创建缺失标签的幂等同步工具，不删除或改写已有标签。

### rsdesign-new pilot repository

- Modify: `AGENTS.md` — 用 v3 判级规则替换 v2“所有变更必须 spec/plan”和绝对禁止治理文件修改的规则。
- Replace: `docs/changes/_template/{00-summary,01-spec,02-plan}.md`
- Create: `docs/changes/_template/03-verification.md`
- Create: `docs/changes/8/{00-summary,01-spec,02-plan}.md`
- External state: Gitea Issue #8 labels and audit comment.

---

### Task 1: Bootstrap the rsdesign-new Issue #8 contract in an isolated worktree

**Files:**
- Modify: `/Users/benque/MyDocs/AISoftPlatform/worktrees/rsdesign-issue-8/AGENTS.md`
- Replace: `/Users/benque/MyDocs/AISoftPlatform/worktrees/rsdesign-issue-8/docs/changes/_template/00-summary.md`
- Replace: `/Users/benque/MyDocs/AISoftPlatform/worktrees/rsdesign-issue-8/docs/changes/_template/01-spec.md`
- Replace: `/Users/benque/MyDocs/AISoftPlatform/worktrees/rsdesign-issue-8/docs/changes/_template/02-plan.md`
- Create: `/Users/benque/MyDocs/AISoftPlatform/worktrees/rsdesign-issue-8/docs/changes/_template/03-verification.md`
- Create: `/Users/benque/MyDocs/AISoftPlatform/worktrees/rsdesign-issue-8/docs/changes/8/00-summary.md`
- Create: `/Users/benque/MyDocs/AISoftPlatform/worktrees/rsdesign-issue-8/docs/changes/8/01-spec.md`
- Create: `/Users/benque/MyDocs/AISoftPlatform/worktrees/rsdesign-issue-8/docs/changes/8/02-plan.md`

**Interfaces:**
- Consumes: Gitea Issue `http://gitea-ci.orb.local:3000/admin/rsdesign-new/issues/8` and the approved rules in `09` §§4.3 and 6.
- Produces: `change/8` as the single pilot branch, a complete complex contract, and project-local v3 templates used by later controller validation.

- [x] **Step 1: Create the isolated pilot worktree**

Use `superpowers:using-git-worktrees` at execution time, then run:

```bash
git -C /Users/benque/Projects/rsdesign-new fetch origin
git -C /Users/benque/Projects/rsdesign-new worktree add \
  /Users/benque/MyDocs/AISoftPlatform/worktrees/rsdesign-issue-8 \
  -b change/8 origin/main
```

Expected: a clean worktree on `change/8`; the existing `/Users/benque/Projects/rsdesign-new` checkout remains on `change/4` with its untracked `.DS_Store` files untouched.

- [x] **Step 2: Replace the project governance rules（历史执行；self-mod 条款已被最终审查 supersede）**

Use `apply_patch` to replace the current “每个改动必须有 spec/plan” and protected-file bullets with these exact rules while preserving all project commands, Prisma constraints, UI conventions and credential rules:

```markdown
- 每个改动对应一个 Issue；`docs/changes/<N>/00-summary.md` 必须存在。AI 根据 Issue、仓库证据和风险规则写入唯一有效的 `complexity/small` 或 `complexity/complex`。
- Bug 修复、纯文档、纯测试和不改变外部行为的内部重构可以是 small；新增功能或任何功能性更改必须是 complex，并补齐 `01-spec.md` 与 `02-plan.md`。
- schema/数据迁移、共享接口、认证授权、安全、CI/部署、Agent 规则、跨模块核心逻辑和破坏性变更强制为 complex。
- Issue 明确要求 complex 时不得自动降级；Issue 要求 small 时仍须通过 AI 校验。判级不清时保持 awaiting-triage，不得开始开发。
- `.gitea/workflows/`、部署脚本、`ecosystem.config.cjs`、`AGENTS.md`、`CLAUDE.md` 和 `.npmrc` 只有在 complex Issue 的 spec 明确列入范围、验证与回滚时才能修改；普通产品 Loop 禁止修改。
- Agent 不得在同一次运行中修改并立即采用约束自身的 `AGENTS.md`；治理规则变更后必须重新启动执行会话。
- 所有新 Issue 从分析开始使用单一 `change/<N>` 分支；最终 PR 使用 `Closes #N`，只有人可以合并受保护的 `main`。
```

Replace the branch rule with:

```markdown
- 变更分支: `change/<N>`（summary、spec/plan、代码和验证共用）；旧 `spec/<N>` 只用于历史兼容
- 提交信息: `<type>: <简述> (#<N>)`，type ∈ feat / fix / chore / docs / refactor / test
```

审计说明：该步骤确实在 pilot 提交 `ee5e9e1` 中修改了 governing `AGENTS.md`。最终整分支审查判定其中“同一次运行可修改但不立即采用”的 self-mod 条款弱于中央安全模型，因此该部分不能作为后续执行先例。remediation 提交 `2f9a4b9` 没有再次修改 `AGENTS.md`，只把 fresh controlled governance run 记录为进入 `approved` 前的阻塞动作。

- [x] **Step 3: Install the four canonical project templates**

Use `apply_patch` so the four pilot templates exactly match the AISoftPlatform canonical templates after Task 3. Verify:

```bash
for name in 00-summary.md 01-spec.md 02-plan.md 03-verification.md; do
  diff -u \
    "/Users/benque/MyDocs/AISoftPlatform/templates/docs/changes/_template/$name" \
    "/Users/benque/MyDocs/AISoftPlatform/worktrees/rsdesign-issue-8/docs/changes/_template/$name"
done
```

Expected: no diff. The approved execution order completes Task 3 before Task 1, so this step copies the final canonical templates directly and does not require a later reconciliation commit.

- [x] **Step 4: Write the Issue #8 summary and spec**

`00-summary.md` must set:

```yaml
issue: 8
gitea_url: http://gitea-ci.orb.local:3000/admin/rsdesign-new/issues/8
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - agent-governance
  - ci-integration
  - deployment-boundary
status: contract-drafting
branch: change/8
```

The summary must cite the inspected v2 facts: current `AGENTS.md` requires spec for every change, uses `spec/N`, and absolutely prohibits governance-file edits; the current platform wrapper still expects `spec/N` and the old summary heading.

`01-spec.md` must include these measurable acceptance criteria:

1. Analyzer outputs `change_type`, requested/assessed/effective complexity, contract effect, confidence, risk flags and required documents.
2. Feature and platform behavior changes always route to complex; safe bug/docs/test/refactor cases can route to small.
3. Explicit complex cannot be downgraded; explicit small cannot bypass forced-complex rules.
4. Unclear classification stays at `awaiting-triage` without a complexity label.
5. A running small Loop stops and requests reclassification when actual scope adds or changes product behavior.
6. Codex validation precedes Claude Code changes; production remains script-only.
7. Controller/runtime installation remains disabled until synthetic and real Issue verification passes.

The spec non-goals must exclude automatic PR merge, production deployment, deletion of v2 fallback scripts, and Claude Code runtime changes.

- [x] **Step 5: Write the Issue #8 ordered plan**

`02-plan.md` must contain this exact phase order:

1. Synchronize central contract documents and regression checks.
2. Synchronize canonical templates and front matter.
3. Update Codex analysis/spec/Loop skills and validate them.
4. Provision type/complexity labels idempotently and label Issue #8.
5. Design and implement the Codex-first analyzer/controller runtime in a later approved execution phase.
6. Run synthetic small/complex/unclear classifier cases.
7. Run one real small Issue and Issue #8 as the real complex case.
8. Record verification before enabling installation; update Claude Code only after Codex parity passes.

Every acceptance criterion must map to at least one `rg`, smoke, `quick_validate.py`, Gitea API assertion or real Issue verification. State “无生产部署；回滚为停止 controller、保持 `IMPLEMENT_PROVIDER=none`、继续使用现有 analyzer 与人工开发”。

- [x] **Step 6: Validate and commit the pilot contract**

Run:

```bash
git -C /Users/benque/MyDocs/AISoftPlatform/worktrees/rsdesign-issue-8 diff --check
rg -n 'effective_complexity: complex|type/feature|Agent 不得在同一次运行|change/<N>' \
  /Users/benque/MyDocs/AISoftPlatform/worktrees/rsdesign-issue-8/AGENTS.md \
  /Users/benque/MyDocs/AISoftPlatform/worktrees/rsdesign-issue-8/docs/changes/8
```

Expected: no whitespace errors; all four contract markers are present.

Commit only the listed governance/template/Issue files:

```bash
git -C /Users/benque/MyDocs/AISoftPlatform/worktrees/rsdesign-issue-8 add \
  AGENTS.md docs/changes/_template docs/changes/8
git -C /Users/benque/MyDocs/AISoftPlatform/worktrees/rsdesign-issue-8 commit \
  -m 'docs: define v3 loop pilot contract (#8)'
git -C /Users/benque/MyDocs/AISoftPlatform/worktrees/rsdesign-issue-8 push -u origin change/8
```

Do not open a docs-only PR and do not add `approved`; Issue #8 remains complex contract work until runtime implementation is explicitly started.

---

### Task 2: Synchronize the AISoftPlatform authoritative documents

**Files:**
- Modify: `AGENTS.md`
- Modify: `README.md`
- Modify: `01-基础设施-VM-Gitea-Runner.md`
- Modify: `03-Issue-Spec-Plan与单闸门开发流程.md`
- Modify: `04-Agent编排与定时任务.md`
- Modify: `08-Codex双工具共存与实施.md`
- Modify: `codex/tests/smoke.sh`

**Interfaces:**
- Consumes: approved design in `09` §§4.3 and 6.
- Produces: one consistent user-facing and agent-facing classification contract.

- [x] **Step 1: Add failing contract regression checks**

Append these checks to `codex/tests/smoke.sh`:

```bash
grep -Fq 'type/feature' "$ROOT/03-Issue-Spec-Plan与单闸门开发流程.md"
grep -Fq 'complexity/complex' "$ROOT/03-Issue-Spec-Plan与单闸门开发流程.md"
grep -Fq 'requested_complexity' "$ROOT/04-Agent编排与定时任务.md"
grep -Fq '功能性更改' "$ROOT/AGENTS.md"

if rg -n 'complexity_recommendation|最终 `complexity` 由人|人确认 Issue 验收标准与 complexity=small' \
  "$ROOT/AGENTS.md" "$ROOT/README.md" \
  "$ROOT/03-Issue-Spec-Plan与单闸门开发流程.md" \
  "$ROOT/04-Agent编排与定时任务.md"; then
  echo '检测到旧的人工确认或复杂度建议合同' >&2
  exit 1
fi
```

- [x] **Step 2: Run the smoke test and confirm the intended failure**

Run:

```bash
bash codex/tests/smoke.sh
```

Expected: non-zero because `03` does not yet contain `type/feature` and still contains `complexity_recommendation`.

- [x] **Step 3: Update the root contract and overview**

Apply these exact semantic changes:

- `AGENTS.md`: state that AI determines effective complexity; list small candidates and forced-complex conditions; allow governance files only when a complex spec explicitly authorizes them; prohibit same-run self-modification of `AGENTS.md`.
- `README.md`: change the sequence diagram from routine human complexity confirmation to AI classification and automatic routing; add the three label dimensions; keep human merge as the only delivery gate.
- `01`: document 16 labels as seven lifecycle, seven type and two complexity labels without claiming they are already live.

- [x] **Step 4: Rewrite the daily workflow and orchestration contract**

In `03`, replace the recommendation model with:

```text
Issue + needs-analysis
  → analyzer identifies type and contract_effect
  → forced-risk and explicit-label checks
  → complexity/small + approved, or complexity/complex + spec-drafting
  → unresolved input: awaiting-triage with no complexity label
```

In `04`, require the analyzer output fields from `09` §4.3, make the wrapper own label mutation, and require the controller to recompute contract validity rather than trusting `approved` alone. Keep the compatibility pause prominent: current VM wrapper remains v2 until Issue #8 runtime work passes tests.

In `08`, add synthetic classifier cases for bugfix/small, feature/complex, explicit-small override, explicit-complex preservation and unclear/awaiting-triage.

- [x] **Step 5: Run the contract regression test**

Run:

```bash
bash codex/tests/smoke.sh
```

Expected: `Codex platform static smoke checks passed.`

- [x] **Step 6: Commit the authoritative document update**

```bash
git add AGENTS.md README.md \
  01-基础设施-VM-Gitea-Runner.md \
  03-Issue-Spec-Plan与单闸门开发流程.md \
  04-Agent编排与定时任务.md \
  08-Codex双工具共存与实施.md \
  codex/tests/smoke.sh
git commit -m 'docs: route issues by AI-assessed complexity'
```

---

### Task 3: Normalize the canonical change-document templates

**Files:**
- Modify: `templates/docs/changes/_template/00-summary.md`
- Modify: `templates/docs/changes/_template/01-spec.md`
- Modify: `templates/docs/changes/_template/02-plan.md`
- Modify: `templates/docs/changes/_template/03-verification.md`
- Modify: `codex/tests/smoke.sh`

**Interfaces:**
- Consumes: classification schema in `09` §4.3.
- Produces: one front matter schema copied unchanged into pilot repositories.

- [x] **Step 1: Add failing template-schema checks**

Add:

```bash
for template in 00-summary.md 01-spec.md 02-plan.md 03-verification.md; do
  file="$ROOT/templates/docs/changes/_template/$template"
  grep -Fq 'change_type:' "$file"
  grep -Fq 'requested_complexity:' "$file"
  grep -Fq 'assessed_complexity:' "$file"
  grep -Fq 'effective_complexity:' "$file"
  grep -Fq 'contract_effect:' "$file"
  grep -Fq 'confidence:' "$file"
  grep -Fq 'risk_flags:' "$file"
done
! rg -n 'complexity_recommendation:' "$ROOT/templates/docs/changes/_template"
```

Run `bash codex/tests/smoke.sh`; expected: non-zero on the first missing `change_type` field.

- [x] **Step 2: Replace the front matter schema**

All four templates must use this shared classification block:

```yaml
change_type: CHANGE_TYPE
requested_complexity: auto
assessed_complexity: ASSESSED_COMPLEXITY
effective_complexity: EFFECTIVE_COMPLEXITY
contract_effect: CONTRACT_EFFECT
confidence: CONFIDENCE
risk_flags: []
```

`00-summary.md` must replace `## 复杂度建议` with `## AI 判级`, include the machine-readable classification values, the evidence, any override reason and missing acceptance criteria. Complex templates must state `effective_complexity: complex`; `03-verification.md` must preserve all `NOT RUN` honesty rules.

- [x] **Step 3: Run smoke and commit**

```bash
bash codex/tests/smoke.sh
git add templates/docs/changes/_template codex/tests/smoke.sh
git commit -m 'docs: normalize AI classification metadata'
```

Expected: smoke passes; only templates and their regression checks are committed.

---

### Task 4: Update Codex skills and onboarding behavior

**Files:**
- Modify: `skill-for-codex/SKILL.md`
- Modify: `skill-for-codex/references/onboarding-runbook.md`
- Modify: `codex/global-AGENTS.md`
- Modify: `codex/skills/gitea-analyze-change/SKILL.md`
- Modify: `codex/skills/gitea-analyze-change/agents/openai.yaml`
- Modify: `codex/skills/gitea-spec-plan/SKILL.md`
- Modify: `codex/skills/gitea-development-loop/SKILL.md`
- Modify: `codex/skills/gitea-implement-change/SKILL.md`
- Modify: `codex/tests/smoke.sh`

**Interfaces:**
- Consumes: canonical type matrix, priority rules and front matter from Tasks 2–3.
- Produces: deterministic analysis output consumed later by the Issue #8 wrapper/controller implementation.

- [x] **Step 1: Add failing skill-contract checks**

Add smoke assertions for `contract_effect`, `requested_complexity`, `effective_complexity`, `type/feature`, `needs-human-decision` and the small-to-complex escalation instruction in the relevant skill files. Run smoke and expect a non-zero result before editing the skills.

- [x] **Step 2: Make gitea-analyze-change classify instead of recommend**

Require exactly these five Markdown sections:

```text
## 问题/需求总结
## 影响范围
## 初步方案与建议
## 风险
## AI 判级
```

The `## AI 判级` section must contain:

```yaml
change_type: bugfix
requested_complexity: auto
assessed_complexity: small
effective_complexity: small
contract_effect: restore
reason: 恢复已经明确的既有行为
risk_flags: []
required_docs:
  - 00-summary.md
confidence: high
override_reason: ''
```

For `needs-human-decision`, omit `effective_complexity`, set `contract_effect: unclear`, and explain the one decision needed. The skill remains read-only: it emits classification data but does not mutate Git or Gitea labels.

- [x] **Step 3: Update planning and implementation skills**

- `gitea-spec-plan`: require `effective_complexity: complex`; reject ceremonial spec/plan for validated small work; use the shared metadata fields.
- `gitea-development-loop`: recompute forced-risk conditions before editing; if a small contract becomes add/change or crosses a forced risk, stop with `NEEDS_HUMAN_DECISION` and `NEXT: reclassify as complex and create spec/plan`.
- `gitea-implement-change`: allow protected governance files only when a complex spec explicitly lists them; never modify and immediately adopt governing `AGENTS.md` in the same worker run.
- `skill-for-codex`, onboarding and global AGENTS: describe type labels as inputs, complexity labels as AI outputs, and lifecycle labels as state.
- `agents/openai.yaml`: change “recommend small or complex” to “classify and explain the effective complexity”.

- [x] **Step 4: Validate every changed skill**

Run:

```bash
for dir in \
  codex/skills/gitea-analyze-change \
  codex/skills/gitea-spec-plan \
  codex/skills/gitea-development-loop \
  codex/skills/gitea-implement-change \
  codex/skills/gitea-platform-ops \
  skill-for-codex; do
  /usr/bin/python3 \
    /Users/benque/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
    "$dir"
done
bash codex/tests/smoke.sh
```

Expected: six `Skill is valid!` results and `Codex platform static smoke checks passed.`

- [x] **Step 5: Commit the skill update**

```bash
git add skill-for-codex codex/global-AGENTS.md codex/skills codex/tests/smoke.sh
git commit -m 'feat: classify Gitea issues before development'
```

Do not run `codex/install-vm.sh`; the checked-in skills are ahead of the current v2 wrapper by design.

---

### Task 5: Provision the Gitea label taxonomy idempotently

**Files:**
- Create: `codex/config/gitea-labels.json`
- Create: `codex/tools/sync-gitea-labels.sh`
- Modify: `codex/tests/smoke.sh`
- External: labels in `admin/rsdesign-new` and labels on Issue #8.

**Interfaces:**
- Consumes: `.agent.env` names without printing their values.
- Produces: exactly seven lifecycle, seven type and two complexity labels; repeated sync creates zero additional labels.

- [x] **Step 1: Add the canonical manifest**

Create a JSON array containing these exact names:

```text
needs-analysis awaiting-triage spec-drafting spec-review approved pr-open deployed
type/bugfix type/feature type/docs type/test type/refactor type/maintenance type/platform
complexity/small complexity/complex
```

Use stable six-digit colors and Chinese descriptions. Add a smoke assertion:

```bash
jq -e '
  length == 16 and
  (map(.name) | unique | length == 16) and
  all(.[]; (.name | length > 0) and (.color | test("^[0-9a-fA-F]{6}$")))
' "$ROOT/codex/config/gitea-labels.json" >/dev/null
```

- [x] **Step 2: Write the non-destructive sync tool**

`codex/tools/sync-gitea-labels.sh` must:

1. use `set -euo pipefail`;
2. load `AGENT_ENV_FILE` or `$HOME/.agent.env`;
3. require `GITEA_URL`, `GITEA_OWNER`, `GITEA_REPO`, `GITEA_TOKEN` and `jq`;
4. GET current repository labels once;
5. POST only manifest entries whose exact name is absent;
6. never DELETE or PATCH an existing label;
7. print only `created=N existing=M`, never headers, tokens or credential paths.

Add `bash -n` coverage to smoke. If ShellCheck is available, require it to pass.

- [x] **Step 3: Validate and commit before touching Gitea**

```bash
bash -n codex/tools/sync-gitea-labels.sh
command -v shellcheck >/dev/null && shellcheck codex/tools/sync-gitea-labels.sh
bash codex/tests/smoke.sh
git add codex/config/gitea-labels.json codex/tools/sync-gitea-labels.sh codex/tests/smoke.sh
git commit -m 'ops: add idempotent Gitea label taxonomy'
```

- [x] **Step 4: Apply the labels twice on local Gitea**

Start the VM if needed, but do not change services beyond normal startup:

```bash
orb start gitea-ci
orb -m gitea-ci sudo -u coder \
  /mnt/mac/Users/benque/MyDocs/AISoftPlatform/codex/tools/sync-gitea-labels.sh
orb -m gitea-ci sudo -u coder \
  /mnt/mac/Users/benque/MyDocs/AISoftPlatform/codex/tools/sync-gitea-labels.sh
```

Expected: the first run reports the number of missing labels created; the second reports `created=0 existing=16`. If the VM cannot start or the API is unavailable, stop with `BLOCKED_EXTERNAL` and do not claim live labels exist.

- [x] **Step 5: Label Issue #8 and verify effective state**

Using the existing credential environment without printing it, assign exactly:

```text
type/platform
complexity/complex
spec-drafting
```

Remove every other `type/*` and `complexity/*` label, plus every lifecycle label except `spec-drafting`. GET Issue #8 afterward and verify the sorted label names match the three names above. Post one audit comment explaining that `type/platform` and forced-risk rules made the effective complexity complex and link `docs/changes/8/` on branch `change/8`.

---

### Task 6: Run cross-repository verification and close the planning rollout

**Files:**
- Modify: `09-v3平台简化与Loop-Engineering文档改造规划.md`
- Modify: `10-AI-Issue判级与标签实施计划.md` — check completed boxes only after evidence exists.

**Interfaces:**
- Consumes: committed central changes, pilot `change/8`, and live Gitea labels.
- Produces: an honest handoff to the separate Codex controller implementation phase.

- [x] **Step 1: Run all central static checks**

```bash
bash -n codex/tests/smoke.sh
bash -n codex/tools/sync-gitea-labels.sh
bash codex/tests/smoke.sh
for dir in codex/skills/* skill-for-codex; do
  /usr/bin/python3 \
    /Users/benque/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
    "$dir"
done
git diff --check
```

Expected: shell syntax passes, smoke prints its success line, every skill validates, and `git diff --check` is silent.

- [x] **Step 2: Verify central/pilot template parity**

```bash
for name in 00-summary.md 01-spec.md 02-plan.md 03-verification.md; do
  diff -u \
    "templates/docs/changes/_template/$name" \
    "worktrees/rsdesign-issue-8/docs/changes/_template/$name"
done
```

Expected: no output.

- [x] **Step 3: Verify the pilot contract without claiming runtime success**

```bash
git -C worktrees/rsdesign-issue-8 status --short
git -C worktrees/rsdesign-issue-8 log -1 --oneline
rg -n 'effective_complexity: complex|contract_effect: add|IMPLEMENT_PROVIDER=none|不自动合并' \
  worktrees/rsdesign-issue-8/docs/changes/8
```

Expected: clean pilot worktree, the Issue #8 contract commit is present, and the four boundaries are documented. Do not run application tests as proof of controller behavior because no controller code is implemented in this rollout.

- [x] **Step 4: Update implementation status and commit**

In `09`, mark only the AI classification contract, template, skill and label rollout complete. Keep Loop controller, real small/complex execution, CI feedback, VM installation and Claude parity unchecked.

```bash
git add 09-v3平台简化与Loop-Engineering文档改造规划.md \
  10-AI-Issue判级与标签实施计划.md
git commit -m 'docs: record AI classification rollout evidence'
```

- [x] **Step 5: Handoff to the Issue #8 runtime implementation**

Report separately:

- implemented and committed central contract/skills;
- live Gitea labels verified or external blocker recorded;
- pilot contract branch and commit;
- VM installation still paused;
- next work: design/implement analyzer parser, `change/N` wrapper, controller, verifier, state store and Gitea PR/CI adapter under Issue #8;
- Claude Code update remains after Codex validation.

Do not mark Issue #8 `approved`, open the final PR, install skills on the VM, or start the controller as part of this plan.

---

## Final branch review remediation

- [x] Central smoke 不再依赖 HEAD 未跟踪的 runtime sources，并在 `f553422` 的干净 checkout 中复验通过。
- [x] README、`01`、`03`、`09` 已区分 live 16-label taxonomy 与尚未启用的 v2 wrapper/runtime routing。
- [x] `00-summary.md`、analyzer/spec/implementation skills 与 small/complex/unclear golden fixtures 已统一 safe/unresolved schema。
- [x] 普通 worker 的 governing `AGENTS.md` self-mod 边界已在中央 skills 中统一；试点合同把 fresh controlled governance run 记录为进入 `approved` 前的阻塞动作。
- [x] Gitea token 改由 curl stdin config 传递，sentinel mock 已验证 argv/stdout/stderr 不含 secret，且双次同步幂等、无 PATCH/DELETE。
- [x] Manifest smoke 锁定 16 个精确名称、六位颜色与非空描述。

Deferred runtime prerequisite：Task 1 的 `ee5e9e1` 曾修改试点 `AGENTS.md`，但其 self-mod 条款已被最终审查 supersede。本次 final-review remediation 没有再次修改该 governing 文件；后续必须由 fresh controlled governance run 应用已批准 proposal，并由另一个 fresh run 复核。在此之前不把 Issue #8 标记为 `approved`。
