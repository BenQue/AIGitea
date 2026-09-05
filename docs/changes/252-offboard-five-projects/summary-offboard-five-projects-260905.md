---
issue: 252
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/252
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 退出五个项目要改两份治理 manifest、重新 pin routine pilot 的 non-target 封印、放宽 contract.py 的 VM profile 与 timer 白名单，并停用一条在跑的 VM timer 与八个 Gitea 身份；命中平台治理与安全强制规则。
risk_flags:
  - platform-governance
  - agent-governance
  - security
  - shared-core
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-offboard-five-projects-260905.md
  spec: spec-offboard-five-projects-260905.md
  plan: plan-offboard-five-projects-260905.md
  verification: verification-offboard-five-projects-260905.md
confidence: high
override_reason: ''
depends_on: []
status: pr-open
branch: change/252-offboard-five-projects
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/256
created: 2026-09-05
updated: 2026-09-05
---

## 问题/需求总结

2026-09-05 用户定案：平台只服务 LocalWMS 与 NewEMaint。rsdesign-new、HSDB、
SFMDigitalBoard、WMPDA、SapTableMigrate 五个项目统一退出平台治理。

退出不是删除。Gitea 仓库、历史、Issue、PR、分支保护全部保留；本次只解除平台侧的
治理绑定与自动化，并保证每一步可按 onboarding runbook 反向恢复。

## 影响范围

退出后 manifest 只剩 aisoft-platform、localwms、newemaint 三个真实项目，加上
myapp 与 smoke-test 两个 public-test 夹具，共五条。

证据收集发现四处 Issue 正文未预见的强绑定，它们决定了本次变更的真实形状：

1. `codex/runtime/aisoft_host_access/contract.py` 硬 require VM profile 仓库集合
   恰好是六个具名仓库。只删 manifest 会让 access contract 直接 `CONTRACT_INVALID`，
   broker 全部操作 fail-closed。已实测复现。
2. 同文件 timer 白名单只允许 emaintenance 与 sfm 两个 unit，sfm 退出后应收紧。
3. `codex/runtime/aisoft_gitea_governance/contract.py` 强制 NewEMaint routine pilot 的
   `non_target_repositories_sha256` 等于「除 NewEMaint 外全部 repository 声明」的
   摘要。删五条仓库必然改变该摘要，必须在同一 commit 重新 pin，否则 governance
   contract 拒绝加载。这是 routine pilot 的防篡改封印，属安全相关改动。
4. `ProfileMigrator` 只有 plan/apply/read-back/consume-check/rollback，**没有删除路径**；
   `bootstrap-gitea-service-account.sh` 只能创建账号与 token，没有回收对应工具。
   因此 VM env/token 文件清理与 Gitea 身份回收无法由 broker typed 操作完成。

myapp 与 smoke-test 必须保留，这不是偏好而是证据：`aisoft_gitea_governance`
contract 把 public allowlist 硬 pin 成 aisoft-platform、myapp、smoke-test 三个；
`test-project-check.sh` 用 `GITEA_REPO=myapp`；`test_host_access.py` 用 myapp 作
「mac_checkout 为 null」与「无 VM profile」两个 fixture。删掉会同时打断这四处。

#172 要求的「project_id 不等于 repository」回归用例在退出后由 localwms/LocalWMS 与
newemaint/NewEMaint 天然继续满足。

## 初步方案与建议

按 Issue 正文顺序执行，但把无法经 broker 完成的动作显式降级为人工交接项：

先停活链路（人工：停用 sfm timer、清三份 VM profile env/token），再改 manifest 与
runtime 与测试与文档（本 PR），再两台重装（人工），再收 Gitea 身份（人工），
最后收口相关 Issue。

已用候选 manifest 在不重装的前提下实测全链路可行：重算摘要后配合 contract.py 补丁，
`aisoft_host_access.cli validate` 返回 `project_count: 5, status: PASS`。

## 风险

- 顺序风险：manifest 合并并重装后，broker 将拒绝五个 project id，届时再想用 broker
  清理它们的 VM profile 已无路径。清理必须发生在重装之前，或全部由人工直接执行。
- 封印风险：重新 pin non-target 摘要会使「pilot 期间非目标仓库声明未变」这条断言
  以新基线继续成立。必须在 spec 中显式授权，并在文档中留下重新 pin 的原因与时点。
- 文档风险：01/02/05/06/07 与 README 中的多数命中是历史 as-built 与踩坑证据，不是
  在册清单。批量清洗会摧毁平台自己的审计轨迹，本次只改读起来像当前状态的语句。
- 残留风险：不清理 VM 文件与 Gitea 身份，退出即只是「平台不再管」，凭据仍然有效。
  这些都在人工交接项里列明，未执行就如实写 NOT RUN。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 退出五个项目要改两份治理 manifest、重新 pin routine pilot 的 non-target 封印、放宽 contract.py 的 VM profile 与 timer 白名单，并停用一条在跑的 VM timer 与八个 Gitea 身份；命中平台治理与安全强制规则。
risk_flags:
  - platform-governance
  - agent-governance
  - security
  - shared-core
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- `change_type: platform` 属 FORCED_COMPLEX_TYPES，单此一项即强制 complex。
- 改 `codex/config/host-access-broker.json` 与 `codex/config/gitea-governance.json`
  两份 canonical governance manifest，命中 platform-governance。
- 改 `aisoft_host_access.contract` 与 `aisoft_gitea_governance.contract` 两个共享
  runtime 契约模块，命中 shared-core。
- 重新 pin routine live pilot 的防篡改摘要、回收八个 Gitea 身份的 token 与
  collaborator 权限，命中 security。
- 停用 gitea-ci 上在跑的 `aisoft-agent@sfm.timer`，命中 agent-governance。
- 声明 `verification`：活 timer 状态、VM env 文件清单、两台重装读回与 Gitea 身份
  回收都无法由 diff review 加 required CI 复现，按 `03` §3 判据必须留验证记录。

### 缺失的 acceptance criteria 或决策

- 无。myapp 与 smoke-test 的取舍由 spec 按上述证据裁定为保留。
