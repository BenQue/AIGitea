---
issue: 121
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/121
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 新增 repository-level Matt 配置并把 AISoftPlatform 纳入受控 Analyzer profile 合同，触及 Agent 治理与 host-access 共享配置，按平台强制规则为 complex
risk_flags:
  - agent-governance
  - platform-governance
  - external-contract
  - cross-module
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
documents:
  summary: summary-matt-repository-adapter-260816.md
  spec: spec-matt-repository-adapter-260816.md
  plan: plan-matt-repository-adapter-260816.md
  verification: verification-matt-repository-adapter-260816.md
depends_on: []
status: pr-open
branch: change/121-matt-repository-adapter
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/122
created: 2026-08-16
updated: 2026-08-16
---

## 问题/需求总结

AISoftPlatform 已完成 repository onboarding，但缺少 Matt repository adapter，且 canonical manifest 对本项目声明
`vm_profile: null`，导致首次 platform Analyzer 无法运行。

本 Change 是 Issue #120 的唯一前置：安装 repository adapter，并新增一个只允许手工 Analyzer、明确关闭
implementation 与 timer 的 project profile。它只交付可审核 source contract，不声称 installed/live profile 已就绪。

## 影响范围

- `CLAUDE.md`：按 upstream selection rule 增加唯一 `## Agent skills` block。
- `docs/agents/`：从 `templates/docs/agents/` byte-identical 安装 Gitea tracker、triage label 与
  single-context domain 配置。
- `codex/config/host-access-broker.json`、`codex/runtime/aisoft_host_access/contract.py` 与 focused tests：
  增加 `aisoft-platform` Analyzer-only profile。
- 本目录的 mapped `summary/spec/plan/verification`。

不修改 `AGENTS.md`、`codex/vendor/mattpocock/`、全局 skills、protected main、required CI、credential、
service/timer 或部署状态。

## 初步方案与建议

1. 复用仓库已提供的三份 Gitea adapter 模板，不再生成另一套 tracker 约定。
2. 选择既有 `CLAUDE.md`，保留 `@AGENTS.md`，只追加 upstream 规定的单一技能路由块。
3. profile 固定为 `name=aisoft-platform`、`repo_dir=work/AISoftPlatform`、
   `analysis_provider=codex`、`implement_provider=none`、`timer_unit=null`。
4. 通过本地 fixture 验证 profile schema 与 `profile-spec` 投影；真实 `plan/apply/read-back`、安装和 canary
   留在合并后的独立授权闸门。

## 风险

- Analyzer profile 误启用 implementation 或 timer；以 manifest 精确断言和 `profile-spec` 测试阻断。
- repository adapter 与 canonical 模板漂移；以 byte comparison 阻断。
- source 合并被误写成 installed/live ready；verification 分层记录并将 live checks 保持 `NOT RUN`。
- #121 本身处在 Analyzer/label projector 引导死锁中；只用 typed broker 更新 lifecycle，不伪造
  `type/*`、`complexity/*` 或 `triage/*` 投影。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 新增 repository-level Matt 配置并把 AISoftPlatform 纳入受控 Analyzer profile 合同，触及 Agent 治理与 host-access 共享配置，按平台强制规则为 complex
risk_flags:
  - agent-governance
  - platform-governance
  - external-contract
  - cross-module
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- typed `host.onboarding.check` 与 `host.access.audit` 已 `PASS`；protected main 禁止 direct/force push，
  required CI 未配置。
- `templates/docs/agents/` 三文件存在，`docs/agents/` 缺失；`CLAUDE.md` 存在且原先只引用
  `AGENTS.md`。
- repository 与 installed host-access manifest 都为 `aisoft-platform` 声明 `vm_profile: null`；typed
  `vm.profile.plan` 返回 `TARGET_UNAVAILABLE`。
- `type/platform`、Agent 治理和共享 host-access contract 均触发强制 complex。

### 缺失的 acceptance criteria 或决策

- 无。用户已批准最小 profile 路径；live install/apply/read-back 保留为独立授权，不改变本 PR 的实现方向。

### Bootstrap 例外记录

#121 是首次 repository adapter 与 Analyzer profile 的引导 Change，因此自动 Analyzer、Matt triage 与
type/complexity projector 在本 Issue 上不可达。当前会话使用同一 runtime schema 对分析 JSON、slug 与 mapped
summary 做了本地确定性验证；live 标签不通过其它入口补写。该例外只适用于 #121，不延伸到 #120。
