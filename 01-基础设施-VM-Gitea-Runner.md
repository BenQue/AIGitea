# 01 · 基础设施：VM / Gitea / Runner / Verdaccio / Mailpit

> as-built 记录（2026-07-11）。重建环境或内网平移时，本册就是安装手册；已踩过的坑直接标注在对应步骤旁。

## 1. 拓扑与端口总表

两台 OrbStack Ubuntu VM（arm64，Apple Silicon）：

| VM | 域名 / IP | 角色 |
|----|-----------|------|
| `gitea-ci` | gitea-ci.orb.local / 192.168.139.49 | Gitea + runner + Verdaccio + Mailpit + 测试环境 + agent |
| `prod-sim` | prod-sim.orb.local / 192.168.139.234 | 离线生产彩排（只收制品） |

| 端口（gitea-ci） | 服务 | 托管方式 |
|------|------|----------|
| 3000 | Gitea 1.26.4 | systemd `gitea.service`（用户 git，配置 `/etc/gitea/app.ini`） |
| 3100 | 测试环境 Next.js（`pm2 rsdesign-new`，用户 gitea-runner） | PM2 |
| 8091 | Nginx 反代 → 3100 | systemd nginx（`/etc/nginx/sites-available/rsdesign-test`） |
| 4873 | Verdaccio（npm 缓存，上游 npmmirror） | PM2（用户 benque） |
| 1025 / 8025 | Mailpit SMTP / Web UI | systemd `mailpit.service` |
| 5432 | PostgreSQL（仅 Gitea 自身用库；**应用是 SQLite**） | systemd |

> ⚠️ OrbStack 事实：`*.orb.local` 域名 Mac 与 VM 内都可解析；Mac 文件系统在 VM 内挂载于 `/mnt/mac`（root 可读，普通新建用户不一定可穿越）。VM 与 Mac 同生共死——Mac 睡眠 VM 即停，「常驻」要等内网平移才真正成立。

## 2. 账号体系（权限隔离的落点）

| 账号 | 位置 | 用途 | 关键约束 |
|------|------|------|----------|
| `admin` | Gitea | 你本人：合并 PR、管仓库 | 唯一有合并权的角色 |
| `ci-bot` | Gitea | agent 的 API/git 身份 | PAT `agent-20260710`，scopes 仅 `write:issue` + `write:repository`；是仓库 Write 协作者；**被分支保护挡在 main 外** |
| `git` | VM 系统用户 | 跑 Gitea 进程 | — |
| `gitea-runner` | VM 系统用户 | 跑 act_runner + PM2 测试环境 | `/opt/rsdesign-test`、`/opt/artifacts` 属主 |
| `coder` | VM 系统用户 | 跑 agent 脚本与 claude CLI | `~/.agent.env`（600）、linger 已开 |
| `benque` | VM 默认用户 | 运维操作、免密 sudo | 凭据文件在其家目录 |

> 🕳️ 踩坑 #8：**Gitea 管理员创建的用户默认 `must_change_password=true`**——改密前该用户所有 API 返回 403（正文 "You must change your password"）。解法：`PATCH /api/v1/admin/users/{u}`，body 带 `{login_name, source_id, must_change_password:false}`。
>
> 🕳️ 踩坑 #7：**token 管理端点只认 basic auth**。给他人签发：`curl -u "admin:密码" -H "Sudo: ci-bot" -X POST .../api/v1/users/ci-bot/tokens`。

## 3. Gitea（安装要点 + as-built 配置）

- 单二进制 `/usr/local/bin/gitea`（1.26.4），systemd 托管，数据 `/var/lib/gitea`，DB 用本机 PostgreSQL（`gitea` 库）。
- Actions 默认启用（1.21+）。
- 仓库 `admin/rsdesign-new`：公开；默认分支 `main`；**分支保护**：
  - 禁止直接 push（对所有人生效，含 admin——一切走 PR）
  - 必须状态检查通过：context = `CI / test (pull_request)`
- 七个流程标签：`needs-analysis / awaiting-triage / spec-drafting / spec-review / approved / pr-open / deployed`
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
- **host 模式含义**：job 直接以 gitea-runner 身份在 VM 上执行 shell——因此流水线能直接操作本机 PM2 和 `/opt` 目录；代价是构建与测试环境同机（可接受，将来可换 container 模式）。
- 注册 token 可命令行生成：`sudo -u git gitea --config /etc/gitea/app.ini actions generate-runner-token`。
- 工作区在 `/opt/act-runner/.cache/act/<hash>/hostexecutor`，**每个 workflow 一个哈希目录、跨 run 复用**（checkout 会清理）。

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

## 7. 重建/平移冒烟清单

```bash
# 全服务在位
systemctl status gitea act_runner mailpit nginx --no-pager | grep -E "●|Active"
curl -fsS http://127.0.0.1:3000/api/v1/version          # {"version":"1.26.4"}
curl -fsS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:4873/   # 200
curl -fsS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8025/   # 200
sudo -u gitea-runner pm2 list                            # rsdesign-new online
curl -fsS http://127.0.0.1:3100/api/health               # {"status":"ok",...}
curl -fsS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8091/   # 200
# Gitea 后台 Site Administration → Actions → Runners:gitea-ci-runner Idle
```
