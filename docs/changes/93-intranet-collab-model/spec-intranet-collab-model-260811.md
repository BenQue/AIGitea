---
issue: 93
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/93
change_type: docs
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - deployment-contract
depends_on: []
status: contract-drafting
branch: change/93-intranet-collab-model
pr_url:
created: 2026-08-11
updated: 2026-08-11
---

# Spec

## 目标与原因

用户 2026-08-11 确认内网目标模型：开发权威永久留在本地（Issue/提交/AI/合并闸门），公司
Gitea 是部署权威（持续同步 + 内网确定性自动部署，无 AI），传输走 GitHub 中继。现有 13 以
「一次性交付 + 公司 Gitea 唯一权威源」为纲且声称「GitHub 与公司 Gitea 无网络关系」，与
12-Linux 的 GitHub 入站设计自相矛盾；13 的内网重建链只有 Windows/ZIP；manifest 与 14 缺
architecture lock 字段。

## Acceptance criteria

- [ ] AC-1 13 含 §0「内网协作模型（权威分工，总纲）」：双权威、GitHub 中继（12-Linux §8 /
      sync/）、Issue/提交留开发机、内网无 AI、incident 证据包回流、交付形态按项目
      delivery profile（docker-release/v2 参照 NewEMaint、PM2 受支持选项、Windows ZIP）+
      流程不变量清单、阶段化路线；§11 明确降级为备选彻底下线路径。
- [ ] AC-2 13/07 不再有无限定的「公司 Gitea 是唯一正式权威源」与「GitHub 与公司 Gitea
      无网络、镜像或发布关系」表述。
- [ ] AC-3 13 §3 manifest 示例含 `architecture_profile_id`/`architecture_catalog_revision`/
      `architecture_lock_sha256` 并注明 07 §10 依据；§7 含 `change/PRD-NNNN` 未启用限定。
- [ ] AC-4 14 Gate C 增 C-13/C-14 lock 检查行，并注明 Linux/Docker 走各自 delivery profile 门。
- [ ] AC-5 07 §1 核心决策与 §2 拓扑图与 13 §0 一致（GitHub 中继边、Mac 对公司侧仅审阅）。
- [ ] AC-6 smoke 全绿；不改脚本/runtime/manifest。

## 接口/数据/兼容影响

纯文档合同表述；`sync/` 子系统、12-Linux §8、docker-release 合同均为既有实现/设计，本变更
只把 13/14/07 的叙述对齐到该模型。实施仍需公司侧真实环境的独立 Issue/verification。

## 治理授权

本 spec 明确授权修改：`13-项目结果迁移与内网切换实施手册.md`、
`14-Windows部署与迁移验收清单.md`、`07-内网与生产平移路线.md`。

## 非目标

- 不实施公司侧任何环境（全部保持 NOT RUN）；不改 sync/ 脚本或 12-Linux 正文；
  不实现 `change/PRD-NNNN`；不迁移任何仓库。
