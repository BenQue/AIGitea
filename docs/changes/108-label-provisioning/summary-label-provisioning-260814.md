---
issue: 108
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/108
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 变更对象是 canonical label manifest 的文件结构与语义（新增项目扩展前缀声明与退役取值声明）、host-access broker 的 typed 操作集合（新增仓库级 label 读取与 provision）、onboarding 的确定性步骤集合，以及两个既有 manifest 消费者的解析合同，属治理合同变更且触及共享核心与凭据路由，强制 complex
risk_flags:
  - platform-governance
  - shared-core
  - cross-module
  - credential-handling
required_docs:
  - summary
  - spec
  - plan
documents:
  summary: summary-label-provisioning-260814.md
  spec: spec-label-provisioning-260814.md
  plan: plan-label-provisioning-260814.md
confidence: high
override_reason: ''
depends_on: []
status: contract-drafting
branch: change/108-label-provisioning
pr_url:
created: 2026-08-14
updated: 2026-08-14
---

## 问题/需求总结

canonical label manifest 的四个维度（`type/*`、`complexity/*`、8 个生命周期、`triage/*`）
全部是**治理**维度，不表达「变更属于哪个功能域」与「优先级」。项目会话在实际工作中按需
自造标签填补空缺：NewEMaint 现有 36 个标签，canonical 24 个全在位，另有 12 个从未出现在
manifest 任何历史版本（`6aa8e07` 16 项 → `badd2eb` 17 项 → `1cbe714` 24 项）中。

这 12 个并非无人使用的垃圾——实测覆盖 37 个 Issue 引用。真正的缺口有四个：

1. **标签 provision 不是平台能力**。`onboarding-runbook.md:241-244` 用散文描述要建哪 24 个
   标签，但那是人工步骤描述，没有接进 onboarding 自动化；实现工具
   `codex/tools/sync-gitea-labels.sh` 存在却不在任何确定性步骤序列里。
2. **manifest 无项目扩展点**。`area/*`（6 个、22 次）与 `priority/*`（2 个、15 次）与治理
   四维正交且在用，但无处声明其合法性。`aisoft-project-check.sh:296-299` 已把非受管前缀
   降级为 `INFO` 而非 `GAP`，可那是**兜底放行**而非**按声明校验**——拼错的 `aera/web`
   同样只会得到 `INFO`。
3. **受管命名空间被侵入且证据不足**。`type/security`（8 次，高于多数 canonical type）、
   `type/reliability`（2）、`type/data`（1）落在受管 `type/*` 内。
   `aisoft-project-check.sh:301-307` 已正确判为 GAP，但只输出标签名，不输出所属 Issue 清单，
   人无法据此决定迁移。
4. **退役取值无迁移路径**。`complexity/standard` 仍挂在 2 个 Issue 上
   （佐证：NewEMaint `docs/changes/63-cleanup-obsolete-docs/summary-*.md` 的
   `effective_complexity: standard`）。`sync-gitea-labels.sh:76-96` 只增不删，退役值永不收敛。

## 影响范围

仅平台仓库。

- `codex/config/gitea-labels.json`：结构从裸数组演进为带 `schema_version` 的对象，新增
  `project_extensions` 与 `retired` 声明。
- `codex/agent/gitea-label-manifest.sh`（新增）：manifest 结构校验、canonical/前缀/退役取值
  读取与受管命名空间判定的共享库，并持有 provision 与 readback 共用的归一化定义，使两者
  对「是否漂移」不可能给出不同答案。
- `codex/tools/sync-gitea-labels.sh`：适配新 manifest 结构，新增幂等 provision 语义与
  drift 修复；不新增删除能力。
- `codex/tools/aisoft-project-check.sh`：`labels-readback` 按声明校验扩展前缀，受管命名空间
  冲突与退役取值在用时输出所属 Issue 清单。
- `codex/runtime/aisoft_host_access/{contract,broker,runner}.py`：新增 `gitea.labels.read` 与
  `gitea.labels.provision` 两个 typed 操作。
- `skill-for-codex/references/onboarding-runbook.md`：把散文步骤替换为确定性命令。
- `skill-for-codex/references/project-align.md`：checklist 第 4 行改述 `labels-readback` 的
  新判定依据（canonical + 声明扩展前缀 + retired）。
- `codex/tests/test-sync-gitea-labels.sh`、`test-project-check.sh`、
  `test-host-access-broker.sh`、`codex/runtime/tests/test_host_access.py`、`smoke.sh`。

不修改：`AGENTS.md` 的判级与单闸门合同、CI workflow、`install-vm.sh`、broker 的身份路由
矩阵与保护分支设置、任何项目仓库的实际标签。

