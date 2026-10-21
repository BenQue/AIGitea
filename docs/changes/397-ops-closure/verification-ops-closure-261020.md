---
issue: 397
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/397
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - shared-core
  - schema-change
  - cross-module
  - rollback
  - agent-governance
  - platform-governance
depends_on:
  - 391
status: pending
branch: change/397-ops-closure
created: 2026-10-20
updated: 2026-10-20
---

# #397 verification：运维闭环第二步（R16）

## 基线与范围

- 基线：`origin/main` = `08be6f44a67ddb755d840611ae249128b574b8b3`（R10a 合并）
- 环境：Mac（darwin，平台主检出与 worktree `/private/tmp/issue-397-ops-closure`）；VM `gitea-ci`（经 `/usr/local/bin/orb -m gitea-ci`，默认用户）
- 本记录负责证明 AC1–AC12；合并后的两台重装与读回（AC12）在收尾第 5 步补记。

## 改动前观测（合并后无法重放）

| Command / check | Result | Evidence |
|---|---|---|
| Mac `bash codex/tools/check-installed-drift.sh` | GAP | `install-skills` PASS（8/8）、`install-host-role` GAP（唯一一条 `symlink-parent`：`/etc/aisoft/host-profile.example.json`，capabilities 20/20）、`install-host-access-broker` PASS（34/34）、`architecture/install` GAP（全部 missing）、`sync/install` GAP（missing 与 `/etc` 的 symlink-parent）、`skill-for-claude/install` PASS |
| VM `orb -m gitea-ci bash /mnt/mac/.../check-installed-drift.sh` | GAP | `install-host-role` PASS、`install-host-access-broker` PASS（34/34）；`install-skills` 0/8、`skill-for-claude/install` 0/2（`/home/benque` 无技能）、`architecture/install`、`sync/install` 全部 missing |
| `git worktree list`（主检出） | 8 prunable | #308×2、#333、#342、#343、#344、#349、#358；另有 3 个 `.claude/worktrees/*` 分离头（最新 10-08）与在用的 #395、#396 |
| `git branch --list 'claude/*'` | 11 | 全部是 `origin/main` 祖先，最新提交 10-08 |
| `git branch -r` 中 `origin/change/*` | 61（59 已并入） | 本地 remote-tracking 引用，`git.fetch.main` 不 prune，可能陈旧 |
| `aigitea-cleanup-merged.sh` 默认 remote | `gitea` | 平台仓 remote 名为 `origin`，默认调用报 `missing gitea/main` |

## 执行结果（2026-10-21，worktree 本地）

| Command / check | Result | Evidence |
|---|---|---|
| `bash codex/tests/test-installed-drift.sh` | PASS | 39 tests OK；新增：主机 SKIP 不读目标、棘轮 regressed/held/tighten、基线与 applies_to 不一致报错、非 macOS 缺 `--host` 报 `host-required`、`/etc` 别名只作用于三个系统链接 |
| Mac：worktree 内 `check-installed-drift.sh`（默认 `--host mac`） | 预期 GAP | `install-host-role` 由 GAP 变 PASS（`/etc` 别名生效）；architecture、sync 报 `SKIPPED SKIP`；剩余 GAP 只有本分支改动的 `issue-session-flow` 字节差与 rotation source 绑定（安装来自 main），合并重装后复核 |
| VM：`orb -m gitea-ci bash /mnt/mac/private/tmp/issue-397-ops-closure/codex/tools/check-installed-drift.sh --host vm` | 预期 GAP | skills、architecture、sync 报 SKIP；host-role PASS；broker 只剩 rotation source 绑定差（同上） |
| `bash codex/tests/test-alert-agent.sh` | PASS | 反向证明：把 `aisoft-alert-poll.sh` 换回 `HEAD~` 版本后同一测试失败，换回新版本通过 |
| `bash codex/tests/test-cleanup-merged.sh` | PASS | 远端仓搬走后仍可运行（不联网）；detached 已合并 worktree 可删；`.git` 丢失的目录作 orphan prune；github 远端排除；两个候选远端时拒绝 |
| `bash codex/tests/test-platform-readiness.sh` | PASS | `PAT_AGE` 回执 200 天 `OVER`、标记 10 天、无元数据 `unknown`；夹具 token 为 000 权限，未被读取 |
| `bash codex/tests/test-deploy-notify.sh` | PASS | 失败、回滚、标题回退、五种前置缺失均退 0；token 只经 curl stdin |
| `PYTHONPATH=codex/runtime python3 -m unittest codex.runtime.tests.test_session_contract` | PASS | 12 tests |
| `usage-bundle.sh --release 1.5.0 --today 2026-10-21` 与 `--verify` | PASS | 最终 `VERIFIED 1.5.0 sha256:ab891216acbd…` |
| `bash codex/tests/smoke.sh` | PASS | exit 0（第二次红在 #380 夹具守卫：readiness 测试读了真实 manifest，已改为由输出推导计数后重跑全绿） |
| ShellCheck（改动的 7 个 shell 文件） | PASS | 无告警 |
| Codex 交叉审查修复后 `bash codex/tests/smoke.sh`（head `80b1877`） | PASS | exit 0；期间撤回未发布的 1.5.0 记录并重发同号（`sha256:ab891216…`），因审查修复改动了 `deploy-notify.sh` |

