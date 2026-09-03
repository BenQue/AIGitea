---
issue: 237
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/237
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 把 07 §5.1「新项目默认」措辞改成与 #232 一致的环境级口径，并对 company-delivery/ 逐文件判定归属（通用去项目名 / 迁 NewEmaint 项目仓 / 迁 archive）。改动的是平台治理文档、被 smoke.sh 与两份 company-delivery 测试守护的 operator bundle 文档，以及钉住文档短语的测试断言；判定为迁项目仓的内容只在平台侧改为指针并由 NewEmaint 仓 Issue 承接。命中 Agent/平台治理与 CI 守卫强制规则，effective complexity=complex；change_control=production 需 spec+plan，逐文件判定表进 spec
risk_flags:
  - platform-governance
  - ci-guard
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-deproject-company-delivery-260903.md
  spec: spec-deproject-company-delivery-260903.md
  plan: plan-deproject-company-delivery-260903.md
  verification: verification-deproject-company-delivery-260903.md
confidence: high
override_reason: ''
depends_on:
  - 233
status: pr-open
branch: change/237-deproject-company-delivery
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/238
created: 2026-09-03
updated: 2026-09-03
---

## 问题/需求总结

#233 收尾时盘点出两处与「项目相关内容由项目自身决定、平台只给环境级指导」（2026-09-02 定案）冲突的
项目专属残留：

1. `07-内网与生产平移路线.md` §5.1 标题「Linux 新项目默认与既有试点」与首句「新 Linux 项目采用
   Docker-first…」把一种交付形态写成平台默认，与 #232 runbook §4（平台只给 Linux 原生 / Linux 容器化 /
   Windows 三类原则，交付形态由项目声明）冲突。
2. `company-delivery/`（19 个文件）是 #120/#124/#126/#128/#130 的公司交付 pilot 产物，目录内 NewEmaint
   计 23 处：`README.md` 9、`runbook.md` 8、`compatibility/newemaint-company-pilot-v1.json` 1、
   `schema/inventory-v1/v2/v3` 2+1+1、`templates/handoff-manifest.example.json` 1。其中 inventory/handoff/
   evidence/gitea-transition schema 与 CLI 是通用交付合同；compatibility matrix、runbook 中的两台公司 VM
   细节与 Stage 进度、README 的 pilot 叙事是 NewEmaint 专属。

Issue 正文的「验收标准」与「非目标」是唯一合同；本 summary 与映射的 spec/plan 不扩张。

## 影响范围

- 平台仓活文档：`07`（§5.1 与 4 处 `company-delivery/` 引用句）、`README.md`（§1/§2/§5/§6 中的 pilot 状态与
  runbook 引用）、`company-delivery/README.md`、`company-delivery/runbook.md`、`company-delivery/schema/
  inventory-v{1,2,3}.schema.json`（只加 `$comment` 标注）。
- `archive/`：新增 pilot 历史记录文件与索引行（迁 archive 的内容）。
- 测试与守卫：`codex/tests/smoke.sh`（新增 `company-delivery/README.md`、`runbook.md` 项目名守卫）、
  `codex/runtime/tests/test_company_delivery.py`（一条钉住 runbook 短语的断言随 `newemaint-prod` →
  `<fixed-target-id>` 同步）；`test-company-delivery-real-release-harness.sh` 与 integration 测试保留不改。
- 下游：NewEmaint 仓另开承接 Issue（只开 Issue，不改该仓）；平台衍生 Issue：runtime 参数化
  compatibility 路径与 `aisoft-inbound-sync@newemaint.timer` unit 名后删除平台副本。
- 不动：`docker-release/`（#65 冻结）、`architecture/`、`codex/runtime/aisoft_company_delivery/`、broker、
  标签 manifest、`12`/`13` 正文（#233 F 组已判定保留为参考记录，链接目标不变）。

## 初步方案与建议

