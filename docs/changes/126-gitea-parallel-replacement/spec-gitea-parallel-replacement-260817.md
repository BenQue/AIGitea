---
issue: 126
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/126
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
  - 120
  - 124
status: approved
branch: change/126-gitea-parallel-replacement
pr_url:
created: 2026-08-17
updated: 2026-08-17
---

# Spec：公司 Pilot greenfield systemd Gitea 并行替换

## 目标与原因

为公司两 VM Pilot 增加一条可机器审计的 `greenfield-parallel-replacement` 路径：在 `scm-ci` 上保留
legacy Docker Gitea 原样运行，同时在完全独立的 Linux identity、systemd unit、PostgreSQL cluster、端口和
目录中建立新的 binary + systemd Gitea。新仓库未来只进入新实例；legacy 仓库的迁移、DNS/TLS 切换和旧实例
退役必须另建 Change，不能被本 Change 隐式授权。

当前 `company-delivery` 1.0.1 的 Stage 10 只探测 PATH 中的 `gitea` binary 与 `gitea.service`，会把“仅有
Docker Gitea”的主机错误投影为 Gitea `ABSENT`。本 Change 将 operator 升级为 1.1.0，引入 inventory v2、
legacy coexistence 探测和严格 transition receipt，并修正 Stage 20/50 的依赖图。

本 Change 只交付 source、portable operator bytes、文档与 local fake 验证。开发机不连接公司内网，也不
执行任何公司 Gitea/PostgreSQL/service 操作。公司已经完成的 1.0.1 Stage 00 仍是独立历史证据；它不能被
重解释为 1.1.0 的 Stage 00。公司 Stage 10 及后续阶段全部保持 `NOT RUN`。

## 固定目标合同

### 版本与上游身份

| 组件 | 固定版本 | 上游 artifact / SHA-256 | 用途 |
|---|---|---|---|
| Gitea | `1.26.4` | `gitea-1.26.4-linux-amd64` / `0faa36d151918f8f7d6e0f3ae67597d1c338583d695add146ac393109d0fc44a` | 仅 `linux/amd64` binary；Stage 50 必须从批准的 offline mirror 逐字校验 |
| PostgreSQL | `18.4` | `postgresql-18.4.tar.bz2` / `81a81ec695fb0c7901407defaa1d2f7973617154cf27ba74e3a7ab8e64436094` | 上游 release provenance；实际 OS package set 必须在 Stage 20 另有完整 SHA-256 manifest，缺失即 `BLOCKED` |

Gitea checksum 来自 Gitea 官方下载站的同名 `.sha256`；PostgreSQL checksum 来自 PostgreSQL 官方 source
release sidecar。checksum 只锁定上游身份，不授权联网下载。公司实际安装 bytes 必须先离线搬运并与批准
manifest 对账；禁止在公司服务器临时 build 或以 mutable package repository 状态代替 checksum。

### 隔离命名空间

| 资源 | 固定值 |
|---|---|
| Linux user/group | `aisoft-gitea` / `aisoft-gitea` |
| Gitea unit | `aisoft-gitea.service` |
| Gitea binary | `/opt/aisoft/gitea/1.26.4/gitea` |
| Gitea config | `/etc/aisoft/gitea/app.ini` |
| Gitea data / log | `/var/lib/aisoft-gitea` / `/var/log/aisoft-gitea` |
| PostgreSQL cluster / unit | `aisoft-gitea` / `postgresql@18-aisoft-gitea.service` |
| PostgreSQL data / database / role | `/var/lib/postgresql/18/aisoft-gitea` / `aisoft_gitea` / `aisoft_gitea` |
| New Gitea HTTP | `127.0.0.1:3000` |
| New PostgreSQL | `127.0.0.1:55432` |
| Public name | Stage 20 protected input，只在 receipt 中保存 `sha256:` fingerprint，不把真实 FQDN/IP 写入 bundle 或回流 evidence |

新实例初始配置固定 `HTTP_ADDR=127.0.0.1`、`HTTP_PORT=3000`、`DISABLE_SSH=true`、
`START_SSH_SERVER=false`。SSH、Runner、Actions auto deploy、inbound timer、production gate、DNS/TLS、
reverse proxy 和正式仓库导入均保持 disabled/inactive 或 `NOT RUN`。Stage 50 只允许本机 health/version/login
和 storage identity 验收；任何对外切流必须是后续独立批准。

### Legacy 不变式

- legacy Docker Gitea 的 container、image、volume、network、database、configuration、port、repository 和
  service lifecycle 均不属于本 Change 的 mutation allowlist。
- pre/post probe 只允许：固定 Docker `publish=<approved-port>` 过滤、container ID 的 SHA-256、固定 loopback
  `GET /api/v1/version` 的 HTTP status 与 semver。不得 `docker inspect`、读取 env/config/log、枚举全部
  container/port，或输出 container ID、主机名、IP、URL、用户名。
