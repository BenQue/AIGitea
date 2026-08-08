# 01 · 基础设施：VM / Gitea / Runner / Verdaccio / Mailpit

> 基础设施 as-built 记录（2026-07-11）+ Issue #21 host-role 收口合同（2026-08-02）。
> 历史端口继续保留为诊断证据，不代表它们符合当前 `scm-ci` 角色；live 迁移/清理结果只认
> `docs/changes/21/03-verification.md`。

## 1. 拓扑与端口总表

2026-08-02 删除 Gate 前的 OrbStack 只读 baseline 有三台 Ubuntu arm64 machine：

| Machine | 域名 / IP | 当前合同与状态 |
|----|-----------|------|
| `gitea-ci` | gitea-ci.orb.local / 192.168.139.49 | 目标 role=`scm-ci`：Gitea + Runner + 受控 CI/CD 辅助服务；历史业务 runtime 尚待逐项 Gate 收口 |
| `AppServer` | AppServer.orb.local / 192.168.139.212 | role=`appserver-test` 候选；每个应用仍须在自己的 Issue/PR 中部署和验收 |
| `prod-sim` | prod-sim.orb.local / 192.168.139.234 | 早期彩排 VM；已获精确删除授权，但 AC-10/AC-11 通过前仍是 live，不能写成 retired |

| 端口（gitea-ci） | 2026-08-02 实时身份 | host-role 判定 |
|------|------|----------|
| 3000 | Gitea 1.26.4 / `gitea.service` | KEEP：SCM |
| 4873 | Verdaccio / `pm2-benque.service` | KEEP：批准的 CI cache |
| 1025 / 8025 | Mailpit SMTP / Web UI | KEEP：批准的通知辅助服务 |
| 5432(loopback) | PostgreSQL；`gitea`、`hsdb_ci` 及遗留 `app_test` | `gitea`/`hsdb_ci` KEEP；业务 DB 必须逐对象 Gate |
| 3100 / 8091 | `rsdesign-new@49033a12...` + Nginx | MIGRATE：AppServer healthy/数据/回滚验收和人工 Gate 后才可停止 |
| 3212 | `act_runner.service` cgroup 内、cwd 已删除的 `sfm-board` | REMOVE candidate：先在应用仓修复 cleanup，再按 PID/cgroup Gate 终止 |
| 8090 | MyApp Notes 静态入口，API 当前 502 | RETIRE candidate：vhost/runtime/DB/制品分别备份、查引用并获授权 |
| 6379(loopback) | Redis，当前 keyspace 无 DB 条目 | REMOVE candidate：无引用、连接和数据证据通过后另行授权 |

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

下表同时区分 live as-built 与 Issue #35 target。候选 PR 未人工合并、未执行 post-merge
reconciliation 前，不得把 target 账号或权限写成已经存在。

| 账号/角色 | 状态 | 位置 | 用途 | 关键约束 |
|------|------|------|------|----------|
| `admin` | live | Gitea | 人工 break-glass、用户/仓库引导、最终 PR merge | 唯一 merge identity；不用于日常 Agent Git/API |
| `ci-bot` | live legacy | Gitea | 已有 analyzer / Loop profile 的 API 与 feature Git | 精确 Write、无 Admin/merge；新项目不再接入；每个 project agent 真实验收后才逐仓库退出 |
| `aisoft-platform-manager` | Issue #35 target，`NOT RUN` | Gitea | 跨项目读取 settings/protection/Actions，执行已批准 reconciliation | 不是 site admin；仅显式 9 仓库 Admin；audit/mutation PAT 分离；不得普通 Git 或 merge |
| `<project>-agent` | Issue #35 target，`NOT RUN` | Gitea | 仅本项目 Issue/branch/commit/push/PR | 精确 Write；唯一项目绑定；不得跨项目 Write/Admin，不得 push/merge `main` |
| `git` | live | VM 系统用户 | 跑 Gitea 进程 | 不承载 Agent 或部署身份 |
| `gitea-runner` | live | VM 系统用户 | 跑 act_runner、构建/测试与制品发布 | 不持有平台 manager、项目 PAT 或生产管理员权限，不长期运行业务应用 |
| `coder` | live | VM 系统用户 | 跑 analyzer/controller | 每项目 mode 600 profile/credential/state/worktree 分离；当前 Loop 未普遍启用 |
| `benque` / platform operator | live | VM 默认用户 | 本地平台引导与运维 | 只在 purpose-built 工具和明确批准中使用 sudo/admin credential；不作为项目 deploy identity |
| `<project>-deploy` | 每应用部署 Change target | AppServer/公司服务器 | 只操作本项目 release/runtime/data/service | 不跨项目，不复用 Gitea PAT；生产仍只运行已验证脚本且无 AI 登录 |

