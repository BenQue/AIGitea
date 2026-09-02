---
name: aisoft-platform
description: AISoft 自托管交付平台（v3.6）的合同与操作入口。Use when 在已接入平台的项目上开发/修复/部署、接入新项目到平台、走 Issue→triage→spec/plan→实现→PR→部署流程、或排查平台 CI/部署/agent 问题。触发词：AISoft、AIGitea、gitea-ci、Gitea Issue、判级、small/complex、change 分支、Development Loop、host-access broker、architecture lock、部署失败、接入平台、project-align。
---

# AISoft 自托管交付平台（v3.6）

自托管的「Issue → AI 分析判级 →（small 直进 / production complex 先 spec/plan / development complex 用 Issue 验收合同）→ 提交确认 → 单 PR → manual 人工合并 / eligible routine small 受控合并 → 独立部署授权」平台。核心原则：**Issue 定义工作，AI 把明确合同做到最终 PR；人确认提交，manual 由人合并，routine small 只由独立 merger 在最终 head 全硬门后合并；部署不由 merge 授权。**

**权威文档**：Mac 用 `~/MyDocs/AISoftPlatform/`；gitea-ci VM 用 `/mnt/mac/Users/benque/MyDocs/AISoftPlatform/`（**不是 `~/Documents/`**——macOS TCC 挡 /mnt/mac，2026-07-19 迁出）。README=总纲 · 03 流程 · 04 Matt 编排与 Loop · 06 运维踩坑与 broker · 08 双工具 · 12-Linux 内网交付；`architecture/` 等子合同目录以 README 目录为准。改配置前先读对应分册。

## 现行合同（v3.6，#208 governance source）

- **可读命名元组**：新变更 = Issue `N` + 分支 `change/N-短描述` + 目录 `docs/changes/N-短描述/` + worktree `issue-N-短描述` + 唯一 PR（`Closes #N`）。编号仍是唯一主键；remote/history evidence 已存在的 `change/N`、`docs/changes/N/` 与 pre-#57 纯数字文档只作读取或维护兼容，新 writer、first push 和 first PR 不得创建。
- **语义文档**：新文档名 `<role>-<短描述>-<YYMMDD>.md`，summary front matter 的 `documents` 字段映射 summary/spec/plan/verification 到真实文件名。解析用 `PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli resolve-documents N --repo <checkout>`，不要 glob 猜。
- **判级**：contract_effect 先行（restore/unchanged → small 候选；add/change → complex；unclear → 人工澄清）。功能新增/变更、schema/迁移、外部契约、安全、共享核心、跨模块、CI/制品/部署/回滚、Agent/治理一律强制 complex。small 还须范围局部、可简单 revert，并有可测验收标准。
- **Matt 主路径**：每个 Issue 走 `$triage #N` → production complex `$to-spec #N` → `$to-tickets #N` → `$implement #N Txx`（经 `$aisoft-matt-workflow` 适配；small 与 development complex 在 triage+summary+判级+`approved` 复核后跳过 spec/plan，后者使用合成 `T01`）。`triage/ready-for-agent` ≠ `approved`。
- **27 标签四维正交**：10 `type/*`（bugfix/feature/docs/test/refactor/maintenance/platform/security/reliability/data）+ 2 `complexity/*`（AI 输出）+ 8 生命周期（`completed` 与 `deployed` 互斥终态）+ 7 `triage/*`（Matt 编排）。
- **单闸门**：最终 PR merge 是唯一交付硬闸门。manual 只由人合并；只有 repository 显式 opt-in、required contexts 非空、提交确认授权且最终 head 全硬门通过的 routine small，才能由独立 per-project merger 合并。provider/project agent 不 merge、不直推受保护 `main`；部署需独立授权。
- **一切 Gitea/Git/OrbStack 访问走 broker**：`/usr/local/libexec/aisoft/host-access-broker --project <manifest项目> --operation <typed操作>`（gitea.issue.create/read/update、gitea.pull.create、git.push.change --branch、host.access.audit…）。不拼 raw token、不传 URL/refspec/shell；Git push 只允许当前 checkout 同名 readable 分支。
- **provider 默认关**：`IMPLEMENT_PROVIDER=none` 是默认；启用是每项目独立验收门。
- **部署边界**：流程不变量全平台一致——不可变制品、测试与生产同字节晋级、真实健康检查、可回滚、生产 script-only；AI 可参与开发/测试环境首次部署并固化为脚本（两次幂等 + 一次故意失败回滚），生产只跑已验证脚本。交付形态由项目自己的 profile 与 `AGENTS.md` 声明和实现，平台不规定。

