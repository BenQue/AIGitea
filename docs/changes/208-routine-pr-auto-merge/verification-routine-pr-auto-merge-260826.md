---
issue: 208
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/208
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - agent-governance
  - security
  - shared-core
  - ci
depends_on:
  - 207
status: pending
branch: change/208-routine-pr-auto-merge
created: 2026-08-26
updated: 2026-08-26
---

# Routine PR 受控自动合并验证记录

## 基线与范围

- Commit SHA: 待 T03/T04 收口
- 基线：`origin/main` = `6e01c877544eb64016006feda76ea699e33a96b6`
- 环境: macOS exact isolated worktree；Gitea 状态只经 project-scoped host-access broker 读取
- 本记录负责证明的 acceptance criteria: AC-1 至 AC-13

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| `git fetch origin --prune` + `git rev-parse origin/main` | PASS | fresh fetch 后 exact merged baseline 为 `6e01c877544eb64016006feda76ea699e33a96b6`，即 #207 PR #209 merge commit |
| broker `gitea.issue.read/comments.read/labels.read --number 208` | PASS | Issue open；0 comments；`type/platform + complexity/complex + spec-drafting`；正文明确 #207 依赖、manual exclusions、hard gates、#208 自身人工合并 |
| broker `gitea.pulls.read --state open` | PASS | 实施前 AISoftPlatform 开放 PR 为 0 |
| source operation/identity audit | GAP（预期基线） | merge operation count=0；identity bindings 仅 manager/project-agent；governance merge allowlist contract 仅 human |
| broker `gitea.protection.read` | GAP（预期基线） | live `main` 禁 direct/force push、block rejected reviews，但 status check disabled/contexts empty，merge allowlist 仅 `admin`；#207 source required context 尚未 live apply |
| Gitea official API documentation check | PASS | `POST .../pulls/{index}/merge` 支持 `head_commit_id`、`force_merge`、`merge_when_checks_succeed`、`delete_branch_after_merge`；本 spec 固定 exact head、non-force、non-scheduled、delete branch |
| mapped document resolver/audit | 待执行 | T01 commit 前运行 |
| governance-only T02 checks | NOT RUN | 待独立 execution |
| T03 定向 Python/shell tests | NOT RUN | 待 fresh runtime execution |
| `bash codex/tests/smoke.sh` | NOT RUN | 待 T04 |
| 修改 shell 的 `bash -n` / ShellCheck | NOT RUN | 待 T04；ShellCheck 可用性届时记录 |
| skills/runtime 安装 | NOT RUN | 本 Issue 禁止安装或更新 live bytes |
| credential provision / live governance apply | NOT RUN | 本 Issue 不创建 merger credential、不修改 live protection |
| deployment | NOT RUN | merge authorization 不传递部署授权；本 Issue 无部署 |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | 待执行 | T02/T03 session and Controller tests |
| AC-2 | 待执行 | Controller state/head tests |
| AC-3 | 待执行 | eligibility matrix |
| AC-4 | 待执行 | forced-complex/manual matrix，包含 #208 |
| AC-5 | 待执行 | governance identity/permission/read-back tests |
| AC-6 | 待执行 | broker typed surface tests |
| AC-7 | 待执行 | hard-gate integration matrix |
| AC-8 | 待执行 | exact Gitea merge payload/head drift tests |
| AC-9 | 待执行 | stable single-reason/zero-POST tests |
| AC-10 | 待执行 | merge receipt/no-deploy/session completion tests |
| AC-11 | 待执行 | manual fallback/stop tests |
| AC-12 | 待执行 | T02/T03 commit and fresh-run evidence |
| AC-13 | 待执行 | final targeted/full validation |

## 遗留风险与未完成项

- 当前 live protection 没有 required contexts，任何 routine merge 必须 fail closed；source 实现不得把它写成 PASS。
- installed skills/runtime、routine merger credential/account/collaborator、live allowlist/protection 与部署全部保持
  `NOT RUN`，必须由合并后的 source 与独立授权分别处理。
- 最终 PR 尚未创建；本任务必须停在提交 PR 前的人工作业闸门。
