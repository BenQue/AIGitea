# 阶段 0 起步清单：OrbStack VM + Gitea + act_runner

> 目标：在开发机（macOS）上用 OrbStack 起一个 Ubuntu VM，把 **Gitea + act_runner + Verdaccio + 测试环境运行时**装好并跑通第一个 CI workflow。跑完这份清单，你的本地原型 CI/CD 中枢就点亮了。
>
> 配套主文档：《软件开发与自动化部署运维平台-方案设计.md》。本清单对应其中的**阶段 0 + 阶段 1（CI 冒烟）**。
>
> 版本锁定：**Gitea 1.26.4**、**act_runner v1.0.7**（2026-07 当前稳定版）。
>
> 约定：命令按从上到下顺序执行。标了 **【手动】** 的是需要在浏览器或交互界面完成的步骤，其余可直接复制粘贴。OrbStack 机器里你的用户默认有免密 `sudo`。

---

## ⚠️ 开始前必读：架构（arch）

OrbStack 在 **Apple Silicon（M 系列）Mac** 上创建的是 **arm64** Linux VM；在 **Intel Mac** 上是 **amd64**。下面所有下载命令都用 `$(dpkg --print-architecture)` 自动取对，你不用手改——但要知道：**下到 VM 里的二进制必须和 VM 架构一致**，别从别处拷一个 amd64 的二进制进 arm64 的 VM。

---

## Part A —【宿主机 macOS】创建 VM

在 macOS 终端执行（先装好 OrbStack.app）：

```bash
# 创建并启动一个 Ubuntu VM，命名 gitea-ci
orb create ubuntu gitea-ci

# 进入 VM 的交互 shell（也可用: ssh gitea-ci@orb）
orb -m gitea-ci
```

> 之后 Part B–H 全部在 **VM 内**执行（即上面进入的 shell 里）。
> 宿主机浏览器访问 Gitea 的地址是 **http://gitea-ci.orb.local:3000** —— OrbStack 自动为每个 VM 分配 `<名字>.orb.local` 域名。

---

## Part B —【VM 内】基础系统

```bash
sudo apt update && sudo apt -y upgrade
sudo apt install -y curl git build-essential postgresql redis-server nginx xz-utils

# Node 20（系统级，供 act_runner / 构建使用）
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
node -v && npm -v   # 记下这个 Node 大版本，后续内网/生产机要一致

# 全局工具
sudo npm i -g pm2 verdaccio

# 确认 PostgreSQL / Redis 已在跑
sudo systemctl enable --now postgresql redis-server
```

---

## Part C —【VM 内】PostgreSQL 建库

给 Gitea 和测试应用各建一个库和用户（密码请自行改强）：

```bash
sudo -u postgres psql <<'SQL'
CREATE USER gitea WITH PASSWORD 'gitea_pw';
CREATE DATABASE gitea OWNER gitea;
CREATE USER app_test WITH PASSWORD 'app_test_pw';
CREATE DATABASE app_test OWNER app_test;
SQL
```

---

## Part D —【VM 内】安装并启动 Gitea + 开启 Actions

```bash
# 1) 下载 Gitea 1.26.4 二进制（架构自动匹配）
ARCH=$(dpkg --print-architecture)
sudo curl -fsSL -o /usr/local/bin/gitea \
  "https://dl.gitea.com/gitea/1.26.4/gitea-1.26.4-linux-${ARCH}"
sudo chmod +x /usr/local/bin/gitea
gitea --version   # 验证能跑

# 2) 建 git 系统用户与数据目录
sudo adduser --system --shell /bin/bash --gecos 'Gitea' --group \
  --disabled-password --home /home/git git
sudo mkdir -p /var/lib/gitea/{custom,data,log}
sudo chown -R git:git /var/lib/gitea/
sudo chmod -R 750 /var/lib/gitea/
sudo mkdir -p /etc/gitea
sudo chown root:git /etc/gitea
sudo chmod 770 /etc/gitea      # 安装向导需要可写；装完再收紧
```

创建 systemd 服务：

