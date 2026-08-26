---
name: aisoft-platform
description: AISoft 自托管交付平台（v3.6）的合同与操作入口。Use when 在已接入项目上开发/修复/部署（NewEMaint、SFMDigitalBoard、HSDB、WMPDA、SapTableMigrate、rsdesign-new、myapp、smoke-test）、接入新项目到平台、走 Issue→triage→spec/plan→实现→PR→部署流程、或排查平台 CI/部署/agent 问题。触发词：AISoft、AIGitea、gitea-ci、Gitea Issue、判级、small/complex、Development Loop、host-access broker、docker-release、architecture lock、部署失败、接入平台。
---

# AISoft 自托管交付平台（v3.6）

自托管的「Issue → AI 分析判级 →（small 直进 / production complex 先 spec/plan / development complex 用 Issue 验收合同）→ 提交确认 → 单 PR → manual 人工合并 / eligible routine small 受控合并 → 独立部署授权」平台。核心原则：**Issue 定义工作，AI 把明确合同做到最终 PR；人确认提交，manual 由人合并，routine small 只由独立 merger 在最终 head 全硬门后合并；部署不由 merge 授权。**

**权威文档**：Mac 用 `~/MyDocs/AISoftPlatform/`；gitea-ci VM 用 `/mnt/mac/Users/benque/MyDocs/AISoftPlatform/`（**不是 `~/Documents/`**——macOS TCC 挡 /mnt/mac，2026-07-19 迁出）。README=总纲 · 03 流程 · 04 Matt 编排与 Loop · 06 运维踩坑与 broker · 08 双工具 · 12-Linux 内网交付 · architecture/ 与 docker-release/ 子合同。改配置前先读对应分册。

## 现行合同（v3.6，#208 governance source）

- **可读命名元组**：新变更 = Issue `N` + 分支 `change/N-短描述` + 目录 `docs/changes/N-短描述/` + worktree `issue-N-短描述` + 唯一 PR（`Closes #N`）。编号仍是唯一主键；remote/history evidence 已存在的 `change/N`、`docs/changes/N/` 与 pre-#57 纯数字文档只作读取或维护兼容，新 writer、first push 和 first PR 不得创建。
- **语义文档**：新文档名 `<role>-<短描述>-<YYMMDD>.md`，summary front matter 的 `documents` 字段映射 summary/spec/plan/verification 到真实文件名。解析用 `PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli resolve-documents N --repo <checkout>`，不要 glob 猜。
- **判级**：contract_effect 先行（restore/unchanged → small 候选；add/change → complex；unclear → 人工澄清）。功能新增/变更、schema/迁移、外部契约、安全、共享核心、跨模块、CI/制品/部署/回滚、Agent/治理一律强制 complex。small 还须范围局部、可简单 revert，并有可测验收标准。
- **Matt 主路径**：每个 Issue 走 `$triage #N` → production complex `$to-spec #N` → `$to-tickets #N` → `$implement #N Txx`（经 `$aisoft-matt-workflow` 适配；small 与 development complex 在 triage+summary+判级+`approved` 复核后跳过 spec/plan，后者使用合成 `T01`）。`triage/ready-for-agent` ≠ `approved`。
- **27 标签四维正交**：10 `type/*`（bugfix/feature/docs/test/refactor/maintenance/platform/security/reliability/data）+ 2 `complexity/*`（AI 输出）+ 8 生命周期（`completed` 与 `deployed` 互斥终态）+ 7 `triage/*`（Matt 编排）。
- **单闸门**：最终 PR merge 是唯一交付硬闸门。manual 只由人合并；只有 repository 显式 opt-in、required contexts 非空、提交确认授权且最终 head 全硬门通过的 routine small，才能由独立 per-project merger 合并。provider/project agent 不 merge、不直推受保护 `main`；部署需独立授权。
- **一切 Gitea/Git/OrbStack 访问走 broker**：`/usr/local/libexec/aisoft/host-access-broker --project <manifest项目> --operation <typed操作>`（gitea.issue.create/read/update、gitea.pull.create、git.push.change --branch、host.access.audit…）。不拼 raw token、不传 URL/refspec/shell；Git push 只允许当前 checkout 同名 readable 分支。
- **provider 默认关**：`IMPLEMENT_PROVIDER=none` 是默认；启用是每项目独立验收门。
- **部署边界**：AI 可参与开发/测试环境首次部署并固化为脚本（两次幂等 + 一次故意失败回滚）；生产只跑已验证脚本。新 Linux 默认 docker-release/v2（NewEMaint 为参照实现），PM2 是受支持的选项路径；各项目技术方案可不同，流程与指导思想全平台一致。