- Stage 10 生成 `legacy_baseline_sha256`。Stage 50 后再次运行 post-install collector；presence 必须仍为
  `present`、health 必须仍为 `healthy`、version 与 baseline 相同且 baseline fingerprint 完全相等。
- 任一 legacy probe 为 `unknown/unhealthy/ambiguous`，或 pre/post 不相等，当前阶段立即 `BLOCKED/FAIL`。
  rollback 只停止和隔离 `aisoft-gitea.service`、`postgresql@18-aisoft-gitea.service` 与上述新 namespace；
  禁止停止、重启、修改或删除 legacy Docker resources。

## Inventory v2 与 transition receipt

### Stage 10 inventory v2

`company-delivery-inventory/v2` 保留 v1 的 host/tool/unit 脱敏事实，并增加 role-specific `scm`：

- `appserver-prod` 的 `scm` 必须为 `null`；`scm-ci` 必须包含 greenfield probe profile。
- legacy 只记录 port target fingerprint、Docker presence enum、container ID fingerprint、health enum、semver 和
  canonical baseline fingerprint；绝不保存 raw output。
- candidate 只记录两个固定端口的 `free|occupied|unknown` 和固定资源的
  `absent|expected-empty|occupied|unsafe|unknown`；不输出目录内容或任意 listener inventory。
- collector mode 只允许 `preflight` 或 `post-install`。preflight PASS 要求 candidate ports free、新 unit
  not-found、固定资源 absent/expected-empty；post-install PASS 要求 candidate ports occupied、新 units
  enabled/active、固定资源 occupied，同时 legacy baseline 保持健康。
- CLI 对 `scm-ci` 强制要求 `--mode` 与 `--legacy-gitea-http-port`；port 只接受十进制 `1..65535`。候选端口
  来自 compatibility contract，不接受调用方覆写。`appserver-prod` 不接受这些参数。

v1 schema/旧 1.0.1 bundle 作为历史 bytes 保留；1.1.0 collector 只产生 v2，不能把 v1 inventory 复用为本
Change 的 Stage 10 PASS。

### Stage 20 transition v1

新增 `company-delivery-gitea-transition/v1` strict receipt 和 `verify-gitea-transition`：

- receipt 绑定 1.1.0 source SHA、两份 Stage 10 inventory SHA-256、public-name fingerprint、legacy baseline、
  固定 target contract、Stage 状态和人工 reviewer decision ID。
- 唯一 decision enum 为 `greenfield-parallel-replacement`、`controlled-upgrade-candidate`、`BLOCKED`。
- greenfield PASS 必须读回两份 inventory：两个 role 均 `PASS`，`scm-ci` 为 preflight、legacy
  `present/healthy`、candidate ports free、固定 resources absent/expected-empty、自动化入口 disabled。
- greenfield 的 Stage map 必须精确为 Stage 00=`PASS`、两份 Stage 10=`PASS`、Stage 20=`PASS`、Stage
  30/40/50=`NOT RUN`。validator 明确拒绝把跳过的 legacy backup/restore 写成 `PASS`。
- controlled upgrade 仍要求 Stage 30 与 40 在进入 Stage 50 前各有独立 PASS evidence；本 Change 不改变其
  backup/restore gate。
- `verify-legacy-health` 将 transition baseline 与 post-install inventory 对账；只有 greenfield 路径可用该
  alternate prerequisite 解锁 Stage 50 验收，且 Stage 30/40 仍保持 `NOT RUN`。

Stage 20 receipt 只证明“候选路径与前置事实可继续评审”，不是安装批准。Stage 50 仍需新的、只绑定 exact
Gitea/PostgreSQL bytes、固定 namespace 和一次 maintenance window 的人工批准。

## Acceptance criteria

- [ ] **AC-1 Inventory v2**：1.1.0 collector 不再以 host binary + `gitea.service` 缺失断言 Gitea 实例
  `ABSENT`；scm-ci 必须同时输出 legacy Docker presence/health fingerprint 与 candidate collision/resource
  enums，appserver-prod 明确 `scm=null`。
- [ ] **AC-2 Probe safety**：collector 只执行固定、read-only、loopback/allowlisted probes；无
  `docker inspect`、全量枚举、env/config/log/Secret 读取或 raw echo。malformed/multiple IDs、敏感输出、
  timeout、unknown port/path 均 fail closed 且 no-echo。
- [ ] **AC-3 Transition state machine**：strict receipt/CLI 绑定两份 inventory 和 target contract；greenfield
  只允许 00/10/20 PASS，30/40/50 保持 NOT RUN；伪造 skipped PASS、不同 checksum/role/mode/baseline 或
  candidate collision 必须拒绝。
- [ ] **AC-4 Fixed target identity**：compatibility/runtime/docs 同时锁定 Gitea 1.26.4、官方 checksum、
  PostgreSQL 18.4 provenance、Linux identities、units、paths、DB names 和 loopback ports；任何 drift 为
  `BLOCKED`。
- [ ] **AC-5 Legacy invariant**：pre/post inventory 只比较 canonical legacy fingerprint；healthy/version/
  presence 任一变化均阻止 PASS，且 rollback allowlist 只包含新实例 namespace。