## 初步方案与建议

1. **manifest 结构演进**：`{schema_version, canonical[], project_extensions{allowed_prefixes[]},
   retired[]}`。两个既有消费者同步适配，保留对旧裸数组的 fail-closed 拒绝（不静默兼容，
   避免半迁移状态）。
2. **新增两个 broker typed 操作**：`gitea.labels.read`（project-agent、只读）与
   `gitea.labels.provision`（project-agent、mutation、幂等）。**不新增删除操作**——这本身
   就是 AC-4「不通过静默删除实现」的机制保证。
3. **provision 语义**：缺失则创建，`color`/`description` 漂移则更新，`retired` 项不创建；
   已一致则 no-op。重复执行为幂等。
4. **核对语义**：符合 `allowed_prefixes` 声明的标签为 `PASS`（不再是兜底 `INFO`）；不符合
   任何声明且不在 canonical 内的报 `GAP`；受管命名空间冲突与 `retired` 在用报 `GAP` 并附
   所属 Issue 清单。
5. **onboarding 接入**：把 §5 的四条散文改为一条确定性命令，与 `host.access.audit` /
   `mac.git.bind` / `host.onboarding.check` 同级。

## 风险

- **manifest 结构破坏性变更**：两个消费者必须与 manifest 同批次交付，否则 `smoke.sh` 立即
  失败。缓解：同一 PR 内交付，且新增结构校验测试；这与 #111 记录的「共享消费者 + 逐项目
  迁移」升级顺序规则同源，但本次消费者全在平台仓内，无跨仓时序问题。
- **`type/*` 三个侵入标签的归宿需要人决策**，见 spec 未决问题。选错方向会导致 11 个 Issue
  的分类语义被改写。本 Issue 不执行任何标签迁移动作。
- **provision 幂等性**：若 Gitea 端 `description` 含尾随空白或大小写差异，可能产生反复更新
  的伪漂移。缓解：比较前做确定性归一化，并加针对性测试。
- **凭据路由**：新增 mutation 操作走 project-agent。已确认 project-agent 的 token scope 含
  `write:issue`（Gitea label 端点属 issue scope），无需 manager 身份。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 变更对象是 canonical label manifest 的文件结构与语义（新增项目扩展前缀声明与退役取值声明）、host-access broker 的 typed 操作集合（新增仓库级 label 读取与 provision）、onboarding 的确定性步骤集合，以及两个既有 manifest 消费者的解析合同，属治理合同变更且触及共享核心与凭据路由，强制 complex
risk_flags:
  - platform-governance
  - shared-core
  - cross-module
  - credential-handling
required_docs:
  - summary
  - spec
  - plan
confidence: high
override_reason: ''
```

### 判级证据

- 强制 complex 规则命中「Agent/治理」：变更对象包含 canonical label manifest 与 onboarding
  确定性步骤，二者都是治理合同。
- 强制 complex 规则命中「共享核心」：`gitea-labels.json` 被 `sync-gitea-labels.sh` 与
  `aisoft-project-check.sh` 共同消费，broker `contract.py` 的 `EXPECTED_OPERATIONS` 被
  broker/runner/两套测试共同消费。
- 强制 complex 规则命中「外部契约」：新增 typed 操作即扩展 broker 对外操作面。
- `contract_effect: change`（非 `add`）的依据：`gitea-labels.json` 现有裸数组格式是既有
  解析合同，本次改变它；新增能力叠加在结构变更之上。
- 无部署影响，故 `required_docs` 不含 `verification`：本变更不产出制品、不触及
  AppServer/production，`ops/` 与 `docker-release/` 不在影响范围内。

### 缺失的 acceptance criteria 或决策

- **未决（需人决策）**：`type/security`、`type/reliability`、`type/data` 是纳入 canonical
  第 8–10 个 type，还是迁移到扩展维度。spec 给出建议方案与理由，进入 `approved` 前必须由
  人拍板。
- 已澄清（不再未决）：本 Issue 与 #115 的边界——#115 的
  `gitea.issue.labels.*` 是 Issue 级标签挂载（`/issues/{index}/labels`），本 Issue 需要的是
  仓库级标签定义 provision（`/repos/{owner}/{repo}/labels`），是两个不同的 Gitea API 面。
  故本 Issue **不阻塞于 #115**，AC-5 由本 Issue 自带的两个 typed 操作满足。
- 已澄清（不再未决）：#111 已于 PR #114 合并，`sync-gitea-labels.sh` 已通过
  `codex/agent/gitea-token.sh` 支持 `GITEA_TOKEN_FILE`，AC-5 的「不依赖内联 token」部分
  已具备基础。
