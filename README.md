# 软件开发与自动化部署运维平台 · 总纲

> 版本：v3.0（通用 Codex runtime candidate）｜ 更新：2026-08-02 ｜ 状态：**Linux PM2 试点与双 provider runtime 已验证；新 Linux Docker-first release contract 为本仓候选，真实 Registry/AppServer/production 尚未验收**
>
> 一句话：**Issue 定义工作，AI Loop 把明确合同做到可审 PR，人决定是否合并；AI 可参与首次非生产部署，生产只运行确定性脚本。**

本文件是全貌与导航；细节在各主题分册。原始设计文档在 [archive/](archive/)，仅作历史参考。v3 的迁移决策与未实施边界见 [09](09-v3平台简化与Loop-Engineering文档改造规划.md)。

---

## 1. 当前状态（2026-08-02）

- ✅ 基础设施：OrbStack 双 VM（gitea-ci / prod-sim）、Gitea 1.26.4 + act_runner + Verdaccio + Mailpit
- ✅ 流水线：PR 触发 CI；合并 main 自动「构建 → 自包含制品 → 部署测试环境 → 健康检查」
- ✅ v2 试点证据：issue #4 已走通三闸门闭环，证明 Issue/文档/PR/部署关联可行
- ✅ 邮件通知：Gitea → Mailpit（演示层），issue/PR 事件自动发信
- ✅ Codex 基础：CLI、认证、skills、AGENTS、sandbox、provider router 已通过 VM 基础验收
- 🟡 私有 Gitea 接入：credential-aware 只读访问、skills-only 安装和固定 `ci-bot` + `write` collaborator gate 已进入 Issue #17 / PR #18 候选；现有仓库只完成只读盘点前置设计，未获批量回补授权，未安装全局稳定版本
- ✅ Claude adapter（Issue #1）：与 Codex 共用 controller/verifier/状态/终态，17 项 parity 测试通过；默认仍 `IMPLEMENT_PROVIDER=none`，真实 VM pilot 未做
- 🟡 v3 文档：Issue 主键、small/complex 双路径、单 PR、单合并闸门、Loop 终态和部署边界已定稿
- 🟡 v3 运行：共享 Codex Loop controller 已在 VM 以 timer 停止、`IMPLEMENT_PROVIDER=none` 的方式验证；rsdesign-new Issue #8 只作为 real complex pilot。中央 source 现提供每项目 profile 和 systemd template，任何项目都必须独立验收后再启用
- ✅ Windows 目标设计：IIS + ASP.NET Core + React `wwwroot` 单制品、PostgreSQL、测试 OpenSSH、生产 SMB + Kerberos WinRM + JEA 的合同已确认
- ✅ 迁移目标设计：本地 Gitea 原型结果一次性交付公司 Gitea；不迁移 Issue/PR；GitHub 只保留本地镜像，与公司无关
- ✅ Windows 快速原型设计：Apple Silicon Mac 使用 VMware Fusion + Windows 11 ARM 调试架构无关部署脚本；不替代 Server 2022 x64 和公司 AD 验收
- 🟡 Linux Docker release contract（Issue #22 candidate）：提供 strict manifest/profile、Registry/offline transports、host-role preflight 和 deterministic deploy/status/rollback；当前只有 fake Docker 与 installer 证据，未安装/启动 Docker daemon，未执行真实 migration、AppServer 部署或 production promotion
- ⏸️ 待办：Windows Server 2022 x64 原型、内网 Runner/依赖缓存、迁移演练、生产 JEA 彩排与 [14](14-Windows部署与迁移验收清单.md) 全量验收

## 2. 三层架构

下图是仍在运行的 PM2/SQLite **as-built legacy 试点**，不是新 Linux 项目的默认目标。新项目
使用受控 builder 一次构建 `linux/amd64` OCI images，由 Gitea Container Registry 或同一
manifest 的 offline bundle 传到独立 test/prod AppServer；`gitea-ci` 只承担 SCM 与明确
批准的 CI/CD 能力，不运行业务容器。