- 07 §5.1：标题改「Linux 容器化交付参考与既有试点」，首句改为「Linux 容器化项目可选用 `docker-release/`
  的 Docker-first、项目无关 release contract 作为参考实现；交付形态由项目声明，平台不设默认」；bullets
  保留为 contract 摘要；pilot 段落改为指向项目仓与 archive 的指针。
- `company-delivery/`：判定表见 spec §「逐文件归属判定表」。通用文件去项目名（角色描述、示例路径、
  target ID 占位符），runtime 硬绑定的 6 处 JSON 标识符保留并标注为 pilot 历史证据，pilot 事实迁
  `archive/company-delivery-pilot-历史-20260903.md` 并由 NewEmaint 仓 Issue 承接当前归属。
- `VERSION` 保持 `1.2.0`：operator 合同语义不变；bundle 字节变化按 runbook 既有规则由新 source SHA
  重新生成 handoff 承接。

## 风险

- runtime `bundle.py` 常量 `COMPATIBILITY_PATH` 与 `contract.py`/`collector.py` 的 timer unit 名绑定项目名；
  本 Issue 不改 runtime（非目标），因此 compatibility 文件与 schema enum 保留，作为显式残留衍生平台 Issue。
- `test_company_delivery.py` 钉住 `aisoft-docker-release-gate <action> newemaint-prod <full-sha>`；去项目名
  必须同步该断言（只改测试字面量，不改 runtime 包）。
- 新增 smoke 守卫必须反向证明会红（临时追加项目名后单独执行守卫块）。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 把 07 §5.1「新项目默认」措辞改成与 #232 一致的环境级口径，并对 company-delivery/ 逐文件判定归属（通用去项目名 / 迁 NewEmaint 项目仓 / 迁 archive）。改动的是平台治理文档、被 smoke.sh 与两份 company-delivery 测试守护的 operator bundle 文档，以及钉住文档短语的测试断言；判定为迁项目仓的内容只在平台侧改为指针并由 NewEmaint 仓 Issue 承接。命中 Agent/平台治理与 CI 守卫强制规则，effective complexity=complex；change_control=production 需 spec+plan，逐文件判定表进 spec
risk_flags:
  - platform-governance
  - ci-guard
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- Issue 正文自述 complex / production，要求 spec 先给逐文件判定表再实施。
- `codex/tests/smoke.sh:274–281` 对 `company-delivery/` 做 JSON 与 Secret 扫描，`:215–220` 运行两份
  company-delivery 测试；改动 CI 守卫命中「CI/制品/部署/回滚」强制规则。
- `codex/runtime/aisoft_company_delivery/bundle.py:33` `COMPATIBILITY_PATH` 与 `codex/runtime/tests/
  test_company_delivery.py:2948`、`:534` 绑定 `compatibility/newemaint-company-pilot-v1.json`；`:2926` 测试钉住
  runbook 短语 `aisoft-docker-release-gate <action> newemaint-prod <full-sha>`。
- `grep -rci NewEmaint company-delivery/` 基线合计 23，与 Issue 正文一致。
- 依赖 #231（`aefb135`）、#232（`0df9217`）、#233（`c98b2e5`）均已在 `origin/main` 历史中。

### 缺失的 acceptance criteria 或决策

- 无缺失验收标准。需在确认点 1 由人认可的 4 项解读见 spec「未决问题」（已给出建议并写入 AC）。

`## AI 判级` YAML 使用 analyzer 的唯一字段集合和顺序。
`required_docs` 使用语义角色：`small` 和 unresolved 只包含 `summary`；
`complex` 必须依次包含 `summary`、`spec`、`plan`；当本次变更的验收证据不能由
diff review 与 required CI 复现时，再追加 `verification`（判据见 `03` §3
「何时声明 `verification`」）。追加它表示这次变更**欠一份验证记录**，不表示
这次变更要部署——部署与迁移必然需要它，但不是只有它们需要。`documents`
把每个角色映射到同目录的 `<role>-<short-slug>-<YYMMDD>.md`；所有角色共用
2–4 词短 slug。
