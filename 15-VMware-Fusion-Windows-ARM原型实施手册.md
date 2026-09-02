# 15 · VMware Fusion + Windows 11 ARM 快速原型实施手册

> 定位（#232，2026-09-02）：本册是交付形态参考（按项目选用），适用环境：Windows（Mac 本地原型）。它不是任何项目部署步骤的事实源；平台只给环境级原则（`skill-for-codex/references/onboarding-runbook.md` §4），具体步骤、脚本、参数与环境差异由项目仓自行声明与实现。正文原样保留，去留由后续「过时文档清理」Issue 处置。

> 状态：Mac 主机预检已完成；VMware Fusion、Windows 11 ARM 和来宾机环境均 `NOT RUN`。本文只建设部署脚本快速调试层，不替代 Windows Server 2022 x64 或公司 AD 环境验收。

## 1. 定位与退出条件

本层的目标是让 Mac 开发机可以低成本、可快照地调试 Windows 部署状态机：

```text
Mac / 本地 Gitea / OrbStack PostgreSQL
                 |
                 v
VMware Fusion + Windows 11 Pro ARM
IIS + ASP.NET Core Hosting Bundle + OpenSSH + PowerShell
```

适合验证：

- IIS 站点、App Pool、ASP.NET Core Module 和 React `wwwroot` 单制品。
- OpenSSH 上传与固定 PowerShell 入口。
- ZIP、SHA256、manifest、`releases`、`current` junction 和外部配置。
- 首次部署、重复部署、健康检查、故意失败和应用回滚。
- PowerShell module 的幂等性、错误处理、结构化日志与 Secret 脱敏。

不在本层声明通过：

- Windows Server 2019/2022 x64 行为、`win-x64` 最终制品和 x64 Runner。
- Windows Server Feature、Server Core、域加入、GMSA 或生产组策略。
- SMB + Kerberos WinRM + JEA 的 AD 信任链。
- PostgreSQL Windows x64 安装、备份恢复和正式兼容性。
- 生产容量、性能、安全加固或生产就绪。

退出条件是部署核心脚本在 ARM 原型中通过正常路径和故意失败路径，然后将同一份架构无关 PowerShell module 带到 Windows Server 2022 x64 重新验收。

## 2. 当前 Mac 预检记录

2026-07-18 的只读检查结果：

| 项目 | 结果 | 判断 |
|---|---|---|
| CPU 架构 | Apple Silicon `arm64`，Apple M4 Pro | 只能运行 ARM64 Windows 来宾机，不能把 x64 Server 来宾机作为正式模拟 |
| CPU / 内存 | 14 cores / 48 GB | 满足单台 Windows 11 ARM 原型 |
| 可用磁盘 | 约 175 GiB | 可建立 100–120 GB 稀疏磁盘；需限制快照和保留至少 40 GB 主机余量 |
| VMware Fusion | 未安装 | 需要从 Broadcom 官方入口人工下载 |
| Homebrew | 已安装 | 当前不存在可用 `vmware-fusion` cask，不能以此作为安装合同 |

建议首台 VM：

| 资源 | 建议 |
|---|---|
| vCPU | 4；构建较慢时可升到 6 |
| 内存 | 8 GB；同时运行 IDE/浏览器时最多 12 GB |
| 系统盘 | 100 GB 稀疏磁盘；安装 SDK/Node 后空间不足再扩容 |
| 网络 | NAT；为来宾机固定 DHCP lease 或记录稳定地址 |
| 剪贴板/共享目录 | 初期关闭共享目录部署，强制经 OpenSSH 验证真实通道 |

## 3. 人工下载入口与安全边界

VMware Fusion 的免费下载需要 Broadcom Support Portal 登录、资料/贸易合规确认和条款接受。这些步骤由人完成，自动化脚本不得代替用户接受协议、抓取受限下载或使用非官方镜像。

人工准备两个文件：

1. Broadcom 官方 VMware Fusion 通用 DMG，支持 Apple Silicon。
2. Microsoft 官方 Windows 11 Arm64 ISO。

推荐保存到：

```text
~/Downloads/VMware-Fusion.dmg
~/Downloads/Windows11_Arm64.iso
```

下载后先记录来源、版本和 SHA256：