```mermaid
flowchart TB
    subgraph MAC["💻 开发机 Mac(交互层——有人)"]
        DEV["Claude Code / Codex<br/>Issue 澄清·spec/plan·交互开发"]
        BROWSER["浏览器<br/>确认合同·合并最终 PR"]
    end

    subgraph VM1["🖥️ gitea-ci VM(自动化中枢——无人值守)"]
        GITEA["Gitea 1.26.4<br/>仓库/issue/PR/Actions"]
        RUNNER["act_runner(host 模式)<br/>CI + 部署流水线"]
        AGENT["coder 用户<br/>自动分析 + Development Loop（候选已安装，自动实现关闭）"]
        VERD["Verdaccio<br/>npm 缓存"]
        MAIL["Mailpit<br/>邮件捕获"]
        TEST["测试环境<br/>PM2 + Next.js :3100 / Nginx :8091"]
    end

    subgraph VM2["🔒 prod-sim VM(离线生产彩排)"]
        PROD["只收制品<br/>备份→迁移→重启→回滚"]
    end

    DEV -->|"git push 分支 / 开 PR"| GITEA
    BROWSER -->|"确认合同 / 合并 PR"| GITEA
    AGENT -->|"分析 Issue·迭代分支·准备 PR"| GITEA
    GITEA -->|"PR/Push 事件"| RUNNER
    RUNNER -->|"部署制品"| TEST
    RUNNER -.->|"人工触发 promote(rsync)"| PROD
    GITEA -->|"通知邮件"| MAIL
```

## 3. 核心设计原则（不可妥协项）

| # | 原则 | 落点 |
|---|------|------|
| 1 | **一次构建，传不可变制品** | 新 Linux 使用完整 Gitea merge SHA + OCI digests + Compose/architecture checksums；PM2 legacy 使用 tar.gz，Windows 使用 zip；生产只接收测试过的相同字节/identity |
| 2 | **制品与环境配置分离** | Linux `/opt/*/.env`、Windows `shared/config` 等由环境持有；制品不含环境 Secret |
| 3 | **新 Linux Docker-first，PM2 legacy** | builder 一次构建，test/prod 只按 digest pull 或 load；目标机不 build/install/fetch，既有 PM2 应用独立迁移验收前保持不变 |
| 4 | **生产部署 script-only** | AI 可参与首次非生产部署；生产只执行已验证脚本和制品 |
| 5 | **任何变更可逆** | 迁移前备份、releases 多版本保留、健康检查失败可回滚 |
| 6 | **判级、合同与执行分离** | AI 判定有效复杂度；controller 独立校验合同；Loop 不得自行改验收标准或扩大范围 |
| 7 | **只有一个交付闸门** | 最终 PR 合并是唯一交付硬闸门；PR CI 必须绿且只有人能合并 `main` |

## 4. 端到端流程（双路径、单合并闸门）

```mermaid
sequenceDiagram
    autonumber
    actor U as 你(人)
    participant G as Gitea
    participant A as Analyzer / Loop
    participant M as 人 + Mac 会话
    participant R as act_runner(自动)

    U->>G: 提 Issue + needs-analysis
    A->>A: 判断 type 与 contract_effect，执行强制风险规则
    alt 信息不足、冲突或风险边界不明
        A->>G: 写 summary → awaiting-triage（不写 complexity 标签）
        break 合同未明确，本次不进入 Loop
            U->>G: 澄清 Issue 合同 → 重新分析
        end
    else effective_complexity=small
        A->>G: 写 summary + type/* + complexity/small；合同完整则 approved
    else effective_complexity=complex
        A->>G: 写 summary + type/* + complexity/complex + spec-drafting
        U->>M: 收敛决策，写 01-spec.md + 02-plan.md
        M->>G: 文档提交到同一 change/N；合同完整则 approved
    end
    A->>A: 实现→测试→失败分析→修复→再验证
    A->>G: 推 change/N → 最终 PR(Closes #N) → pr-open
    R->>G: PR CI 必须绿；失败反馈给 Loop
    Note over U,G: 【唯一交付闸门】人审核并合并最终 PR
    G->>U: 📬 邮件通知(Mailpit);issue 被 Closes 自动关闭
    alt 变更需要部署
        R->>R: 构建→制品→测试部署→健康检查；生产仅运行已验收脚本
        R->>G: 生命周期改为 deployed
    else 变更明确无需部署
        M->>G: 生命周期改为 completed
    end
```

