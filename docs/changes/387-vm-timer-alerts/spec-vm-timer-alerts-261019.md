---
issue: 387
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/387
change_type: reliability
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - shared-core
  - rollback
  - platform-governance
depends_on: []
status: approved
branch: change/387-vm-timer-alerts
created: 2026-10-19
updated: 2026-10-19
git_scope:
  - docs/changes/387-vm-timer-alerts/summary-vm-timer-alerts-261019.md
  - docs/changes/387-vm-timer-alerts/spec-vm-timer-alerts-261019.md
  - docs/changes/387-vm-timer-alerts/plan-vm-timer-alerts-261019.md
  - docs/changes/387-vm-timer-alerts/verification-vm-timer-alerts-261019.md
  - codex/runtime/aisoft_host_access/contract.py
  - codex/runtime/aisoft_host_access/broker.py
  - codex/config/host-access-broker.json
  - codex/tests/fixtures/manifests/host-access-broker.json
  - codex/runtime/tests/test_host_access.py
  - codex/tests/test-host-access-broker.sh
  - codex/tools/aisoft-platform-readiness.sh
  - codex/tests/test-platform-readiness.sh
  - codex/tools/aisoft-alert-poll.sh
  - codex/tools/install-alert-agent.sh
  - codex/launchd/com.aisoft.platform-alerts.plist.template
  - codex/tests/test-alert-agent.sh
  - codex/tests/smoke.sh
  - 05-通知与多人协作.md
  - 06-运维手册与踩坑集.md
---

# #387 spec：运维止血——停用 VM 上持续失败的 agent 定时器，补上失败观测与通知

`git_scope` 在合同确认时只列了映射文档；实现线程按实际改动补全（broker typed 操作、readiness、通知脚本与 launchd 模板、`05`/`06`、smoke 登记），在确认点 2 一并复核。除此之外合同正文与确认版一致，只按模板补了「接口、数据与兼容性影响」与「未决问题」两节。

## 目标与原因

gitea-ci VM 上两个 agent 定时器自 2026-08 起每 15 分钟失败一次，两个多月无人知道（复审 P0-3）。平台对自己的 VM 没有任何观测，失败通知自 7 月备案未实施（复审 P1-6，`05` §1/§5）。本批只做止血：停掉失败源，让同类失败今后能被发现并通知到人。不裁决 Development Loop、routine merge 的去留。

## 已核对的事实（2026-10-19，`origin/main` `7eca227`）

1. `agent-poll.timer`、`aisoft-agent@emaintenance.timer`（`coder` 用户、systemd --user）enabled，`OnUnitActiveSec=15min`；对应服务每次 `exit 20`。10-18 以来分别失败 262、131 次。
2. `aisoft-agent@emaintenance`：`BLOCKED_EXTERNAL: project profile identity or target validation failed`；broker `vm.profile.plan --project newemaint` 读回 `action: apply`（VM profile 与 manifest 不一致，manifest 为 provider `none`）。
3. `agent-poll.*` 是 #172 之前的旧单元，不在 `codex/systemd/`，`install-vm.sh` 既不装也不清。
4. 三个 VM profile 都是 `IMPLEMENT_PROVIDER=none`，Loop 无真实消费者。
5. broker 现有 `orbstack.vm.status` 只回 machine 状态；没有读取 systemd --user 单元健康的 typed 操作。`check-installed-drift` 不看 timer 健康。

## 负责人裁决（2026-10-19 确认合同：D1 选 a，D2 选 a）

- **D1 停用方式**（默认 a）
  - a. `systemctl --user disable --now` 两个 timer：单元文件保留，回滚 `systemctl --user enable --now <timer>`。去留留给「自动化裁决」批次。
  - b. `mask`：比 disable 更硬，回滚多一步 `unmask`。
  - c. 删除单元文件：不可简单回滚，不推荐在去留裁决前做。
- **D2 通知方式**（默认 a）
  - a. Mac 本地通知：一个只读轮询脚本，由用户级 launchd 每 15 分钟运行，经 broker 读平台仓开放 PR 的 CI 状态与 VM 定时器健康，失败时弹 macOS 通知；状态文件只在本机，不含凭据。launchd 由负责人运行安装脚本启用，可一条命令卸载。
  - b. Gitea 邮件：依赖 SMTP，当前只有 Mailpit 捕获，人收不到，不推荐作为本批唯一通知。
  - c. 本批只做观测，不做通知。

## Acceptance criteria

1. **停用（运维，D1）**：在 gitea-ci 以 `coder` 用户按 D1 停用两个 timer；前后各读回 `list-timers --all` 与 `is-enabled`，记录时间与回滚命令。停用后 30 分钟内两个服务无新的失败日志。由合同授权、实现线程执行（非 sudo 操作）；若需要 sudo 或执行失败则停下交给负责人。
2. **观测**：broker 新增只读 typed 操作（暂名 `orbstack.vm.units.read`），返回 VM 上 `coder` 用户 systemd --user 的 timer 与对应服务：名称、enabled、active、最近结果、最近失败时间与 24 小时失败次数；不返回日志正文与环境变量。按「broker typed 操作新增清单」同步全部登记点与测试。
3. `aisoft-platform-readiness.sh` 增加 VM 定时器一节：任一 enabled timer 的服务在 24 小时内失败即报 `GAP`；无 enabled timer 报 `PASS`。有夹具测试覆盖 PASS、GAP、broker 操作未安装三种情况。
4. **通知（D2）**：按 D2 默认交付轮询脚本、launchd plist 模板与安装/卸载脚本，夹具测试覆盖：CI 失败、timer 失败、无变化不重复通知、broker 不可用只报一次。`05` 更新状态行，§5 写清启用与卸载步骤。
5. `06` 记一条踩坑：VM profile 与 manifest 不一致导致定时器静默失败，以及发现方式。
6. 全量 smoke 通过；Codex 只读交叉审查通过；合并后由负责人重装 broker（两台），实现线程读回新操作可用、readiness 本节 PASS。

## 接口、数据与兼容性影响

- broker 新增一条只读 typed 操作 `orbstack.vm.units.read`（host-operator、无参数），operation_count 38 → 39；已有操作与参数不变。未重装的 broker 对它返回 `REQUEST_DENIED: requested operation is not allowlisted`。
- `aisoft-platform-readiness.sh` 多输出一行 `LIVE_VM_TIMERS`，退出码语义不变（任一层 DRIFT/GAP/BLOCKED 即 1）。
- 无数据迁移；通知状态只在负责人 Mac 的用户目录。

## 风险与回滚约束

- 停用：`systemctl --user enable --now <timer>` 恢复；不删文件、不改 profile。
- broker 新操作只读；新增 typed 操作需两台重装，未装时 readiness 报「操作未安装」而不是 PASS。
- 通知：`launchctl bootout` 加删除 plist 即卸载；脚本只读。

## 非目标

不修 newemaint VM profile 不一致（随自动化裁决处理）；不删除 Loop、routine merge 代码；不做 #370 runner 缓存；不改 CI workflow；不碰生产。

## 未决问题

- 无。
