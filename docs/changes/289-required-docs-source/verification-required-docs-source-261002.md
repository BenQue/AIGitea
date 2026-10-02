---
issue: 289
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/289
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - shared-core
  - platform-governance
depends_on: []
status: approved
branch: change/289-required-docs-source
created: 2026-10-02
updated: 2026-10-02
---

# #289 证据与验证记录

## 当前阶段

基线阶段（2026-10-02）：triage 与完整合同草稿准备完成，当时尚未 approved、尚未实现。以下 PASS 是基线观察与复现执行成功，不是修复后验收 PASS。spec AC-1～AC-7 的修复后验证全部 NOT RUN。

## 可核对基线

- 平台 authoritative main：5c2cd726c9aeaee9d17541d8feb049e33881bbac；broker git.fetch.main 返回 PASS。
- #289 Issue open；初始入口 needs-analysis，完成草稿后已投影 type/platform、complexity/complex、spec-drafting；classification --verify 289 返回 result=projected。评论无已有启动批准；gitea.pulls.read open 返回 []。
- host.onboarding.check PASS：project-agent write；protected main can_push=false、can_force_push=false；required CI=CI / verify (pull_request)；routine disabled。
- exact tuple：change/289-required-docs-source；issue-289-required-docs-source；docs/changes/289-required-docs-source；本聊天 session=01a0fc7b-dfb2-77b3-a089-2d0f73ac8554，claim-worktree created。
- manifest：aisoft-platform deployment_lifecycle=none；缺 change_control → production。SFM development/selective，与 verification 义务独立。

## 原始历史复现

真实来源：SFM 本地 Git 历史 516d24a9ca9638b4ac8fcba041296547c75a8198（来源 Issue 已指出 merge，当前只读提取）；原样 summary 在 evidence/sfm-142-summary-516d24a.txt；SHA256=bb03c58dda71fccd923af20b1a0c45675d7f49a57e01fc36320e643462d7e446。git cat-file -e <sha>:docs/changes/142-architecture-lock-declaration/verification-architecture-lock-declaration-260910.md 非零，证明历史对象内缺失。

构造仅包含原样 summary 的 /private/tmp/aisoft-289-evidence/sfm-142-missing/docs/changes/142-architecture-lock-declaration/，不改 SFM 当前 checkout；结果保存在 evidence/baseline.json。

| 真实执行 | 当前结果 | 意义 |
|---|---|---|
| PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli resolve-documents 142 --repo /private/tmp/aisoft-289-evidence/sfm-142-missing | exit=0；返回含 verification 的完整映射 | 证实缺文件不报错 |
| PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli check-change-documents --repo /private/tmp/aisoft-289-evidence/sfm-142-missing | exit=0；PASS 两项、gap=0 | 证实假绿 |
| 同一 summary Classification.route(change_control=development) | (summary, verification) | 纠正原 Issue 对 route 的推测 |
| 同一 fixture load_contract；合成 open/approved、type/platform、complexity/complex Issue | ContractError: missing required contract documents: verification-architecture-lock-declaration-260910.md | 当前 Loop readiness 已拒绝；audit 漏检仍真实 |
| bash codex/tools/mark-completed-issues.sh --repo /private/tmp/aisoft-289-evidence/sfm-142-missing --project sfm-digital-board 142，固定本仓 governance/access manifests | exit=0；action=set-completed；reason=deployment-not-guaranteed；applied=false | terminal dry-run 仍接受虚假声明，零 live 写入 |

fixture 的 git remote 只写本地 metadata 供项目绑定校验，没有访问远端，也没有 --apply。

## 当前 checkout 基线

- platform audit：exit=0，change-documents PASS / change-pr-url PASS。
- SFM 当前 db3c80af5ccb46b363dafe37848df15761b9b5d5：exit=1，change-documents GAP（已有历史数字目录 front matter），change-pr-url PASS；原始清单 evidence/sfm-audit-baseline.txt。该共享工作树有既有未跟踪 docs，保持未动。此结果仅该 checkout 当前状态，不冒充 authoritative remote 或全仓 PASS。
- 可解析平台 144 个/SFM 43 个 change：无显式 documents 缺文件，required_docs 均存在；历史不可解析目录按原 audit GAP 保留。不修其它 Issue 文档。

## 修复后验收

| 项目 | 状态 |
|---|---|
| AC-1～AC-7 修复后 | NOT RUN |
| targeted / 全量 runtime | NOT RUN |
| bash -n / ShellCheck / smoke | NOT RUN |
| PR CI | NOT RUN |
| installed / live runtime / deployment | NOT RUN；本次无授权 |
| 用户合同启动确认 | PASS：本聊天明确回复“确认”；摘要记录见 evidence/contract-approval.json |
| 最终 PR 提交确认 / 人工 merge | NOT RUN |

## 治理执行顺序

先获得本 spec/plan 的明确确认；T01 仅治理 README/03 说明应用后停止；fresh run 重读后再实现 T02/T03。没有运行的验证不能填通过；终态工具只证明声明文件和仓库生命周期，不证明 verification 文本每项已执行。

## 投影与能力 GAP

真实执行 apply-classification-labels --apply 289 → updated；--verify 289 → projected（type=platform, complexity=complex）。lifecycle spec-drafting → PASS；未设置 approved。

Matt 类别/ready 标签未投影：尝试 gitea.issue.labels.extension.set 的 triage/bug 与 triage/ready-for-agent 均被 broker 拒绝（REQUEST_DENIED: label is canonical or retired and cannot use the project-extension writer）。源代码确认 extension writer 不接受 canonical triage，现有 lifecycle writer 只支持 delivery lifecycle，classify writer 只支持 type/complexity。本次停止这些写入，没有绕过 broker，也不以安装/扩权解决。triage 判断在本 Issue 评论与合同中保存，canonical 标签 GAP 交调度核对独立治理范围；不是 #289 代码修复内容。

## T01 独立治理步骤（2026-10-02）

用户已确认本 Issue 精确 spec/plan 与启动开发，未确认最终 PR 提交。原批准文档 SHA256 和 exact branch/manual/session 绑定见 evidence/contract-approval.json。

真实执行：

- broker gitea.issue.labels.set --number 289 --lifecycle approved → PASS，after=[approved,complexity/complex,type/platform]。
- broker live gitea.issue.read + 本地 load_contract → PASS，issue=289、branch=change/289-required-docs-source、effective_complexity=complex、acceptance_criteria_count=7。
- git diff --check → exit=0。
- check-change-documents --repo . --porcelain → change-documents PASS、change-pr-url PASS。
- 人工模型 diff review：README/03 的全部新增约束与已批准 spec 一致；声明来源、route 最低要求、严格 reader、首次 publisher、legacy 兼容、非法合同零写入、独立 deployment_lifecycle 均已覆盖。文档明确 runtime 待 T02/T03，未把新增 CLI 写成已实现。
- 本步骤未修改 runtime、shell、AGENTS.md、manifest、template、CI 或其它 Issue 文件。因此 runtime tests / bash -n / ShellCheck / smoke 仍 NOT RUN，留 T02/T03 执行。

T01 完成本地 commit 后按治理规定停止；fresh run 重新读取更新后的 AGENTS.md、README、03、spec/plan，再执行 T02。无需重复请求合同启动确认；唯一最终 PR 提交确认仍保留。