**实施状态**：AI 自动分析仍可用；共享 Codex Development Loop 候选已完成 synthetic、临时 HOME、VM 禁用式安装和 rsdesign-new real complex pilot，PR #9 已由人合并，合并后两个测试入口健康。该 pilot 只证明通用 controller 能在一个应用工作，不把平台绑定到该仓库。每个目标项目由独立 profile 指定 Gitea 坐标、clone、provider、state 和 worktrees，默认 `IMPLEMENT_PROVIDER=none`。AISoftPlatform 是文档、模板、skills 与 runtime source 仓库，本身不需要应用部署流水线。Claude Code Loop 和生产相关自动操作仍未启用。

标签采用三个正交维度：七个 `type/*` 描述变更是什么，两个 `complexity/*` 记录 AI 判定所需路径，八个流程状态标签描述当前阶段。`completed` 表示最终 PR 已合并且明确无需部署；`deployed` 只表示确定性部署与验证成功，两者互斥。`complexity/small` 不能绕过强制复杂规则；无法安全判级时不添加 complexity 标签。17-label taxonomy 必须对每个接入仓库独立 provision 和读回，不能把其它仓库的外部状态当作平台全局状态。

## 5. 文档导航

| 分册 | 内容 | 读者场景 |
|------|------|----------|
| [01-基础设施-VM-Gitea-Runner](01-基础设施-VM-Gitea-Runner.md) | VM/Gitea/runner/Verdaccio/Mailpit 搭建与账号体系、端口总表 | 重建环境、内网平移 |
| [02-CI与自动部署流水线](02-CI与自动部署流水线.md) | Docker-first 默认合同与 PM2/SQLite as-built legacy 证据 | 改流水线、排部署问题 |
| [03-Issue/Spec/Plan 与单闸门流程](03-Issue-Spec-Plan与单闸门开发流程.md) | small/complex 双路径、文档绑定、标签语义、最终 PR | 日常使用平台 |
| [04-AI 分析与 Development Loop](04-Agent编排与定时任务.md) | analyzer、Loop、verifier、终态、provider adapter | 调整 agent 行为 |
| [05-通知与多人协作](05-通知与多人协作.md) | Gitea mailer、Mailpit、事件覆盖、切真实 SMTP | 配通知、加协作者 |
| [06-运维手册与踩坑集](06-运维手册与踩坑集.md) | 日常命令速查、私有 Gitea 访问、16 条实证踩坑、AI 故障包、凭据位置 | 排障必读 |
| [07-内网与生产平移路线](07-内网与生产平移路线.md) | 原型孵化、结果迁移、权威源切换和 Linux/Windows 双目标 | 规划内网平移 |
| [08-Codex-first 与双工具共存](08-Codex双工具共存与实施.md) | 共享 controller、Codex 验证矩阵、Claude parity 条件 | 接入或切换 provider |
| [09-v3 文档改造规划](09-v3平台简化与Loop-Engineering文档改造规划.md) | v3 决策、影响矩阵、迁移顺序、回滚边界 | 审核或实施 v3 |
| [10-AI Issue 判级与标签计划](10-AI-Issue判级与标签实施计划.md) | 判级、标签和 wrapper 实施记录 | 追溯 analyzer 设计 |
| [11-Codex Loop runtime 计划](11-Codex-Loop运行时实施计划.md) | provider-neutral runtime 与验证计划 | 追溯 Loop 实现 |
| [12-Windows 自动部署方案](12-Windows平台自动部署方案.md) | IIS/.NET/React/PostgreSQL、制品、OpenSSH、SMB/WinRM/JEA | 建设 Windows 交付链 |
| [13-结果迁移与内网切换手册](13-项目结果迁移与内网切换实施手册.md) | 不迁 Issue/PR 的结果基线迁移、重建和切换 runbook | 执行项目迁移 |
| [14-Windows 部署与迁移验收](14-Windows部署与迁移验收清单.md) | 构建、部署、数据库、JEA、切换和灾备证据 | 正式上线验收 |
| [15-Fusion Windows ARM 原型](15-VMware-Fusion-Windows-ARM原型实施手册.md) | Mac 预检、Fusion/Windows 11 ARM、OpenSSH/IIS 脚本调试和 x64 升级边界 | 本地快速原型 |
| [12-Linux GitHub → Gitea 双服务器方案](12-Linux-GitHub-Gitea-双服务器自动部署方案.md) | GitHub 入站候选、内网 PR、Linux 测试与生产分离目标合同 | 建设 Linux 内网交付链 |

