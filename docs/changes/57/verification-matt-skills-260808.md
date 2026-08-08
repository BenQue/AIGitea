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
status: ready-for-review
branch: change/57
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/59
created: 2026-08-08
updated: 2026-08-08
---

# Matt skills development orchestration verification

## 环境与版本

- Repository: `/private/tmp/aisoft-change-57`
- Branch: `change/57`
- Matt snapshot: `v1.2.2`
- Upstream commit: `8b36d4fb2635b3c21998dcd8144439c9e5ba7302`
- ShellCheck: `/opt/homebrew/bin/shellcheck`

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests -p 'test_*.py'` | PASS | 240 tests，全部通过 |
| `PYTHONDONTWRITEBYTECODE=1 bash codex/tests/smoke.sh` | PASS | 包含 `bash -n`、ShellCheck、runtime、label、installer 与 snapshot 静态/合成验证 |
| `bash codex/tests/test-agent-runtime.sh` | PASS | 两次安装幂等，35 个 Matt skills、`current` symlink 与无伪造 N-1 rollback 通过 |
| `python3 -m aisoft_loop.matt_snapshot verify ...` | PASS | tag `v1.2.2`、35 skills、exact upstream commit 与 manifest hash 一致 |
| `git diff --check` | PASS | 无 whitespace error |
| 高置信 Secret pattern scan | PASS | private key、GitHub PAT、OpenAI-style key 未命中；既有 sentinel fixture 明确排除 |
| Gitea PR #59 pre-handoff read-back | PASS | open、base `main`、implementation head `e650fd9ffd1d4076ac3ac378ba9edf86c4ba9061`、`mergeable: true`；本记录的纯文档 handoff commit 会再推进 head |
| Gitea commit status contexts | NOT CONFIGURED | combined state 为 `pending`，但 `total_count: 0` 且 `statuses` 为空；不得表述为 CI 已运行或通过 |

## Acceptance criteria 结果

- AC-1–AC-4：PASS。新命名与显式 resolver 已覆盖；legacy fixtures 继续通过。
- AC-5：PASS。platform 与 Matt 标签独立 reconciliation，错误组合 fail closed。
- AC-6–AC-7：PASS。spec/plan publisher 只写当前 Issue 映射路径；Ticket graph frontier 与 runtime completion 有合成测试。
- AC-8–AC-10：PASS。Agent 本地 commit、Controller post-validation/push/单 PR 与无 merge/deploy surface 有测试。
- AC-11：PASS。完整 vendor snapshot、license、manifest、control hash、重大更新分级与 installer rollback 模型通过。
- AC-12：PASS。focused、full suite、smoke、ShellCheck 与 diff checks 通过。

## 未运行与独立门禁

- 当前 Gitea 仓库的 24-label live provision/read-back：`NOT RUN`。source manifest 与 mock transport 已通过；不在 PR 合并前推广 live taxonomy。
- 用户级或 VM live Matt skills 切换：`NOT RUN`。安装器仅在临时 HOME 验证，未修改现有全局 skills 或 Claude plugin。
- 根级 `AGENTS.md` 与 `codex/global-AGENTS.md` 的 Matt 路由更新：`DEFERRED`。本次运行不得修改其正在遵循的根级说明；合并后必须走独立 governance step。
- PR required CI：`NOT CONFIGURED`。当前 live head 没有任何 status context；本仓库 manifest 的 required contexts 也为空。
- PR merge：`NOT RUN`，只允许人工操作。
- Deployment：`NOT RUN / NOT APPLICABLE`，本 Change 不部署应用或生产环境。

## 回滚

- 代码与文档：人工 revert 最终 PR；legacy resolver 保持可用，不需要重命名历史 Issue 文件。
- Matt 安装：安装器只在 verified snapshot 后原子切换 `current`；版本变化时保留 `previous`，失败可恢复 N-1。
- 标签：未执行 live provision，因此本次无外部标签回滚动作。

## 遗留风险

- 在独立治理步骤更新根级 Agent 路由前，仓库文档与 runtime 已支持 Matt，但根指令仍会优先提示旧固定 basename 与 `gitea-*` skills。该差异已显式保留，不能在本 PR 中宣称“全局生效”。
