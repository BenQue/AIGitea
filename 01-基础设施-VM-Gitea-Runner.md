# 01 · 基础设施：VM / Gitea / Runner / Verdaccio / Mailpit

> 基础设施 as-built 起点为 2026-07-11；本册当前状态已按 Issue #21（2026-08-04 完成）和
> Issue #35（2026-08-09 最后回读）收口。环境事实会漂移，执行操作前仍须实时只读核对；历史细节见
> `docs/changes/21/03-verification.md` 与 `docs/changes/35/03-verification.md`。

## 1. 拓扑与端口总表

最后一次完整 host-role 收口证据区分两台保留机器与一台已退役机器：

| Machine | 域名 / IP | 当前合同与状态 |
|----|-----------|------|
| `gitea-ci` | gitea-ci.orb.local / 192.168.139.49（历史地址） | role=`scm-ci` 已配置；保留 Gitea、Runner、受控缓存/通知/CI 资源，业务 runtime/DB/代理已按 Issue #21 收口 |
| `AppServer` | AppServer.orb.local / 192.168.139.212（历史地址） | role=`appserver-test`；每个应用仍须在自己的 Issue/PR 中独立部署和验收 |
| `prod-sim` | 历史地址 192.168.139.234 | 2026-08-04 已按 name+ID、依赖、数据和可重建 Gate 精确退役；不得再作为脚本目标 |

| 端口（gitea-ci） | Issue #21 最终证据 | host-role 判定 |
|------|------|----------|
| 3000 | Gitea 1.26.4 / `gitea.service` | KEEP：SCM |
| 4873 | Verdaccio / `pm2-benque.service` | KEEP：批准的 CI cache |
| 1025 / 8025 | Mailpit SMTP / Web UI | KEEP：批准的通知辅助服务 |
| 5432(loopback) | PostgreSQL 保留 `gitea`、`hsdb_ci`；遗留 `app_test` 已备份、恢复验证并删除 | KEEP 仅限批准的 SCM/CI 数据；新业务 DB 拒绝 |
| 3100 / 8091 | 旧 `rsdesign-new` runtime/vhost 已删除，应用转至 AppServer | ABSENT；不得恢复为 `scm-ci` 业务入口 |
| 3212 | 孤儿 smoke 进程与 15 个临时 DB 已精确清理，应用 cleanup 修复已合并/部署 | ABSENT；job 必须在成功、失败和取消路径清理 |
| 8090 | MyApp runtime/vhost/DB 已备份、恢复验证并精确清理 | ABSENT；不得恢复历史演示部署 |
| 6379(loopback) | Redis 无引用/连接/数据验证通过后已卸载并清理 | ABSENT；重新引入须新合同 |

`scm-ci` 允许 checkout、build、test、package、registry/artifact publish、批准的缓存/通知
服务和只读 retention inventory；application deploy/start、业务数据库、长驻 smoke 进程在
任何 mutation 前一律拒绝。端口或目录存在不等于获准，必须同时检查进程、cgroup、owner、
workflow、数据和引用。

> ⚠️ OrbStack 事实：`*.orb.local` 域名 Mac 与 VM 内都可解析；Mac 文件系统在 VM 内挂载于 `/mnt/mac`（root 可读，普通新建用户不一定可穿越）。VM 与 Mac 同生共死——Mac 睡眠 VM 即停，「常驻」要等内网平移才真正成立。
>
> 🚫 **`/mnt/mac` 读不到 macOS 隐私保护目录（`~/Documents`、`~/Desktop`、`~/Downloads`）**——2026-07-19 实测：`ls /mnt/mac/Users/benque/Documents/` 返回 `Operation not permitted`，**`sudo` 提权同样失败**（这是 macOS TCC，不是 Unix 权限，故上一条的「root 可读」对这三个目录不成立）；同一时刻 `/mnt/mac/Users/benque/Projects/` 正常可读。
>
> ✅ **这就是本套平台文档不放 `~/Documents` 的原因。** 权威根目录已于 2026-07-19 从 `~/Documents/AISoftPlatform/` 迁至 **`~/MyDocs/AISoftPlatform/`**，VM 内对应 `/mnt/mac/Users/benque/MyDocs/AISoftPlatform/`（已实测 `benque` 与 **`coder`** 两个身份均可读——`coder` 是 Codex 的运行身份，这一条是迁移的验收判据）。
> **为何选迁移而非授权**：给 OrbStack 授予「文稿」权限也能解决，但那会让 VM 内的自治 agent 获得**整个 `~/Documents`** 的读权限，且属于不进版本库的机器本地设置——换机重装即复发且无痕。迁移是一次性的、自解释的。
> **不影响推送**：应用仓库本就在 `~/Projects/` 下，挂载一直正常；平台文档库从 Mac 直接 `git push` 即可（Mac 已配凭据）。

