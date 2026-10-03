---
name: aisoft-matt-workflow
description: Configure and run the complete Matt Pocock engineering workflow inside AISoftPlatform Gitea governance. Use during repository initialization or when dispatching triage, to-spec, to-tickets, and implement without weakening protected-main, contract, PR, CI, or deployment controls.
disable-model-invocation: true
---

# AISoftPlatform Matt workflow adapter

This skill adapts the complete vendored Matt skills to AISoftPlatform. It does not replace or edit their upstream
`SKILL.md` files.

## Repository initialization

1. Finish AISoftPlatform repository onboarding first: exact Gitea profile, protected `main`, required CI, project Agent
   permission gate and the 27-label manifest must all read back successfully.
2. Explicitly invoke `$setup-matt-pocock-skills` once. Select **Other** for the tracker and use the three files under
   `templates/docs/agents/` as the Gitea, triage and domain configuration.
3. Add the upstream skill's `## Agent skills` block only in the repository instruction file selected by that skill. If
   the current run is governed by that same file, produce a reviewable proposal and apply it in a separate authorized
   governance step.
4. Confirm `docs/agents/issue-tracker.md`, `triage-labels.md` and `domain.md` exist before the first Issue flow.

## Per-Issue flow

1. `$triage #N` — preserve Matt's complete verify/grill/brief flow. Mutate triage labels through the platform label
   projector; `ready-for-agent` never implies `approved`.
2. Run the platform analyzer. It validates one immutable slug and creates the exact `change/N-short-description`, `docs/changes/N-short-description/`, `issue-N-short-description` tuple plus mapped summary. Existing legacy names are discovered from evidence, never selected by a caller flag.
3. For production complex work, run `$to-spec #N`. Publish to the mapped `spec` file and keep lifecycle `spec-drafting`
   until the complete contract is validated. Development complex uses measurable Issue acceptance criteria and skips
   ceremonial spec/plan.
4. For production complex work, run `$to-tickets #N`. Publish the approved `Txx` vertical-slice dependency graph to
   the mapped `plan` file. Development complex uses synthetic `T01`. Default mode stays inside the parent Issue.
5. After contract validation sets `approved`, the Controller dispatches `$implement #N Txx` for one frontier ticket.
   The Agent owns tests, review and one or more atomic local commits; the Controller owns remote mutation.
6. Controller verification first produces the policy-specific final-PR candidate handoff and enters
   `AWAITING_PR_CONFIRMATION`. Only after explicit confirmation may it fast-forward push and create the one final PR
   with exact readable head, mapped summary and one `Closes #N` line, then follow required CI. Manual work ends at
   `READY_FOR_REVIEW`; eligible routine-small work may reach `AUTO_MERGED` only through the independent merger and
   final-head hard gates. Deployment is independent.

## #327 保留历史的整合、FF 与生效边界

provider只追加本Issue线性本地commit，不创建mergecommit。只有外层Controller在批准合同、
本人worktree内可构造精确`[已核验Issue第一父链末端, fresh manifest main]`的可复算无冲突整合。
original/current remote tip必须始终为候选祖先；broker独立核验来源、完整DAG/tree/scope、fresh main、
本次exact head与传输remote tip，随后只普通FF发表。已发表rebase/amend、force/lease-force、
任意/跨Issue/octopus merge、自动解冲突与身份fallback均拒绝；仍要逐push核对真实remote与本次SHA锚。

#298 AC-5/AC-6与06/#136的历史重写口径由#327覆盖；历史文档保留，single-writer与回执义务保留。
新治理不证明runtime/installed支持；旧installed leased push包括首推均不可沿用。治理应用独立commit
后立即停止，fresh run重读后才可runtime。#327自身first PR只按其映射spec由负责人本人Gitea UI
发表到exactbranch、保留唯一manualPR；Agent不代UI、不directGit/API、不安装unmerged代码。
两机安装各需exact版本批准、完整前后bytes/mode/owner、realFF与rollback实证，#316授权不继承。
installed AC未闭合不把source merge/自动closed当实际完成、不提前cleanup/归档；原owner的人工PR更新
独立验收，不机械等待#327。

**#327 T04 可信证据治理合同（尚未实现/启用）**：trusted-critical Controller 的冻结上下文、受控执行/观察、限定整合和记录由固定 installed verification authority 保管；authority 实际 EUID=0，仅执行已审计平台代码。provider/项目 verifier 以登记非 root UID/GID 在真实 OS 隔离内运行，不能访问 protected ledger、broker credential 或控制入口；只降低 UID、root-owned 文件或 peer UID 不证明程序/批准身份。缺隔离、可信工具链或记录均 fail closed/GAP，不用环境、source wrapper 或身份 fallback。

