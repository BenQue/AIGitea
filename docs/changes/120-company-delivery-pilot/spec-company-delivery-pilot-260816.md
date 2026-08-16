---
issue: 120
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/120
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - schema-change
  - security
  - external-contract
  - shared-core
  - cross-module
  - ci-change
  - artifact
  - deployment
  - compatibility
  - rollback
  - platform-governance
depends_on:
  - 121
status: approved
branch: change/120-company-delivery-pilot
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/123
created: 2026-08-16
updated: 2026-08-16
---

# Spec：公司两 VM 与 NewEmaint 确定性交付试点

## 目标与原因

为 NewEmaint 准备一套可审核、可携带、由人逐阶段执行的公司侧 operator workflow。开发会话不连接
公司内网，也不声称已安装或部署；本 Change 只交付版本化工具、strict schemas、模板、runbook 与本地
fake/disposable 验证。

本 Spec 覆盖旧文档中“公司另建 `appserver-test`、形成三台公司 VM”的假设。当前正式拓扑只有两台
公司 Linux VM；第三个 trust role 仍存在，但由本地 OrbStack NewEmaint DockerLab 承担非生产验证：

| 位置 | machine identity / role | 允许职责 | 明确禁止 |
|---|---|---|---|
| 公司 VM 1 | `gitea-ci` / `scm-ci` | Gitea、GitHub 入站、PR/CI、`act_runner`、Registry/cache、artifact-only verification、受控发布编排 | 业务 runtime、业务 DB、application deploy/start、生产 Secret |
| 本地 | OrbStack DockerLab / `appserver-test` | 对 exact `docker-release/v2` bytes 做非生产 deploy、migration、health、rollback 验证 | 作为公司 live evidence；向公司提供凭据或内网入口 |
| 公司 VM 2 | `appserver` / `appserver-prod` | NewEmaint runtime、PostgreSQL、Nginx、fixed production target gate | Gitea、通用 Runner、源码构建、AI、任意 shell 发布入口 |

公司 Gitea 是部署权威；本地 Gitea 保持开发权威；私有 GitHub 只运输 source provenance 或 approved
bundle。公司必须重新创建 PR、运行自己的 CI/verification 并由人合并，不能继承 GitHub 或本地 PR 的
审批结论。

## Operator bundle 合同

### 版本、内容与确定性

仓库新增 `company-delivery/`，其 `VERSION` 固定 operator contract 版本。构建入口只能从 clean Git
worktree、完整 40 位 source SHA 与显式 `docker-release/v2` release root 生成 bundle，输出至少包含：

```text
aisoft-company-delivery-<version>-<source-sha>/
├── operator/                 # collector、validator、runbook、schema、template、compatibility
├── release/                  # exact 已验证 docker-release/v2 bytes；不得重建
├── handoff-manifest.json     # source/release/bundle identity 与逐文件摘要
└── SHA256SUMS                # 排序、相对路径、SHA-256
```

- archive 与伴随 checksum 由同一 build 产生；重复使用同一 source、release bytes、版本与显式时间输入必须
  得到相同 checksum。
- `handoff-manifest.json` 必须绑定 operator 版本、完整 Git SHA、release ID、release manifest SHA256、
  compatibility matrix SHA256、每个 payload 文件 SHA256、预期 role/architecture 与 transport。
- `SHA256SUMS` 不覆盖自身；handoff manifest 中也不嵌入 archive 自身 checksum，避免自引用。archive 的
  SHA256 作为相邻 `.sha256` 文件传输并在解包前验证。
- release root 必须先通过现有 `docker-release/v2` artifact-only contract；任何缺失 digest、短 SHA、
  mutable-only image、错误架构、checksum drift 或不同 bytes 均在公司 mutation 前 `BLOCKED`。
- 如果公司政策要求内网重新 build，且公司没有与生产隔离的测试环境可验证这些新 bytes，结论固定为
  `BLOCKED`；不得把不同 bytes 标为“本地已测试”。

### Secret 与文件安全

- bundle、命令参数、stdout/stderr、inventory 和 evidence 不得包含 PAT、token、password、SSH/private key、
  connection string、`.env` 值或认证 header。
