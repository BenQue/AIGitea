# 14 · Windows 部署与迁移验收清单

> 状态：全部 `NOT RUN`。本文件是未来真实实施时的验收合同和记录模板，不代表任何公司环境已经建成或验证。

## 1. 记录规则

- 每个检查记录环境、命令、时间、执行身份、结果和脱敏证据位置。
- 只有真实运行并得到预期结果后才能标记 `PASS`。
- 无法运行写 `BLOCKED` 并说明外部条件；尚未运行保持 `NOT RUN`。
- Secret、密码、token、私钥和完整数据库连接串不得进入本文或 CI 日志。
- 生产验收由人触发；AI 只能协助分析脱敏证据。

状态枚举：

```text
NOT RUN | PASS | FAIL | BLOCKED
```

## 2. 基线信息

```yaml
application:
project_code:
prototype_change_prefix:
production_change_id:
source_repository:
target_repository:
handoff_tag:
source_commit_sha:
artifact_name:
artifact_sha256:
gitea_version:
runner_version:
windows_server_version:
dotnet_version:
node_version:
postgresql_version:
deployment_contract_version:
verification_date:
```

## 3. Gate A：迁移基线

在 Gate A 之前，可选执行 [15](15-VMware-Fusion-Windows-ARM原型实施手册.md) 的 Fusion Windows 11 ARM 快速原型。该原型使用单独的 `ARM-NN` 记录，只用于早期发现部署脚本缺陷；即使全部通过，也不能把本文件 Gate C–H 标记为 `PASS`。

| ID | 检查 | 状态 | 证据 |
|---|---|---|---|
| A-01 | 本地 `main`、handoff tag 与 manifest SHA 一致 | NOT RUN | |
| A-02 | 公司 `main` 与 handoff SHA 一致 | NOT RUN | |
| A-03 | 必需 tags 和长期分支已迁移 | NOT RUN | |
| A-04 | `git fsck --full` 无错误 | NOT RUN | |
| A-05 | Git LFS 数量、大小和下载验证一致 | NOT RUN | |
| A-06 | submodule 均指向可达的内网目标 | NOT RUN | |
| A-07 | `.gitea/workflows`、部署脚本、migration、测试和 lock files 存在 | NOT RUN | |
| A-08 | 仓库中不存在 `.env`、token、密码、私钥和原型数据库 | NOT RUN | |
| A-09 | 公司 Gitea 无 GitHub mirror、外部 webhook 和本地 PAT | NOT RUN | |
| A-10 | 原型文档和正式 `PRD-NNNN` 命名空间可区分 | NOT RUN | |

建议命令：

```bash
git rev-parse refs/heads/main
git ls-remote <local-url> refs/heads/main
git ls-remote <company-url> refs/heads/main
git fsck --full
git lfs ls-files
git submodule status --recursive
```

## 4. Gate B：Gitea 与 Runner

| ID | 检查 | 状态 | 证据 |
|---|---|---|---|
| B-01 | Gitea 使用公司 FQDN、TLS 和内部 DNS | NOT RUN | |
| B-02 | 组织、团队和最小权限已配置 | NOT RUN | |
| B-03 | `main` 禁止直接 push，只允许人工合并 PR | NOT RUN | |
| B-04 | required status context 与实际 workflow job 名一致 | NOT RUN | |
| B-05 | Windows x64 Runner 与 Gitea 分机 | NOT RUN | |
| B-06 | Runner 使用独立服务账号且不是生产管理员 | NOT RUN | |
| B-07 | Actions 依赖不要求运行时访问 GitHub | NOT RUN | |
| B-08 | NuGet/npm 缓存可从干净工作区命中 | NOT RUN | |
| B-09 | Actions Secret/Variable 在公司重新创建 | NOT RUN | |
| B-10 | Gitea 数据库、repositories、LFS、Packages 和配置已备份 | NOT RUN | |

## 5. Gate C：Windows 构建与制品

| ID | 检查 | 状态 | 证据 |
|---|---|---|---|
| C-01 | `npm ci` 使用 lock file 成功 | NOT RUN | |
| C-02 | React 测试与构建成功 | NOT RUN | |
| C-03 | React 输出已进入 ASP.NET Core `wwwroot` | NOT RUN | |
| C-04 | `dotnet restore` 使用锁定依赖成功 | NOT RUN | |
| C-05 | .NET 单元/集成测试成功 | NOT RUN | |
| C-06 | 空 PostgreSQL migration 验证成功 | NOT RUN | |
| C-07 | `dotnet publish -r win-x64` 成功 | NOT RUN | |
| C-08 | migration bundle 可在测试 Windows 执行 | NOT RUN | |
| C-09 | ZIP、manifest 和 SHA256 已生成 | NOT RUN | |
| C-10 | manifest 中 Change ID、commit SHA、RID 和 migration 正确 | NOT RUN | |
| C-11 | 制品不包含 Secret、环境地址和构建缓存 | NOT RUN | |
| C-12 | Gitea Package 相同版本不能被静默覆盖 | NOT RUN | |

