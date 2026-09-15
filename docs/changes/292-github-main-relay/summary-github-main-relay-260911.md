---
issue: 292
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/292
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - security
  - platform-governance
  - shared-core
depends_on: []
status: spec-drafting
branch: change/292-github-main-relay
created: 2026-09-11
updated: 2026-09-15
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-github-main-relay-260911.md
  spec: spec-github-main-relay-260911.md
  plan: plan-github-main-relay-260911.md
  verification: verification-github-main-relay-260911.md
reason: 新增受治理的跨托管平台写入、认证隔离与自动同步能力
override_reason: ''
pr_url:
---

# 单向 main 出站同步（已被原生 Push Mirror 路线取代）

## 当前决定（2026-09-12 裁决，2026-09-15 收口）

用户确认本机 Gitea 是唯一代码源，指定私有 GitHub 仓库只作**可覆盖镜像**，不保留镜像端独立开发成果；
接受 Gitea 原生 Push Mirror 的强推、分支/tag 同步与镜像端删除语义。该决定只适用于指定的 GitHub
镜像目标，不许可强推本机 Gitea、公司内网 Gitea 或任何其它仓库。

因此本票原定的自研 fast-forward-only main relay（typed plan/reconcile/status、pre-push 协商 OID 门、
独立 PAT 审核回执、launchd 调度与安装脚本）**不再实施**：旧 T02–T05 停止，不安装、不调度、不作为公司
部署前置。T01 已提交的三个合同 commit 与本次文档修订保留为历史追溯；未提交的自研代码不记为交付。

2026-09-15 用户裁决选项 A：提交本次文档修订，以「被原生 Push Mirror 路线取代」收口并关闭 #292。
本 PR 只修改本票四份映射文档，不改 runtime、`sync/`、broker manifest 或治理文件。

## 现行路线与执行边界

- M-1：用户核对唯一源与指定私有目标，确认目标独有成果无需保留；私有端点与源 SHA 只留项目记录。
- M-2：用户按交接指南手工配置原生 Push Mirror，使用目标仓库专用凭据；不降低源 `main` 保护、不建立回推、
  不自动扩大权限。
- M-3：首次同步状态成功后，独立读回目标 `main` 与源 SHA 一致，并核对镜像 branch/tag 范围；启用前确认
  目标仓库 workflow 影响。
- M-4：后续正常已批准的源更新通过原生触发或周期同步到目标，读回一致后才认定自动同步通过。
- M-5：公司按原入站/PR/CI/人工审核流程消费版本，部署另行验收；镜像覆盖许可不得延伸到公司 `main`。
- M-6：停用镜像只停止未来同步，不自动恢复被覆盖历史；恢复另行绑定准确目标。

M-2/M-3/M-4 由用户在 NewEMaint 项目侧手工完成并在该项目 #80 记录，不属于本 PR 交付；截至本次修订
全部 NOT RUN。

## 问题/需求总结（历史）

平台 `sync/inbound-sync.sh` 只承载 GitHub→Gitea 入站，没有相反方向的受控 main relay；host-access-broker
操作表没有 GitHub 出站写入。当时判断 Gitea 内建 Push Mirror 会覆盖分支/tag，不能满足 main-only、
fast-forward-only、no-force/no-delete 语义，于是立本票自研。2026-09-12 用户改变了对镜像语义的要求，
该前提不再成立。

## 影响范围

本次修订只影响 `docs/changes/292-github-main-relay/` 四份文档。平台 runtime、broker 操作表、
`sync/` 入站组件、installer 与 source guard 均无变更；`README.md` 与 07 不需要新增交叉引用，07 §1
已把 GitHub 描述为本地镜像与向内网的搬运中继，与现行路线一致。

## 风险

- 原生 Push Mirror 会强推与删除镜像端 refs：已由用户明确接受，且只对指定目标生效。
- 镜像凭据由用户在 Gitea 界面手工配置，不经 broker，不进入本仓库；本票不核验其范围。
- 关闭 #292 后若再需要 fast-forward-only 语义，需另开 Issue，不复用本票分支。

## AI 判级

判级已于立票时投影到 Gitea（`type/platform`、`complexity/complex`），本次收口不重判；以下为立票时的
判级记录，保留以维持 front matter 与标签一致。

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 新增受治理的跨托管平台写入、认证隔离与自动同步能力
risk_flags:
  - security
  - platform-governance
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

立票时新增外部写入与自动运行，触发 security/platform-governance/shared-core 强制 complex；实际安装与
live 校验不能由 diff/CI 代替，因此声明 verification。现行路线下该 verification 记录的是镜像启用、
同步读回与公司导入均 NOT RUN 的事实。

### 缺失的 acceptance criteria 或决策

- 无。镜像语义已由用户 2026-09-12 裁决，收口方式已由用户 2026-09-15 裁决（选项 A）；不再重复询问。