- 工具只接受无 Secret 的 metadata。未来需要凭据的人工步骤只引用 root-owned/protected file 或公司
  secret store 的逻辑名称，不读取、复制或打印值。
- 输出文件使用 mode `0600`，目录使用 `0700`；world/group writable、symlink input、绝对/上跳 payload path、
  重复 path、未知 schema 字段或可疑 Secret sentinel 均 fail closed。
- no-secret scanner 只报告固定 reason/code 和字段路径，不回显命中的敏感值。

## Inventory、handoff 与 evidence schema

三个 JSON schema 使用 `additionalProperties: false`，版本固定并由 stdlib validator 实施相同边界：

1. `inventory-v1`：记录 role、collector/version/time、OS/architecture、hostname 与 machine-id 的 SHA256
   fingerprint、CPU/内存/根卷余量、严格解析后的工具版本及 allowlisted systemd unit 的
   `enabled/disabled/masked/not-found`、`active/inactive/failed/not-found` 状态。禁止输出 raw hostname、
   machine-id、用户名、IP、mount 列表、环境变量、配置内容、日志和任意 probe 原始输出。
2. `handoff-v1`：记录 operator/source/release/compatibility identity、transport、payload 清单与摘要；完整
   SHA/digest/相对路径均严格校验，逐文件 bytes 必须与摘要一致。
3. `evidence-v1`：一个文件只记录一个批准阶段；顶层 outcome 只允许 `PASS`、`FAIL`、`BLOCKED`、
   `NOT RUN`，并把 `observed`、`changed`、`verified`、`pending` 分开。每条事实含 code、status、脱敏
   detail 与 artifact refs，不允许把 local/fake/CI 结果投影为 company/production scope。

collector 只执行固定 read-only probe，不接受 raw command、shell expression、URL、credential path 或任意
service unit。版本输出只提取 allowlisted semver；无法安全解析时记录固定 `BLOCKED` reason，不保存原文。

## 分阶段人工 runbook

runbook 固定以下阶段。人每次只能批准一个 stage，完成 evidence review 后才可批准下一阶段；没有当前阶段
批准记录时必须保持 `NOT RUN`：

| Stage | 目标 | 允许性质 | 强制停止点 |
|---|---|---|---|
| 00 | 验证 archive、`SHA256SUMS`、handoff、release 与 compatibility | 只读 | 任一 identity/checksum/权限失败即 `BLOCKED` |
| 10 | 分别收集 `gitea-ci` 与 `appserver` 脱敏 inventory | 只读 | role/arch/版本/磁盘或 unit 状态未知即等待人工裁决 |
| 20 | 选择 Gitea side-by-side 或 controlled upgrade | 决策 | 未完成 inventory、备份范围或回滚路径不得安装 |
| 30 | 建立 Gitea/AppServer backup | live mutation，未来独立批准 | 未取得脱敏 backup identity/checksum 不进入 restore drill |
| 40 | isolated restore drill | 隔离环境 mutation，未来独立批准 | restore、登录、repo/LFS/package/attachment 对账未通过即停止 |
| 50 | Gitea install/upgrade 与首次验收 | live mutation，未来独立批准 | sync timer、Actions auto deploy、production gate 保持 disabled/inactive |
| 60 | company Gitea repo/bootstrap/protection | live mutation，未来独立批准 | GitHub SHA、company baseline、protection/CI context 未读回即停止 |
| 70 | one-shot inbound、Runner 与 Registry verification | live mutation，未来独立批准 | 正负权限、one-shot 幂等、不可覆盖制品未通过即停止 |
| 80 | `scm-ci` artifact-only verification | 只读制品验证 | 禁止 target profile/Secret/Docker mutation；失败不搬到 AppServer |
| 90 | `appserver-prod` read-only target readiness | 只读 | fixed target/role/compatibility/backup 未齐即 `BLOCKED` |
| 100 | stage/migrate/activate/rollback 演练或生产执行 | production mutation，未来独立批准 | 只接受 fixed action、fixed target、full SHA、verified release identity |
| 110 | evidence bundle 脱敏、对账与回流 | 只读/归档 | 未完成项继续 `NOT RUN`，不得补写为 PASS |