## 6. 关键地址速查

| 入口 | 地址 |
|------|------|
| Gitea | http://gitea-ci.orb.local:3000；`admin/rsdesign-new` 仅为现有 as-built/pilot 示例，实际目标由项目 profile 指定 |
| 测试环境应用 | http://gitea-ci.orb.local:8091 |
| Mailpit 收件箱 | http://gitea-ci.orb.local:8025 |
| Verdaccio | http://gitea-ci.orb.local:4873 |
| 凭据文件 | gitea-ci VM `~benque/gitea-ci-credentials.txt`（admin/ci-bot；600） |
| Mac 工作克隆 | `~/Projects/rsdesign-new`（与 RSDesignTool monorepo 完全独立） |

私有仓库检查不得从匿名 API 开始。先解析目标 project profile/remote，再按 [06 §1.1](06-运维手册与踩坑集.md#11-私有-gitea-的只读检查) 使用最小权限 profile、既有 Git credential、VM-local 管理员只读 helper 或已登录浏览器；`404`/`Repository not found` 在认证与 ACL 未核对前不构成“不存在”证据。

本地 Gitea 软件仓库通过 AISoftPlatform skill 初始化、接入或准备部署时，必须先按 onboarding runbook 运行固定 `ci-bot` + `write` collaborator gate，并回读权限、真实 bot 仓库访问和现有 `main` 分支保护。失败终态为 `BLOCKED_EXTERNAL`，不得静默继续。现有仓库的回补必须先给出显式接入清单并由人确认，不得扫描后批量修改全部仓库或平台控制仓库。

## 7. 术语

- **Issue 合同**：Issue、有效评论、summary，以及复杂变更的 spec/plan 共同定义的执行边界
- **Development Loop**：在合同内反复实现、验证、自修复和处理 CI 反馈，直到完成或升级给人
- **`approved`**：合同已明确、允许启动 Loop；不授权合并或部署
- **`change/N`**：Issue N 从分析到最终 PR 共用的单一分支
- **`docs/changes/N/`**：summary、复杂变更的 spec/plan，以及部署/迁移变更的 verification
- **Linux release**：新项目为 `release.json` + digest-pinned OCI images + Compose/architecture checksums；Registry 与 offline bundle 共享同一 release identity
- **PM2 legacy 制品**：`/opt/artifacts/rsdesign-new-<sha>.tar.gz`，只代表既有试点；测过的字节 = 上线的字节
- **Change ID（Windows 目标合同）**：原型 `<项目三字符代码>-NNNN`、正式 `PRD-NNNN`；用于分支、文档、制品和部署记录。现有 runtime 尚未实现该格式
- **权威源切换**：迁移前本地 Gitea 是原型权威源；迁移后公司 Gitea 是唯一正式权威源，GitHub 不进入公司链路
