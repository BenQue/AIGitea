---
issue: 275
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/275
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
branch: change/275-onboard-sfmdigitalboard
created: 2026-09-07
updated: 2026-09-07
---

# Spec 重新接入 SFMDigitalBoard

## 目标与原因

把 `SFMDigitalBoard` 加回两份治理 manifest，恢复 Mac 侧 typed 操作通道，使该项目
重新走 Issue → 判级 → 单 PR → 人工合并的标准流程。其余四个 #252 退出的项目保持退出。

判据：`--project sfm-digital-board` 的 typed 操作不再返回
`requested project is not explicitly managed`，`host.access.audit` PASS、
`host.onboarding.check` 无 GAP。

## 治理文件修改授权

授权仅限本节语义，不授权任何其它治理放宽。

1. `codex/config/host-access-broker.json`：`projects[]` 新增一条
   `sfm-digital-board`，`vm_profile: null`、`git_remote_name: "gitea"`。
2. `codex/config/gitea-governance.json`：`repositories[]` 新增一条
   `SFMDigitalBoard`，`change_control: development`、
   `routine_auto_merge_enabled: false`、
   `status_check_contexts: ["CI / verify (pull_request)"]`（读回值）。
3. `codex/config/gitea-governance.json`：重新 pin NewEMaint
   `routine_live_pilot.non_target_repositories_sha256`。**授权范围**仅因本次接入
   导致非目标仓库集合合法扩张而重算，新值须由
   `repository_declarations_sha256(repositories, exclude_name='NewEMaint')`
   在同一 commit 上现算得出，算式与新旧值记入 verification。不得借此调整任何
   既有保留仓库的声明内容。
4. 花名册耦合断言（`codex/tests/test-host-access-broker.sh`、
   `codex/runtime/tests/test_host_access.py`、
   `codex/runtime/tests/test_gitea_governance.py`）：只更新与项目集合直接耦合的
   取值，不改断言语义强度。`git_remote_name` 那一处由「只有 newemaint」改写为
   「声明该键的项目精确列举，且取值必须都是 gitea」——**强度提高**，不是放宽。
5. `03-Issue-Spec-Plan与单闸门开发流程.md` 与 `README.md` 中读作当前状态的项目
   计数与治理集合语句。

### 不在授权内

- `codex/runtime/aisoft_host_access/contract.py` 与
  `codex/runtime/aisoft_gitea_governance/contract.py`（保持 #252 的收紧状态）
- 另外四个已退出项目的任何恢复
- 分支保护、CI 定义、部署脚本、provider 开关
- routine auto-merge eligibility 的任何放宽
- SFMDigitalBoard 仓内任何文件
- `codex/tests/smoke.sh`（含项目名禁写守卫正则）

## Acceptance criteria

- [ ] AC-1 两份 manifest 各新增且仅新增一条 SFMDigitalBoard 条目；另外四个已退出
      项目仍不在清单内。
- [ ] AC-2 `validate` 返回 `status: PASS` 且 `project_count: 6`。
- [ ] AC-3 `non_target_repositories_sha256` 新值等于同一 commit 现算摘要；
      verification 记录算式、旧值、新值。
- [ ] AC-4 两个 `contract.py` 相对 `main` 零 diff。
- [ ] AC-5 `bash codex/tests/smoke.sh` 全绿（exit 0）。
- [ ] AC-6 `codex/tests/smoke.sh` 相对 `main` 零 diff（含项目名禁写守卫正则）。
- [ ] AC-7 源码级回滚演练：revert 治理 commit 后 `validate` 读回 `project_count: 5`，
      重新应用后回到 6。
- [ ] AC-8 人工交接项清单完整落在 verification，未执行项如实标 NOT RUN。
- [ ] AC-9 重装后 `host.access.audit` PASS、`host.onboarding.check` 无 GAP；
      `localwms` / `aisoft-platform` 同类回读不回归。依赖人工重装，未执行标 NOT RUN。
- [ ] AC-10 PR 的 required CI context 读回 `success`。

## 接口、数据与兼容性影响

broker 对外接口不变：36 条操作、参数集合逐条不变。变的只是 `--project` 取值集合
由五个扩为六个。无数据库迁移，无外部 API 变更。

## 风险与回滚约束

- **两份 manifest 必须同 commit**：`contract.py` 强制
  `repositories == set(governance_by_name)`，分步提交会让 broker 在中间态对全部
  项目 fail-closed。
- **封印必须同 commit 重算**：否则 governance contract 直接拒绝加载。
- **`git_remote_name` 不可为了让测试变绿而删除**：SFM checkout 的 `origin` 指向
  GitHub，删掉该键会让 `git.push.change` 推错仓库，且测试会变绿——这是本次唯一
  的「测试绿着失效」风险点。
- **回滚**：`git revert` 治理 commit 后两台重装即回到接入前；AC-7 做源码级演练。

## 非目标

- 不恢复 rsdesign-new、HSDB、WMPDA、SapTableMigrate
- 不恢复任何 VM profile、token 或 timer
- 不改分支保护、CI 定义、部署脚本
- 不启用 routine auto-merge，不恢复 `sfm-board-routine-merger`
- 不新增任何 broker typed 操作
