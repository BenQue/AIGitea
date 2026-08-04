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
updated: 2026-08-04
---

# Spec

## 目标与原因

把 `gitea-ci` 收敛成可审计的 `scm-ci` 主机：允许 Gitea、Runner、受控工具链、缓存、
通知和不可变制品，禁止任何业务 Web/API/worker、业务数据库和长驻 smoke 进程。平台通过
版本化 host-role 合同和 deterministic guard 阻止回归，并按独立回滚边界迁移或清理现存
业务运行时。

同时退役只用于早期测试的 OrbStack `prod-sim`。删除只覆盖 name `prod-sim`、ID
`01KX3FFXSJVYPDHZVY4MZB7CQZ`；删除前确认无唯一数据和实时依赖，删除后证明其它正式主机
与平台服务不受影响。

## Acceptance criteria

- [ ] **AC-1** 提供 versioned host profile schema、capability catalog 和示例，至少定义
  `scm-ci`、`appserver-test`、`appserver-prod`；未知 role/capability、身份不匹配、宽松文件
  权限或缺字段必须 fail closed。
- [ ] **AC-2** 提供单一 host-role guard。`scm-ci` 允许 source checkout、build、test、
  package、registry/artifact publish 和批准的 CI 辅助服务；application deploy/start、业务
  database create/use 和长驻 smoke 必须在任何 mutation 前被拒绝。
- [ ] **AC-3** guard 绑定 root/operator-owned profile 与实际 hostname/machine identity，不以
  调用方可任意覆盖的环境变量作为唯一信任源；输出不包含 token、`.env` 或业务数据。
- [ ] **AC-4** README、01/02/06/07/09/12 分册明确 `gitea-ci` 与 AppServer 分离，历史同机
  PM2/SQLite 流程仅作为 as-built/legacy 证据，不再是新项目默认目标。
- [ ] **AC-5** `rsdesign-new` 必须先在 AppServer 部署并验证精确 Gitea `main` SHA、唯一
  runtime、SQLite 数据、HTTP/SHA health 和回滚，再停止 `gitea-ci:3100/8091`；应用仓库
  变更走其自己的 Issue/PR，本平台 Change 不直接改其 protected `main`。
- [ ] **AC-6** `sfm-board:3212` 的进程/cgroup 身份被重新确认后才可终止；所属应用仓库补
  cleanup/trap 和成功、失败、取消三类无残留测试，验证端口、进程、临时 DB 与已删除 cwd
  均不再残留。
- [ ] **AC-7** MyApp Notes 在保存可恢复 inventory/backup 后，按独立 Gate 清除 `8090`
  vhost、`/opt/app-test`、`app_test` 数据库和仅属于它的旧制品；任何共享引用都会阻断删除。
- [ ] **AC-8** Gitea、`gitea` DB、`act_runner`、Verdaccio、Mailpit、`/opt/node22`、
  `/opt/hsdb-ci`、`hsdb_ci` 和仍被引用的制品在收口前后均通过真实健康/消费检查。
- [ ] **AC-9** `/opt/artifacts` 使用项目 allowlist、SHA/checksum、引用保护、保留数量/期限、
  dry-run 和审计日志；不得按文件名或年龄直接批量删除。Redis 仅在无引用、连接和数据后
  移除；Nginx 仅在不再承担 Gitea 入口或其它批准职责时移除。对不满足 checksum/reference
  前置的 legacy artifact，fail-closed 保留即为本 Change 的安全终态；若其容量不构成压力，
  不要求为完成本 Change 补签历史 checksum 或执行删除，未来任何 apply 仍须独立策略与 Gate。
  2026-08-04 所有者进一步授权以 AppServer current deployment 为保护集合：只在精确 SHA、现场
  checksum、零打开引用和 Gitea commit 可重建性全部通过时删除其它列明 legacy artifact；该授权
  不包含 Gitea repository、AppServer runtime/release/data 或未列明路径，禁止 glob 删除。
- [ ] **AC-10** 删除前同时由 `orb info prod-sim` 和 `orb list` 回读精确 name/ID，盘点其
  进程、监听、挂载、timer、数据和仓库引用；唯一数据、实时依赖或身份差异使 Gate
  `BLOCKED`。
- [ ] **AC-11** 保存最小可重建基线后，仅执行 `orb delete --force prod-sim`，禁止
  `--all`；随后 `orb list` 不再包含该 VM、`orb info prod-sim` 失败，并验证 `gitea-ci`、
  AppServer 和正式项目 health 不受影响。
- [ ] **AC-12** 自动测试至少覆盖允许 action、禁止 action、身份不匹配、profile 权限错误、
  未知 capability 和 guard 重复执行；真实环境执行两次只读 inventory，并故意请求一次
  禁止的 application start 证明零 mutation。
- [ ] **AC-13** `03-verification.md` 对每项分别记录 PASS/FAIL/BLOCKED/NOT RUN、精确 SHA、
  前后状态和回滚/重建证据；计划、备份或 candidate 不得写成迁移/删除完成。
- [ ] **AC-14** 除用户已明确授权的 `prod-sim` 删除外，其它服务停止、数据库/目录删除和
  应用迁移在执行前仍需对应 Gate 的明确授权；不得自动合并或部署生产。

## 接口、数据与兼容性影响

- Host profile 包含 `contract_version`、`host_id`、`hostname`、`role`、
  `allowed_capabilities`、`profile_revision` 和 `managed_by`；live profile 不提交凭据。
- Guard 接受固定 action 与资源类别，不接受任意 shell。退出码区分 allowed、denied、
  invalid-profile 与 identity-mismatch，便于 workflow 在 mutation 前 fail closed。
- #22 Docker release runtime 消费 role 语义，但本 Issue 不拥有 OCI release manifest。
- 已有 PM2 应用在各自迁移验收前仍可作为 AppServer legacy adapter；本 Change 不强迫其
  同时改用 Docker。
- 真实数据库内容不进入仓库；verification 只记录脱敏元数据、大小、连接数和校验结果。

## 风险与回滚约束

- 平台代码/文档通过 revert PR 回滚；host profile 通过恢复上一版本文件回滚。
- `rsdesign-new` 只有 AppServer healthy 且可回切时才停止旧 runtime；SQLite 数据先备份并
  验证恢复路径。
- MyApp/Redis/目录删除必须先有按对象恢复证据，不能用一次全局 tar 代替数据库恢复验证。
- `prod-sim` 删除永久丢失 VM 文件，没有原地 rollback；恢复只能按版本化基线新建 VM。
- 任何探针发现事实与 Issue 快照不一致时停止，重新规划而不是根据旧端口/目录继续。

## 非目标

- 不删除、重建或重命名 `gitea-ci`、AppServer 或其它 OrbStack machine。
- 不把所有非 Gitea 组件都视为违规；批准的 CI/CD allowlist 必须保留。
- 不在 AISoftPlatform 分支直接修改应用仓库 protected `main`。
- 不在本 Change 引入 Kubernetes、替换 Gitea、轮换 Secret 或执行生产部署。
- 不宣称重新创建一台同名 VM 可以恢复未备份数据。

## 未决问题

无。Nginx/Redis 的操作选择由上述可验证 predicate 决定，不需要临场猜测。
