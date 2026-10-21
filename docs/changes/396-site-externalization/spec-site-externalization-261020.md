---
issue: 396
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/396
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - shared-core
  - schema-change
  - cross-module
  - rollback
  - platform-governance
depends_on:
  - 391
status: approved
branch: change/396-site-externalization
created: 2026-10-20
updated: 2026-10-20
git_scope:
  - docs/changes/396-site-externalization/summary-site-externalization-261020.md
  - docs/changes/396-site-externalization/spec-site-externalization-261020.md
  - docs/changes/396-site-externalization/plan-site-externalization-261020.md
  - docs/changes/396-site-externalization/verification-site-externalization-261020.md
  - 01-基础设施-VM-Gitea-Runner.md
  - 07-内网与生产平移路线.md
  - 13-项目结果迁移与内网切换实施手册.md
  - README.md
  - codex/config/host-access-broker.json
  - codex/config/project-leak-baseline.json
  - codex/lib/install-source-guard.sh
  - codex/runtime/aisoft_host_access/broker.py
  - codex/runtime/aisoft_host_access/contract.py
  - codex/runtime/aisoft_host_access/credential_rotation.py
  - codex/runtime/aisoft_loop/documents.py
  - codex/runtime/tests/rotation_cli_fixture.py
  - codex/runtime/tests/test_credential_rotation.py
  - codex/runtime/tests/test_host_access.py
  - codex/runtime/tests/test_project_leak.py
  - codex/tests/check-project-leak.py
  - codex/tests/fixtures/manifests/README.md
  - codex/tests/fixtures/manifests/host-access-broker.json
  - codex/tests/test-host-access-broker.sh
  - codex/tests/test-registry-preflight.sh
  - codex/tools/apply-classification-labels.sh
  - codex/tools/install-runner-flutter.sh
  - docs/governance/remediation-roadmap.md
  - skills/aisoft-platform/SKILL.md
  - skills/aisoft-platform/references/onboarding-runbook.md
  - skills/aisoft-platform/references/private-gitea-access.md
  - templates/project/ci/ci.yml
  - templates/project/ci/registry-preflight.sh
  - usage/bundle.json
---

# #396 spec：站点外置与守卫补齐（R13）

