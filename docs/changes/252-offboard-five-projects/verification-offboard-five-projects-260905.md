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
status: pending
branch: change/252-offboard-five-projects
created: 2026-09-05
updated: 2026-09-05
---

# Verification 统一退出五个项目

## 基线与范围

- 基线：`origin/main` = 00f7d53（本分支已 rebase 到 #250 合并之后）
- 环境：Mac 本地 checkout。**已安装的 broker 仍是退出前的十项目版本**，两台重装是
  人工交接项，因此凡需要重装才成立的结论一律 NOT RUN，不由源码推断。
- 本记录负责证明的 acceptance criteria: AC-1 到 AC-13

## 改动前基线证据

合并后无法重放，先记录。全部取自**未重装**的 installed broker。

| 观测 | 取值 | 来源 |
|---|---|---|
| installed manifest 项目数 | 10 | `/usr/local/share/aisoft/host-access-broker.json` |
| 仓库树 manifest 项目数（改动前） | 10 | revert 后 `validate` |
| non-target 摘要原值 | 5629608e7f658aa55b0affd8e41f7b96dcfe6f2277fa5004b3e5d2c4614f0369 | manifest |
| 已退出项目当时可寻址 | `admin/SFMDigitalBoard` archived=False private=True | `--project sfm-digital-board --operation gitea.repo.read` |
| 只删 manifest 不改 contract 的后果 | `CONTRACT_INVALID: VM profile migration set must contain exactly the six approved repositories` | 候选 manifest 实测 |
| smoke 基线 | 671 tests OK | `bash codex/tests/smoke.sh` |

### 与本次变更无关的既有状况

以下两条在**未重装的 installed broker** 上观测到，因此早于本次变更，不由 #252 引入，
本次也不处理。

| 项目 | 结果 | 说明 |
|---|---|---|
| newemaint | `BLOCKED_EXTERNAL HTTP_403` | `host.access.audit` 连续两次同样 403，不是 `06` 踩坑里的偶发 `TRANSPORT_ERROR`。NewEMaint 是保留项目，值得单独立案。 |
| myapp | `BLOCKED_EXTERNAL CREDENTIAL_UNAVAILABLE` | public-test 夹具，`mac_checkout` 为 null，从未配发 project-agent 凭据，符合预期。 |

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| `validate`（改后仓库树） | PASS | `project_count: 5, operation_count: 33, merge_operation_count: 1` |
| `jq` 读回两份 manifest 条目 | PASS | projects 与 repositories 均为 aisoft-platform、localwms、myapp、newemaint、smoke-test |
| 现算 non-target 摘要并与 manifest 比对 | PASS | computed == pinned == `d64ccb588cecb6219b7d1b8c43caa13857ce4aaee42063045c53e052c69426c2` |
| `bash codex/tests/smoke.sh` | PASS | 672 tests OK；`Codex platform static smoke checks passed.` |
| `bash codex/tests/test-host-access-broker.sh` | PASS | `host access broker shell and installer tests passed`（该测试成功时不打印断言细节） |
| `bash codex/tests/test-bootstrap-gitea-service-account.sh` | PASS | `bootstrap Gitea service account tests passed` |
| `shellcheck` 三份改动的 shell 测试 | PASS | 无输出，退出 0 |
| `bash -n` 三份改动的 shell 测试 | PASS | 无输出 |
| `git diff origin/main -- codex/tests/smoke.sh` | PASS | 空 diff，守卫正则逐字未变 |
| 回滚演练：revert 治理 commit 后 `validate` | PASS | `project_count: 10, status: PASS` |
| 回滚演练：`git reset --hard` 还原后 `validate` | PASS | `project_count: 5, status: PASS`，工作树 clean |
| 重装后行为（已退出项目被拒、保留项目 audit） | NOT RUN | 需要两台 sudo 重装，人工交接项 H-3 |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | PASS | 两份 manifest 各只剩五条，见执行结果第 2 行 |
| AC-2 | PASS | `validate` 返回 `status: PASS`、`project_count: 5` |
| AC-3 | PASS | 现算摘要与 manifest 取值逐字相等 |
| AC-4 | PASS | contract.py diff 为 4 增 121 删中的两处收紧；VM profile 集合三个仓库，timer 白名单只剩 emaintenance |
| AC-5 | PASS | smoke 672 tests OK；`project_count` 断言已随清单改为 5 |
| AC-6 | PASS | #172 回归由 `test-mark-completed-issues.sh` 的合成夹具 `no-deploy-project` -> `NoDeployRepository` 与真实 `localwms` -> `LocalWMS` 两侧承载，两者都在保留范围内，未改动 |
| AC-7 | PASS | `smoke.sh` 空 diff |
| AC-8 | PASS | myapp 与 smoke-test 保留；`test_gitea_governance` 的 public allowlist 断言与 `test-project-check.sh` 的 myapp fixture 全绿 |
| AC-9 | PASS | 01/02/03/04/06/README 只改读作当前状态的语句；02 的 legacy 章节整节加退出说明，历史证据未删 |
| AC-10 | PASS | `06` 新增踩坑 23，含退出顺序、三处治理钉子、不重装验收命令与 revert 回滚方式 |
| AC-11 | PASS | 回滚演练两步都读回预期值 |
| AC-12 | PASS | 人工交接项清单见下节，未执行项全部 NOT RUN |
| AC-13 | NOT RUN | 需要人工重装，不由源码推断 |

