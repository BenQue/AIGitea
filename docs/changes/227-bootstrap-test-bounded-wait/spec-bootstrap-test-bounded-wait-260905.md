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

# Spec: test-bootstrap-gitea-service-account.sh 有界失败

## 目标与原因

让 `codex/tests/test-bootstrap-gitea-service-account.sh` 在任何失败路径下都在有界时间内
退出并留下可搜索的错误标记，而不是无限期阻塞。该脚本是 required 检查 `CI / verify` 的
一部分，gitea-ci 是 `maxParallel=1` 的实例级 runner，因此它一挂就是全平台 CI 停摆。

## 取证结论（决定实现方向）

三条证据已在 Linux 容器内取得，直接决定本 spec 的范围：

1. **`wait_for_partner` 只可能来自真实 FIFO 的 `open()`。** 在 OrbStack Linux 上对照实验：
   `mkfifo` 后无对端 `open()` 得到
   `wait_for_partner → fifo_open → vfs_open → path_openat → __arm64_sys_openat`，
   与事故栈逐帧一致；而 bash 进程替换得到 `anon_pipe_read`（一次 `read()`）。
   内核把 `wait_for_partner` 挡在 `!is_pipe` 之后，匿名管道永远到不了它。
2. **本脚本不可能产生该栈。** 全仓无 `mkfifo`；`strace` 全量 `openat` 显示脚本从不打开
   `/dev/fd`、`/proc/*/fd` 或任何 FIFO 路径；bash 的命名管道回退路径由编译期
   `#if !defined (HAVE_DEV_FD)` 关闭，Linux 发行版 bash 不走它；act host executor
   给步骤分配的是 PTY 而非 FIFO。
3. **脚本确有一处可复现的无界等待，但它是 `read` 不是 `open()`。** mock `curl` 用 glob
   分派，`*"/api/v1/user"*` 会吞掉 `/api/v1/users/<任何第三个用户名>`，落到
   `read -r auth` 读继承来的 stdin。在 stdin 不会 EOF 的条件下实测阻塞，8 秒超时返回 124。

因此：事故栈的 FIFO 来源在本脚本之外（runner 或宿主侧），本次不追加对它的猜测性改动；
本次修的是脚本自身**确实存在**的无界等待，并让脚本对任何挂起都有界失败。

## Acceptance criteria

- [ ] AC-1 复现记录成立：给出上述三条证据的真实命令与输出，包含对 mock `curl`
      fall-through 的实测阻塞（返回码 124），以及无法把事故栈归因到本脚本的论证。
- [ ] AC-2 mock `curl` 不再存在 glob fall-through：按精确 endpoint 分派，未知 URL 立即以
      非零码退出并打印含 `MOCK_CURL_UNEXPECTED_URL` 的可搜索标记，不读 stdin。
- [ ] AC-3 需要 Authorization 头的分支在对端不出现时有界失败：读取带上界，超时后打印含
      `MOCK_CURL_MISSING_CONFIG_STDIN` 的可搜索标记并以非零码退出。
- [ ] AC-4 整脚本有界：存在看门狗，超过上界后打印含
      `AISOFT_TEST_DEADLINE_EXCEEDED` 的可搜索标记，终止自身与后代进程并以非零码退出；
      并有自检用例证明它在注入挂起时触发、在正常路径下不触发。
- [ ] AC-5 稳定性：修改后的脚本在 Linux bash 5 容器内连续运行不少于 20 次全部通过，
      在本机 bash 3.2 下通过，`bash codex/tests/smoke.sh` 通过。
- [ ] AC-6 盘点：spec 或 verification 中列出该脚本其余等待点及其有界性判定。

## 接口、数据与兼容性影响

- 无外部接口、数据结构或制品变更。被测工具
  `codex/tools/bootstrap-gitea-service-account.sh` 不改动，其所有既有断言保持不变。
- 新增两个可选环境变量，仅供测试自身与自检使用，默认值保证 CI 行为不变。

## 风险与回滚约束

- 主风险是 required CI 硬门回归。回滚方式：`git revert` 该单一 commit，脚本回到当前形态；
  改动仅限一个测试文件，无迁移、无状态、无制品。
- 看门狗误触发会让 CI 假红。以自检用例与容器内 20 次重跑作为闸门。

## 非目标

- 不给 runner 或 job 加 per-job timeout 与停滞检测（Issue 正文已标注为另一条 Issue）。
- 不修改 `.gitea/workflows/ci.yml`、`codex/tests/smoke.sh` 或被测工具。
- 不在 `06-运维手册与踩坑集.md` 记录「先取消 run 再杀孤儿进程」的处置顺序（属 Issue 228）。
- 不用加大超时代替修根因；看门狗是兜底，AC-2 与 AC-3 才是根因修复。

## 未决问题

- 无。