> 负责人 2026-10-20 15:21Z 确认本合同。Issue：[#396](http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/396)；分支 `change/396-site-externalization`，worktree `/private/tmp/issue-396-site-externalization`（基于 `origin/main` `08be6f4`）。任务书：`platform-remediation-plan-261020-final.md` §4 R13 与 §6；D5 = a。

## 判级

| 字段 | 值 |
|---|---|
| change_type | platform |
| complexity | **complex**（production：spec + plan + verification） |
| contract_effect | change |
| risk_flags | shared-core、schema-change、cross-module、platform-governance、rollback |
| 理由 | 改 broker manifest schema 与 `aisoft_host_access` 合同校验、broker 与轮换读取路径、泄漏守卫、技能与下发模板（发布包成员），合并后两台重装 |
| verification | 需要：合并后两台重装读回无法由 diff review 与 CI 重放 |

## 已核对的事实（2026-10-20，`origin/main` `08be6f4`，只读）

1. 站点字面量在内核代码里只剩 `aisoft_host_access/contract.py` 四处：凭据根 `:358`、owner `:361`、机器 `:371`、运维账号 `:372`（`:297` 的 `environment` 是拓扑类型，不算站点值）。broker、轮换、runner 已全部从 manifest 读值：`broker.py` 9 处读 `raw["mac_host"]`（其中 5 处读本批要迁的三个键），`credential_rotation.py` 4 处。
2. Gitea 地址只在 governance manifest 的 `base_url`；所有 runtime 读者都走 `contract.governance.base_url`。
3. 任务书里的 `codex/global-AGENTS.md` 与 `smoke.sh:514` 已在 R8/R10a 删除，本批无事可做。
4. 泄漏守卫 `check-project-leak.py` 只收 `classification == internal-application`，漏了 `myapp`、`smoke-test`（`public-test`）；没有站点值集合。
5. 若按本合同的站点值集合（见决定 4）计数，允许区之外现有 29 个文件 107 处：文档 `01`/`README`/`02`/`03`/`05`/`07`/`12`/`13`、`architecture/evidence` 与三份 decision、`skills/aisoft-platform` 三个文件、`templates/project/ci` 两个文件、`codex/tools` 七个文件、`contract.py`、两处代码注释。
6. `templates/project/ci/ci.yml` 是发布包 `seed` 成员（只在采用时复制一次），已采用的项目不受模板改动影响。
7. 并行批次：R10b（#395）改的是 `aisoft_loop` 的 summary front matter 解析与 `skills/aisoft-platform/SKILL.md`（新增「路由」一节），与本批的 `aisoft_host_access/contract.py` 不是同一文件；`SKILL.md` 两批都改，本批只动 `:14` 一行。R10b 预定发布包 1.5.0。

## 决定（确认点 1 默认值，负责人可覆盖）

1. **一处来源，迁移而不复制。** manifest 新增 `site` 段，八个键：`gitea_url`、`orbstack_machine`、`orbstack_user`、`credential_root_mac`、`credential_root_vm`、`platform_checkout_mac`、`platform_checkout_vm`、`npm_registry`。`mac_host` 的 `credential_root`、`orbstack_machine`、`orbstack_user` 删除并迁入 `site`，`broker.py` 与 `credential_rotation.py` 改读 `site`。与别处已有的声明做一致性校验，不另立第二来源：`gitea_url` 必须等于 governance `base_url`；`platform_checkout_mac` 必须等于 `public-platform` 仓库对应项目的 `mac_checkout`。
2. **结构校验取代字面量。** 路径必须是绝对路径；`credential_root_mac` 不得落在任何项目 `mac_checkout` 或 `platform_checkout_mac` 之内（原来「固定在仓库之外」的意图）；机器名与账号是合法标识符；`mac_host.credential_owner` 保留并要求等于 `site.orbstack_user`（同一位 Mac 运维账号既持有凭据又执行 `orb`，现值也一致）；`npm_registry` 是不带凭据、query、fragment 的 http(s) URL。`environment == local-orbstack`、`vm_runtime.runtime_user`、轮换策略里 `/usr/local/...` 的安装约定路径不是站点值，保持原样。
3. **下发模板改占位。** `ci.yml` 的 `NPM_CONFIG_REGISTRY` 改为字面占位 `REPLACE_WITH_SITE_NPM_REGISTRY`，注释写「取值见平台 manifest `site.npm_registry`」。不用 `${AISOFT_NPM_REGISTRY}`：Gitea Actions 的 `env:` 不展开 shell 变量，会把这串字面量交给 npm。占位不替换时 `registry-preflight.sh` 在依赖安装前失败（fail closed）。备选是 `${{ vars.AISOFT_NPM_REGISTRY }}`，要求各项目在 Gitea 设变量，属新外部依赖，本批不选。
4. **守卫两组集合，同一棘轮。** 项目名 = `repositories[]` 中除 `public-platform` 外全部仓库及其 `project_id`（新增 `myapp`、`smoke-test`）+ retired。站点值 = `site` 段的八个值（URL 取 host:port），按最长优先匹配计数，路径里的账号不重复计。允许区与项目名相同。基线文件分两个键（`files` 不变，新增 `site_files`），只减不增；新文件出现任一值即红。
5. **本批清到零的位置**：`contract.py`、`skills/aisoft-platform/` 三个文件、`templates/project/ci/` 两个文件、四处代码注释（`install-source-guard.sh`、`apply-classification-labels.sh`、`install-runner-flutter.sh`、`documents.py`），以及 `01`/`07`/`13`/`README` 里硬写的 public allowlist（改为「以 manifest `classification: public-*` 为准」）。其余文档与 `architecture/evidence` 的站点值进基线，由 R14 文档现行态处理；`codex/tools` 里 VM 侧脚本可由环境变量覆盖的默认路径（`gitea-readonly.sh`、`bootstrap-gitea-service-account.sh`、已退役的 `ensure-gitea-collaborator.sh`）与 `rotate-gitea-service-account.md` 进基线，不在本批改写。
6. **发布包** 取合并时下一个空闲版本。R10b 先合并则本批用 merge commit 集成 `main` 后发 1.6.0；本批先合并则发 1.5.0，R10b 顺延。

## Acceptance criteria

1. **AC1 代码不钉字面量**：单测把 `site` 整组换成另一组结构合法的假值（机器、账号、路径、URL 全换，governance `base_url` 与平台 `mac_checkout` 同步换）后 `load_access_contract` PASS；结构非法的值（相对路径、凭据根落在 checkout 内、`gitea_url` 与 `base_url` 不一致、owner 与运维账号不一致、registry 带凭据）各自被拒。`rg` 证明 `aisoft_host_access/*.py`（测试除外）不再含 `benque`、`gitea-ci`、`/Users/`。
2. **AC2 守卫反向证明**：在守卫范围内一个不在基线的文件里各塞一处 `smoke-test` 与 `gitea-ci.orb.local`，守卫分别变红；删掉后恢复绿。两条做成 `test_project_leak.py` 用例，另在 worktree 里手工跑一次并记录输出。
3. **AC3 清零位置**：决定 5 列出的文件在两组集合下计数为 0，基线里没有它们。
4. **AC4 broker 行为不变**：`test_host_access*`、`test_credential_rotation`、`test-host-access-broker.sh` 全过；源码 runtime 用真实 manifest 跑一次只读 `host.access.audit` 与 `validate`，结果与改动前一致。
5. **AC5 全量验证**：`bash codex/tests/smoke.sh` 全绿；`usage-bundle.sh --verify` 通过；Codex 只读交叉审查 PASS（记录写项目库 `codex-review-396.md`）。
6. **AC6 合并后读回**（负责人 sudo，会话读回）：两台重装 broker 后 `check-installed-drift` 的 `install-host-access-broker` 面 PASS（34/34），`host.access.audit` 不劣于改动前（5 PASS，`myapp`、`smoke-test` 为既有 `CREDENTIAL_UNAVAILABLE`）。

## 接口、数据与兼容性影响

- manifest schema 变化：旧 broker 读新 manifest 会因 `_exact_keys` 拒绝，反之亦然。installer 同时装代码与 manifest，所以重装前已安装的 broker 不受影响；源码 runtime 与已安装版本在合并到重装之间不一致，只影响用源码 runtime 做的候选验收。
- 发布包：`ci.yml`（seed）与 `aisoft-platform` 技能改动，已采用项目只在升级发布包时看到新占位。
- 测试夹具 manifest 同步改，夹具 README 说明同步。

## 风险与回滚约束

- 回滚 = revert 合并提交后两台重装 broker；manifest 与代码同一提交，不存在只回一半的状态。
- 不动凭据文件、grant 文件与 VM 副本；轮换 grant 里的 `credential_root` 仍与 manifest 值逐字比较，值不变。
- 与 R10b 冲突面：`skills/aisoft-platform/SKILL.md`、`usage/bundle.json` 与发布记录。后合并者 merge commit 集成，不 rebase。

## 非目标

多站点部署；凭据实际位置与 VM 副本；governance manifest 结构；`environment` 与轮换安装约定；VM 工具脚本的默认路径改写；文档站点值的整体改写（R14）；`check-installed-drift` 的 `applies_to`（R16）。

## Ticket 草图

| Ticket | 内容 |
|---|---|
| T01 | 技能与模板（治理文件）：`SKILL.md:14`、两份 references、`ci.yml` 占位、`registry-preflight.sh`；单独 commit 后停下重读 |
| T02 | manifest `site` 段 + `contract.py` 结构校验 + broker/轮换读取迁移 + 夹具 + 单测（AC1、AC4） |
| T03 | 泄漏守卫两组集合 + 基线 + 反向证明用例（AC2、AC3）；文档 public allowlist 指向 manifest；注释清理 |
| T04 | 发布包升版、路线图状态、全量 smoke、Codex 审查、判级投影（AC5） |