## 会话标准动作（Mac 交互开发，最常见）

> **会话本身的编排**（一 Issue 一会话、提交 PR 确认、manual/routine 分流、merge 后收尾与归档确认）见 `issue-session-flow` skill；本段只覆盖单个会话内部到 PR candidate 为止的动作。

1. 需求/缺陷 → broker `gitea.issue.create`（正文写可测验收标准）。
2. `python3 -m aisoft_loop.cli change-name N <slug>` 校验命名 → `git worktree add /private/tmp/issue-N-<slug> -b change/N-<slug> origin/main`（并行会话必须各自 worktree；commit 前 `git branch --show-current` 核对——踩坑 #15）。
3. 按判级与 `change_control` 写映射文档（production complex 补 spec/plan；development complex 从 Issue 读取验收标准并用合成 `T01`），实现 + 测试全绿（改 shell 后跑 `bash codex/tests/smoke.sh`）。`verification` 由证据能否经 diff review + required CI 重放决定，不等同部署。summary 此时写**真实的**前置 `status`（通常 `approved`），`pr_url` 留空——PR 还不存在。
4. 判级投影，**窗口在合并时关闭**：`codex/tools/apply-classification-labels.sh N` 先看计划，
   确认后 `--apply` 经 broker `gitea.issue.labels.classify` 把 summary 的 `change_type` 与
   `effective_complexity` 写成 Gitea 的 `type/*` 与 `complexity/*`（#160）；再用
   `--verify N` 读回确认。计划模式对「已投影」与「从没投影过」输出逐字相同，
   `--verify` 是唯一能区分两者的检查，只在两个维度都读回 `projected` 时退 0（#167）。
   Issue 一旦被合并转 closed，工具永久拒绝补写且没有 override，`--verify` 只会报
   `projection-window-closed`——所以这一步必须在开 PR 到合并之间做完。
   报 `broker-operation-missing` = 本机 broker 是安装期旧表、**不是**权限问题，
   两台重装 `sudo bash codex/install-host-access-broker.sh` 后重跑（06 踩坑 20）。
   不做这一步，判级就只活在文档里、Gitea 上看不见也检索不到——`apply-analysis` 只在
   Loop 内跑，交互会话不经过它。生命周期与 `triage/*` 标签不受影响。
5. commit 与本地验证完成后先进入 `AWAITING_PR_CONFIRMATION`，输出绑定 exact Issue、branch 与
   `manual|routine-auto` policy 的 PR candidate。routine 文本必须明确“当前合同内 CI 修复可继续，最终
   head 的 required CI 全绿且全部硬门通过后，允许受控自动合并”；manual 文本不得包含该 marker。
   用户确认后才 broker `git.push.change --branch change/N-<slug>` → broker `gitea.pull.create --issue N`（正文含 `Closes #N` 与文档链接）→
   `PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli backfill-pr-url N --repo <checkout> --pr-url <PR URL>`
   把 `pr_url` 与 `status: pr-open` 一起写进 summary（#142；只写 summary，spec/plan/verification 不带该键），再 commit + push 一次。**到开 PR 为止。**
   该命令幂等：值已正确时一个字节都不写；出现第二个不同的 `pr_url` 会 fail-closed 报错而不是覆盖。
   自查用 `python3 -m aisoft_loop.cli check-change-documents --repo <checkout>`——它对每个 change 目录断言 `resolve-documents` 成功，并拦住「`status: pr-open` 但 `pr_url` 为空」这种静默漏做。
