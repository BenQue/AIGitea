---
name: aisoft-platform
description: AISoft 自托管交付平台（v3.4）的合同与操作入口。Use when 在已接入项目上开发/修复/部署（NewEMaint、SFMDigitalBoard、HSDB、WMPDA、SapTableMigrate、rsdesign-new、myapp、smoke-test）、接入新项目到平台、走 Issue→triage→spec/plan→实现→PR→部署流程、或排查平台 CI/部署/agent 问题。触发词：AISoft、AIGitea、gitea-ci、Gitea Issue、判级、small/complex、Development Loop、host-access broker、docker-release、architecture lock、部署失败、接入平台。
---

# AISoft 自托管交付平台（v3.4）

自托管的「Issue → AI 分析判级 → (small 直进 / complex 先 spec/plan) → 单 PR → 人合并 → 确定性部署」平台。核心原则：**Issue 定义工作，AI 把明确合同做到可审 PR，人决定是否合并；AI 可参与开发/测试环境首次部署并把流程固化为脚本，生产只运行已验证脚本且没有 AI。**

**权威文档**：Mac 用 `~/MyDocs/AISoftPlatform/`；gitea-ci VM 用 `/mnt/mac/Users/benque/MyDocs/AISoftPlatform/`（**不是 `~/Documents/`**——macOS TCC 挡 /mnt/mac，2026-07-19 迁出）。README=总纲 · 03 流程 · 04 Matt 编排与 Loop · 06 运维踩坑与 broker · 08 双工具 · 12-Linux 内网交付 · architecture/ 与 docker-release/ 子合同。改配置前先读对应分册。

## 现行合同（v3.4，#57/#60/#75 后）

- **可读命名元组**：新变更 = Issue `N` + 分支 `change/N-短描述` + 目录 `docs/changes/N-短描述/` + worktree `issue-N-短描述` + 唯一 PR（`Closes #N`）。编号仍是唯一主键；remote/history evidence 已存在的 `change/N`、`docs/changes/N/` 与 pre-#57 纯数字文档只作读取或维护兼容，新 writer、first push 和 first PR 不得创建。
- **语义文档**：新文档名 `<role>-<短描述>-<YYMMDD>.md`，summary front matter 的 `documents` 字段映射 summary/spec/plan/verification 到真实文件名。解析用 `PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli resolve-documents N --repo <checkout>`，不要 glob 猜。
- **判级**：contract_effect 先行（restore/unchanged → small 候选；add/change → complex；unclear → 人工澄清）。功能新增/变更、schema/迁移、外部契约、安全、共享核心、跨模块、CI/制品/部署/回滚、Agent/治理一律强制 complex。small 还须范围局部、可简单 revert，并有可测验收标准。
- **Matt 主路径**：每个 Issue 走 `$triage #N` → `$to-spec #N` → `$to-tickets #N` → `$implement #N Txx`（经 `$aisoft-matt-workflow` 适配；small 在 triage+summary+判级+`approved` 复核后可跳过 spec/plan）。`triage/ready-for-agent` ≠ `approved`。
- **24 标签四维正交**：7 `type/*`（作者输入）+ 2 `complexity/*`（AI 输出）+ 8 生命周期（`completed` 与 `deployed` 互斥终态）+ 7 `triage/*`（Matt 编排）。
- **单闸门**：人合并最终 PR 是唯一交付硬闸门；任何会话/agent 不合并、不直推受保护 `main`，也不得擅自部署（部署需独立授权）。
- **一切 Gitea/Git/OrbStack 访问走 broker**：`/usr/local/libexec/aisoft/host-access-broker --project <manifest项目> --operation <typed操作>`（gitea.issue.create/read/update、gitea.pull.create、git.push.change --branch、host.access.audit…）。不拼 raw token、不传 URL/refspec/shell；Git push 只允许当前 checkout 同名 readable 分支。
- **provider 默认关**：`IMPLEMENT_PROVIDER=none` 是默认；启用是每项目独立验收门。
- **部署边界**：AI 可参与开发/测试环境首次部署并固化为脚本（两次幂等 + 一次故意失败回滚）；生产只跑已验证脚本。新 Linux 默认 docker-release/v2（NewEMaint 为参照实现），PM2 是受支持的选项路径；各项目技术方案可不同，流程与指导思想全平台一致。

