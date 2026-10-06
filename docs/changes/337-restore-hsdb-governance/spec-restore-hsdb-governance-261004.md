---
issue: 337
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/337
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - agent-governance
  - security
  - shared-core
depends_on: []
status: approved
branch: change/337-restore-hsdb-governance
created: 2026-10-04
updated: 2026-10-04
---

# Spec 恢复 HSDB 治理注册

## Problem Statement

HSDB 已由 #252 退出平台。用户现已决定重新接入，installed broker 无法识别 hsdb，
业务仓不能从正常 project-agent typed 通道继续自己的 Issue/PR。需先恢复治理声明，
保留现有项目范围、安全保护和人工合并，避免把源码恢复误作 Secret 或部署验收。

## Solution

恢复两份 manifest 的唯一 HSDB 注册，采用 Mac 交互通道与 `vm_profile=null`。
只修改独立治理合同和必要验证，不新增生产 runtime；本步骤完成后停止在 final PR 门禁。
若需 runtime 或 VM 自动化，必须另有合同并在 fresh run 重新读取治理后实施。

## User Stories

1. 作为 HSDB 负责人，我要 hsdb 被 broker 识别，以便随后以项目独立身份完成 onboarding。
2. 作为平台 owner，我要 live 的 private/manual/required CI 被精确声明，以保留最小权限。
3. 作为 NewEMaint owner，我要合法扩展非目标集合后 seal 仍可验证，以保持现有唯一 routine pilot。
4. 作为总调度，我要 source/local/CI/installed/live/UAT 独立的结果，以按真实准入推进下游。
5. 作为操作人，我要 exact pin、readback 与恢复卡，以在独立批准窗口可回滚地安装。

## Implementation Decisions

- governance HSDB：internal-application/private、project_agent=hsdb-agent，routine_auto_merge_enabled=false，
  routine_merge_agent=null，status_check_contexts=[CI / test (pull_request)]，required_approvals=0。
  change_control 缺省 production、deployment_lifecycle 缺省 application-deploy-selective、template holder 缺省 true，
  与原 HSDB 范围一致，不改为 development 或虚构必然部署链。
- host-access hsdb：repository=HSDB、project_agent=hsdb-agent、routine_merge_agent=null，
  mac_checkout=/Users/benque/Projects/HSDB、vm_profile=null；不声明 git_remote_name，按既有合同取 origin，
  两条 remote URL 当前均为 exact Gitea HSDB。当前本地存在的 github remote 不作为 broker 目标。
- 现有六仓所有声明保留；NewEMaint 唯一允许变更为 non_target_repositories_sha256 的集合封印。
- live HSDB manager=Admin、agent=Write，但 agent 禁止登录；只记录 metadata，不改变账号或凭据。
- 不启用 provider、timer、routine merger；IMPLEMENT_PROVIDER=none 直到独立项目 acceptance matrix 完成。

### 治理文件明确修改授权

本独立受控步骤只授权以下文件和语义：

| 文件 | 允许的变化 |
|---|---|
| `codex/config/gitea-governance.json` | 新增唯一 HSDB 条目；按既有 `repository_declarations_sha256(repositories, exclude_name='NewEMaint')` 重 pin seal |
| `codex/config/host-access-broker.json` | 新增唯一 hsdb 条目，Mac-only，vm_profile=null；operation/identity/profile policy 不变 |
| `codex/tests/test-host-access-broker.sh` | project_count 6→7；增加 HSDB 注册/零自动化精确断言，保留所有现有硬门 |
| `codex/runtime/tests/test_host_access.py` | count 6→7；恢复条目的 bounded mapping 与拒绝 VM 扩张回归 |
| `codex/runtime/tests/test_gitea_governance.py` | count 6→7、private 集合包含 HSDB；manual/CI/identity/default phase 回归 |
| `README.md`、`03-Issue-Spec-Plan与单闸门开发流程.md` | 只同步 HSDB 注册、七仓计数和 project_id/仓库名对照，保留 installed/live 边界 |
| `docs/changes/337-restore-hsdb-governance/` | 映射四件套、fresh read/验证/回滚证据与具体安装恢复卡 |

两份生产 `contract.py`、`AGENTS.md`、Agent/controller、CI workflow、deploy/install scripts、smoke.sh 零 diff。
治理先落完整 spec/plan 后才应用清单；没有后续 runtime 实施，不需借改变本次规则继续实现。

## Acceptance criteria

- [ ] AC-1 两份 manifest 集合精确相等、各仅新增一条 HSDB；rsdesign-new/WMPDA/SapTableMigrate 仍退出。
- [ ] AC-2 strict validate PASS，project_count=7，operation_count=38，merge_operation_count=1。
- [ ] AC-3 新 seal 等于同树现算；移除 HSDB 并还原 seal 后的全部保留仓/policy 与基线字节语义相同。
- [ ] AC-4 HSDB private/manual/CI/agent/origin/canonical checkout 正确；无 VM profile/routine merger，
  尝试追加 HSDB VM profile 被现有 exact-three contract 拒绝；两份生产 contract.py 与保护文件零 diff。
- [ ] AC-5 targeted tests、完整 smoke、改动 shell 的 bash -n/ShellCheck（可用时）、document checker、diff check 通过。
- [ ] AC-6 隔离源码 revert/reapply 演练：7→6→7，seal 同步，恢复后 manifests byte-identical；没有 live 安装。
- [ ] AC-7 单一 Issue/branch/worktree/owner 与分类标签 projected；最终提交卡为 manual，push/PR 等待具体确认。
- [ ] AC-8 人工 merge 后 fresh-read exact merge SHA、主干归属及最终 head required PR CI success；此前 NOT RUN。
- [ ] AC-9 独立安装窗口完成后两端 installed manifests 与已合并 source pin 同字节，installed broker 对 hsdb
  不再报 unknown project；access/onboarding 的 credential/account GAP 不抹除，凭据问题不降低准入标准。

总调度 T01 完成条件是 AC-8 与 AC-9 均成立。平台 Issue 的 completed 是 source lifecycle，
不能把它自动提升成 HSDB access/onboarding/UAT 完成。

## Testing Decisions

使用已有 strict contract、broker shell、runtime unittest 与完整 smoke seams，验收可观察的项目映射、
exact required context、权限策略和 VM 扩张拒绝。新用例禁止产生任何 live/Secret mutation。
以基线规范比较保护不变量，并在独立 scratch checkout 演练真实 git revert/reapply，非 fake installed PASS。

## Out of Scope

不改 HSDB 文件、旧 Issue/PR、CI、业务、数据库、服务或部署；不恢复另外退出项目；
不解除 hsdb-agent 停用、不读取或打印凭据值、不创建/旋转 token、不执行 protection apply、
mac.git.bind、标签 provision、真实 canary、timer/provider/routine 启用；不安装，不借 #327/#333 的批准。

## Further Notes 与回滚

fresh preflight 保存本地/远端 HSDB 两个 SHA；下游必须处理差异，不默认采用交接旧 SHA。
source rollback 同时 revert 两份 manifest 与 seal；安装后用已保存上一 merged pin 通过受控 installer
恢复 Mac/VM 两端并 readback。安装和 installed rollback 都需要独立 exact pin/窗口授权。