```bash
sudo tee /etc/systemd/system/gitea.service >/dev/null <<'UNIT'
[Unit]
Description=Gitea
After=network.target postgresql.service

[Service]
Type=simple
User=git
Group=git
WorkingDirectory=/var/lib/gitea/
ExecStart=/usr/local/bin/gitea web --config /etc/gitea/app.ini
Restart=always
RestartSec=2s
Environment=USER=git HOME=/home/git GITEA_WORK_DIR=/var/lib/gitea

[Install]
WantedBy=multi-user.target
UNIT

sudo systemctl daemon-reload
sudo systemctl enable --now gitea
sudo systemctl status gitea --no-pager   # 应为 active (running)
```

---

## Part E —【手动】Gitea 首次初始化

1. 宿主机浏览器打开 **http://gitea-ci.orb.local:3000**，进入安装向导。
2. **数据库设置**：
   - 类型：`PostgreSQL`
   - 主机：`127.0.0.1:5432`
   - 用户名：`gitea`　密码：`gitea_pw`　数据库名：`gitea`
3. **一般设置**：站点 URL 填 `http://gitea-ci.orb.local:3000/`（其余默认即可）。
4. 展开 **「管理员账号设置」**，直接创建你的管理员账号（例如 `admin`）——比装完再建省事。
5. 点「立即安装」。完成后回到 VM 收紧权限：

```bash
sudo chmod 750 /etc/gitea
sudo chmod 640 /etc/gitea/app.ini
sudo systemctl restart gitea
```

> **Actions 默认已开启**（Gitea 1.21+ 起默认启用）。确认一下 `/etc/gitea/app.ini` 里有（没有就加上再 `sudo systemctl restart gitea`）：
>
> ```ini
> [actions]
> ENABLED = true
> ```

6. 顺手建 agent 用的机器人账号（也可稍后阶段 2.5 再建）：Gitea 右上角 → Site Administration → 用户管理 → 新建用户 `ci-bot`。

---

## Part F —【VM 内】安装并注册 act_runner（host 模式）

```bash
# 1) 下载 act_runner v1.0.7（架构自动匹配）
ARCH=$(dpkg --print-architecture)
sudo curl -fsSL -o /usr/local/bin/act_runner \
  "https://dl.gitea.com/act_runner/1.0.7/act_runner-1.0.7-linux-${ARCH}"
sudo chmod +x /usr/local/bin/act_runner
act_runner --version
# 若上面 404：去 https://gitea.com/gitea/runner/releases 复制对应架构资源链接，
# 若拿到的是 .xz 包，下载后 `xz -d 文件名` 解压再 chmod +x。

# 2) 建 runner 运行用户与工作目录
sudo useradd --system --create-home --home-dir /opt/act-runner --shell /bin/bash gitea-runner

# 3) 从 Gitea 直接生成注册 token（无需进后台点按钮）
TOKEN=$(sudo -u git gitea --config /etc/gitea/app.ini actions generate-runner-token)
echo "runner token = $TOKEN"

# 4) 注册（host 模式：job 直接在宿主机跑，不用 Docker）
cd /opt/act-runner
sudo -u gitea-runner act_runner register --no-interactive \
  --instance http://localhost:3000 \
  --token "$TOKEN" \
  --name gitea-ci-runner \
  --labels ubuntu-latest:host
# 成功后 /opt/act-runner 下会生成 .runner 文件
```

用 systemd 托管 runner：

```bash
sudo tee /etc/systemd/system/act_runner.service >/dev/null <<'UNIT'
[Unit]
Description=Gitea Act Runner
After=network.target gitea.service

[Service]
Type=simple
User=gitea-runner
WorkingDirectory=/opt/act-runner
ExecStart=/usr/local/bin/act_runner daemon
Restart=always
RestartSec=2s
# 让 runner 能找到 node / npm / git
Environment=PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

[Install]
WantedBy=multi-user.target
UNIT

sudo systemctl daemon-reload
sudo systemctl enable --now act_runner
sudo systemctl status act_runner --no-pager
```

回 Gitea 后台 **Site Administration → Actions → Runners**，应能看到 `gitea-ci-runner` 在线（Idle）。

---

## Part G —【VM 内】Verdaccio（npm 缓存代理，弱网救星）

```bash
# 用 pm2 托管 verdaccio（默认端口 4873）
pm2 start verdaccio --name verdaccio
pm2 save
pm2 startup   # 按输出提示执行它给的那条 sudo 命令，实现开机自启
```

配上游走国内镜像做缓存代理：