## 2. 账号体系（权限隔离的落点）

下表采用 Issue #35 最后一次 live reconciliation 与后续 broker 证据。账号、PAT 和 ACL 仍是外部状态，
每次操作前必须通过 manifest 工具或 host access broker 重新读回。

| 账号/角色 | 状态 | 位置 | 用途 | 关键约束 |
|------|------|------|------|----------|
| `admin` | live | Gitea | 人工 break-glass、用户/仓库引导、最终 PR merge | 唯一 merge identity；不用于日常 Agent Git/API |
| `ci-bot` | 账号保留、manifest 仓库 collaborator 已移除 | Gitea | 仅作历史兼容证据 | 不得用于新接入、普通项目 Git/API 或 merge |
| `aisoft-platform-manager` | live，Issue #35=`deployed` | Gitea | 跨项目读取 settings/protection/Actions，执行明确批准的 reconciliation | 不是 site admin；仅显式 9 仓库 Admin；audit/mutation PAT 分离；不得普通 Git 或 merge |
| `<project>-agent` | live，9 个 manifest 项目逐一验证 | Gitea | 仅本项目 Issue/branch/commit/push/PR | 精确 Write；唯一项目绑定；不得跨项目 Write/Admin，不得 push/merge `main` |
| `git` | live | VM 系统用户 | 跑 Gitea 进程 | 不承载 Agent 或部署身份 |
| `gitea-runner` | live | VM 系统用户 | 跑 act_runner、构建/测试与制品发布 | 不持有平台 manager、项目 PAT 或生产管理员权限，不长期运行业务应用 |
| `coder` | live | VM 系统用户 | 跑 analyzer/controller | 每项目 mode 600 profile/credential/state/worktree 分离；当前 Loop 未普遍启用 |
| `benque` / platform operator | live | VM 默认用户 | 本地平台引导与运维 | 只在 purpose-built 工具和明确批准中使用 sudo/admin credential；不作为项目 deploy identity |
| `<project>-deploy` | 每应用部署 Change target | AppServer/公司服务器 | 只操作本项目 release/runtime/data/service | 不跨项目，不复用 Gitea PAT；生产仍只运行已验证脚本且无 AI 登录 |