人类合同/最终 PR 确认须经另获 exact 授权的非 Agent operator 登记为 protected grant/PR授权；local approved、owner marker、commit subject 和 caller PASS 均不是可信根。grant 冻结 exact tuple、scope/内容目的、graph、required verifier、source/policy pin 和 R0，记录由 authority 自己观察执行并逐对象验证；已有/未知或跨 Issue 对象须明确 adoption，来源只指已验证/采用对象，不声称物理创作分支。broker 仍独立重算完整 DAG/tree/delta，核对 sealed checkpoint、PR授权与 strict remote tip，再普通 FF；不重置 R0 或弱化原 per-push/readback 门。

新 public 操作仅 `git.change.begin(branch,ticket)`、`git.change.verify(branch,ticket,sha)`；`git.push.change(branch)` 参数不变。无 public approve/merge、自由 command/path/socket/UID/PASS 入口。代码/config/service 的 exact source 范围及固定路径以 #327 映射 spec 为准，默认 disabled、UID/GID 空、provider none、服务描述 inert。原治理 T04 只应用映射文本、验证/local commit 后 STOP；后续 fresh run 重读才实施 T02。source 合并后的 I01 文件安装与 I02 每主机 exact 权限绑定、注册/启停、真实隔离/FF/rollback 各依独立 operator 卡；不继承 T01、路线选择或 #316，不自动 provision/启动。AC-7/AC-9/AC-10/AC-11 未闭合保持实际未完成，不把 mock/source/自动 closed 当 installed/live 验收。

**#327 T05 资源与工具链治理合同（source 已批准；installed/live 未验收）**：critical 入口由固定 installed native bootstrap 在任何 Python 平台模块导入前核验完整 toolchain closure 与角色绑定；范围包括 interpreter/stdlib/late import/native loader/library/Git transport/helper/OS delegate、OS alias 与 Mac dyld shared cache/subcache。完整目录/build dependency inventory及静态/显式动态解析为基线，loaded-module集合或一次trace不能证明完整；未知依赖/漂移/未注册一律GAP。严格清env/FD、canonical regular最终程序、无source/PATH/未知shim fallback；bootstrap自身OS loader为冻结TCB，不声称main前无库执行。exact source、固定incoming path/FD、build/descriptor与默认disabled空host registry遵映射spec，不自动安装新工具链或以root构建项目。

Mac scratch固定64 MiB UDIF/UDRW/HFSX无分区模板，root Git暂存256 MiB；模板create仅未来exact I02 operator，runtime不格式化任意设备。真实ownership/容量/nodev/nosuid/noexec/nobrowse与镜像→device→mount映射须读回，单scratch/单readonly input、最多两个对象卷；CONTEXT/temp/复制双份窗口全部创建前预留并计入8 GiB保留预算、64 MiB平台元数据上限，input≤256 MiB/4096entries/depth16。Linux同等scratch/对象tmpfs上限及inode/namespace隔离须真实验收。每verifier新own-lease，descendant未退出、busy、device复用、未知映射、崩溃/断电均保留预算/证据并quarantine；不force/resize/hosttmp fallback/盲重试/递归清理user卷/自动删除历史。只依protected exact FD清单和确认own detach后的readback回收；R0不重pin。Mac noexec不支持scratch中新产native binary执行，能力不足明确GAP，不泛称SDK/build可用。

public policy仍`change-verification/v1`四key、public仅begin/verify且push仅branch；private grant/record/operator为v2并绑定closure/resource/lease digest，v1只作历史只读，不自动迁移/清空。publish先持久pending再transport，断线/重启/重入只poll既有attempt、不重复推送；真实possible-write/已落地H保留，不能把传输失败写为零mutation。T05仅原14治理文本+四角色（18文件）独立应用/验证/local commit后STOP，后续fresh重读才继续既有T02 WIP；不混runtime。I01只惰性文件安装/hash-mode-owner、installer no-op与文件失败rollback；I02每主机exact卡独立批准registry/模板/own-device/服务启停/真实权限、FF/publish no-op/reject与运行资源rollback，AC-7要求不减。默认none/disabled，不provision账户/凭据/grant/全局SDK/provider。AC-7/9/10/11未闭合不把source/mock/自动closed当实际完成，不提前cleanup/归档，不继承#316或路线选择权限。

## Stable adapter interfaces

- Label projection: platform and Matt dimensions update independently while preserving unmanaged labels.
- Document resolution: use `python3 -m aisoft_loop.cli resolve-documents N --repo <checkout>`; never guess with a broad
  glob.
- Spec publication: update only the mapped `spec` document and link it from the existing Issue.
- Plan publication: update only the mapped `plan` document with `Txx`, `blocked_by`, AC and verification mappings.
- Ticket execution: include the exact Issue and ticket in the explicit `$implement` prompt; include spec/plan paths
  only when the route requires them.

The Matt skill, provider and project agent never merge or receive the routine merger credential. Never deploy,
rewrite history, force-push, or silently switch to a different tracker or repository.