> 🕳️ 踩坑 #8：**Gitea 管理员创建的用户默认 `must_change_password=true`**——改密前该用户所有 API 返回 403（正文 "You must change your password"）。解法：`PATCH /api/v1/admin/users/{u}`，body 带 `{login_name, source_id, must_change_password:false}`。
>
> 🕳️ 踩坑 #7：**token 管理端点只认 basic auth**。给他人签发：`curl -u "admin:密码" -H "Sudo: ci-bot" -X POST .../api/v1/users/ci-bot/tokens`。

## 3. Gitea（安装要点 + as-built 配置）

- 单二进制 `/usr/local/bin/gitea`（1.26.4），systemd 托管，数据 `/var/lib/gitea`，DB 用本机 PostgreSQL（`gitea` 库）。
- Actions 默认启用（1.21+）。
- 仓库 `admin/rsdesign-new`：2026-08-08 live 仍公开，Issue #35 target 为 private；默认分支 `main`；**分支保护**：
  - 禁止直接 push（对所有人生效，含 admin——一切走 PR）
  - 必须状态检查通过：context = `CI / test (pull_request)`
- 当前 canonical manifest 定义 17 个规范标签，分为三个正交维度：
  - 七个类型标签：`type/bugfix`、`type/feature`、`type/docs`、`type/test`、`type/refactor`、`type/maintenance`、`type/platform`。
  - 两个复杂度标签：`complexity/small`、`complexity/complex`；由 AI 判定有效路径，无法安全判级时两个都不写。
  - 八个流程状态标签，其中 `completed` 表示合并且无需部署，`deployed` 表示部署验证完成。
- 2026-07-15 的初始 16-label 在线复验为 `created=0 existing=16`；Issue #19 后续把 canonical taxonomy 扩展为 17 个。标签属于可漂移的 Gitea 外部状态，后续操作前必须重新同步并 GET 验证。
- 上述结果只证明 taxonomy 已创建且 Issue #8 标签可写；当前 VM 的 v2 wrapper 尚未消费新字段，Development Loop runtime routing 仍未启用。
- Issue #35 发布前，`ensure-gitea-collaborator.sh` 的固定 `ci-bot` + `write` 只服务已有 profile
  的迁移兼容。发布后新项目必须先进入 strict governance manifest，再创建唯一 project agent，
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
  deleted cwd；job 结束后仍在线的 `sfm-board:3212` 是失败证据，不是部署。

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
最终验收还必须证明 `3100/3212/8090/8091` 等业务入口已按各自 Gate 收口，以及
Gitea、Runner、Verdaccio、Mailpit、HSDB CI 和有效制品消费仍正常。

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
接口。安装候选不表示已配置 live profile，更不表示服务已经迁移或部署。

## 9. Windows 与公司内网目标边界

本册只记录 Mac OrbStack 上的 Linux as-built。公司内网不要求逐机复制这一拓扑，而是复用其职责分离：Gitea、Runner、制品、测试环境、部署控制端和生产运行环境分别建立明确身份与权限。

Windows 新目标使用 Windows x64 Runner、IIS、ASP.NET Core、React `wwwroot`、PostgreSQL、测试 OpenSSH，以及生产 SMB + Kerberos WinRM + JEA。详细设计与实施入口：

- [07-内网与生产平移路线](07-内网与生产平移路线.md)
- [12-Windows平台自动部署方案](12-Windows平台自动部署方案.md)
- [13-项目结果迁移与内网切换实施手册](13-项目结果迁移与内网切换实施手册.md)
- [14-Windows部署与迁移验收清单](14-Windows部署与迁移验收清单.md)

上述内容当前均为目标设计，未在公司环境执行；不得把 Linux 冒烟结果作为 Windows 或生产验收证据。
