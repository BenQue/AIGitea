---
issue: 146
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/146
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
depends_on: []
status: approved
branch: change/146-loop-controller-pr-url
created: 2026-08-23
updated: 2026-08-23
---

# Implementation plan

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | `documents.backfill_pr_number()` 与单测 | - | done |
| T02 | `LocalGit.commit_paths()`：恰好相等校验 + 单测 | - | done |
| T03 | Controller 在 `create_pr` 后回填、提交、push、更新 `head_sha` | T01, T02 | done |
| T04 | 失败升级为 NEEDS_HUMAN_DECISION 的三条路径与测试 | T03 | done |
| T05 | Codex 侧文档说明该步骤已自动完成 | T03 | done |
| T06 | 全量测试与 verification | T03, T04, T05 | done |

## T01 — 按 PR 号回填

`backfill_pr_number(repo, issue_number, pr_number) -> tuple[Path, bool]`：校验 `pr_number` 为正整数，用既有 `_pull_url_prefix()` 从 summary 的 `gitea_url` 推出 URL，委托 `backfill_pr_url()`。不复制任何校验逻辑。

## T02 — 受限提交

`LocalGit.commit_paths(paths: Sequence[str], subject: str) -> str`：

- `git status --porcelain` 的变更路径集合必须**恰好等于** `paths`，否则 `ProviderError`；
- `git add -- <paths>`、`git commit -m <subject>`，返回新 `head_sha`；
- 单测：正常提交、工作树多一个脏文件被拒、声明的路径没有改动被拒。

## T03 — 接入 Controller

在 `if pr_number is None:` 分支内、`_set_lifecycle` 之后：

```
summary_path, changed = backfill_pr_number(self.repo, issue_number, pr_number)
if changed:
    self.git.commit_paths((relative(summary_path),), f"docs(change-{n}): 回填 pr_url {pr} (#{n})")
    head_sha = self.git.push()
```

`changed` 为假时不提交、不 push。commit subject 与人工路径产出的那条保持同形。

## T04 — 失败升级

`ContractError` 与 `ProviderError` 都捕获 → `_set_lifecycle("awaiting-triage")` + `_finish(NEEDS_HUMAN_DECISION, redact(str(exc)), ...)`，与既有 `validate_provider_commit` 失败处置同形。

测试三条：summary 缺 `pr_url` 键、已有不同值、提交被 `commit_paths` 拒。

## T05 — Codex 侧文档

在 `skill-for-codex/SKILL.md` 的 `Preserve the Development Loop boundary` 一节与 `codex/skills/gitea-development-loop/SKILL.md` 写明：建 PR 后 Controller 自动回填 summary 的 `pr_url` 与 `status`，**不是**人工步骤；失败会升级为 `NEEDS_HUMAN_DECISION`。

## T06 — 验证

`test_controller.py` 的既有 fake git/gitea 扩展出 `commit_paths` 与真实 summary 文件，跑通完整一轮；全量 python 单测 + `smoke.sh`。

## 回滚

纯新增方法与一段接入代码，`git revert` 单个 commit 即可。不涉及安装、不改 broker、不需重装。