## 6. Gate D：Windows 测试部署

### D1. 主机预检

建议记录：

```powershell
Get-ComputerInfo |
  Select-Object WindowsProductName, WindowsVersion, OsArchitecture,
    CsTotalPhysicalMemory

Get-WindowsFeature Web-Server
Get-Service W3SVC, sshd
dotnet --list-runtimes
Get-Volume
```

| ID | 检查 | 状态 | 证据 |
|---|---|---|---|
| D-01 | Windows Server 2022 x64 版本与资源满足基线 | NOT RUN | |
| D-02 | IIS、Hosting Bundle 和 ASP.NET Core Module 可用 | NOT RUN | |
| D-03 | OpenSSH 使用独立 deploy key 和来源防火墙限制 | NOT RUN | |
| D-04 | `C:\Apps\MyApp` 权限符合最小权限 | NOT RUN | |
| D-05 | 配置、Data Protection keys、日志位于 release 外 | NOT RUN | |
| D-06 | Runner 可上传到 `incoming`，不能任意管理主机 | NOT RUN | |

### D2. 正常发布

| ID | 检查 | 状态 | 证据 |
|---|---|---|---|
| D-07 | ZIP/SHA/manifest 校验成功 | NOT RUN | |
| D-08 | 新 release 解压且旧 release 保留 | NOT RUN | |
| D-09 | PostgreSQL 备份在 migration 前完成 | NOT RUN | |
| D-10 | 计划停机、App Pool 停止和 migration 顺序正确 | NOT RUN | |
| D-11 | `current` junction 指向目标 SHA | NOT RUN | |
| D-12 | App Pool 身份和状态正确 | NOT RUN | |
| D-13 | HTTP health 返回目标 commit SHA | NOT RUN | |
| D-14 | 第一次完整部署成功 | NOT RUN | |
| D-15 | 相同制品第二次执行不破坏环境和数据 | NOT RUN | |

### D3. 故意失败

至少选择一个不损坏真实数据的场景：

- 修改测试副本 SHA256，证明校验失败时不停止当前应用。
- 使用无效外部配置，证明 preflight 失败时不切换。
- 在测试 migration 中注入可恢复失败，证明不切换 release。
- 让新版本 health endpoint 返回失败，证明应用回切。

| ID | 检查 | 状态 | 证据 |
|---|---|---|---|
| D-16 | 故意失败被正确检测 | NOT RUN | |
| D-17 | 当前稳定应用未被错误替换 | NOT RUN | |
| D-18 | 回滚后 health 和 commit SHA 正确 | NOT RUN | |
| D-19 | 部署记录明确标记失败与回滚结果 | NOT RUN | |

## 7. Gate E：PostgreSQL

| ID | 检查 | 状态 | 证据 |
|---|---|---|---|
| E-01 | 生产 Web 与 PostgreSQL 分机 | NOT RUN | |
| E-02 | PostgreSQL TLS 和来源地址限制生效 | NOT RUN | |
| E-03 | runtime、migrator、backup 三类角色分离 | NOT RUN | |
| E-04 | 应用运行身份不能执行 schema migration | NOT RUN | |
| E-05 | migration 不在应用启动时自动执行 | NOT RUN | |
| E-06 | `pg_dump` 备份成功并记录 backup ID | NOT RUN | |
| E-07 | 备份已在隔离测试库真实恢复 | NOT RUN | |
| E-08 | expand/contract 允许新旧应用兼容 | NOT RUN | |
| E-09 | 应用回滚不自动覆盖生产数据库 | NOT RUN | |

## 8. Gate F：生产传输与 JEA

| ID | 检查 | 状态 | 证据 |
|---|---|---|---|
| F-01 | 批准制品由部署控制端下载并验证 SHA256 | NOT RUN | |
| F-02 | SMB 只允许部署身份写入专用 `incoming` | NOT RUN | |
| F-03 | 制品先落生产本地，再启动 WinRM/JEA | NOT RUN | |
| F-04 | WinRM 使用 FQDN 和 Kerberos，不使用 IP/Basic | NOT RUN | |
| F-05 | JEA Endpoint 只授权指定 AD 组 | NOT RUN | |
| F-06 | JEA 只暴露安装、状态、健康和回滚函数 | NOT RUN | |
| F-07 | 通用 PowerShell、cmd 和任意文件写入被拒绝 | NOT RUN | |
| F-08 | JEA transcript 已启用且不泄漏 Secret | NOT RUN | |
| F-09 | 生产 IIS 不含 Git、SDK、Node、Runner、AI 和 AI 凭据 | NOT RUN | |
| F-10 | 生产使用与测试完全相同的 ZIP/SHA256 | NOT RUN | |

