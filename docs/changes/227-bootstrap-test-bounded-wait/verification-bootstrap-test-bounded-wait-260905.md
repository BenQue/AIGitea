---
issue: 227
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/227
change_type: bugfix
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - ci-change
depends_on: []
status: approved
branch: change/227-bootstrap-test-bounded-wait
created: 2026-09-05
updated: 2026-09-05
---

# Verification: 227 有界失败

## 基线与范围

- Commit SHA: `030f37a`（rebase 到 `00f7d53` 之后，在 `origin/main` 之上共三个 commit）
- 基线：`origin/main` = `00f7d53`（首次建分支时为 `071b6b0`，实现期间 main 前进四个 commit，已 rebase 并重跑 smoke）
- 环境：Mac 本机 bash 3.2.57；Linux 复跑用 OrbStack 上的 `ubuntu:24.04` 容器，bash 5.2.21，
  arm64，与 gitea-ci 同一 OrbStack 内核家族。
- 本记录负责证明：AC-1 到 AC-6 全部六条。

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| 内核栈对照实验：容器内 `mkfifo` 后无对端 `open()`，读 `/proc/PID/stack` | PASS | `wait_for_partner+0x84 → fifo_open+0x1b8 → vfs_open → path_openat → __arm64_sys_openat`，与事故栈逐帧一致 |
| 同一实验的对照组：`while read ... done < <(sleep 600)` | PASS | `anon_pipe_read+0x26c → __arm64_sys_read`；是 `read()` 不是 `open()`，且 `/dev/fd → /proc/self/fd` |
| 全仓 `grep -rn mkfifo . --exclude-dir=.git`（改动前） | PASS | 零命中，仓库不创建任何 FIFO |
| `strace -f -e trace=mknod,mknodat,openat` 跑改动前的测试 | PASS | `mknod`/`mknodat` 零次；23260 条 `openat` 中 `/dev/*` 只有 `/dev/null`、`/dev/urandom`、`/dev/fd/63` 与非阻塞的 `/dev/tty`（`O_RDWR\|O_NONBLOCK`，返回 ENXIO） |
| bash 5.2 源码 `subst.c` 的命名管道回退条件 | PASS | `mkfifo`/`sh-np` 分支位于 `#if !defined (HAVE_DEV_FD)`，编译期决定；容器内 `/dev/fd -> /proc/self/fd` 存在，故不走该分支 |
| runner 执行器判定 | PASS | `01-基础设施-VM-Gitea-Runner.md` §4：act_runner 注册标签 `ubuntu-latest:host`；act 的 `pkg/container/host_environment.go` 用 PTY（`setupPty`）而非 FIFO，源码全仓 `Mkfifo` 零命中 |
| 改动前复现无界等待：抽出 mock `curl`，用第三个用户名调用且 stdin 不 EOF | PASS | `timeout 8` 返回 `rc=124`，仍在阻塞 |
| 改动后同一调用（bash 5.2 容器） | PASS | `rc=2`，stderr 命中 `MOCK_CURL_UNEXPECTED_URL` 一次，立即返回 |
| 改动后同一调用（本机 bash 3.2） | PASS | `rc=2`，`MOCK_CURL_UNEXPECTED_URL` 一次 |
| 改动后 `/api/v1/user` 但不给 stdin 对端（bash 5.2 容器） | PASS | `MOCK_CURL_STDIN_TIMEOUT=2`，`rc=3`，命中 `MOCK_CURL_MISSING_CONFIG_STDIN` |
| 改动后同一场景（本机 bash 3.2） | PASS | `rc=3`，命中 `MOCK_CURL_MISSING_CONFIG_STDIN` |
| 看门狗注入挂起（本机 bash 3.2） | PASS | 子进程阻塞在 `exec 9<...selftest-hang.fifo` 的 `open()`；5 秒整被打断，stderr 为 `AISOFT_TEST_DEADLINE_EXCEEDED: ... exceeded 5s; killing pid ... and its descendants` 与 `Interrupted system call`，`elapsed=5s` |
| **看门狗自杀缺陷（第一版实现，Linux 上抓到）** | **FAIL，已修** | 第一版 `kill_descendants "$target"` 会先杀掉看门狗子 shell 自己（它就是 target 的子进程），TERM 与 KILL 都没送出，注入的挂起在容器里活了 6 分钟以上：`/proc/2049/wchan = wait_for_partner`，且 `ps` 里 PPID=2049 的进程为空。macOS 当时看着是绿的，是因为自杀产生的 SIGCHLD 恰好把 `open()` 打断了，属偶然 |
| 修复后同一注入（Linux bash 5.2 容器） | PASS | `AISOFT_TEST_DEADLINE_EXCEEDED ... exceeded 5s`，`child rc=143`（TERM trap 转成的普通退出），`elapsed=5s`，`leftover temp dirs: 0` |
| 看门狗守卫的反向证明：把 `AISOFT_TEST_DEADLINE_EXCEEDED` 改成别的串再跑整脚本 | PASS | `rc=1`（断言变红）；改回后 `rc=0`。守卫是活的，不是恒真 |
| `bash -n codex/tests/test-bootstrap-gitea-service-account.sh` | PASS | 无输出 |
| `shellcheck codex/tests/test-bootstrap-gitea-service-account.sh` | PASS | 无输出 |
| `bash codex/tests/test-bootstrap-gitea-service-account.sh`（本机 bash 3.2） | PASS | `bootstrap Gitea service account tests passed` |
| Linux bash 5.2 容器内连续 20 次 | PASS | `RESULT: 20 runs on bash 5.2, fail=0`，`leftover temp dirs: 0` |
| `bash codex/tests/smoke.sh`（本机，看门狗修复并 rebase 到 `00f7d53` 之后） | PASS | `Ran 671 tests in 35.449s` `OK`；`Codex platform static smoke checks passed.`；`SMOKE_RC=0` |
| `bash codex/tests/smoke.sh`（rebase 之前的一次） | FAIL，非本次 diff 所致 | `ERROR: architecture/install: source checkout is 4 commit(s) behind origin/main`，是 staleness 闸门。broker `git.fetch.main` + `git rebase origin/main` 后重跑即绿 |
| `PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli check-change-documents --repo .` | PASS | `PASS: change-documents`、`PASS: change-pr-url`、`result: changes=113 pass=2 gap=0` |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 复现或静态论证 | PASS | 两条都做到了。**无界等待已复现**：改动前 mock `curl` 在第三个用户名下 `rc=124` 仍阻塞。**事故栈已归因到脚本之外**：内核只在 `!is_pipe` 时走 `wait_for_partner`，容器对照实验显示真实 FIFO 的 `open()` 给出与事故逐帧一致的栈，而进程替换给出 `anon_pipe_read`；再加仓库零 `mkfifo`、`strace` 零 FIFO 打开、bash 命名管道回退编译期关闭、act host executor 用 PTY，四条独立证据一致排除本脚本 |
| AC-2 未知 URL 不读 stdin 且 fail closed | PASS | 精确 endpoint 分派；未知 URL 在任何 `read` 之前 `rc=2` + `MOCK_CURL_UNEXPECTED_URL`，bash 3.2 与 5.2 一致 |
| AC-3 对端不出现时有界失败 | PASS | `read -t` 上界；`rc=3` + `MOCK_CURL_MISSING_CONFIG_STDIN`，bash 3.2 与 5.2 一致 |
| AC-4 整脚本有界且自检证明看门狗触发 | PASS | 注入的挂起是真实的无对端 FIFO `open()`，5 秒被打断并留下 `AISOFT_TEST_DEADLINE_EXCEEDED`；反向证明确认断言会变红；正常路径下看门狗不触发 |
| AC-5 稳定性 | PASS | Linux bash 5.2 容器连续 20 次全绿且零残留临时目录；本机 bash 3.2 单次 PASS；`bash codex/tests/smoke.sh` PASS |
| AC-6 其余等待点盘点 | PASS | 见下表 |

