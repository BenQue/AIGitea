---
issue: 252
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/252
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
status: contract-drafting
branch: change/252-offboard-five-projects
created: 2026-09-05
updated: 2026-09-05
---

# Spec 统一退出五个项目

## 目标与原因

把 rsdesign-new、HSDB、SFMDigitalBoard、WMPDA、SapTableMigrate 五个项目从 AISoft
平台治理中退出，使平台只治理 LocalWMS 与 NewEMaint 两个业务项目，外加
aisoft-platform 自身与 myapp、smoke-test 两个 public-test 夹具。

退出的含义是解除治理绑定与自动化，不是删除资产。判据：退出完成后，对这五个
project id 的任何 typed 操作返回 `requested project is not explicitly managed`，
而它们的 Gitea 仓库、分支保护、历史、Issue 与 PR 全部保持原状。

## 治理文件修改授权

本 spec 显式授权本次变更修改以下治理与共享契约文件。授权仅限本节列出的语义，
不授权任何其它治理放宽。

1. `codex/config/host-access-broker.json`：删除五条 `projects[]` 条目。
2. `codex/config/gitea-governance.json`：删除五条 `repositories[]` 条目，并重新
   pin NewEMaint `routine_live_pilot.non_target_repositories_sha256`。
   **重新 pin 的授权范围**：仅因本次退出导致非目标仓库集合合法收缩而重算，
   新值必须由 `repository_declarations_sha256(repositories, exclude_name='NewEMaint')`
   在同一 commit 的 manifest 上现算得出，并在 verification 中留下算式与取值。
   不得借此调整任何保留仓库的声明内容。
3. `codex/runtime/aisoft_host_access/contract.py`：VM profile 仓库集合由六个收敛为
   `aisoft-platform`、`NewEMaint`、`LocalWMS` 三个；timer 白名单由两个 unit 收紧为
   只剩 `aisoft-agent@emaintenance.timer`。两处都是收紧，不放宽。
4. `01-基础设施-VM-Gitea-Runner.md` 与 `06-运维手册与踩坑集.md`：更新读作当前状态的
   语句，并在 06 新增一条记录退出顺序与回滚方式的踩坑条目。
5. `03-Issue-Spec-Plan与单闸门开发流程.md`：更新两处随项目数变化的活语句
   （项目计数与 Gitea remote 名单）。

不在授权内：`AGENTS.md`、`README.md` 的治理条款、CI 与部署脚本、分支保护、
任何 provider 开关、任何保留项目的配置。

## Acceptance criteria

- [ ] AC-1 `codex/config/host-access-broker.json` 的 `projects[]` 与
      `codex/config/gitea-governance.json` 的 `repositories[]` 各只剩
      aisoft-platform、localwms、newemaint、myapp、smoke-test 五条。
- [ ] AC-2 在改后的仓库树上，
      `python3 -m aisoft_host_access.cli --access-manifest ... --governance-manifest ... validate`
      返回 `status: PASS` 且 `project_count: 5`。
- [ ] AC-3 `non_target_repositories_sha256` 的新值等于同一 commit 上现算的摘要。
- [ ] AC-4 `contract.py` 的 VM profile 集合为三个仓库，timer 白名单只剩
      emaintenance；两处都以收紧方向变更。
- [ ] AC-5 `bash codex/tests/smoke.sh` 全绿；`test-host-access-broker.sh` 的
      `project_count` 与新清单一致。
- [ ] AC-6 #172 的「project_id 不等于 repository」回归用例仍然存在，且由保留项目
      （localwms 或 newemaint）承载。
- [ ] AC-7 `smoke.sh` 的项目名禁写守卫正则逐字未变。
- [ ] AC-8 myapp 与 smoke-test 保留；`aisoft_gitea_governance` 的 public allowlist
      断言与 `test-project-check.sh` 的 myapp fixture 未受影响。
- [ ] AC-9 文档中读作当前状态的项目清单、端口表与 timer 表反映退出后状态；历史
      as-built 与踩坑证据保持可追溯，不被清洗。
- [ ] AC-10 06 新增一条踩坑条目，写明退出顺序与 `git revert` 加重装的回滚方式。
- [ ] AC-11 源码级回滚演练：在改后的树上 revert 治理 commit，`validate` 读回退出前
      的 `project_count: 10`，再重新应用后回到 5。
- [ ] AC-12 人工交接项清单完整落在 verification 中，未执行项如实标 NOT RUN：
      停用 sfm timer、清理三份 VM profile env 与 token、两台重装、八个 Gitea 身份
      的 token 撤销与 collaborator 移除与账号停用。
- [ ] AC-13 重装后对已退出 project id 的 typed 操作返回
      `requested project is not explicitly managed`；对保留项目
      `host.access.audit` 为 PASS、`host.onboarding.check` 无 GAP。AC-13 依赖人工
      重装，未执行则标 NOT RUN，不得推断。

## 接口、数据与兼容性影响

- broker 对外接口不变：操作目录仍是 33 条，参数集合逐条不变。变的只是 `--project`
  可接受的取值集合由十个收缩为五个。
- 已退出项目的本地 checkout 不受影响，仓库仍可用普通 Git 访问；只是不再有平台
  typed 操作与 project agent 凭据路径。
- 无数据库迁移。无外部 API 变更。

## 风险与回滚约束

- **顺序不可颠倒**：manifest 合并并重装后 broker 拒绝五个 project id，VM profile 的
  清理届时无 broker 路径。清理必须先于重装完成，或全部由人直接执行。
- **无删除路径是既有事实**：`ProfileMigrator` 无 retire 操作，
  `bootstrap-gitea-service-account.sh` 无回收操作。本次不新增破坏性 typed 操作
  ——为一次性退出给平台增加删文件与销账号的能力，风险高于收益。若退出成为常规
  动作，另开 Issue 评估。
- **回滚**：`git revert` 治理 commit 后两台重装即恢复原状；VM profile 与 Gitea 身份
  按 onboarding runbook 重新接入。源码级回滚在本次以 AC-11 演练证明。
- **封印重 pin**：重算摘要后，「pilot 期间非目标仓库声明未变」这条断言以新基线
  继续成立。原值与新值都记入 verification，使这次合法变更本身可审计。

## 非目标

- 不删除任何 Gitea 仓库、分支、Issue、PR，不 archive 仓库，不改分支保护。
- 不改 LocalWMS 与 NewEMaint 的任何配置。
- 不动项目仓内的 `AGENTS.md` 指针节与 `.gitea/workflows`。
- 不处理项目仓的 `.aisoft/architecture.json` 与 lock。
- 不新增任何 broker typed 操作。
- 不改 `smoke.sh` 的项目名禁写守卫正则。
- 不删除 PostgreSQL 的 `hsdb_ci` 数据库；01 中只把它标注为已退出待复核。

## 未决问题

无。
