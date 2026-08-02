---
issue: 21
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/21
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - security
  - shared-core
  - ci-change
  - deployment
  - migration
  - destructive-operation
  - rollback
  - platform-governance
depends_on: []
status: approved
branch: change/21
pr_url:
created: 2026-08-02
updated: 2026-08-02
---

# Implementation plan

## 任务分解

1. 重新读取 `origin/main`、Issue #21、三个 VM identity 和 `gitea-ci` 实时进程/端口/
   cgroup/systemd/PM2/Nginx/timer/workflow/数据库/制品引用，建立脱敏 baseline；事实漂移时先
   修订 verification，不执行 mutation。
2. 在 `codex/config/` 与 `templates/hosts/` 建立 host profile schema、capability catalog
   和无 Secret 示例，定义 `scm-ci` 与 AppServer roles 的唯一语义。
3. 实现 `codex/tools/verify-host-role.sh`（或等价单一入口）及 installer/调用约束，在任何
   deploy/start/database mutation 前验证受保护 profile、机器 identity 与 action allowlist。
4. 添加 shell mock 与 integration fixtures，覆盖 allow/deny、身份不匹配、权限错误、未知
   action、重复执行和脱敏；把定向测试接入 `codex/tests/smoke.sh`。
5. 更新 README、01/02/06/07/09/12 和 onboarding 资料，区分历史同机证据、当前
   `scm-ci` 角色、AppServer 和 #22 Docker release 合同。
6. 在 `rsdesign-new` 正式仓库建立/复用独立 Issue 与 PR，先把批准 SHA 部署到 AppServer
   并完成数据/health/rollback 验收；经人工 Gate 后才停旧 3100/8091，并读回两端状态。
7. 在 SFMDigitalBoard 正式仓库建立/复用独立 Issue 与 PR，修复 smoke cleanup/finalizer；
   重新确认 PID/cgroup 后经 Gate 终止 3212，执行成功/失败/取消三类残留检查。
8. 为 MyApp Notes 保存 inventory 与数据库/目录恢复证据，经独立 Gate 删除其 vhost、
   runtime、DB 和专属制品；随后按引用 predicate 收口 Redis/Nginx。
9. 实现并 dry-run `/opt/artifacts` retention 清单；只对无引用、超出策略且 checksum 可核对
   的制品申请执行 Gate，保留审计日志。
10. 对 `prod-sim` 执行两轮只读 inventory，核对 name 与 ID、无唯一数据/依赖，并记录
    Ubuntu release、architecture、资源和重建来源；条件不满足则 `BLOCKED`。
11. 在用户已给出的单目标授权内执行 `orb delete --force prod-sim`，随后用 `orb list`、
    `orb info prod-sim`、DNS/连接与 `gitea-ci`/AppServer health 完成删除和无影响验证。
12. 填写 `03-verification.md`；提交、推送 `change/21` 并创建 `Closes #21` 的最终 PR。
    停在人工合并闸门；未获授权的 live Gate 保持 `NOT RUN/BLOCKED`，不得为了关闭 Issue
    代执行。

## 涉及文件

- `docs/changes/21/{00-summary,01-spec,02-plan,03-verification}.md`
- `codex/config/host-role.schema.json`
- `codex/config/host-capabilities.json`
- `templates/hosts/host-profile.example.json`
- `codex/tools/verify-host-role.sh`
- `codex/tests/test-host-role-guard.sh`
- `codex/tests/fixtures/host-role/*`
- `codex/tests/smoke.sh`
- `README.md`
- `01-基础设施-VM-Gitea-Runner.md`
- `02-CI与自动部署流水线.md`
- `06-运维手册与踩坑集.md`
- `07-内网与生产平移路线.md`
- `09-v3平台简化与Loop-Engineering文档改造规划.md`
- `12-Linux-GitHub-Gitea-双服务器自动部署方案.md`
- 应用仓库文件由各自 Issue/PR 确认，不能在本计划中根据旧路径猜测。

## 数据库迁移

平台代码无 schema migration。Live 收口涉及 SQLite 迁移/备份、MyApp PostgreSQL
`app_test` 删除和 Redis 判定：每个对象单独快照、恢复验证与授权；不得批量处理，也不得
读取业务数据内容。`prod-sim` VM 删除不以数据库 restore 冒充整机 rollback。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | schema 正反 fixtures；`jq` 校验 roles/capabilities 唯一且 unknown fail closed |
| AC-2 | `bash codex/tests/test-host-role-guard.sh` 的 allow/deny mutation-order 断言 |
| AC-3 | profile mode/owner 与 hostname/ID mismatch fixtures；Secret marker 扫描 |
| AC-4 | `rg` + 文档 review，证明 current/legacy/retired 状态一致 |
| AC-5 | AppServer 与旧 host 的 exact SHA、PM2、SQLite、HTTP health、rollback 证据 |
| AC-6 | SFM workflow CI + success/failure/cancel residual process/port/DB/cwd checks |
| AC-7 | MyApp pre/post inventory、backup restore proof 与共享引用检查 |
| AC-8 | `systemctl`/health/consumer checks：Gitea、runner、Verdaccio、Mailpit、HSDB CI |
| AC-9 | artifact/Redis/Nginx dry-run 与 before/after diff；共享引用故意失败 fixture |
| AC-10 | 两次 `orb info prod-sim`/`orb list` 与 repository reference scan |
| AC-11 | `orb delete --force prod-sim` 后 list/info 断言及其它主机 health |
| AC-12 | 定向 tests、`bash -n`、ShellCheck、`bash codex/tests/smoke.sh` |
| AC-13 | `03-verification.md` 状态审查与 exact SHA/command/evidence 映射 |
| AC-14 | destructive action ledger 与逐 Gate 授权审查；PR/merge/deploy 状态读回 |

## 部署与回滚

Host-role runtime 安装只复制版本化文件和示例，不创建 Secret、不 enable/start 服务。
Guard 在同一 profile 上重复执行两次应得到相同结果，并故意请求一次禁止 action 证明零
mutation。应用迁移、服务清理和 `prod-sim` 删除分别执行，禁止一个脚本串联所有 destructive
actions。平台回滚走 revert PR；应用回滚走已验证 release/data backup；VM 删除只能重建。
