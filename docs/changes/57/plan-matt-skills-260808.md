---
issue: 57
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/57
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
  - shared-core
depends_on: []
status: pr-open
branch: change/57
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/59
created: 2026-08-08
updated: 2026-08-08
---

# Matt skills development orchestration plan

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 新旧 change 文档合同与确定性 resolver | - | completed |
| T02 | 新格式 analyzer、模板、skills 和 PR 链接 | T01 | completed |
| T03 | 正交 triage 标签及单一 LabelProjector | T01 | completed |
| T04 | to-spec/to-tickets Gitea tracker adapters | T01, T02 | completed |
| T05 | implement Agent commit 与 Controller post-validation | T01 | completed |
| T06 | 完整 Matt snapshot manifest 与更新分级检查 | T04, T05 | completed |
| T07 | 文档、全量验证和最终 PR | T02, T03, T04, T05, T06 | completed |

## Tasks

### T01 — Change document resolver

- 扩展受限 front matter parser，仅为 `documents` 支持一层安全 mapping。
- 新合同接受语义 `required_docs` 并严格解析显式 mapping；legacy 合同只接受四个旧 basename。
- 校验角色、相同短 slug、YYMMDD 与 `created`、basename 长度、目录边界和唯一 active 文件。
- 先写 red fixtures，再实现解析；`Contract.required_docs` 返回实际 basename。

### T02 — Writers, templates and PR links

- 将 analyzer/template 写入从 Issue #57 起切换为短 slug 新名称，并固定创建日期。
- 更新 PR body、CLI、wrapper、source skills 和文档引用，使其读取 resolver 结果。
- 保留 legacy reader tests；所有新 writer tests 断言不产生数字前缀 basename。

### T03 — Triage label projection

- 定义两个 category 与五个 state 的 namespaced label contract。
- 建立唯一 LabelProjector，保证 Matt 标签与现有 type/complexity/lifecycle 独立更新。
- 增加 provision/read-back 与 mock transport tests；`ready-for-agent` 不改变 `approved`。

### T04 — Spec and plan adapters

- 实现 `publish_spec(issue, body)` 与 `publish_plan(issue, graph)` 的 Issue-bound adapter。
- spec 写当前映射的 `spec-*`；plan 写 `plan-*` 并保留 `Txx`、`blocked_by`、AC mapping 和 expected
  touch points。
- 默认禁止创建子 Issue；拒绝不存在 Issue、错误 branch、重复 active 文档和越界路径。

### T05 — Implement commit boundary

- Development Loop 显式分派 `$implement` 与 frontier `Txx`。
- provider 允许在 exact `change/N` 原子 commit，但禁止远端 mutation。
- Controller 在 push 前验证 branch、ancestry、commit message、merge/rebase/force 边界、改动路径、Secret、
  clean tree 和 tests；使用追加 fix commit 保留审计历史。

### T06 — Matt update integrity

- 保存完整 snapshot manifest、source/tag/commit、skill 清单、hash、license 和 adapter contract version。
- 提供隔离 staging 和 conformance check；不直接对 live global skills 运行 latest update。
- 兼容更新可生成 maintenance 候选；skill 增删/流程/权限/工具/网络/Git 副作用变化输出 complex gate。
- 保留 N-1 rollback 元数据，不修改 Claude-owned plugin。

### T07 — Documentation and delivery

- 更新 README、编号分册、模板说明和 source skills，但不在当前运行中修改生效中的根级代理说明文件。
- 运行 focused unit tests、完整 Python suite、smoke、`bash -n`、ShellCheck（可用时）、diff 与 Secret checks。
- Agent 创建范围内原子 commits；Controller fast-forward push `change/57` 并创建唯一 `Closes #57` PR。
- 等待 required CI，停止在人工 merge gate；部署为 `NOT RUN`。

## Expected touch points

- `codex/runtime/aisoft_loop/{classification,contract,gitea,controller,cli}.py`
- `codex/runtime/tests/` 与 `codex/tests/`
- `codex/agent/` analyzer wrappers
- `codex/skills/` Matt/Gitea adapters
- `codex/tools/` label、snapshot 与 conformance helpers
- `templates/docs/changes/_template/`
- `README.md`、`03-Issue-Spec-Plan与单闸门开发流程.md`、`04-Agent编排与定时任务.md`、
  `08-Codex双工具共存与实施.md`
- `docs/changes/57/`

以上只是预期位置，不扩大 spec 授权；实现可按现有模块边界调整并在 PR 中说明。

## Acceptance criteria mapping

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | `python3 -m unittest codex.runtime.tests.test_contract` + filename boundary fixtures |
| AC-2 | resolver created/updated/slug uniqueness tests |
| AC-3 | new mapping success and invalid mapping fail-closed tests |
| AC-4 | legacy contract fixtures + static check that new writers do not emit legacy names |
| AC-5 | mock Gitea LabelProjector tests and label provision fixture |
| AC-6 | spec/plan adapter tests with exact Issue and branch boundaries |
| AC-7 | ticket graph schema/frontier/AC mapping tests |
| AC-8 | temporary Git repo tests for Agent commit permissions and forbidden operations |
| AC-9 | Controller post-validation success/failure fixtures |
| AC-10 | Gitea PR contract tests plus review that no merge endpoint exists |
| AC-11 | snapshot manifest/hash/change-classification tests |
| AC-12 | `PYTHONDONTWRITEBYTECODE=1 bash codex/tests/smoke.sh`; `bash -n`; ShellCheck; `git diff --check` |

## Database migration

无数据库迁移。

## Deployment and rollback

不执行部署。代码可通过 revert 最终 PR 回滚；legacy reader 保留，因此回滚不会要求重命名历史文档。
Matt snapshot 更新失败时保持当前已固定版本并使用 N-1 元数据恢复。PR 合并只由人工操作。
