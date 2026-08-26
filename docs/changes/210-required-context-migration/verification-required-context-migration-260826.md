---
issue: 210
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/210
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - security
  - shared-core
  - ci-integration
  - rollback
  - platform-governance
depends_on: []
status: verified
branch: change/210-required-context-migration
created: 2026-08-26
updated: 2026-08-26
---

# Evidence-approved required-context migration 验证记录

## 基线与范围

- Commit SHA: `e2b2aa019c6f1984f26813f6dbe51cf3810fa22d`（runtime/config/tests 实施；本验证记录随后的收口 commit 另计）。
- 基线：`origin/main` = `6e01c877544eb64016006feda76ea699e33a96b6`。
- 环境：macOS 本地 exact worktree；Gitea 只读状态通过受控 broker 读取。
- 本记录负责证明的 acceptance criteria：AC-1 至 AC-9。

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| fresh `git.fetch.main` | PASS | broker 返回 exact project/remote PASS；`origin/main` 与 HEAD 均为 `6e01c877544e…` |
| 同类 open Issue 去重 | PASS（在 broker exact-read 能力边界内） | #208 是不同范围的 auto-merge；#210 创建前不存在；repository docs 无同 slug/change；broker 无通用 Issue search surface |
| 改动前 live readiness | PASS/GAP | SOURCE、INSTALLED_CODEX、INSTALLED_CLAUDE、LIVE_REPO 均 PASS；LIVE_PROTECTION 为 status check disabled、contexts empty |
| 改动前 governance plan/apply | FAIL（预期基线） | 现场证据：action=`update-main-protection` 同时 blocker=`status-check-context-drift`；apply 在 snapshot/PATCH 前拒绝，live 未 mutation |
| PR #209 exact evidence read-back | PASS | PR #209 merged；head `de85f1d…` 的唯一 commit status id=3、context=`CI / verify (pull_request)`、state=success；Actions run #717 event=pull_request、conclusion=success、40s |
| red test baseline | FAIL（预期） | manifest 首次加入 evidence 时，旧 parser 对 25 个 test 报 unknown `required_context_migration`；证明测试先捕获缺口 |
| `PYTHONPATH=codex/runtime python3 -m unittest codex.runtime.tests.test_gitea_governance` | PASS | 28 tests；覆盖 strict evidence、显式 selector、普通 drift、snapshot/PATCH/read-back 失败、全字段 read-back、rollback 正反例 |
| `PYTHONPATH=codex/runtime python3 -m unittest codex.runtime.tests.test_gitea_governance codex.runtime.tests.test_host_access` | PASS | 135 tests；exit 0 |
| `python3 -m compileall -q codex/runtime/aisoft_gitea_governance` | PASS | exit 0 |
| `bash -n codex/tools/gitea-governance.sh codex/tests/smoke.sh` | PASS | exit 0 |
| `shellcheck codex/tools/gitea-governance.sh codex/tests/smoke.sh` | PASS | ShellCheck 可用；exit 0 |
| `PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli check-change-documents --repo .` | PASS | change-documents 与 change-pr-url 均 PASS；gap=0 |
| `bash codex/tests/smoke.sh` | PASS | 561 tests；exit 0；Codex platform static smoke checks passed |
| 最终 live protection read-back | GAP（预期，且证明未 mutation） | `main` direct/force push disabled、merge allowlist=`[admin]`、status check=false、contexts=[] |
| live branch protection apply | NOT RUN | 本 Issue 明确禁止 |
| runtime/skills 安装 | NOT RUN | 本 Issue 无安装范围 |
| 部署 | NOT RUN | 本 Issue 无部署范围 |
| final PR create/update | NOT RUN | 等待用户确认 |
| merge | NOT RUN | 永远由用户人工执行 |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | PASS | manifest evidence optional strict schema；CLI 只增加布尔 selector，没有 context/URL/repo override |
| AC-2 | PASS | exact repo/context/PR/head SHA/Actions run/status id/event/success 的正反 parser tests；真实 broker evidence 与 manifest 一致 |
| AC-3 | PASS | 只允许 disabled+empty 起点；wrong context、merge protection drift 与 undeclared repo 均 blocker |
| AC-4 | PASS | 默认 plan 保留 `status-check-context-drift`；显式安全路径只显示 `migrate-required-status-context` |
| AC-5 | PASS | pre snapshot 在 PATCH hook 前已存在；mode/写入失败时 zero PATCH；snapshot mode 600 原子发布 |
| AC-6 | PASS | PATCH、GET/read-back 失败测试；direct push 与 merge allowlist corruption 均被完整 read-back 捕获 |
| AC-7 | PASS | exact snapshot rollback 正例；extra key、wrong repo/main branch、missing protection field 在 mutation 前拒绝 |
| AC-8 | PASS | 28 定向、135 governance+host、561 smoke、compileall、bash -n 与 ShellCheck 均通过 |
| AC-9 | PASS | 当前停在唯一 final PR 创建前；live apply、安装、部署与 merge 全部保持 NOT RUN |

## 遗留风险与未完成项

- live apply、runtime/skills 安装、部署、final PR 与 merge 均未执行；live protection 最终只读值仍为 GAP。
- 本地测试只能证明确定性约束；未来 live migration 仍需独立授权、真实 snapshot、apply 后完整
  read-back 与 rollback 演练证据，不能从本 Change 的 source tests 推定 live 已收敛。
