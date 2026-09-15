---
issue: 293
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/293
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 把 12-Windows §2、07 §1 与 onboarding-runbook §4 对齐到 2026-09-15 决定的「本机构建、本地测试、GitHub Release 资产中转、公司 Gitea 只核验与独立授权部署」路线，并在 runbook §4.4/§4.5 与项目 AGENTS.md 模板新增 producer 钉版本不变量与 release_producer/transport 声明位。只改文档与模板，但改的是平台交付合同本身（结果定义、构建位置、GitHub 角色、新增不变量），contract_effect=change；onboarding-runbook 安装为两侧 Agent 行为源、templates/project/AGENTS.md 复制进每个下游项目，命中 Agent/平台治理强制规则，effective complexity=complex，需 spec+plan
risk_flags:
  - platform-governance
  - agent-governance
  - external-contract
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-delivery-producer-align-260915.md
  spec: spec-delivery-producer-align-260915.md
  plan: plan-delivery-producer-align-260915.md
  verification: verification-delivery-producer-align-260915.md
confidence: high
override_reason: ''
depends_on: []
status: pr-open
branch: change/293-delivery-producer-align
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/294
created: 2026-09-15
updated: 2026-09-15
---

## 问题/需求总结

2026-09-15 调度会话与用户复核部署方案后决定：现阶段所有项目采用「本机（Mac）构建 → 本地 OrbStack
测试 → 发布包以 GitHub Release 资产中转 → 公司内网 Gitea 只做核验与独立授权部署」；GitHub Actions
构建只作候选，一个项目只能选一种 producer；公司内网不能联网构建。Issue #293 正文列出平台参考文档与
该路线的 5 处不一致或缺失，本 summary 以它为合同、不扩范围：

1. `12-Windows平台自动部署方案.md` §2「已确认决策」表仍写公司 Windows x64 Runner 构建、公司 Gitea
   唯一正式权威源、GitHub 与公司 Gitea 无关系，与 07 §1（2026-08-11 双权威定案）及本次决定冲突。
2. `07-内网与生产平移路线.md` §1「结果」定义把原型制品整体排除在迁移之外，未区分已测试的 versioned
   release bundle，也未把 GitHub Release 资产列为允许的传输介质。
3. `skill-for-codex/references/onboarding-runbook.md` §4.4 不变量缺 producer 可复现约束（固定版本 SDK
   容器构建、lock 文件进仓库、locked-mode restore）。
4. 全部文档未提及 arm64 Mac 上 linux/amd64 交叉构建（buildx / OrbStack Rosetta），以及 DockerLab 模拟
   amd64 运行时的测试证据应标注 emulated。
5. runbook §4.5 与 `templates/project/AGENTS.md`「项目事实」缺 `release_producer`（local 或 github）与
   transport 的项目级声明位；GitHub Actions 构建未作为候选记录适用条件。

## 影响范围

- `12-Windows平台自动部署方案.md`：§2 决策表改写三行并新增传输行；§3 拓扑图与角色表把「公司
  Windows x64 Runner 构建」改为本机 producer 与 GitHub Release 中转；§5 构建顺序注明 producer 位置与
  locked-mode；§8 把「Runner」措辞改为部署执行端；§13 非目标补「公司内网联网构建」。
- `07-内网与生产平移路线.md`：§1 第 2 条 GitHub 角色改为原生 Push Mirror 与 Release 资产中转，新增
  构建位置一条，「结果」段落改写为含已测试 versioned release bundle 与允许的传输介质；§2 拓扑图仅当
  确认点 1 认可时把公司侧「Windows x64 Runner 构建」节点改为核验入口（见未决问题）。
- `skill-for-codex/references/onboarding-runbook.md`：§4.2 补 arm64 交叉构建与 emulated 证据标注；§4.4
  新增 producer 工具链钉版本不变量；§4.5 新增 `release_producer` 与 transport 声明要求及 GitHub Actions
  候选适用条件。该 references 同时装进 Claude 侧 `aisoft-platform` skill，改后本机 `check-drift.sh`
  会报 DRIFT，需 `bash skill-for-claude/install.sh` 重装回 CLEAN。
- `templates/project/AGENTS.md`：「项目事实」新增 `release_producer` 与 `transport` 两个占位字段。
- 本仓语义文档 `docs/changes/293-delivery-producer-align/`。

不改：根 `AGENTS.md`、`README.md`（除非需要交叉引用）、`06`、`13`、`14`、`15`、`12-Linux`、
`codex/runtime/`、`codex/tools/`、`codex/config/`、`codex/tests/`、`docker-release/`、`company-delivery/`、
`architecture/`、`sync/`、任何 CI workflow 或 manifest；不改变合同语义以外的任何部署行为；company-delivery
Stage 00–110 与 docker-release consumer 合同不动；平台 #292 不动。

## 初步方案与建议

1. 以 Issue 正文 6 条验收标准为合同源；spec 把每一处改动落成「文件:位置 → 现状 → 改后」清单，行号以
   `origin/main` = `a2f8854`（PR #291 merge）为准。
