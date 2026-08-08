---
issue: 58
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/58
status: pr-open
branch: change/58
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/64
created: 2026-08-08
updated: 2026-08-08
---

# Verification

## 基线

| Check | Status | Evidence |
|---|---|---|
| Fresh Gitea main | PASS | `origin/main@58daf44b0d48daa93d0fe6d9b95e910f191b1357`；`change/58` 已在 PR #63 merge 后再次 rebase |
| PR #40 ancestry | PASS | `825995faf1ecf40dc0981c46281c0213c86bd421` is ancestor of fresh main |
| Duplicate branch/PR | PASS | live read-only query found no `change/58` branch or PR |
| Protected main | PASS | direct/force push disabled; merge allowlist `admin`; required status check disabled |
| Canonical checkout preservation | PASS | user `.DS_Store` remains untracked and untouched; development uses Codex worktree |
| Change document resolver | PASS | 按用户明确要求保留四个 basename，并以 `summary.documents` 显式映射全部语义角色 |
| Baseline focused runtime tests | PASS | 60 tests passed before modification |

## 实现后验证

| Check | Status | Command / evidence |
|---|---|---|
| Focused release unit/fake integration | PASS | `PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests -p 'test_release_*.py'` → 77 tests |
| Artifact zero-call / phase negative call-count | PASS | `test_release_phases.py`：artifact 0 Docker calls；readiness 0 mutation；stage 0 migration/up；migrate 0 transport/up；activate/rollback 0 transport/migration |
| Fixed action gate | PASS | `test_release_gate.py`：fixed argv、sanitized env、started/completed audit；arbitrary action/relative profile/short SHA/writable grant 在 command 前拒绝 |
| Contract/schema/state migration | PASS | strict v2 manifest project/model binding、v1 release compatibility、state v1→v2 与 malformed receipt tests |
| Installer repeatability | PASS | `bash codex/tests/test-docker-release-install.sh` twice-manifest check；未调用 Docker，未创建 live profile/grant/Secret |
| Fake image-store harness | PASS | `bash codex/tests/test-docker-image-store-e2e-harness.sh` |
| Real harness default safety | PASS | full smoke 调用无参数 harness，仅断言 `NOT RUN: Docker image-store E2E`；未访问 daemon |
| Python syntax | PASS | `python3 -m compileall -q codex/runtime/aisoft_release codex/runtime/tests` |
| Shell syntax | PASS | `bash -n` 覆盖 install、CLI、gate、installer test 与 full smoke 中全部平台 shell |
| ShellCheck | PASS | `shellcheck` 覆盖新 gate/wrapper、installer、full smoke 与既有平台 shell |
| Platform full smoke | PASS | latest `origin/main` 上 `bash codex/tests/smoke.sh` → 275 tests + static checks |
| JSON schema/files | PASS | full smoke `jq empty` 覆盖 `docker-release/**/*.json`；schema contract unit tests PASS |
| Compatibility matrix unchanged | PASS | `git diff --quiet origin/main -- docker-release/compatibility/image-stores-v1.json` → exit 0 |
| Whitespace/diff integrity | PASS | `git diff --check` |

Focused tests在 artifact-only case 删除 target profile/env file 后仍 PASS，证明 producer conformance
不依赖 target inputs。Target readiness 的 fake event 精确为 capability/config；staging receipt绑定
full SHA、transport 与逐 service exact image ID。Activation failure只执行新/旧 release 的两次
`up`，没有 pull/load/tag/migration，并保持 state current release 不变。

`docker-release/v1` legacy `verify/deploy/status/rollback` 继续可读；单独 regression 证明 v1 rollback
仍保留旧 transport prepare 语义。`verify-artifact` 对 v1 返回明确 migration guidance，不静默补字段。

## 需要额外授权的真实环境验证

| Area | Status | Reason |
|---|---|---|
| Disposable Engine 29/containerd + Compose 5.1.4 consumer E2E | BLOCKED / NOT RUN | 未授权真实 Docker/VM mutation；matrix 不变 |
| Real Docker build/save/load/transfer | BLOCKED / NOT RUN | 未指定并授权 disposable daemon/VM |
| DockerLab/AppServer/production deployment | BLOCKED / NOT RUN | 明确排除 |
| Real PostgreSQL migration/backup/restore | BLOCKED / NOT RUN | 明确排除 |
| Application activation/health/browser acceptance | BLOCKED / NOT RUN | 无部署授权与独立 target |
| Real runtime rollback | BLOCKED / NOT RUN | 无已授权 disposable deployment |

以上 BLOCKED 项不影响 code/fake/installer 合同验收，但阻止 Compose 5.1.4 supported matrix 变更，
也阻止任何“已部署”“真实 migration/health/rollback PASS”的结论。

## 交付边界

本 Change 只交付可审 PR 和 exact verification handoff。PR、local tests 或绿色 CI 都不表示已部署；
人工 merge 是代码交付硬闸门，deployment、migration、health 与 rollback 仍需后续独立授权和证据。

## 当前发布门禁

| Check | Status | Evidence |
|---|---|---|
| Local `change/58` | PASS | coherent Issue branch，基于 fresh `origin/main`；实现头已通过 77 focused / 275 smoke |
| Gitea write credential | PASS | 用户在 macOS Keychain 更新临时 `admin` credential；显式绑定 username 后真实 push PASS，token value 未被读取或打印 |
| Remote `change/58` | PASS | initial implementation head `48970a6b64548021dcca05790742308942b8cba7` 与本地一致；本次 metadata 回填将生成 final head |
| Authenticated API fallback | NOT RUN | Git write path 已恢复，不再需要 Swagger/API fallback |
| Final PR | PASS | PR #64 `change/58 -> main` 为 Open、mergeable、未合并；正文包含真实换行的 `Closes #58` |
| Final-head CI | NOT CONFIGURED / NOT RUN | live `main` protection 的 `Enable Status Check` 未勾选、patterns 为空；不得将本地 275 tests 写成 remote CI PASS |

最终 metadata commit 推送后必须 read back PR #64 的 exact remote final head、Open/mergeable/unmerged
状态和 required CI 配置。不得修改权限、绕过保护、自动 merge 或把 PR 状态解释为 deployment。
