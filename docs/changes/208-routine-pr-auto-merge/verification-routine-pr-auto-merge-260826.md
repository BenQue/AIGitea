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
status: verified
branch: change/208-routine-pr-auto-merge
created: 2026-08-26
updated: 2026-08-26
---

# Routine PR 受控自动合并验证记录

## 基线与范围

- Commit SHA: `892d5fa6e80bc222db8bbf14e05bc8080f6455a1`（T03 implementation head；本 T04 验证/修复 commit 随后追加）
- 基线：fresh fetch 后 `origin/main` = `5de8defc510fe057fbe92c33112c3d482b6d0d75`
- 环境: macOS exact isolated worktree；source tests 使用 fake transports/临时目录；readiness 为只读检查
- 本记录负责证明的 acceptance criteria: AC-1 至 AC-13

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| `git fetch origin --prune` + `git rev-parse origin/main` | PASS | exact merged baseline 为 `5de8defc510fe057fbe92c33112c3d482b6d0d75`，即 #210/PR #211 人工合并结果 |
| T02/T03 commit boundary | PASS | T02 commits `bc5c551`、`62aad82`；T03 `892d5fa` 的 parent 精确为 `62aad82`；恢复执行已重读最新 `AGENTS.md` 与全部合同文档 |
| Gitea 1.26 API 文档核对 | PASS | official source 证明 merge payload 包含 `head_commit_id`、`force_merge`、`merge_when_checks_succeed`、`delete_branch_after_merge`；review schema 含 `stale`/`dismissed`，实现只拦有效拒绝 |
| canonical manifest static audit | PASS | AISoftPlatform context 精确为 `CI / verify (pull_request)`；10/10 repositories 的 `routine_auto_merge_enabled=false`；routine identity route 只有 `gitea.pull.merge.routine(number,sha)` |
| `PYTHONPATH=codex/runtime python3 -m unittest ...test_routine_merge ...test_controller ...test_state ...test_gitea_governance ...test_host_access` | PASS | 205 tests；exit 0；覆盖两确认点、manual matrix、#208、identity/custody、push/force allowlist、hard gates、final head、zero POST/fallback |
| `bash codex/tests/test-bootstrap-gitea-service-account.sh` | PASS | fake binary/curl/临时 credential root；只验证 deterministic bootstrap source，未 provision live identity/token |
| `bash codex/tests/test-host-access-broker.sh` | PASS | fake broker/installer tests；exit 0 |
| `PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli resolve-documents 208 --repo .` | PASS | summary/spec/plan/verification exact semantic mapping |
| `PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli check-change-documents --repo .` | PASS | `changes=95 pass=2 gap=0` |
| `bash codex/tests/smoke.sh` | PASS | 583 tests；exit 0；fake/preflight/integration harness 未触达 live provisioning |
| 修改 shell 的 `bash -n` | PASS | 3 个 modified shell；exit 0 |
| 修改 shell 的 ShellCheck | PASS | `/opt/homebrew/bin/shellcheck` 可用；3 个 modified shell；exit 0 |
| `bash codex/tools/aisoft-platform-readiness.sh` | GAP/BLOCKED | source PASS（当前 committed HEAD，exact SHA 记录于交接）；installed Codex DRIFT 7、Claude DRIFT 5；live repo/protection BLOCKED，未伪装成 PASS |
| skills/runtime 安装 | NOT RUN | 本 Issue 禁止安装或更新 live bytes |
| credential provision / live governance apply | NOT RUN | 本 Issue 不创建 merger credential、不修改 live protection |
| deployment | NOT RUN | merge authorization 不传递部署授权；本 Issue 无部署 |
| 最终 PR / PR CI | NOT RUN | 按合同停在创建唯一最终 PR 前；未 push，因此 CI 不能写成 PASS |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | PASS | Codex/Claude session contract test 锁定“合同/启动 + 提交最终 PR”两点，并拒绝归档确认 |
| AC-2 | PASS | persisted confirmation 绑定 Issue/branch/policy；CI repair 与 final exact SHA tests 通过 |
| AC-3 | PASS | routine small 正例要求 small、restore/unchanged、局部可逆、internal-application、opt-in、non-empty contexts |
| AC-4 | PASS | complex、feature/security/data/platform、#208、major/phase、shared-core/cross-module、CI/artifact/deploy/rollback/governance 全部负例 |
| AC-5 | PASS | `native_merge_only_acl=false`；exact-repo Write identity、broker-exclusive custody、cross-project denial；main push/force allowlist 为空 |
| AC-6 | PASS | manifest 只有一个 routine merger operation，参数精确为 number+sha；extra/raw target 参数拒绝 |
| AC-7 | PASS | authorization、summary/Gitea 分类、exact tuple/唯一 PR、state/base/head、protection、CI、review、dependency、final diff 固定顺序 fail closed |
| AC-8 | PASS | 唯一 POST payload 精确；initial/final head drift 均在 POST 前拒绝；non-force/non-scheduled/delete branch |
| AC-9 | PASS | hard-gate failure matrix 返回稳定首个 code；所有负例 merge POST=0、fallback=0 |
| AC-10 | PASS | receipt 不触发 deploy/deployed；session 合同规定确定性终态/文档/cleanup/归档，不再增加确认点 |
| AC-11 | PASS | manual 到 `READY_FOR_REVIEW`；routine broker/GAP 失败停机，不切换 admin/manager/project-agent |
| AC-12 | PASS | commit parent 证据与本 fresh recovery run 重读治理合同 |
| AC-13 | PASS | 定向 205 tests、smoke 583 tests、bash -n、ShellCheck、change-documents 均真实通过；installed/live 如实 GAP/BLOCKED |

## 遗留风险与未完成项

- readiness 无法确认 live repository/protection；任何 routine merge 必须 fail closed，不能从 source PASS 推定 live PASS。
- installed skills/runtime、routine merger credential/account/collaborator、live allowlist/protection 与部署全部保持
  DRIFT、BLOCKED 或 `NOT RUN`，必须由合并后的 source 与独立授权分别处理。
- 最终 PR 尚未创建；本任务必须停在提交 PR 前的人工作业闸门。