## 会话标准动作（Mac 交互开发，最常见）

> **会话本身的编排**（一 Issue 一会话、何时开调度会话、PR 后的待合并提示、人合并后的收尾与归档）见 `issue-session-flow` skill；本段只覆盖单个会话内部从 Issue 到开 PR 为止的动作。

1. 需求/缺陷 → broker `gitea.issue.create`（正文写可测验收标准）。
2. `python3 -m aisoft_loop.cli change-name N <slug>` 校验命名 → `git worktree add /private/tmp/issue-N-<slug> -b change/N-<slug> origin/main`（并行会话必须各自 worktree；commit 前 `git branch --show-current` 核对——踩坑 #15）。
3. 按判级写映射文档（complex 补 spec/plan，模板在 `templates/docs/changes/_template/`），实现 + 测试全绿（改 shell 后跑 `bash codex/tests/smoke.sh`）。summary 此时写**真实的**前置 `status`（通常 `approved`），`pr_url` 留空——PR 还不存在。
4. 判级投影：`codex/tools/apply-classification-labels.sh N` 先看计划，确认后
   `--apply` 经 broker `gitea.issue.labels.classify` 把 summary 的 `change_type` 与
   `effective_complexity` 写成 Gitea 的 `type/*` 与 `complexity/*`（#160）。
   不做这一步，判级就只活在文档里、Gitea 上看不见也检索不到——`apply-analysis` 只在
   Loop 内跑，交互会话不经过它。生命周期与 `triage/*` 标签不受影响；已关闭的 Issue 会被跳过。
5. commit → broker `git.push.change --branch change/N-<slug>` → broker `gitea.pull.create --issue N`（正文含 `Closes #N` 与文档链接）→
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

- **Claude Code（Mac 交互）**：开发与设计——需求澄清、spec/plan、实现、测试、重构。
- **Codex**：维护与部署——VM headless 分析、运维排障、部署验收、平台治理演进。
- 二者共用同一平台合同与 provider 中立机制（`ANALYSIS_PROVIDER`/`IMPLEMENT_PROVIDER` 按项目 profile 显式选择），随时可互换补位。

## 接入新项目 / 项目对齐 / 私有访问

- 新项目接入：先读 [references/onboarding-runbook.md](references/onboarding-runbook.md)——governance manifest + project-agent gate、host-role gate、architecture 声明、CI/部署与验收顺序都有既定约定，不得跳步。
- 项目对齐（初始化=更新，幂等）：入口 [references/project-align.md](references/project-align.md)——checklist 盘点缺口、逐项走目标仓独立 Issue/小 PR；确定性核对用 `codex/tools/aisoft-project-check.sh --repo <checkout>`（PASS/GAP，只读）。
- 私有 Gitea 检查：先读 [references/private-gitea-access.md](references/private-gitea-access.md)；**匿名 404 不构成不存在证据**（private-repository `404` 歧义），按 authenticated ladder 走。

## Common Mistakes

- 用数字命名新建分支/文档（`change/N`、`00-summary.md`）——新写入会被 fail-closed 拒绝；readable 元组才是现行合同。
- 绕过 broker 直接 `git push`/裸 token `curl`——治理写路径只认 broker typed 操作。
- 把 `triage/ready-for-agent` 或 Issue `approved` 当成可以合并/部署——唯一闸门是人合并最终 PR，部署另需独立授权。
- 在共享 checkout 并行开会话不建 worktree——HEAD 是全局可变状态，B 的 commit 会落进 A 的分支（踩坑 #15）。
- 从 rsdesign-new 或任何示例推断目标仓库/端口/部署合同——一切以显式 project profile/manifest 为准。
- 把平台 candidate/参照实现写成业务已部署——NewEMaint 的 DockerLab 证据不等于其它项目或生产完成。