## 等待点盘点

| 位置 | 构造 | 改动前有界性 | 现状 |
|---|---|---|---|
| mock `curl` 未知 URL | glob fall-through 落进 `read -r auth` | **无界，已复现** | 精确匹配 + fail closed，不再读 stdin |
| mock `curl` `/user` 与 `/notifications` | `read -r auth` 读 stdin | 无界（对端不出现时） | `read -t`，超时给可搜索标记后退出 |
| 第 431 行与第 549 行 `done < <(find ...)` | bash 进程替换 | 有界 | 不改。`find` 遍历本地临时目录必然终止；且实验证明该构造阻塞时是 `anon_pipe_read`，与事故栈不符 |
| 各处 `$(...)` 命令替换 | 匿名管道 | 有界 | 不改。被调方全部本地、无网络、必然退出；看门狗兜底 |
| mock `git` 的 `exec /usr/bin/git "$@"` | 真实 git 继承 stdin | 本测试路径不触发 | 不改。被测路径只用 `show` 与 `merge-base --is-ancestor`，两者都被 mock 拦下。真实 git 若被触发并提示凭据会无界等待，属工具侧 |
| 工具侧 `aisoft_gitea_governance.cli._git_output` | `subprocess.run` 未设 `timeout` | 本测试中被 mock 覆盖 | 不改，记为遗留项，见下节 |
| 整脚本 | 无任何上界 | 无界 | 看门狗，默认 600 秒，超时打 `AISOFT_TEST_DEADLINE_EXCEEDED` 并杀后代与自身 |

## 遗留风险与未完成项

- **事故那一刻 FIFO 的真实创建者仍未定位。** 已排除本脚本与 act 的 host executor，
  但没有拿到 gitea-ci 上的现场证据。broker 没有任何 shell 类 typed 操作，只有
  `gitea.actions.run.read`（按 sha）与 `gitea.actions.job.logs.read`（按 job id），
  而事故 job 恰好零日志，因此这条路取不到证据。**NOT RUN：VM 侧取证。** 需要另行授权
  的取证途径才能继续；本次不猜测、不据此改动。
- `codex/runtime/aisoft_gitea_governance/cli.py` 的 `_git_output` 调用 `subprocess.run`
  时没有 `timeout`，也继承 stdin。本次范围只改测试脚本，未改动它；建议另开 Issue。
- runner 级 per-job timeout 与停滞检测未做，Issue 正文已标注为另一条 Issue。
- `06-运维手册与踩坑集.md` 的「先取消 run 再杀孤儿进程」处置顺序未写，属 Issue #228。
- 看门狗在触发时先杀后代再杀自身，用 `ps -Ao pid=,ppid=` 递归枚举。若宿主没有 `ps`，
  枚举会静默跳过，只剩对自身的 TERM/KILL；这是降级而不是失败。
