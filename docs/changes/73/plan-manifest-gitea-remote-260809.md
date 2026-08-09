---
issue: 73
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/73
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - authentication
  - authorization
  - security
  - external-contract
  - shared-core
  - platform-governance
depends_on: []
status: awaiting-merge
branch: change/73
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/74
created: 2026-08-09
updated: 2026-08-09
---

# Manifest-fixed Gitea remote implementation plan

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | triage、semantic contract、live baseline 与 approval gate | - | complete |
| T02 | manifest remote compatibility + all Git operation tracer bullet | T01 | complete |
| T03 | fail-closed onboarding check/bind + installer/controller/helper/documentation tracer bullet | T02 | complete |
| T04 | complete local verification + exact broker delivery/PR/CI handoff | T02, T03 | complete (pre-merge) |

## T01 — Contract and approval gate

- 读取 Issue/评论、root rules、Matt adapter、authoritative platform docs 与 #61/#67/#70 contracts。
- 通过 installed broker fresh fetch/read Issue/PR/open PR/protection/status/access audit；逐字节核对 installed
  source，读取 NewEmaint dual remote、repo-local binding 和不接触 credential contents 的 aggregate boundary。
- 写四份映射 semantic documents，运行 resolver/contract validation；投影 exactly one triage category/state
  和 platform type/complexity/lifecycle，读回 `approved` 前不进入 T02。

## T02 — Manifest remote and Git operations

- 先增加 strict manifest/schema/public-seam failing tests：optional safe remote name、origin default、NewEmaint
  gitea、unsafe/extra/caller argument denial。
- 扩展 project contract 与 source manifest；只在 NewEmaint row 声明 `gitea`。
- 让 remote validation、fetch main/change、push change 与 binding 使用 resolved remote；同时校验唯一 exact
  fetch/push URL，保持 same common-dir/branch/HEAD/ancestry/clean/no-merge/non-force gates。
- 用 real temp canonical/worktree 覆盖 origin compatibility、dual remote、GitHub origin unchanged、missing/wrong/
  multiple/cross-project remote、main/other N/merge/dirty/non-fast-forward negatives。

## T03 — Project onboarding closure

- 新增无参数 read-only `host.onboarding.check`，复用 access audit 后核对 canonical checkout、remote fetch/push
  URL 和 repo-local fixed helper/username/useHttpPath；错误脱敏并在 mutation 前失败。
- 扩展 typed runner 与 tests；证明无 direct curl/security/generic Git fallback，无 merge/permission/protection/
  credential provision surface。
- 覆盖 `mac.git.bind` first-run/second-run no-op、wrong remote early fail、helper protocol 与 manifest-derived URL。
- 扩展 fake-root installer twice/no-op、installed-byte manifest 与 security scan；证明不创建 credential/remote/
  profile/service/timer/deployment state。
- 更新 README、`06`、private-access/onboarding runbook 与 platform-ops guidance，写清 access audit → separately
  approved credential provision if needed → bind → onboarding check → fresh-session canary 顺序。

## T04 — Verification and delivery

- 运行 focused Python/shell/runtime/helper/controller tests，随后 full platform smoke；修复所有范围内失败。
- 对修改 shell 运行 `bash -n` 与 ShellCheck（若可用）；运行 strict JSON、document resolver、Secret/cache scan、
  `git diff --check`，确认无 NewEmaint source 改动。
- 自审 branch/ancestry/commit subject/touch points/clean tree；创建原子本地 commit。
- 用 installed broker fresh fetch、exact `git.push.change`、唯一 `gitea.pull.create/read/update`；读回 Issue、
  PR head/base/merged、protection 与 final-head status。
- 更新 verification/PR evidence 时只追加同一 branch/PR；remote CI 按 live protection分类，最终停在人工 merge。

## Expected touch points

- `docs/changes/73/` semantic documents。
- `codex/config/host-access-broker.json`。
- `codex/runtime/aisoft_host_access/{contract,broker,runner}.py`。
- `codex/runtime/tests/test_host_access.py`、`codex/tests/test-host-access-broker.sh` 与相关 fixtures。
- `README.md`、`06-运维手册与踩坑集.md`、private Gitea/onboarding/platform-ops guidance。

以上是 scope guidance，不授权修改 root `AGENTS.md`、NewEmaint source、credential contents、Gitea
account/PAT/ACL/permission/protection、Docker/VM/profile/service/database/deployment 或 production。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1, AC-2 | strict contract tests + real temp dual-remote CLI/Git seam；unsafe/extra/cross-project negatives |
| AC-3 | real temp linked-worktree fetch/change/push matrix；main/other/dirty/merge/non-FF denial |
| AC-4 | repo-local config snapshot、first bind/second no-op、remote config byte-identical、Secret-free config scan |
| AC-5 | `host.onboarding.check` public seam：access/protection/CI/checkout/remote/helper drift matrix |
| AC-6 | operation catalog/schema scans、early-fail resolver spies、forbidden string/argv/output checks |
| AC-7 | focused unit/shell/runner/helper、fake installer twice、full smoke、bash-n/ShellCheck/JSON/Secret/diff |
| AC-8 | local/remote branch and PR de-dup、broker push/create/read、live protection/status readback |
| AC-9 | platform PR 中 `NOT RUN`；人工 merge 后独立 NewEmaint adoption Issue only |

## Deployment and rollback

本 Change 不部署。Candidate 回滚为 revert。未来 post-merge 安装只能从 exact protected-main bytes 执行，
保留 `.previous` 并要求第二次 no-op。Repo binding 回滚只恢复 pre-binding local Git config；不修改 remote 或
history。Credential provision、NewEmaint adoption、DockerLab 与任何 deployment 都需要独立 Issue/审批。
