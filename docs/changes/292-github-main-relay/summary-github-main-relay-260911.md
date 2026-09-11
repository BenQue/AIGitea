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
status: approved
branch: change/292-github-main-relay
created: 2026-09-11
updated: 2026-09-11
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

# 单向 main 出站同步

## 问题/需求总结

平台 sync/inbound-sync.sh 只承载 GitHub→Gitea 入站，没有相反方向的受控 main relay。现有 host-access-broker 操作表没有 GitHub 出站写入。Gitea内建Push Mirror会覆盖分支/tags，不能满足用户已批准的main-only、fast-forward-only、no-force/no-delete语义。

用户已通过既有项目任务明确批准本机Gitea→指定私有GitHub自动同步及必要安全实现；本票将该范围转为平台版本化能力，不重复请求行为授权。私有项目端点、提交、授权回传证据保留在项目私有协调记录，本公开票不复制凭据或现场配置。

## 影响范围

host-access typed操作与专用relay模块、严格项目绑定、隔离认证、受控调度安装及回归测试。只允许显式opt-in项目；其它项目默认不可调用。新安装候选本身不启用调度、不创建凭据。

## 初步方案与建议

提供plan/reconcile/status三个typed操作；调用方只选现有project，不提供URL/refspec/credential path。与平台既有Git访问合同同样fail closed。通过版本化pre-push校验验证Git实际协商的旧OID，防止预检查后远端推进或删除竞态；正常push不携带force/mirror/delete/tag参数。

## 风险

共享broker兼容、Git进程环境和hook继承、并发竞态、凭据作用域、不同主机安装差异。映射spec明确拒绝和测试，不用临时推送兜底。源码/CI/installed/live各自计证。

## AI 判级

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

新增外部写入与自动运行，触发security/platform-governance/shared-core强制complex；实际安装与live校验不能由diff/CI代替，因此声明verification。

### 缺失的 acceptance criteria 或决策

行为范围无未决设计；实际项目GitHub专用凭据由用户本地受控配置，缺失时停在credential provisioning，不读取或提升现有宽身份。最终PR仍保留人工提交/合并流程；安装只允许merged exact-source版本。本轮最新批准仅覆盖实现、本地测试与PR材料，明确不允许实际同步、凭据配置、安装或启用调度、公司及旧服务操作。