本 Change 只真实运行 Stage 00 的 fake/local 路径与工具测试；所有公司 Stage 10–110 均为 `NOT RUN`。

## Gitea 安装/升级、备份和回滚 gate

- inventory 未发现可受控的现有实例时，选择 side-by-side；使用独立目录/数据库/端口，验证完成前不接管
  DNS/TLS/正式仓库。
- inventory 发现现有实例且版本、安装形态、external storage、数据库与 rollback 兼容性全部已知时，才可
  候选 controlled upgrade；不得跨未知 major、不得直接覆盖 current。
- 任何 upgrade 前，backup 必须覆盖 Gitea DB、`app.ini` 与实例 keys、repositories、LFS、packages、
  attachments、avatars 以及配置引用的 external storage；加密介质、保留期和异机存放由公司策略决定。
- `backup completed`、archive 可列出或 `pg_restore --list` 均不等于 restore PASS。Stage 40 必须在隔离目标
  恢复并对账登录、仓库 refs、LFS、packages、attachments、关键设置与 protection；不连接生产客户端。
- Gitea rollback 是恢复先前 binary/config/data snapshot；NewEmaint application rollback 只切回 previous
  release；PostgreSQL restore 是独立人工决策，永远不由 application rollback 自动触发。

## GitHub、Gitea、Runner、Registry 与 production gate

- GitHub inbound 只允许 `sync/inbound-sync.sh reconcile <allowlisted-profile>` 的 one-shot 验收；安装时 timer
  保持 disabled/inactive，future enable 需独立批准。
- company Gitea bootstrap 必须证明 GitHub allowlisted ref 与初始 `main` full SHA 一致，然后立即保护
  `main`；sync/project/runner identity 均不得直接或 force push/merge `main`。
- PR CI 只使用 disposable dependencies，不持有 production SSH/sudo/database Secret。Runner 负向验证必须
  证明 application start、business database 与 production target action 被拒绝。
- Registry 验证覆盖 digest pull/publish、同 identity 幂等和覆盖拒绝；不得把 tag 当唯一 identity。
- Stage 80 只能调用 existing `verify-artifact`；Stage 100 只能经 existing fixed action grant/gate 映射受保护
  target profile。普通 Runner 不获得任意 SSH、sudo、Docker shell 或数据库入口。

## Acceptance criteria

- [ ] **AC-1 Read-only inventory**：两个 role 的 collector 仅有 allowlisted read-only probes，输出通过 strict
  schema、默认 `0600`、不含 raw hostname/machine-id/path/IP/Secret；unknown/unparseable 项为 `BLOCKED` 或
  `NOT RUN`，测试证明 probe 原文中的 Secret sentinel 不会泄漏。
- [ ] **AC-2 Staged manual operation**：runbook 含 Stage 00–110，每阶段有前置、批准对象、精确允许动作、
  停止点、evidence、回滚边界；任何时刻只执行一个批准阶段。
- [ ] **AC-3 Deterministic handoff**：builder 绑定 full Git SHA、operator version、exact `docker-release/v2`
  release identity、compatibility 与逐文件 SHA256；同输入重复构建 byte-identical，篡改/短 SHA/错误 digest/
  错架构/上跳路径 fail closed。
- [ ] **AC-4 Evidence contract**：inventory/handoff/evidence 三 schema 与模板可机器验证；evidence 分开
  `observed/changed/verified/pending`，且状态只使用 `PASS/FAIL/BLOCKED/NOT RUN`。
- [ ] **AC-5 Gitea decision gate**：runbook 明确 side-by-side/controlled-upgrade 输入与 fail-closed 决策，
  backup 覆盖 DB/config/keys/repos/LFS/packages/attachments/external storage，并要求 isolated restore drill。
- [ ] **AC-6 Exact bytes**：公司 artifact-only verification 不读取 target Secret、不 build、不 deploy；不同
  bytes 或公司无隔离测试环境而要求重建时固定 `BLOCKED`。