> 🕳️ 踩坑 #8：Gitea 1.26.4 的 bot 创建流程可能留下 `must_change_password=true`，导致 API 403。
> 当前只能通过 versioned `bootstrap-gitea-service-account.sh` 和精确 readback 处理；不得复制历史 raw
> admin API/token 命令或在 argv 中传凭据。完整边界见 [06 §1.2](06-运维手册与踩坑集.md#12-gitea-governance-manifest-与-project-agent-gate)。

## 3. Gitea（安装要点 + as-built 配置）

- 单二进制 `/usr/local/bin/gitea`（1.26.4），systemd 托管，数据 `/var/lib/gitea`，DB 用本机 PostgreSQL（`gitea` 库）。
- Actions 默认启用（1.21+）。
- 仓库 `admin/rsdesign-new`：Issue #35 live reconciliation 后为 private；默认分支 `main`；**分支保护**：
  - 禁止直接 push（对所有人生效，含 admin——一切走 PR）
  - 必须状态检查通过：context = `CI / test (pull_request)`
- 当前 canonical manifest 共定义 27 个规范标签：平台三维 20 个（十个 `type/*`、两个
  `complexity/*`、八个流程状态），加 Matt triage 维度 7 个 `triage/*`（category 2 个 + state 5 个）。
  Issue #108 把 `type/*` 从 7 个扩为 10 个，并把 `complexity/standard` 记入 `retired`。
  准确取值与语义以 `codex/config/gitea-labels.json`（`schema_version: 2`）的 `canonical` 与
  03 §4 为准，本文不再复制枚举；`triage/*` 语义另见 `templates/docs/agents/triage-labels.md`。
  manifest 同时声明 `project_extensions.allowed_prefixes`（`area/`、`priority/`），项目本地维度
  在该前缀下自定取值，受管三维仍是封闭集合。
- 2026-07-15 的初始 16-label 在线复验为 `created=0 existing=16`；Issue #19 后续把 canonical taxonomy 扩展为 17 个。标签属于可漂移的 Gitea 外部状态，后续操作前必须重新同步并 GET 验证。
- taxonomy 与 runtime source 已支持当前字段；每个仓库的 live 标签集合仍须单独同步并 GET 回读，
  `IMPLEMENT_PROVIDER=none` 的默认值也不得因 source 能力存在而推定为已启用。
- Issue #35 live reconciliation 后，共享 `ci-bot` 已退出 manifest 仓库 collaborator。新项目必须先进入
  strict governance manifest，再创建唯一 project agent，
  使用 `gitea-governance.sh check` 做只读 diff，最后以 exact repository 单次 apply；未知仓库只
  report。manager/agent/visibility/protection 任一读回失败均为 `BLOCKED_EXTERNAL`。
- visibility policy：默认 private；当前 public allowlist 只能是 `admin/aisoft-platform`、
  `admin/myapp`、`admin/smoke-test`。内部应用即使只能在内网访问也保持 private；新 public 例外
  必须先经独立 Issue/PR 修改 manifest。
- `app.ini` 追加段（邮件，详见 [05](05-通知与多人协作.md)）：

```ini
[service]
ENABLE_NOTIFY_MAIL = true

[mailer]
ENABLED = true
PROTOCOL = smtp
SMTP_ADDR = 127.0.0.1
SMTP_PORT = 1025
FROM = "RSDesign Gitea" <gitea@rsdesign.local>
```

## 4. act_runner（host 模式）

- 二进制 `/usr/local/bin/act_runner`（1.0.7），注册标签 `ubuntu-latest:host`，工作目录 `/opt/act-runner`，systemd 托管，运行用户 `gitea-runner`。
- **host 模式含义**：job 直接以 gitea-runner 身份在 VM 上执行 shell。它可以访问批准的
  构建、缓存和制品路径，但不再因此获得在本机启动 PM2/业务数据库的许可。所有 application、
  database 和 long-running smoke mutation 必须先通过固定 host-role guard；`scm-ci` 必须
  确定性拒绝。历史“构建与测试 runtime 同机”只作 legacy 证据，不再接受为新项目默认。
- 注册 token 可命令行生成：`sudo -u git gitea --config /etc/gitea/app.ini actions generate-runner-token`。
- 工作区在 `/opt/act-runner/.cache/act/<hash>/hostexecutor`，**每个 workflow 一个哈希目录、跨 run 复用**（checkout 会清理）。
- host executor 的成功、失败和取消路径都必须断言无残留业务 PID、监听端口、临时 DB 或
  deleted cwd；历史 `sfm-board:3212` 已清理，其 Change 只作为此门禁的回归证据。

## 5. Verdaccio（弱网救星）

- 全局安装，PM2 托管（benque 用户），监听 `0.0.0.0:4873`，上游 `https://registry.npmmirror.com/`。
- 仓库根 `.npmrc`（进 git）：

```ini
registry=http://gitea-ci.orb.local:4873/
fetch-retries=5
fetch-retry-factor=2
fetch-timeout=120000
```

- 用 `gitea-ci.orb.local` 而非 `localhost`：**Mac 和 VM 内共用同一份配置**。内网平移时只改这一行。
- Prisma 引擎二进制另有下载渠道，CI 里已设 `PRISMA_ENGINES_MIRROR=https://registry.npmmirror.com/-/binary/prisma`。

### Verdaccio 是 CI 的硬依赖（Issue #201）

`4873` 一停，**所有需要下载缓存外新包的 CI 都会以 `ECONNREFUSED` 失败**。2026-08-24 起它停过
约 28 小时，期间没有任何既有闸门报警。

- 🚫 **应用仓不得改自己的 `ci.yml` 去绕过 `NPM_CONFIG_REGISTRY`。** 把 registry 指向
  `registry.npmjs.org` 确实能让那条 PR 变绿，但它同时抹掉两样东西：离线安装能力，以及这条故障的
  可见性。要绕过必须先有独立 Issue 和明确授权，不能作为「让 CI 过」的临时手段。
- ✅ 每个装 npm 依赖的项目在**依赖安装之前**跑一次 registry 存活断言，参考实现
  `templates/project/ci/registry-preflight.sh`；它做的是真实取包（packument 加 tarball），
  不读 npm 缓存也不问 pm2。采纳情况由 `aisoft-project-check.sh` 的 `ci-registry-preflight` 回读。
- 🕳️ **暖缓存会把这个故障藏起来**：`npm ci` 命中 runner 的 `/opt/act-runner/.npm/_cacache` 时
  根本不发起网络请求，所以只用既有依赖的 PR 在故障期间照样 20 秒全绿。**不要拿「别的 PR 是绿的」
  当 registry 健康的证据。**
- 🕳️ **`pm2 list` 会说谎**：进程已死时它仍可能显示 `online`。判活三件套见
  [06 踩坑 23](06-运维手册与踩坑集.md#2-踩坑集-编号即正文引用号)。

## 6. Mailpit（邮件捕获，演示层）

- 二进制 `/usr/local/bin/mailpit`（v1.30.4），systemd 托管（User=nobody）：SMTP `0.0.0.0:1025`，UI `0.0.0.0:8025`。
- 捕获**任意收件人**的邮件——Gitea 用户邮箱是假地址也能收到，适合演示与联调。
- 切真实 SMTP：只改 `app.ini [mailer]` 四行，见 [05](05-通知与多人协作.md)。

## 7. `scm-ci` 重建/平移冒烟清单

```bash
# 全服务在位
systemctl status gitea act_runner mailpit --no-pager | grep -E "●|Active"
curl -fsS http://127.0.0.1:3000/api/v1/version          # {"version":"1.26.4"}
curl -fsS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:4873/   # 200
curl -fsS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8025/   # 200
# host profile 安装并经独立 change 验收后：
/usr/local/libexec/aisoft/verify-host-role --action run --resource build
set +e
/usr/local/libexec/aisoft/verify-host-role --action start --resource application
test "$?" -eq 20
set -e
# Gitea 后台 Site Administration → Actions → Runners:gitea-ci-runner Idle
```

负向 guard 只证明 mutation 会在入口前被拒绝；它不替代 listener/process/database inventory。
Issue #21 已证明当时 `3100/3212/8090/8091` 等业务入口收口，并回读 Gitea、Runner、Verdaccio、
Mailpit、HSDB CI 和有效制品消费。重建或后续运维仍须重新验证，不能把 2026-08-04 证据当作永久健康。

## 8. Versioned host profile 与 guard

仓库提供：

- schema：`codex/config/host-role.schema.json`；
- capability catalog：`codex/config/host-capabilities.json`；
- 无 Secret 示例：`templates/hosts/host-profile.example.json`；
- 单一决策入口：`codex/tools/verify-host-role.sh`；
- 只复制版本化文件、不创建 live profile/service/timer 的 installer：
  `codex/install-host-role.sh`。

live profile 固定为 `/etc/aisoft/host-profile.json`，必须由 root 持有，mode 只能是
`400/440/600/640`，父目录也不得 group/other writable。profile 同时绑定
`hostname` 与 `/etc/machine-id`，其 capability 集必须与 catalog 中该 role 完全一致；不能
用环境变量、任意 profile 路径或调用方自报 hostname 绕过。退出码：`0=allow`、`20=deny`、
`30=invalid-profile/request`、`40=identity-mismatch`、`64=usage`。

guard 只给决定，不执行后续命令。应用仓库的 root-owned deploy/start/database wrapper
必须先调用固定安装路径，并仅在退出码 0 时继续；测试中的 fixture 注入不属于安装 CLI
接口。source 或 installer 存在不表示目标主机已配置 live profile，更不表示服务已经迁移或部署。

## 9. Windows 与公司内网目标边界

本册只记录 Mac OrbStack 上的 Linux as-built。公司内网不要求逐机复制这一拓扑，而是复用其职责分离：Gitea、Runner、制品、测试环境、部署控制端和生产运行环境分别建立明确身份与权限。

Windows 新目标使用 Windows x64 Runner、IIS、ASP.NET Core、React `wwwroot`、PostgreSQL、测试 OpenSSH，以及生产 SMB + Kerberos WinRM + JEA。详细设计与实施入口：

- [07-内网与生产平移路线](07-内网与生产平移路线.md)
- [12-Windows平台自动部署方案](12-Windows平台自动部署方案.md)
- [13-项目结果迁移与内网切换实施手册](13-项目结果迁移与内网切换实施手册.md)
- [14-Windows部署与迁移验收清单](14-Windows部署与迁移验收清单.md)

上述内容当前均为目标设计，未在公司环境执行；不得把 Linux 冒烟结果作为 Windows 或生产验收证据。