2. 三份文档对同一事实统一措辞：本机 Gitea 是唯一源码源（开发权威）；构建位置在开发侧
   （`release_producer=local` 为默认，`github` 为候选，一个项目只能一种）；GitHub 私有仓是本机 Gitea 的
   原生 Push Mirror（NewEMaint #80 路线）并以 Release 资产中转已测试发布包；公司内网 Gitea 是部署权威，
   只核验校验和与 release SHA 并独立授权部署；GitHub 不进入公司信任链。
3. 改文档前先核对 `codex/runtime/tests` 与 `codex/tests/smoke.sh` 钉住的 07 短语（「两台公司」「本地
   OrbStack」「exact `docker-release/v2` bytes」「公司要求内网重建」「BLOCKED」「生产环境只执行版本化、
   已验证、可回滚的确定性脚本，不安装或调用 AI」「Architecture catalog 采用门」「company-delivery/runbook.md」）
   与 runbook 短语（`ensure-gitea-collaborator.sh`、`gitea-governance.json`、`gitea.labels.provision`、
   「Architecture declaration onboarding」）；本次只增不删。
4. 验证：`bash codex/tests/smoke.sh` 全绿；`PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests`
   全量通过；`check-change-documents` PASS；Issue AC-1 三句在 12-Windows 的 rg 命中为 0；
   `skill-for-claude/check-drift.sh` 重装后 CLEAN；逐条记入映射的 verification。
5. 唯一最终 PR 为 manual，由人合并；不部署。

## 风险

- 治理文件：onboarding-runbook 与 `templates/project/AGENTS.md` 都在 `smoke.sh` 的 governance_set 里，
  且由 installer 复制为两侧 Agent 行为源；改动由 spec 显式授权，不触碰根 `AGENTS.md`。
- 项目模板解析：`aisoft-project-check.sh` 从「交付形态」bullet 起读到下一个 bullet 为止判占位符；新增
  两行放在「部署方案位置」之后、作为独立 bullet，且不含 `docker-release/v2`、`PM2`、`Windows/IIS`
  三个命中词，不会让已对齐项目的 delivery-profile 检查变红。
- 措辞冲突：07 §2 拓扑图仍画公司侧 Windows Runner 构建；若确认点 1 不授权改图，则在 verification 记录
  并另开衍生 Issue，不在本 PR 顺手扩范围。
- 数字与日期：12-Windows §2 历史注记写明 2026-09-15 与 07 §1 的 2026-08-11 两个日期，避免再次漂移。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 把 12-Windows §2、07 §1 与 onboarding-runbook §4 对齐到 2026-09-15 决定的「本机构建、本地测试、GitHub Release 资产中转、公司 Gitea 只核验与独立授权部署」路线，并在 runbook §4.4/§4.5 与项目 AGENTS.md 模板新增 producer 钉版本不变量与 release_producer/transport 声明位。只改文档与模板，但改的是平台交付合同本身（结果定义、构建位置、GitHub 角色、新增不变量），contract_effect=change；onboarding-runbook 安装为两侧 Agent 行为源、templates/project/AGENTS.md 复制进每个下游项目，命中 Agent/平台治理强制规则，effective complexity=complex，需 spec+plan
risk_flags:
  - platform-governance
  - agent-governance
  - external-contract
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- 根 `AGENTS.md` 工作原则：「外部契约……以及 Agent 或平台治理变更一律按 complex 处理」；「只有 complex
  变更映射的 `spec` 明确授权时，才能修改 `AGENTS.md`、Agent 行为……或其他治理文件」。
- `codex/tests/smoke.sh` governance_set 显式包含 `templates/project/AGENTS.md`；`skill-for-claude/install.sh`
  与 `codex/install-skills.sh` 把 `skill-for-codex/references/onboarding-runbook.md` 复制为两侧 skill 的
  references（#264 先例同样据此判 complex）。
- `contract_effect: change`：07 §1「结果」定义从「原型制品不迁移」改为「已测试 versioned release bundle
  可迁移」，runbook §4.4 新增一条不变量、§4.5 新增两个必填声明；这些是对下游项目生效的合同文字，
  不是目录或日期补齐（对照 #264 的 unchanged）。
- `change_type: platform`：`type/platform` 定义为「平台、Agent、CI、部署或治理合同变更」；`type/docs` 定义为
  「仅修改文档……不改变运行行为」。本次运行行为确实不变，但改的是治理合同文字，两者都可成立；取
  platform 是因为 contract_effect=change，routine_merge 与 FORCED_COMPLEX_TYPES 对两者结论一致（manual、
  complex），不影响路由。
- `verification` 的声明依据是 `03` §3：AC-1 的跨文档一致性 rg、`check-drift.sh` 改前 DRIFT/重装后 CLEAN
  的前后观测、全量 Python 测试都是 required CI（只跑 smoke）不复现的确定性命令或一次性观测。

### 缺失的 acceptance criteria 或决策

- 无缺失的验收标准。两项解读已在确认点 1（2026-09-15）由用户认可：（a）`change_type` 取 `platform`；
  （b）07 §2 拓扑图公司侧「Windows x64 Runner · React + .NET 构建」节点在本 PR 内最小改写为「公司
  scm-ci 核验 Release 资产」，纳入范围。
