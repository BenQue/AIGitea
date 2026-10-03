---
name: aisoft-platform
description: Operate or onboard projects to the AISoft self-hosted Gitea delivery platform. Use for private local Gitea repository, Issue, PR, Actions, branch-protection, or authentication inspection; Issue analysis; small-or-complex routing; spec/plan contracts; Development Loop work; Codex/Claude provider coexistence; CI/deployment incidents; first non-production deployments; rollback planning; or production script boundaries.
---

# AISoft self-hosted delivery platform

## Read the contract

Read `README.md` and the relevant numbered document before acting. On Mac the authoritative root is `~/MyDocs/AISoftPlatform/`; on gitea-ci it is `/mnt/mac/Users/benque/MyDocs/AISoftPlatform/` (readable as both `benque` and `coder`, verified 2026-07-19).

⚠️ **Not `~/Documents/AISoftPlatform/` — that was the location until 2026-07-19 and it is unreachable from the VM.** macOS TCC blocks `/mnt/mac` access to `~/Documents`, `~/Desktop` and `~/Downloads`, and `sudo` does not help (`Operation not permitted` as both `benque` and `root`). The repo was moved to `~/MyDocs/` precisely so the mount works; see 01 §1.

Use:

- `03` for Issue, complexity, documents, labels, and the final PR gate.
- `04` for analyzer, Development Loop, verifier, terminal states, and provider adapters.
- `02` and `06` for deployments and incidents.
- `08` for provider coexistence and parity validation.
- `09` for migration scope and unimplemented boundaries.

## Apply the v3 workflow

Select the target project explicitly before any Gitea or Git mutation. A project profile binds one profile name to `GITEA_URL`, `GITEA_OWNER`, `GITEA_REPO`, `AGENT_REPO_DIR`, provider selection, and a namespaced state/worktree root. Never infer the target repository from another project or example, and never reuse one project's state directory for another project.