```bash
mkdir -p ~/.config/verdaccio
tee ~/.config/verdaccio/config.yaml >/dev/null <<'YAML'
storage: ./storage
listen: 0.0.0.0:4873
uplinks:
  npmmirror:
    url: https://registry.npmmirror.com/
packages:
  '@*/*':
    access: $all
    publish: $authenticated
    proxy: npmmirror
  '**':
    access: $all
    publish: $authenticated
    proxy: npmmirror
YAML

pm2 restart verdaccio
curl -s http://localhost:4873/ >/dev/null && echo "Verdaccio OK"
```

> 之后 CI 构建让项目根目录 `.npmrc` 指向它（这行可进仓库）：
> ```ini
> registry=http://localhost:4873/
> fetch-retries=5
> fetch-timeout=120000
> ```

---

## Part H —【手动 + VM 内】冒烟测试：跑通第一个 workflow

目的：验证「push → act_runner 执行 → 绿灯」整条最小链路。

1. **【手动】** 在 Gitea 用你的账号新建一个仓库，例如 `smoke-test`（勾选初始化 README）。
2. 在 VM 里克隆并加一个最小 workflow：

```bash
cd ~
git clone http://gitea-ci.orb.local:3000/<你的用户名>/smoke-test.git
cd smoke-test
mkdir -p .gitea/workflows
tee .gitea/workflows/ci.yml >/dev/null <<'YAML'
name: smoke
on: [push]
jobs:
  hello:
    runs-on: ubuntu-latest      # 对应注册时的 label
    steps:
      - uses: actions/checkout@v4
      - run: node -v
      - run: echo "act_runner 跑通了 ✅"
YAML

git add .
git commit -m "ci: smoke test"
git push
```

> 首次 push 会要求登录，输入你的 Gitea 用户名 + 密码（或个人访问令牌）。

3. **【手动】** 回到 Gitea 仓库页面的 **Actions** 标签，应看到 `smoke` 工作流触发并变绿。看到 `node -v` 输出和那句成功打印，即代表阶段 0 完成。

---

## ✅ 阶段 0 验收清单

- [ ] `orb -m gitea-ci` 能进 VM；宿主机浏览器能打开 `http://gitea-ci.orb.local:3000`
- [ ] Gitea 安装完成，管理员账号可登录，`app.ini` 权限已收紧
- [ ] `systemctl status gitea` / `act_runner` / 均为 running
- [ ] Gitea 后台能看到 `gitea-ci-runner` 在线（Idle）
- [ ] Verdaccio 在 `http://localhost:4873/` 响应，上游指向 npmmirror
- [ ] `smoke-test` 仓库的 Actions 工作流跑出绿灯

全部打勾后，你的本地 CI/CD 中枢就点亮了。下一步（阶段 1–2）是：配 Prisma `binaryTargets` + 写 `pack.sh`/`deploy-local-test.sh` 把真实应用制品化并部到 VM 内测试环境，再起 `prod-sim` VM 彩排离线上生产——这些主文档里都有模板，需要时我再陪你逐段跑。

---

## 常见坑速查

| 现象 | 排查 |
|------|------|
| Gitea 下载 404 | 确认 `dpkg --print-architecture` 值；用它拼 `dl.gitea.com/gitea/1.26.4/gitea-1.26.4-linux-<arch>` |
| act_runner 下载 404 或是 .xz | 去 `gitea.com/gitea/runner/releases` 复制对应架构链接；.xz 包需 `xz -d` 解压 |
| runner 显示 offline | `systemctl status act_runner`；确认 `--instance` 用的是 `http://localhost:3000`，token 未过期（过期就重新 `generate-runner-token` 再 register）|
| workflow 一直 pending | 检查 job 的 `runs-on` label 是否与注册时 `--labels` 里的 `ubuntu-latest` 一致 |
| CI 里 `npm ci` 慢/断 | 项目 `.npmrc` 指到 `http://localhost:4873/`（Verdaccio）；首次拉包仍需联网，之后走缓存 |
| Actions 标签不出现 | `/etc/gitea/app.ini` 加 `[actions] ENABLED=true` 后 `systemctl restart gitea` |

---

*本清单命令中的密码、用户名、仓库名请按实际替换。遇到卡点把报错贴给我，我帮你定位。*