- [ ] **AC-6 Initial isolation**：SSH、Runner、timer、Actions auto deploy、production gate、DNS/TLS、proxy、
  repo import 初始全部 disabled/inactive 或 NOT RUN；Stage 50 PASS 不能暗示 traffic cutover 或 legacy
  migration。
- [ ] **AC-7 Portable operator**：VERSION 升至 1.1.0；inventory v2、transition schema/runtime/template、
  compatibility 和 runbook 被 deterministic handoff 收录并通过 tamper/no-secret/repeatability 验证。旧
  1.0.1 Stage 00 不得投影为新 Stage 00。
- [ ] **AC-8 Runbook**：Stage 10、20、30、40、50 的 prerequisites、commands、evidence、stop point 与
  greenfield-only rollback 精确对齐；controlled upgrade 保留原 backup/restore gate。
- [ ] **AC-9 Validation**：focused unit/security negatives、full runtime suite、platform smoke、所有 JSON parse、
  `bash -n`、ShellCheck（可用时）、`git diff --check` 和 dual-axis review 全部通过。
- [ ] **AC-10 Governed delivery**：唯一 readable branch/docs/PR；PR body 恰有一行 `Closes #126`；final head、
  protected main 与 CI 状态通过 typed broker 读回，AI 不合并。
- [ ] **AC-11 Execution boundary**：公司 Stage 10、20、30、40、50 及所有 service/database/network/repo
  mutation 均为 `NOT RUN`；本地 tests/source/PR 不能写成公司部署成功。

## 接口、数据与兼容性影响

- `collect-inventory` 对 `scm-ci` 增加必填 typed options 与 mode；这是 operator 1.1.0 的有意 breaking
  contract。1.0.1 archive 仍可用其自带 runtime 验证自身历史 evidence，不与 1.1.0 混用。
- inventory contract 从 v1 升至 v2；handoff/evidence 仍保持 v1。新增 transition v1，不扩展 generic evidence
  为可以伪造跨阶段状态的自由字段。
- bundle source mapping 已覆盖整个 `company-delivery/` 与 runtime，因此新增 schema/template 会自动进入
  payload inventory、SHA256SUMS 与 no-secret scan。
- 无平台数据库 schema migration；未来新 Gitea database/role/cluster 是 Stage 50 的公司 live mutation，当前
 不连接也不创建。

## 风险与回滚约束

| 风险 | 缓解与回滚 |
|---|---|
| Docker-only legacy 被误判为不存在 | inventory v2 用 typed Docker publish + loopback health；unknown 不降级为 absent |
| 探测泄漏公司拓扑或 Secret | raw 值不落盘；port/FQDN/container 只保存 fingerprint 或 enum；固定 no-echo error |
| 新旧实例端口、目录、unit 或 DB 冲突 | preflight 对固定候选资源 fail closed；Stage 20 receipt 绑定完整 target tuple |
| 跳过 Stage 30/40 被伪造成 PASS | transition validator 要求 greenfield 30/40 精确 NOT RUN；controlled upgrade 仍要求 PASS |
| Stage 50 影响 legacy | pre/post canonical baseline equality；失败只 stop/isolate 新 units 和新 namespace |
| 新 Gitea 被误当为已切换生产 | loopback-only + SSH/Runner/timer/gates/DNS/TLS disabled；repo migration/retirement 独立 Change |
| 新 operator 与旧 Stage 00 混用 | VERSION、schema/version、source SHA 和 handoff checksum 绑定；必须重新生成/执行 1.1.0 Stage 00 |

source 回滚为单 PR revert。本 Change 不产生 live state，因此没有公司 live rollback；未来 greenfield Stage 50
回滚只能停止新 units 并隔离新 paths/DB，legacy 继续运行。任何 database delete、package purge 或 legacy
mutation 都需要新的破坏性批准，不能自动执行。

## 非目标

- 不访问公司内网，不读取或保存真实 hostname/IP/FQDN、账号、config、log、repository 或 Secret。
- 不升级、重启、停止、迁移、备份、恢复或退役 legacy Docker Gitea。
- 不在本 Change 安装 Gitea/PostgreSQL，不创建用户/目录/DB/unit，不改 firewall/DNS/TLS/reverse proxy。
- 不启用 SSH、Runner、Actions auto deploy、sync timer 或 production gate。
- 不迁移 legacy repository；不决定 legacy phase-out 日期或删除条件。
- 不执行公司 Stage 10 或 Stage 20，不复用当前 1.0.1 Stage 00 作为 1.1.0 PASS。
- 不修改 NewEmaint application release，不部署 production，不合并 PR。

## 未决问题

无改变实现方向的未决问题。真实 legacy loopback port、public FQDN、OS package checksums、容量与 company
approval IDs 都是未来 protected Stage 10/20 输入；缺失或不匹配产生 `BLOCKED/NOT RUN`，不会触发猜测或
silent fallback。