## 9. Gate G：权威源切换

| ID | 检查 | 状态 | 证据 |
|---|---|---|---|
| G-01 | 本地 Gitea 已冻结正式项目写入 | NOT RUN | |
| G-02 | 本地 Gitea 最终 bundle/备份已归档 | NOT RUN | |
| G-03 | 公司 `main`、tag 和 handoff manifest 已最终对账 | NOT RUN | |
| G-04 | Mac `origin` 指向公司 Gitea | NOT RUN | |
| G-05 | Mac `prototype` 仅保留本地历史，可选 | NOT RUN | |
| G-06 | Mac 已完成一个公司分支和 PR | NOT RUN | |
| G-07 | 公司 CI、邮件和权限在该 PR 上生效 | NOT RUN | |
| G-08 | 公司 Gitea 与 GitHub 无任何 mirror/webhook | NOT RUN | |
| G-09 | 已宣布公司 Gitea 为唯一正式权威源 | NOT RUN | |

## 10. Gate H：备份与灾难恢复

| ID | 检查 | 状态 | 证据 |
|---|---|---|---|
| H-01 | Gitea PostgreSQL 备份可恢复 | NOT RUN | |
| H-02 | repositories、LFS、attachments 和 Packages 可恢复 | NOT RUN | |
| H-03 | Gitea 配置和实例密钥纳入受控备份 | NOT RUN | |
| H-04 | 应用制品和部署记录可恢复 | NOT RUN | |
| H-05 | 生产 PostgreSQL 恢复时间和责任人已验证 | NOT RUN | |
| H-06 | 公司 Gitea 接受新工作后的回退边界已记录 | NOT RUN | |

## 11. 执行结果模板

每项真实检查使用：

```markdown
### Check D-14

- Status: NOT RUN
- Environment:
- Commit SHA:
- Artifact SHA256:
- Executed by:
- Started at:
- Finished at:
- Command/check:
- Expected:
- Actual:
- Evidence:
- Secrets redacted: YES/NO
- Follow-up:
```

## 12. 独立 Review 要求

Claude Code 与 Codex 的 provider parity 只证明两者能复用同一 controller、verifier、状态和终态，不证明 Windows 部署实现正确。任何 Windows workflow、PowerShell module、OpenSSH、SMB、WinRM/JEA 或 PostgreSQL migration 实现都必须经过独立 review。

| Review 层 | 必查内容 | 通过条件 |
|---|---|---|
| 合同 review | 是否符合 [12](12-Windows平台自动部署方案.md) 和 [13](13-项目结果迁移与内网切换实施手册.md) | 没有未声明的范围或安全例外 |
| 代码 review | workflow、PowerShell、manifest/hash、错误处理、幂等和日志脱敏 | Reviewer 不是本次实现的唯一作者，阻断项清零 |
| 安全 review | Runner 权限、Secret、SMB ACL、Kerberos、JEA Role Capability、transcript、数据库角色 | 最小权限和拒绝路径有证据 |
| 集成 review | Windows Server 2022、IIS、OpenSSH、PostgreSQL 的真实执行结果 | Gate C–E 通过，不能只靠 mock |
| 生产准备 review | 同制品晋级、备份恢复、计划停机、回滚、监控和责任人 | Gate F–H 通过并由人批准 |

推荐让 Claude Code 或 Codex 中的一个负责实现，另一个结合人工审核负责独立 review；不能让同一实现会话自行宣布生产就绪。Review 发现的问题必须通过新的提交修复并重新运行受影响的 Gate。

当前仓库只完成 Windows 目标文档，没有 Windows workflow、PowerShell module 或公司环境执行证据，因此当前只能进行设计 review，不能进行实现或生产准备 review。

## 13. 发布批准

```yaml
repository_migration: NOT RUN
internal_ci: NOT RUN
test_deploy_first: NOT RUN
test_deploy_second: NOT RUN
deliberate_failure_and_rollback: NOT RUN
database_restore: NOT RUN
smb_winrm_jea: NOT RUN
production_rehearsal: NOT RUN
authority_cutover: NOT RUN
approved_for_production: false
approved_by:
approved_at:
```

`approved_for_production` 只有在人审核全部适用证据后才能改为 `true`。
