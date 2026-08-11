---
issue: 93
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/93
change_type: docs
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 按用户 2026-08-11 决策把 13/14/07 的内网模型改写为「开发权威在本地、公司 Gitea 为部署权威、GitHub 中继持续同步、交付形态按项目 delivery profile」
risk_flags:
  - deployment-contract
required_docs:
  - summary
  - spec
  - plan
documents:
  summary: summary-intranet-collab-model-260811.md
  spec: spec-intranet-collab-model-260811.md
  plan: plan-intranet-collab-model-260811.md
confidence: high
override_reason: ''
depends_on: []
status: ready-for-review
branch: change/93-intranet-collab-model
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/94
created: 2026-08-11
updated: 2026-08-11
---

## 问题/需求总结

公司内网暂不能用 AI agent。用户确认目标模型：Issue/提交/AI 永远留在开发机；公司 Gitea
持续同步仓库与部署脚本并做确定性自动部署。旧 13 以「一次性权威切换」为纲、且与 12-Linux
的 GitHub 入站设计矛盾；内网重建链只有 Windows/ZIP；manifest/14 缺 architecture lock 字段。

## 影响范围

13（新 §0 总纲、§1 拓扑、§3 manifest、§7 PRD 限定、§11/§12.2 备选化）、14（Gate C 增
C-13/C-14 + Linux 分流说明）、07（§1 核心决策、§2 拓扑图）。不改 sync/ 脚本、12-Linux
正文、runtime。

## 初步方案与建议

以 13 §0 为唯一总纲：双权威分工、GitHub 中继（复用 12-Linux §8 与 sync/ 子系统）、
incident 证据包回流、交付形态按项目 delivery profile（docker-release/v2 参照 NewEMaint、
PM2 受支持选项、Windows ZIP）+ 全平台一致的流程不变量、阶段化路线。公司侧制品默认由
受控 builder 按同一 merge SHA 构建；需跨环境字节一致时用 offline bundle，二选一入项目
verification。

## 风险

- 「备选彻底切换路径」若不显式标注会与总纲抢权威——§11/§12.2 已加限定头。
- 公司侧实施仍是 NOT RUN；本变更只统一合同表述，不宣称任何环境建成。

## AI 判级

```yaml
change_type: docs
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 按用户 2026-08-11 决策把 13/14/07 的内网模型改写为「开发权威在本地、公司 Gitea 为部署权威、GitHub 中继持续同步、交付形态按项目 delivery profile」
risk_flags:
  - deployment-contract
required_docs:
  - summary
  - spec
  - plan
confidence: high
override_reason: ''
```

### 判级证据

- 改写迁移/部署合同表述，用户显式批准方向；按平台惯例 complex。

### 缺失的 acceptance criteria 或决策

- 公司侧逐阶段实施各需独立 Issue 与真实 verification（含 Registry/offline 介质二选一决策）。

## 验收结果

| 检查项 | 结果 | 证据 |
|---|---|---|
| AC-1 13 §0 总纲与备选化 | PASS | `内网协作模型` 在文；§11 头部有「备选路径，当前不采用」 |
| AC-2 反向串清零 | PASS | 「无网络、镜像或发布关系」0 命中；残留「唯一权威源」两处均在备选限定语境 |
| AC-3 manifest 三字段 + PRD 限定 | PASS | `architecture_profile_id` 在文；§7 引 07 §4 |
| AC-4 14 C-13/C-14 + 分流说明 | PASS | 行存在 |
| AC-5 07 与 13 §0 一致 | PASS | 核心决策改写；mermaid 改 GH→CG 入站边、Mac 虚线审阅边 |
| AC-6 smoke | PASS（叠加 #82 修复验证） | #77 先例；还原后 worktree 干净 |
| 公司侧实施 | NOT RUN | 本变更不建设任何环境 |