```bash
shasum -a 256 ~/Downloads/VMware-Fusion.dmg
shasum -a 256 ~/Downloads/Windows11_Arm64.iso
```

不要把 DMG、ISO、Windows 产品密钥或 Broadcom 凭据提交到 Gitea。

## 4. 安装与 VM 建立步骤

### 4.1 安装 Fusion

1. 从官方 DMG 启动安装。
2. 在 macOS 管理员提示中由人确认安装和必要系统权限。
3. 首次启动后记录 Fusion 完整版本。
4. 不启用不需要的宿主机目录共享或来宾机管理员自动登录。

### 4.2 安装 Windows 11 Pro ARM

1. 新建 VM，选择 Microsoft 官方 Arm64 ISO。
2. 按第 2 节分配资源，使用 NAT 网络。
3. 安装 Windows 11 Pro ARM，完成更新并激活合法许可证。
4. 创建独立本地管理员用于 bootstrap；部署测试另建最小权限身份。
5. 安装 VMware Tools，确认网络、时间同步和关机功能正常。

### 4.3 快照策略

只保留少量可解释快照：

```text
00-clean-windows
01-iis-openssh
02-dotnet-powershell
03-first-deploy-ready
```

每次快照前正常关机；完成一个稳定里程碑后删除被替代的旧中间快照，避免耗尽 Mac 磁盘。快照不是备份，核心脚本和配置样例仍必须提交到 Gitea。

## 5. Windows 来宾机 bootstrap

目标组件：

- IIS、Management Tools、WebSocket/静态内容等应用确实需要的组件。
- 与项目目标 .NET 版本匹配的 Windows Arm64 ASP.NET Core Hosting Bundle。
- Windows OpenSSH Server。
- PowerShell 7 Arm64。
- Git 仅用于原型调试；部署过程不得依赖目标机 `git pull`。
- Node.js Arm64 和 .NET SDK 仅在需要验证本机构建时安装；正式生产 IIS 不安装它们。

执行顺序：先启用 IIS，再安装 Hosting Bundle；如果顺序相反，修复或重装 Hosting Bundle，确保 ASP.NET Core Module 正确注册。安装后记录：

```powershell
Get-ComputerInfo |
  Select-Object WindowsProductName, WindowsVersion, OsArchitecture,
    CsTotalPhysicalMemory

Get-WindowsOptionalFeature -Online -FeatureName IIS-WebServerRole
Get-Service W3SVC, sshd
dotnet --list-runtimes
pwsh --version
```

原型目录沿用正式合同：

```text
C:\Apps\MyApp\
├── incoming\
├── releases\<commit-sha>\
├── current\
├── shared\config\
├── shared\data-protection\
├── shared\logs\
├── backups\
└── state\
```

## 6. 网络与本地服务

Windows VM 需要访问：

- Mac/OrbStack 中的本地 Gitea。
- 作为临时外部数据库的 OrbStack PostgreSQL。
- 必要的依赖源；可复现后应尽量切本地缓存。

`*.orb.local` 在 Windows 来宾机中不保证可解析。正式调试前应选择一种稳定方式并记录：

1. 在来宾机 hosts 中绑定当前可达地址；地址变化时同步更新。
2. 建立开发 DNS，将 Gitea/PostgreSQL 映射到稳定名称。
3. 使用经过验证的 Mac/OrbStack 可达地址，但不能把该地址写进制品。

必须从 Windows VM 内部验证 DNS、TCP 和 HTTP，而不能只从 Mac 验证：

```powershell
Resolve-DnsName <gitea-host>
Test-NetConnection <gitea-host> -Port 3000
Test-NetConnection <postgres-host> -Port 5432
Invoke-WebRequest http://<gitea-host>:3000/api/healthz
```

OpenSSH 从 Mac 或 Runner 到 Windows VM 的入口必须使用独立 key；管理员登录只用于 bootstrap，不作为部署常态。

## 7. ARM 原型制品合同

原型允许构建：

```text
MyApp-XXX-0001-<commit-sha>-win-arm64.zip
```

manifest 必须明确：

```json
{
  "runtimeIdentifier": "win-arm64",
  "validationTier": "fusion-windows11-arm-prototype"
}
```