- [ ] **AC-7 Inbound/SCM verification**：one-shot inbound、company bootstrap、protected `main`、required CI、
  Runner 与 Registry 都有正负验收；timer 与 Actions auto deploy 在首次验收保持 disabled/inactive。
- [ ] **AC-8 Fixed production target**：production 只接受 fixed action、target ID、full SHA、已验证 release；
  普通 Runner 无生产 SSH/sudo/DB；app rollback 与 DB restore 分离。
- [ ] **AC-9 Topology/docs**：README、07、12-Linux、13 对齐“两台公司 VM + 本地 DockerLab”，保留三种
  role 的 capability 隔离，但不再要求第三台公司 VM。
- [ ] **AC-10 Validation**：focused unit/fake tests、deterministic repeat、tamper/security negatives、JSON parse、
  `bash -n`、ShellCheck（可用时）、full runtime suite、`bash codex/tests/smoke.sh` 与 `git diff --check` 通过。
- [ ] **AC-11 Governed delivery**：唯一 readable tuple 和唯一 PR；PR body 恰有一行 `Closes #120`；exact final
  head 的 required CI 如实分类，AI 不合并。
- [ ] **AC-12 Evidence boundary**：公司 VM、公司 Gitea/Runner/Registry、backup/restore、NewEmaint target、
  production、timer/service enable/restart、database migration/restore 全部保持 `NOT RUN`。

## 接口、数据与兼容性影响

- 新增 `company-delivery/v1` operator contract，不修改既有 `docker-release/v1/v2`、`sync/`、host-role 或
  fixed gate 接口；bundle 只组合并验证其 exact bytes。
- 新 schema 是 additive V1。未知 version/字段一律拒绝，没有 silent coercion 或 legacy fallback。
- capability catalog 仍保留 `appserver-test`；变化仅是此 NewEmaint pilot 的该 role 位于本地 DockerLab，
  不对应第三台公司 VM。
- 无数据库 schema migration；未来公司 Gitea/PostgreSQL 操作只在 runbook 的独立人工阶段发生。

## 风险与回滚约束

| 风险 | 缓解/回滚 |
|---|---|
| 不同 bytes 被冒充为已测试 release | manifest + per-file checksum + archive checksum；identity 不同立即 BLOCKED |
| collector 泄漏 Secret/主机标识 | 固定 probe + 严格解析 + fingerprint + fixed reason；不保存 raw stdout/stderr |
| 两 VM 约束弱化 role 隔离 | role 跨本地/公司分布；`scm-ci` application/DB capability 继续 fail closed |
| blind Gitea in-place upgrade | side-by-side 优先 gate；controlled upgrade 前完整 backup + isolated restore |
| Runner 越权生产 | fixed gate 与负向验证；通用 Runner 无 SSH/sudo/DB/target profile path |
| 文档/本地测试误报 live success | evidence scope 字段 + verification 中所有 company/live 项固定 NOT RUN |

source 回滚为单 PR revert。由于本 Change 不执行公司 mutation，不存在 live rollback；未来每个批准 stage 按
runbook 自己的 stop/rollback 条款处理，不能用后续 stage 掩盖前一阶段失败。

## 非目标

- 不连接公司内网，不索要或发现公司 SSH 入口。
- 不创建、读取、复制、轮换或打印 Secret/PAT/key。
- 不安装/升级公司 Gitea、Runner，不启用/重启 service/timer，不改 DNS/TLS/firewall。
- 不执行真实 backup/restore、database migration、test deployment 或 production deployment。
- 不修改 NewEmaint 应用仓、镜像或 release bytes；真实 release 输入缺失时保持 `NOT RUN`。
- 不启用公司 Actions 自动部署或 production gate，不运行公司侧 AI/Analyzer/Loop。
- 不合并 PR。

## 未决问题

无。公司 inventory、地址、版本、存储、RTO/RPO 和 Secret store 均是未来 Stage 10/20 的输入；缺失会产生
`BLOCKED/NOT RUN` evidence，而不是本地实现方向未决。