## 人工交接项

平台没有对应 typed 操作，或需要 sudo，必须由人执行。

**顺序不可颠倒**：H-1 与 H-2 必须在 H-3 之前完成。重装后 broker 对已退出的
project id 一律返回 `requested project is not explicitly managed`，届时
`vm.profile.*` 也调不动，VM 上的 env 与 token 只能人工上机清理。

| 编号 | 动作 | 为什么不能由 agent 做 | 状态 |
|---|---|---|---|
| H-1 | 停用并禁用 `aisoft-agent@sfm.timer`，确认 `aisoft-agent@emaintenance.timer` 仍 active | 无 typed 操作，需 sudo | NOT RUN |
| H-2 | 删除 VM 上 `sfm` / `rsdesign` / `hsdb` 三份 profile env 与对应 project-agent token | `ProfileMigrator` 只有 plan/apply/read-back/consume-check/rollback，没有删除路径 | NOT RUN |
| H-3 | Mac 与 gitea-ci 两台重装 broker 与 host-role | 需 sudo | NOT RUN |
| H-4 | 撤销八个 Gitea 身份的 token | 无 typed 操作；`bootstrap-gitea-service-account.sh` 只能建不能收 | NOT RUN |
| H-5 | 从五个仓库移除对应 collaborator | 无 typed 操作 | NOT RUN |
| H-6 | 停用八个 Gitea 账号（`admin user` 层面停用，**不删除**，保留审计） | 无 typed 操作 | NOT RUN |
| H-7 | 关闭 rsdesign-new #19、HSDB #18、SFMDigitalBoard #112 | 三个仓已出平台范围 | NOT RUN |

八个身份：`rsdesign-agent`、`hsdb-agent`、`sfm-board-agent`、`wmpda-agent`、
`sap-table-migrate-agent`、`rsdesign-routine-merger`、`hsdb-routine-merger`、
`sfm-board-routine-merger`。

H-2 的路径由 manifest `vm_profile_policy` 与 `identity_bindings` 推出：
profile 在 `/home/coder/.config/aisoft/projects/<profile>.env`（`sfm.env`、
`rsdesign.env`、`hsdb.env`）；token 在
`/home/coder/.config/aisoft/credentials/projects/<project_id>/project-agent.token`
（`sfm-digital-board`、`rsdesign-new`、`hsdb`）；来源凭据在
`/home/benque/.config/aisoft/credentials/<agent>-project-agent.token`。
删除前先 `ls -l` 列清单并抄进本节，删除后按 H-3 重装再回读。

H-3 之后的回读（对应 AC-13）：

- 已退出：`--project sfm-digital-board --operation gitea.repo.read`
  应返回 `REQUEST_DENIED: requested project is not explicitly managed`。
- 保留：`--project localwms --operation host.access.audit` 应为 PASS，
  `--project aisoft-platform --operation host.onboarding.check` 应无 GAP。
- `newemaint` 的 HTTP 403 属既有状况，重装不会改变它，不要当成本次回归。

## 遗留风险与未完成项

- AC-13 与全部七个人工交接项 NOT RUN。未执行 H-1 到 H-6 之前，「退出」仅指平台
  源码不再治理这五个项目；VM timer 仍在跑，凭据仍然有效。
- `hsdb_ci` PostgreSQL 库按 spec 非目标保留，已在 `01` 标注为孤儿库待单独立案。
- NewEMaint 的 `host.access.audit` HTTP 403 是既有问题，建议单独立案。
- 计划的 touch points 未列 `02` 与 `04`，实际按 AC-9 的语义各改了一处读作当前状态的
  语句。范围未超出 spec 授权的「读作当前状态的语句」，如实记录该偏差。
