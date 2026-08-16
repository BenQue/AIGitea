---
issue: 120
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/120
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 本 Issue 覆盖既有三角色公司拓扑并新增跨同步、制品、安全、部署与回滚的公司 operator 合同及结构化 schema，命中多项强制 complex 规则
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
  summary: summary-company-delivery-pilot-260816.md
  spec: spec-company-delivery-pilot-260816.md
  plan: plan-company-delivery-pilot-260816.md
  verification: verification-company-delivery-pilot-260816.md
status: spec-drafting
branch: change/120-company-delivery-pilot
pr_url:
created: 2026-08-16
updated: 2026-08-16
---

## 问题/需求总结

当前仓库把公司 Linux 交付描述为 scm-ci、appserver-test、appserver-prod 三个隔离 machine identity；Issue #120 以两台公司 VM 加本地 OrbStack DockerLab 覆盖这一假设，并要求建立不连接公司内网、不执行部署的可携带人工交付工作流，包括脱敏 inventory、分阶段 runbook、checksum-pinned handoff、结构化 evidence、Gitea 安装或升级决策、备份恢复与回滚合同。

## 影响范围

预计需要修订 README.md、07-内网与生产平移路线.md 和 12-Linux-GitHub-Gitea-双服务器自动部署方案.md 的拓扑与权威边界，并新增版本化 operator bundle、inventory/handoff/evidence schemas、只读 collectors 和阶段 runbook。实现应复用而非绕过 sync/inbound-sync.sh、sync/install.sh、docker-release/schema/release-manifest-v2.schema.json、codex/runtime/aisoft_release/contract.py、runner.py、gate.py 及 codex/tools/verify-host-role.sh。测试面至少涉及 sync/tests/test-inbound-sync.sh、codex/runtime/tests/test_release_contract.py、test_release_transport.py、test_release_gate.py、test_release_safety.py、codex/tests/test-host-role-guard.sh 和 codex/tests/smoke.sh；公司及生产验证仍必须记录为 NOT RUN。

## 初步方案与建议

先用 spec 和 plan 固定两台公司 VM、本地 DockerLab、公司侧不重建不同 bytes、逐阶段人工批准及 fail-closed BLOCKED 语义。随后建立自包含且 checksum 固定的 operator bundle：collector 仅执行 allowlisted read-only probes并默认脱敏；handoff manifest 绑定 bundle 版本、full Git SHA、docker-release/v2 release identity、逐文件 SHA256、架构和兼容矩阵；evidence schema 分离 observed、changed、verified、pending 及 PASS、FAIL、BLOCKED、NOT RUN。runbook 应逐阶段定义前置条件、停止点、失败处置、回滚边界和 evidence 输出，并显式覆盖 Gitea side-by-side/controlled-upgrade 决策、完整备份与 isolated restore drill、one-shot inbound reconcile、Runner/Registry 正负验证、artifact-only verification 及 fixed production action gate。使用 fake/disposable 环境覆盖 checksum 篡改、错误 SHA/digest/架构、Secret sentinel、权限过宽和 timer/Actions 保持禁用等负向测试，不执行任何公司或生产动作。

## 风险

- 若只改部署示意而未同步现有三角色合同，operator 可能错误地把业务 runtime 或数据库放到 scm-ci，或误删仍适用于本地测试环境的 appserver-test 角色。
- handoff manifest、SHA256 或 release identity 绑定不完整会允许公司侧重建不同 bytes 后冒充已验证制品。
- inventory、命令输出、日志或 evidence 的脱敏不完整可能泄露 PAT、SSH key、数据库连接或其他 Secret。
- Gitea controlled upgrade 若未覆盖数据库、配置、repositories、LFS、packages、attachments 和 external storage 的完整备份及隔离恢复演练，失败后可能无法可靠回滚。
- 普通 Runner 若能获得生产 SSH、sudo、数据库权限或任意命令入口，会绕过 fixed action、target_id、full SHA 和人工阶段闸门。
- 本地 DockerLab、fake tests 或绿色 CI 可能被错误投影为公司 Runner/Registry、AppServer 或生产 PASS；这些 live 状态必须保持 NOT RUN。
- 公司架构、Docker Engine/Compose/image-store 或离线政策若不满足已固定兼容矩阵，必须返回 BLOCKED；不得通过放宽验证或内网重建规避。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 本 Issue 覆盖既有三角色公司拓扑并新增跨同步、制品、安全、部署与回滚的公司 operator 合同及结构化 schema，命中多项强制 complex 规则
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

- README.md 当前将独立 appserver-test 作为新 Linux 强制职责合同，并明确业务 Registry、AppServer 与 production 尚未验收。
- 12-Linux-GitHub-Gitea-双服务器自动部署方案.md 明确要求 scm-ci、appserver-test、appserver-prod 三个隔离 machine identity，与 Issue #120 的两台公司 VM 决策存在需要受控更新的合同差异。
- codex/config/host-capabilities.json 允许 scm-ci 构建、测试和发布制品，但不允许 application deploy/start 或 business-database use；appserver-prod 才拥有生产 runtime 能力。
- sync/inbound-sync.sh 只提供 allowlisted main 的 reconcile、immutable sync branch 和公司 Gitea PR，不写或合并 main，并对 history rewrite 与冲突 branch fail closed。
- sync/install.sh 只安装 runtime、示例和 systemd 模板，明确不创建凭据且 timer 保持 disabled/inactive；sync/tests/test-inbound-sync.sh 覆盖幂等、pending SHA、API failure、history rewrite、无共同历史和 Secret 泄漏负例。
- docker-release/schema/release-manifest-v2.schema.json 将 release 绑定到 full Git SHA、linux/amd64、Compose、architecture lock、image identities 与 offline bundle checksums。
- codex/runtime/aisoft_release/runner.py 提供独立 verify-artifact，并限制 scm-ci 不得执行 stage、migrate、activate 或 rollback；结果明确记录 database_restore 为 NOT_RUN_MANUAL_ONLY。
- codex/runtime/aisoft_release/gate.py 只接受固定 action、target_id 和 40 位 SHA，并从受保护 grant 派生固定 profile/argv；test_release_gate.py 与 test_release_safety.py 覆盖任意 action、短 SHA、宽松权限、shell 和敏感输出拒绝。
- architecture/reference/newemaint/gap-report.md 明确 NewEmaint 当前只有 target candidate，尚未迁移或部署，不能作为公司 AppServer 或 production 验证证据。
- Git evidence 已存在精确本地 ref change/120-company-delivery-pilot，且未发现竞争性的 Issue #120 branch 名或 docs/changes/120* 文档目录。

### 缺失的 acceptance criteria 或决策

- 无；如后续发现缺失则回到 awaiting-triage。