## 本机清理（AC4，会话执行，2026-10-21）

`codex/tools/aigitea-cleanup-merged.sh /Users/benque/MyDocs/AISoftPlatform --branches --apply`（新版本，先经 broker `git.fetch.main`）：
prune 8 个残留 worktree 元数据，删除 3 个 `.claude/worktrees/*`（已合并、干净），`git branch -d` 删除 `change/308-installed-drift-check`
与 11 个 `claude/*`。读回 `git worktree list` 只剩主检出与 #370、#395、#396、#397 四个在用 worktree。

未删（需要负责人决定）：`change/333`、`342`、`343`、`344`、`347`、`349`、`358` 七个本地分支对应 Issue 均已关闭但未并入
`main`，只能 `git branch -D`；`/private/tmp/issue-333-governance`、`/private/tmp/issue-342-hsdb-login-recovery`、
`/private/tmp/issue-358-hsdb-stack-profile` 三个目录只剩零散文件，需要 `rm -rf`。

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC1 | 源码与夹具 PASS；两台真实 PASS 待合并重装后读回 | 上表 |
| AC2 | PASS | `skills/issue-session-flow/SKILL.md` 收尾第 5 步与「本机清扫（每周）」 |
| AC3 | PASS | alert 测试与反向证明 |
| AC4 | PASS（含上述待决定项） | 本机清理节 |
| AC5 | PASS | readiness 测试；`06` §4 |
| AC6 | PASS | deploy-notify 测试；`05` §1.1 |
| AC7 | 源码 PASS；`main` 上 push 运行待合并后读回 | `.gitea/workflows/ci.yml` |
| AC8 | PASS | 负责人选「等 R13」；R13（PR 398）合并后撤回本地 1.5.0、用 merge commit `9721ca7` 集成 main，再删除 routine manifest 字段、policy、K1 routine 种类与 `aisoft-loop` 死路径（`3db58fc`、`e12901e`、`1db67ea`）；两个 `validate` 对真实与夹具 manifest PASS（34 操作、7 项目/仓库）；runtime 单测 671 个通过；Go helper 源码不变，`helper_test.go` 把 `routine-merge-agent` 从必须绑定改为必须 `TARGET_UNMANAGED`，VM 上 `test-gitea-pat-helper-linux.sh` PASS（build/model/race/process）；剩余 `routine` 命中均为历史说明、退役文件清单、拒绝旧字段的负向测试与 vendor 英文词 |
| AC9 | PASS | 治理提交 `8a67c51` 单独提交后重读 |
| AC10 | PASS | 集成 R13 后发 1.6.0；R10b（PR 399）合并占用 1.6.0 后撤回本地记录、用 merge commit 再次集成 main 并改发 1.7.0（`sha256:b0e24512149f…`）；`10382ab` 上 smoke 全绿；本机 `golang:1.26.3` 容器内 `go vet`、`go test`、`go test -race` ok；VM 上 `test-gitea-pat-helper-linux.sh` 在 `58d8048` PASS，`10382ab` 重跑因下载 Go 工具链 TLS 失败 NOT RUN；`--isolated-container` 进程测试 NOT RUN（CI 不跑） |
| AC11 | PASS | Codex 只读审查 6 轮：第 4 轮对 `80b1877` PASS；集成 R13 与 AC8 后第 5 轮 FAIL（PAT helper 隔离进程测试夹具仍用 routine 种类），修复后第 6 轮对 `10382ab` PASS（记录：项目库 `codex-review-397.md`）；`apply-classification-labels.sh --verify 397` 读回 `projected` |
| AC12 | NOT RUN | 合并后 |