6. push 报 `BASE_BRANCH_STALE` = 分支不是基于最新 `main`（`main` 在你开分支后前进了）→
   broker `git.fetch.main` 取新基线 → 本地 `git rebase origin/main` → broker
   `git.push.change --branch change/N-<slug>` 重推。#136 起推送使用
   `--force-with-lease=refs/heads/<branch>:<remote-sha>`，rebase 重写出的历史推得上去；
   在此之前 rebase 会让已推送的分支永久推不动（三条约束互锁，见 `06` broker 段落）。
   **remote 访问始终只走 broker**——不直接 `git fetch`/`git push`；rebase 是本地操作，不受此限。
7. push 报 `REMOTE_BRANCH_MOVED` = 远端 change 分支在 broker 读取 lease 之后被改动，
   **推送已被拒绝，远端没有被覆盖**。处置是 broker `git.fetch.change --branch change/N-<slug>`
   看清远端到底改了什么再决定（多半是同一 Issue 有第二个写者，或分支被人工改过），
   不要试图用更强的 force 绕过去——lease 拒绝是保护，不是需要压制的噪声。

## 工具分工（默认偏好，非硬规则）

- **Codex（默认主处理者）**：从 Issue 分析、合同、实现、测试、PR/CI 修复到待合并交接的完整路径。
- **Claude Code（对等补位）**：复杂设计讨论、专项复核、既有 Claude 会话延续，或项目 profile 显式选择的 provider 工作。
- 二者共用同一平台合同与 provider 中立机制（`ANALYSIS_PROVIDER`/`IMPLEMENT_PROVIDER` 按项目 profile 显式选择），随时可互换补位，但不各自发明流程。

## 接入新项目 / 项目对齐 / 私有访问

- 新项目接入：先读 [references/onboarding-runbook.md](references/onboarding-runbook.md)——governance manifest + project-agent gate、host-role gate、architecture 声明、CI/部署与验收顺序都有既定约定，不得跳步。
- 项目对齐（初始化=更新，幂等）：入口 [references/project-align.md](references/project-align.md)——checklist 盘点缺口、逐项走目标仓独立 Issue/AI 判级的单一 PR；确定性核对用 `codex/tools/aisoft-project-check.sh --repo <checkout>`（PASS/GAP，只读）。
- 私有 Gitea 检查：先读 [references/private-gitea-access.md](references/private-gitea-access.md)；**匿名 404 不构成不存在证据**（private-repository `404` 歧义），按 authenticated ladder 走。

## Common Mistakes

- 用数字命名新建分支/文档（`change/N`、`00-summary.md`）——新写入会被 fail-closed 拒绝；readable 元组才是现行合同。
- 绕过 broker 直接 `git push`/裸 token `curl`——治理写路径只认 broker typed 操作。
- 把 `triage/ready-for-agent`、green CI 或 Issue `approved` 当成 routine 授权——提交确认、repository opt-in 与 final-head 全硬门缺一不可，部署仍需独立授权。
- 让 provider/project agent 自己 merge，或把空 contexts/public-platform 设为 routine enabled——必须 fail closed；source merged 也不等于 credential/protection/live 已 apply。
- 把 routine merge receipt 当成部署授权或 `deployed` 证据——merge 不调用 deploy，也不传递生产授权。
- 把判级投影留到收尾再补——窗口在合并时关闭，closed Issue 永久拒绝补写；进入待合并前必须用 `apply-classification-labels.sh --verify N` 读回 `projected`（#167）。
- 把 broker 的 `REQUEST_DENIED / not allowlisted` 当权限问题查——那是安装期操作表陈旧，两台重装即可（06 踩坑 20）。
- 在共享 checkout 并行开会话不建 worktree——HEAD 是全局可变状态，B 的 commit 会落进 A 的分支（踩坑 #15）。
- 从 rsdesign-new 或任何示例推断目标仓库/端口/部署合同——一切以显式 project profile/manifest 为准。
- 把平台 candidate/参照实现写成业务已部署——NewEMaint 的 DockerLab 证据不等于其它项目或生产完成。