## approved 之后默认自主推进

人在确认点 1 确认合同后，以下动作不再逐项询问：证据收集与判级、合同文档补齐、合同内实现与本地原子 commit、测试与普通修复、必需的更宽闸门（smoke、required CI）、判级投影，以及确认点 2 之后的 push、唯一最终 PR 与 PR CI 修复。不要把每张 ticket、每条测试命令、每次 commit 或 CI 重试变成确认点；合同里已定下的选择不再重问。

## 只在这些情况暂停

合同冲突；范围扩张；破坏性迁移；新的安全/权限/架构决策；任何直接生产动作；外部依赖缺失（凭据、服务、权限）；验证不可靠（环境不可达、结果不可复现）；同一根因连续三次失败。宿主要求的 sandbox/网络授权是执行许可，不是新的产品决策。暂停时报告真实 blocker 并等人，不自行决定。

## 会话标准动作（Mac 交互开发，最常见）

> **会话本身的编排**（一 Issue 一会话、合同/启动确认、提交 PR 确认、manual/routine 分流、merge 后确定性收尾与归档）见 `issue-session-flow` skill；本段只覆盖单个会话内部到 PR candidate 为止的动作。

1. 需求/缺陷 → broker `gitea.issue.create`（正文写可测验收标准）。
2. `python3 -m aisoft_loop.cli change-name N <slug>` 校验命名 → `git worktree add /private/tmp/issue-N-<slug> -b change/N-<slug> origin/main`（并行会话必须各自 worktree；commit 前 `git branch --show-current` 核对——`06` 踩坑 15）。
3. 按判级与 `change_control` 写映射文档（production complex 补 spec/plan；development complex 从 Issue 读取验收标准并用合成 `T01`），实现 + 测试全绿（改 shell 后跑 `bash codex/tests/smoke.sh`）。`verification` 由证据能否经 diff review + required CI 重放决定，不等同部署。summary 此时写**真实的**前置 `status`（通常 `approved`），`pr_url` 留空——PR 还不存在。
4. 判级投影：`codex/tools/apply-classification-labels.sh N` 看计划 → `--apply` → `--verify N` 读回两个维度都 `projected` 才算完成；窗口在合并时关闭，closed Issue 永不补写。读到 `broker-operation-missing` 见 `06` 踩坑 20，结论与 Gitea 事实不符见踩坑 21。
5. 本地验证完成后进入 `AWAITING_PR_CONFIRMATION`（候选格式见 `issue-session-flow`）；确认后 broker `git.push.change --branch change/N-<slug>` → broker `gitea.pull.create --issue N`（正文含 `Closes #N`）→ `PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli backfill-pr-url N --repo <checkout> --pr-url <URL>` 回填 summary 再 commit + push，**到开 PR 为止**；`pr_url` 合同见 `03` §3，自查用 `check-change-documents --repo <checkout>`。
6. push 报 `BASE_BRANCH_STALE`：broker `git.fetch.main` → 本地 `git rebase origin/main` → broker 重推（remote 只走 broker，rebase 是本地操作）；lease 语义见 `06` §1.0。
7. push 报 `REMOTE_BRANCH_MOVED`：推送已被拒、远端未被覆盖，先 broker `git.fetch.change --branch change/N-<slug>` 看清远端再决定，不用更强的 force 压过去；见 `06` §1.0。

## 工具分工

Claude Code 与 Codex 共用同一平台合同，能力等价、可互换、不分主辅；两个模型互相取长补短、目标一致，
都不各自发明流程。自动化 provider 仍由项目 profile 的 `ANALYSIS_PROVIDER`/`IMPLEMENT_PROVIDER`
显式选择（默认 `none`）。

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
- 把 broker 的 `REQUEST_DENIED / not allowlisted` 当权限问题查——那是安装期操作表陈旧，两台重装即可（`06` 踩坑 20）。
- 在共享 checkout 并行开会话不建 worktree——HEAD 是全局可变状态，B 的 commit 会落进 A 的分支（`06` 踩坑 15）。
- 从任何示例项目推断目标仓库/端口/部署合同——一切以显式 project profile/manifest 为准。
- 把平台 candidate/参照实现写成业务已部署——一个项目在某个环境的证据不等于其它项目或生产完成。