`win-arm64` 原型和 `win-x64` 正式制品不是同一字节，不能把 ARM 测试结果冒充“测试制品直接晋级生产”。应保持相同的源码 commit、manifest schema、目录结构和部署 module，再由公司 Windows x64 Runner 构建 `win-x64`，完成 Windows Server 2022 测试后才建立“同一 x64 ZIP 晋级生产”的证据。

部署核心应只依赖 PowerShell、IIS 管理接口、文件系统和 manifest，不根据 CPU 架构复制两套状态机。RID 差异只属于构建/bootstrap 和制品校验。

## 8. PostgreSQL 原型策略

Fusion 原型默认连接 OrbStack 中的 PostgreSQL，不在 Windows 11 ARM 中建立正式数据库基线。这样可以先验证：

- 外部配置注入和连接失败的 fail-closed 行为。
- migration bundle 的执行顺序和独立 migrator 身份。
- migration 前备份调用接口、部署日志和失败停止。

原型数据必须是可丢弃测试数据。Windows PostgreSQL x64、TLS、角色隔离、`pg_dump`/恢复仍在 Windows Server 2022 x64 或公司测试数据库中重新验收。

## 9. 最小验证矩阵

| ID | 场景 | 预期 |
|---|---|---|
| ARM-01 | 首次安装 | 创建 release、junction、IIS 站点，health 返回目标 SHA |
| ARM-02 | 重复执行同一制品 | 幂等成功，不破坏配置、数据或当前版本 |
| ARM-03 | 修改 ZIP/SHA256 | 切换前失败，当前应用继续健康 |
| ARM-04 | 缺失/无效外部配置 | preflight 失败，不停当前 App Pool |
| ARM-05 | 可恢复的 migration 失败 | 不切换 release，记录失败与备份 ID |
| ARM-06 | 新版本 health 失败 | 回切上一 junction，health 与 SHA 恢复 |
| ARM-07 | 日志检查 | 不含 token、密码、私钥或完整连接串 |
| ARM-08 | OpenSSH 最小权限 | 部署身份能调用固定入口，不能任意管理主机 |

每项保留脱敏的命令、时间、commit SHA、artifact SHA256、预期、实际和日志路径。当前全部 `NOT RUN`。

## 10. 升级到 x64 与公司环境

```text
Fusion / Windows 11 ARM
    部署脚本快速迭代
          |
          v
Hyper-V / Windows Server 2022 x64
    IIS + OpenSSH + win-x64 + PostgreSQL 正式非生产验证
          |
          v
公司 AD 环境
    SMB + Kerberos WinRM + JEA + 生产彩排
```

进入 x64 层时必须重新执行 [14](14-Windows部署与迁移验收清单.md) Gate C–E；进入公司层时继续执行 Gate F–H。ARM 层只提供早期缺陷发现证据，不降低任何正式 Gate。

## 11. 回滚与清理

- Fusion 安装失败：退出安装，不修改仓库；保留官方 DMG 的 SHA256 以便排查。
- Windows bootstrap 失败：回到最近稳定快照，而不是在未知状态上继续叠加修改。
- 部署测试失败：保持当前 junction，不自动恢复测试数据库；使用测试备份重建可丢弃数据库。
- 磁盘不足：关闭 VM，删除确认无用的旧快照或扩容；不得直接删除未知 `.vmwarevm` 内容。
- 放弃原型：先导出必要的脱敏证据和脚本提交，再由人确认后删除 VM。

## 12. 官方参考

- [Broadcom：下载与许可 VMware Desktop Hypervisor](https://knowledge.broadcom.com/external/article/368667/download-and-license-vmware-desktop-hype.html)
- [Broadcom：下载免费软件需要的 Portal 步骤](https://knowledge.broadcom.com/external/article/397417/downloading-free-software-from-the-broad.html)
- [Broadcom：下载和安装 VMware Fusion](https://knowledge.broadcom.com/external/article/315638/download-and-install-vmware-fusion.html)
- [Broadcom：Fusion on Apple Silicon 兼容性](https://knowledge.broadcom.com/external/article?legacyId=90364)
- [Microsoft：Windows 11 Arm64 ISO](https://learn.microsoft.com/en-us/windows/arm/iso)
- [Microsoft：Windows on Arm 概览](https://learn.microsoft.com/en-us/windows/arm/overview)
- [Microsoft：ASP.NET Core on IIS](https://learn.microsoft.com/en-us/aspnet/core/host-and-deploy/iis/)
