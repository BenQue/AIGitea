---
issue: 126
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/126
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 修改现有 company-delivery operator 的探测、安全、阶段依赖、制品、部署与回滚合同，并新增 greenfield 并行替换路径，命中多项强制 complex 规则
risk_flags:
  - schema-change
  - security
  - external-contract
  - shared-core
  - cross-module
  - ci-change
  - artifact
  - deployment
  - compatibility
  - rollback
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
documents:
  summary: summary-gitea-parallel-replacement-260817.md
  spec: spec-gitea-parallel-replacement-260817.md
  plan: plan-gitea-parallel-replacement-260817.md
  verification: verification-gitea-parallel-replacement-260817.md
status: approved
branch: change/126-gitea-parallel-replacement
pr_url:
created: 2026-08-17
updated: 2026-08-17
---

## 问题/需求总结

现有 company-delivery 1.0.1 把 PATH 中的 gitea binary 与 gitea.service 作为 Gitea 存在性依据，因此无法识别仅以 Docker 运行的 legacy Gitea，可能错误投影为 ABSENT。现有 Stage 20–50 又只支持无 current instance 的 side-by-side 或既有实例升级/恢复路径，无法表达保留 legacy Docker 实例不变、同时建立完全隔离的 binary + systemd + PostgreSQL 新实例。

## 影响范围

主要影响 company-delivery 的 inventory schema、collector/validator、compatibility matrix、Stage 依赖和 runbook，以及 bundle contract/version。预计涉及 codex/runtime/aisoft_company_delivery/collector.py、contract.py、bundle.py、company-delivery/schema/inventory-v1.schema.json、compatibility/newemaint-company-pilot-v1.json、runbook.md、README.md、VERSION、codex/runtime/tests/test_company_delivery.py、smoke 与 shell harness，并同步更新 README.md、07、12-Linux、13 等权威文档。该变更只交付 operator bytes、文档和验证证据，不授权 Stage 10 或任何公司 live action。

## 初步方案与建议

在新版 contract 中增加 collision-only、no-secret 的 Docker legacy presence、占用端口、容量和资源/路径冲突指纹，严格区分 confirmed absent、unknown 与 blocked；增加独立的 greenfield-parallel-replacement 决策 enum 和机器可验证的阶段图，允许明确跳过 legacy backup/restore/import，同时保持未运行阶段为 NOT RUN。compatibility/runbook 应锁定新 Gitea 与 PostgreSQL 的版本、checksum、identity、目录、数据库、端口和 FQDN，初始关闭 SSH、Runner、timer、Actions auto deploy 与 production gate，并在安装前后执行 legacy health gate。失败时只停止和隔离新实例，禁止修改或删除 legacy Docker resources。最后 bump operator version，重建 deterministic handoff，并覆盖 focused security negatives、full runtime、smoke、shell/JSON/schema、repeatability、tamper/no-secret 和 diff checks。

## 风险

- Docker presence 与端口探测若不完整，仍可能把 legacy 实例误判为 ABSENT，导致后续安装发生资源冲突。
- collector 必须在识别容器与冲突的同时避免读取 container env、Secret、app.ini、数据库、仓库内容或 raw logs；错误回显会破坏现有 no-secret 合同。
- greenfield 阶段跳过规则若与 evidence 状态机不一致，可能把未执行的 Stage 30/40 错写为 PASS，或错误解锁 Stage 50。
- 新实例的用户、目录、数据库、端口、FQDN、日志和回滚边界若未完全隔离，安装或失败清理可能影响 legacy Docker Gitea。
- operator/schema/version、compatibility、bundle payload 和权威文档若不同步，1.0.1 Stage 00 证据可能被错误复用于新流程。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 修改现有 company-delivery operator 的探测、安全、阶段依赖、制品、部署与回滚合同，并新增 greenfield 并行替换路径，命中多项强制 complex 规则
risk_flags:
  - schema-change
  - security
  - external-contract
  - shared-core
  - cross-module
  - ci-change
  - artifact
  - deployment
  - compatibility
  - rollback
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- origin/main:codex/runtime/aisoft_company_delivery/collector.py 将 Gitea 探测固定为 `gitea --version` 和 `gitea.service`；命令缺失且 unit 为 not-found/not-found 时会投影为 ABSENT/confirmed-not-installed。
- origin/main:company-delivery/schema/inventory-v1.schema.json 只建模 host、tools 与 systemd units，并把 Gitea ABSENT 绑定到 gitea.service 缺失；没有 Docker container presence、occupied ports、resource/path conflicts 或 legacy fingerprint 字段。
- origin/main:company-delivery/runbook.md 的 Stage 20 只允许 side-by-side、controlled-upgrade-candidate 或 BLOCKED，并把 side-by-side 限定为无 current instance；Stage 50 当前要求 Stage 40 PASS。
- origin/main:company-delivery/runbook.md 的 Stage 30/40 默认覆盖 Gitea backup 和 isolated restore，包括 DB、app.ini、keys、repositories、LFS、packages、attachments、avatars 与 external storage，与零 legacy 数据继承的 greenfield 路径不符。
- origin/main:company-delivery/compatibility/newemaint-company-pilot-v1.json 当前 pin Gitea 1.26.4 candidate 和两 VM policy，但没有 greenfield-parallel-replacement enum、legacy coexistence 或独立 namespace 合同。
- origin/main:codex/runtime/tests/test_company_delivery.py 明确测试缺少 gitea binary 且 gitea.service not-found 时得到 PASS inventory 和 Gitea ABSENT；现有 collector 测试没有 legacy Docker Gitea presence 用例。
- origin/main:codex/runtime/aisoft_company_delivery/bundle.py 将 company-delivery operator、runtime、compatibility 和 runbook 打入 deterministic handoff；现有测试固定 operator_version 为 1.0.1 和 handoff contract v1。
- origin/main:07-内网与生产平移路线.md 与 13-项目结果迁移与内网切换实施手册.md 明确 company-delivery Stage 00–110 是公司两 VM 的权威 operator 路径，并声明公司 live 阶段仍为 NOT RUN。

### 缺失的 acceptance criteria 或决策

- 在进入 approved 前，spec 需锁定新 Gitea/PostgreSQL 的 exact version 与上游 checksum，以及独立 Linux identity、目录、数据库、端口和 FQDN 的具体值。
- 需定义 greenfield 路径的精确阶段状态机：哪些 Stage 被跳过、它们如何保持 NOT RUN、Stage 50 的替代前置证据以及 validator 如何拒绝伪造 PASS。
- 需固定 legacy pre/post health 的 allowlisted probes、等价阈值和失败判定，并给出只隔离新实例的精确回滚目标与验收读回。