Every local Gitea software repository must first exist in the strict `codex/config/gitea-governance.json`
manifest (the Issue #35 governance contract is live). Validate the
manifest, bootstrap the non-site-admin platform manager for one exact repository, run read-only governance
`check`, then apply one exact repository with the manifest-declared project agent. Unknown repositories are
report-only; never infer visibility, ownership, or permissions from discovery.

Every mutation requires the exact repository, Issue #35, a byte-identical merged platform SHA, the manager
mutation credential, and a new evidence directory. The tool must read back private/public visibility,
manager=Admin, project-agent=Write, no cross-project Write/Admin, merge-after-branch cleanup, and protected
`main`. Direct/force push is disabled. Repositories without routine opt-in keep a human-only merge allowlist;
an enabled repository may add only its independent exact-repository routine merger. Manager, project agent,
provider, shared bot and site admin never act as that merger.

Routine opt-in is fail-closed: only `classification=internal-application` with non-empty canonical required status
contexts may declare `routine_auto_merge_enabled=true`. `aisoft-platform`, every public-platform repository, and
every context-empty repository stay disabled. Source declarations, installed bytes, credential provision, protection
apply and live read-back are separate evidence; this contract never infers one from another.

The shared `ci-bot` collaborator gate is retired: `ensure-gitea-collaborator.sh` remains only as historical
compatibility and regression-test evidence and must never onboard, repair, or serve as a broker fallback for any
project; see `06` §「旧 `ci-bot` gate（已退役）」.

Do not use the mutation path as an inspection shortcut. Prefer the exact project profile; for cross-project
settings/protection use the manager audit PAT and `gitea-governance.sh check`.

## Access private Gitea deterministically

Before inspecting a private repository, Issue, PR, Actions run, branch protection, or repository setting, read [references/private-gitea-access.md](references/private-gitea-access.md).

- Resolve and verify the exact Gitea remote or project profile first.
- Do not start with an anonymous API request. A private-repository `404` or Git `Repository not found` is inconclusive.
- Prefer the exact project profile and minimum-privilege identity. For Git refs, reuse the configured Git credential helper.
- Use the independent platform-manager audit PAT for cross-project read-only settings/protection inventory; do not substitute the mutation PAT or ordinary Git.
- If no profile/manager exists or ACL blocks the exact target, use the VM-local administrator credential only
  for an authorized, sanitized, read-only helper call. Do not copy credentials to the Mac or broaden bot access.
- Use an existing authenticated browser session as a read-only fallback when the helper is unavailable or UI evidence is required.
- Report network, credential availability, repository ACL, and object existence as separate facts.

Treat every new request, defect, or platform change as a Gitea Issue `N` bound to one immutable readable tuple: branch `change/N-short-description`, semantic directory `docs/changes/N-short-description/`, worktree basename `issue-N-short-description`, and one final PR with `Closes #N`. The Issue number remains the unique key; the shared slug is for humans. Pre-#57 numeric names (`change/N`, `docs/changes/N/`, `00-summary.md`…`03-verification.md`) are evidence-derived read/maintenance compatibility only — never new-writer targets.

- Require a mapped `summary` document for every Issue. New documents use `<role>-<short-description>-<YYMMDD>.md`; the summary front matter's `documents` field maps `summary`/`spec`/`plan`/`verification` roles to real basenames. Resolve them with `python3 -m aisoft_loop.cli resolve-documents N --repo <checkout>`, never with a broad glob.
- Treat `type/*` labels as Issue-author inputs describing what the change is; AI verifies or corrects one primary type from repository evidence.
- Treat `complexity/*` labels as AI classification outputs describing which path is required, never as an Issue-author override of contract impact or forced risk.
- Treat the eight unprefixed lifecycle labels as workflow state, separate from the 10 `type/*` labels and two complexity labels. `completed` means merged with no deployment required; `deployed` requires deterministic deployment and verification. The Matt triage dimension (`triage/*`: 2 category + 5 state labels; 27-label manifest in total) is orthogonal to all three, and `triage/ready-for-agent` never substitutes for platform `approved`.
- Classify contract impact first: `restore`/`unchanged` is only a `small` candidate, `add`/`change` is `complex`, and `unclear` requires human triage.
- Route a clear, local, reversible restore/unchanged change with no forced risk as `small`; route feature/functional behavior, schema/data, external contract, security, shared core, cross-module/service, CI/artifact/deployment/rollback, and Agent/platform governance changes as `complex`.
- Respect an explicit complex request, but never let a requested small value bypass AI validation or forced-complex rules.
- Require mapped `spec` plus `plan` documents for production-phase effective complexity `complex`; development-phase complex takes measurable acceptance criteria from the Issue and uses synthetic `T01`. Do not create ceremonial spec/plan for validated `small` or development-phase complex work.
- Require a mapped `verification` document whenever acceptance evidence cannot be reproduced by diff review and required CI. Deployment and migration always qualify, but `verification` does not imply deployment.
- Treat `approved` as permission to start the Development Loop, not permission to merge or deploy.
- Keep final PR merge as the only delivery gate. Manual PRs are human-merged; only an explicitly confirmed eligible
  routine-small PR may use the independent broker merger after every final-head hard gate passes.

The primary per-Issue development path is the complete Matt workflow behind the platform adapter: initialize with `$aisoft-matt-workflow` (which chains `$setup-matt-pocock-skills` with the `templates/docs/agents/` tracker/triage/domain files), then run `$triage #N` → production complex `$to-spec #N` → `$to-tickets #N` → `$implement #N Txx`. Platform-validated `small` and development-phase complex work skip spec/plan only after triage, mapped summary, classification, measurable Issue acceptance criteria, and `approved` revalidation.

Claude Code and Codex share this one platform contract as equal, interchangeable providers with no primary or secondary role; the two models complement each other toward the same goal, and neither invents its own classification, document, or delivery workflow. Automation providers are still selected explicitly by the project profile's `ANALYSIS_PROVIDER`/`IMPLEMENT_PROVIDER` (default `none`).

The `gitea-*` skills are compatibility adapters, not a second development method:

- `$gitea-analyze-change`, `$gitea-spec-plan`, `$gitea-development-loop`, `$gitea-implement-change` remain only for Gitea label projection, semantic document resolution/publication, Controller integration, and legacy callers.
- `$gitea-platform-ops` stays independent for platform evidence, first non-production deployment, incidents, and rollback.

## Preserve the Development Loop boundary

Let the Loop handle ordinary compile, lint, type, test, build, browser, and CI failures. Escalate contract conflicts, scope expansion, destructive migrations, new security/permission/architecture decisions, missing external dependencies, unreliable verification, three same-root-cause attempts, or configured limits.

After the user approves an Issue contract or an explicit implementation plan, continue through in-scope
implementation, tests and repair without intermediate confirmations. Then enter `AWAITING_PR_CONFIRMATION` and ask
once to submit the unique final PR, binding exact Issue/branch and `manual|routine-auto` policy. Manual work ends at
`READY_FOR_REVIEW`; eligible routine-small work may reach `AUTO_MERGED` only through the independent broker merger.
After merge, automatically complete terminal reconciliation, document checks, cleanup and archival without another
confirmation. `issue-session-flow` owns the contract/start and final-PR confirmation formats.

Accept `AWAITING_PR_CONFIRMATION`, `READY_FOR_REVIEW`, `AUTO_MERGED`, `NEEDS_HUMAN_DECISION`,
`BLOCKED_EXTERNAL`, or `FAILED_LIMIT` as governed states. Never describe unrun checks as passed.

In a Controller-managed run, after it opens the pull request, the Controller writes that PR's URL into the change
summary's `pr_url` front matter field and advances the summary's `status` to `pr-open`, commits exactly that one
document, and pushes it (#146). This is automatic within that path — do not duplicate its backfill step or treat
the extra commit as provider work. `pr_url` lives in the summary only (#142); spec, plan and verification documents do not carry it. If the
summary does not declare `pr_url`, or already declares a different one, the Controller fails closed and returns
`NEEDS_HUMAN_DECISION` rather than overwriting or skipping — a change has exactly one PR, so a second value
means the premise broke. Verify any checkout with
`PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli check-change-documents --repo <checkout>`.

In a Mac interactive session that creates the PR with broker `gitea.pull.create` without invoking the Controller,
the session must run
`PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli backfill-pr-url N --repo <checkout> --pr-url <actual PR URL>`,
commit exactly the mapped summary and push the same change branch through the broker. The standalone
`gitea.pull.create` call does not run the Controller's automatic backfill. Before the PR exists, leave `pr_url`
empty and keep the real pre-PR status; then run `check-change-documents` on the updated checkout.
For both Controller and Mac paths, PR summary-only backfill creates a legitimate new head. Before that
subsequent push, review the mapped-summary-only diff with the actual PR URL/status, run the document check
and verify ownership, exact branch and a clean worktree; record the freshly verified exact head and compare
`pushed_head` with it. In-contract CI repair follows the same fresh-validation/read-back rule with its
required tests. The first push still compares against the verified final-PR candidate. Authorization stays
bound to exact Issue/branch/policy, without a confirmation per legitimate commit; stop on scope expansion,
other-session rewriting or any mismatch. See `issue-session-flow` for the complete comparison contract.

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

## Preserve the deployment boundary

For an onboarded application that has deployment scope, help design and execute the first real development/test deployment, convert manual steps into versioned scripts, run twice from a repeatable state, and exercise one deliberate failure/rollback path. Documentation-only platform repositories such as AISoftPlatform do not need an application deployment pipeline.

In production, run only pre-validated artifacts and scripts. For failures, stop/rollback, collect sanitized evidence, reproduce and fix in non-production, verify, and prepare a PR. Never generate or execute ad hoc production commands.

## Protect the platform

- Never let a provider, project agent, manager or shared bot merge a PR. Never invoke routine merge without explicit
  policy confirmation, a final exact head pin and every broker hard gate. Never push directly to protected `main`.
- Preserve `CI / test (pull_request)`, immutable artifacts, environment separation, real health checks, and rollback.
- Never print tokens, passwords, `.env`, auth files, or Git credentials.
- Never add a project profile or collaborator permission merely to make read-only inspection convenient;
  account and repository mutation is reserved for the merged governance manifest and exact-repository tools.
- Keep Gitea manager/project PATs, OrbStack host control, VM operator accounts, and per-project deploy identities
  separate. A Gitea credential never authorizes SSH, sudo, VM lifecycle, database, or production access.
- Keep Claude and Codex configuration independent while sharing the outer controller and verifier contract.
- Do not describe the v3 Loop as deployed for any provider until that provider's validation matrix in `08` passes.

For a new project, read [references/onboarding-runbook.md](references/onboarding-runbook.md) before changing infrastructure.

Initializing a new project and re-aligning an onboarded one are the same idempotent
operation: follow [references/project-align.md](references/project-align.md) and use the
read-only checker `codex/tools/aisoft-project-check.sh --repo <checkout>` (PASS/GAP) to
inventory gaps, then fix each gap through the target repository's own Issue and an AI-classified PR; never assume every alignment gap is `small`.
