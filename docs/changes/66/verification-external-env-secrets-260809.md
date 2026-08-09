---
issue: 66
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/66
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - security
  - external-contract
  - shared-core
  - artifact
  - deployment
depends_on: []
status: local-verified
branch: change/66
pr_url:
created: 2026-08-09
updated: 2026-08-09
---

# External environment reference verification

## 环境与版本

- Worktree: `/Users/benque/.codex/worktrees/faa3/AISoftPlatform`
- Branch: `change/66`
- Fresh Gitea main / baseline: `dd5b2b9e0b22e4cd20effef5e22edce8765b6813`
- Gitea: `1.26.4`
- Docker/Compose/target/Secret: `NOT READ / NOT CALLED`

## 实时基线

| Check | Result | Evidence |
|---|---|---|
| Issue #66 | PASS | live `open`；正文与 AC 一致；0 comments；无已有 branch/PR |
| Issue #58 / PR #64 | PASS | closed/merged；merge SHA `97445947fff79a4c2db6fa764feb21660e281556` |
| Issue #67 / PR #68 | PASS | closed/merged；merge SHA `dd5b2b9e0b22e4cd20effef5e22edce8765b6813`；exact-main broker/helper 重装与二次 no-op PASS；`aisoft-platform-agent` 真实 push/read-back/delete canary PASS |
| Protected main | PASS | live `main.protected=true` |
| Required status check | NOT CONFIGURED | live `main.enable_status_check=false`；baseline SHA statuses 为空 |
| Issue #65 boundary | PASS | live `open`；真实 Engine 29/containerd + Compose 5.1.4 E2E 独立授权与证据闸门不变 |
| Current defect reproduction | PASS | 合法 `JWT_SECRET=${JWT_SECRET:?required}` 返回 `INVALID_CONTRACT ... environment.JWT_SECRET` |
| Pre-change focused release suite | PASS | 77 tests |

匿名 branch-protection detail 与 Actions runs API 返回 401。未查询任何 credential，因此不能从该端点
证明 merge allowlist 或 Actions run 状态；final-head 时只记录公开可回读的 required status 事实。

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| Focused contract/Compose/CLI/phase tests | PASS | red run 精确暴露 5 failures + 3 errors；rebase 到 Issue #67 merged main 后指定三个模块 43 tests PASS |
| Full release suite | PASS | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests -p 'test_release_*.py'` → 86 tests |
| Artifact-only CLI evidence | PASS | 合法 `JWT_SECRET`/`DATABASE_URL` 输出 `ok=true`、`target_facts=NOT_READ`、`docker_calls=0`；profile/env file 已删除 |
| Python compile | PASS | `python3 -m compileall -q codex/runtime/aisoft_release codex/runtime/tests` |
| Installer/fake harness | PASS | `test-docker-release-install.sh` 与 `test-docker-image-store-e2e-harness.sh`；未调用真实 Docker |
| Shell syntax / ShellCheck | PASS | docker-release install/CLI/gate、installer/fake/real-default harness 的 `bash -n` 与 ShellCheck |
| Platform full smoke | PASS | `PYTHONDONTWRITEBYTECODE=1 bash codex/tests/smoke.sh` → 289 Python tests + platform static/shell/install checks |
| Compatibility matrix zero diff | PASS | `git diff --quiet origin/main -- docker-release/compatibility/image-stores-v1.json` → exit 0 |
| High-confidence credential scan | PASS | changed runtime/release production files 未命中 private key、GitHub PAT、OpenAI-style key pattern |
| `git diff --check` | PASS | 无 whitespace error |
| Final-head PR/CI readback | NOT RUN | 尚未提交/推送/创建 PR |

## Acceptance criteria 结果

- AC-1：PASS。loader、Compose validator、CLI/runner 正例覆盖 `${NAME}`、`${NAME:?required}`、
  `JWT_SECRET` 与 `DATABASE_URL`。
- AC-2：PASS。literal Secret/URL/token/password、null sensitive value、default/alternate literal 全部拒绝。
- AC-3：PASS。`services.web.api_secret` 即使 value 是外部引用仍由 producer loader 与 target validator 拒绝。
- AC-4：PASS。manifest、architecture lock、offline inventory、target profile 与 state 有显式回归；
  通用 scanner 调用点未放宽。
- AC-5：PASS。CLI/runner success payload 保持 `target_facts=NOT_READ`、`docker_calls=0`，fake events `[]`。
- AC-6：PASS。敏感 environment producer/target model 相同则通过，引用 drift 则在 mutation 前拒绝。
- AC-7：PASS。legacy v1、schema/state/phase/transport tests 保持通过，compatibility matrix zero diff。
- AC-8：PASS。86 release tests、289 full smoke、installer/fake/syntax/ShellCheck/compile/diff checks 通过。
- AC-9：PARTIAL / NOT RUN。单一 local branch 已满足；commit、push、唯一 PR 与 final-head status 尚待执行。

## 真实环境与独立门禁

| Area | Result | Reason |
|---|---|---|
| Issue #65 Engine 29/containerd + Compose 5.1.4 E2E | BLOCKED / NOT RUN | 独立 Issue、环境与授权；本 Change 不替代 |
| Docker build/pull/save/load/config/up | NOT RUN | 明确禁止；测试使用 fake/临时 JSON |
| DockerLab/company server/AppServer/production | NOT RUN | 明确排除 |
| Target profile/Secret/env file | NOT READ | artifact-only isolation contract |
| Database/migration/Nginx/health/browser/rollback | NOT RUN | 无环境或部署授权 |
| Workflow dispatch/VM or Docker restart/prune | NOT RUN | 明确禁止 |
| PR merge | NOT RUN | 只允许用户人工操作 |

## 回滚

- 代码与文档：人工 revert 最终 PR。
- Artifact：不原地修改已发布 release；producer 以新的 exact platform merged SHA/bytes 重新生成。
- Environment/database：本 Change 无 mutation，因此没有环境或数据回滚动作。

## 遗留风险与未完成项

- Gitea 写入可能因新的 `admin` credential 缺失而阻塞；不得查询或借用 `ci-bot`。
- live required status 当前为 `NOT CONFIGURED`；PR 创建后必须按 final head 重新回读，不能用本地 PASS
  冒充 remote CI。
