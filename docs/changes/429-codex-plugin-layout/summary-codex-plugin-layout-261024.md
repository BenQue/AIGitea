---
issue: 429
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/429
change_type: bugfix
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - external-contract
depends_on: []
branch: change/429-codex-plugin-layout
created: 2026-10-24
updated: 2026-10-25
reason: 恢复已安装版本的准确诊断；需要兼容新版官方插件目录及元数据，按外部契约判 complex
override_reason: ''
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-codex-plugin-layout-261024.md
  spec: spec-codex-plugin-layout-261024.md
  plan: plan-codex-plugin-layout-261024.md
  verification: verification-codex-plugin-layout-261024.md
route_provider: codex
route:
  process: complex-production
  tier: frontier
  effort: max
  skills: to-spec, to-tickets, implement, issue-session-flow
  method: spec-plan
  verify: full+reverse-proof
  review: cross-provider
  confirm: 2
status: pr-open
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/431
---

# Codex 官方插件目录识别修复

## 合同与授权

用户 2026-10-24 在会话 01a16b94-fd7f-7842-852c-af5e58c3f9df 明确要求：“Claude 侧等官方市场更新。这边先按平台流程修复版本检查器对 Codex 新插件目录的识别问题，完成后再核验一下。”前轮已复现和界定缺陷，本轮指令作为本范围的启动授权；不重复请求同一个修复的启动确认。最终 PR 提交保留确认点 2。

目标：admin/aisoft-platform#429；唯一写者：上述会话；worktree：/private/tmp/issue-429-codex-plugin-layout；change_base：08aac8d5b9af4d334c53bcf34029870f09e50bf0（broker fresh-fetch）。

## 已确认事实与方案

旧检查器只读 config.toml 中的 marketplace 注册和同名缓存。当前配置启用 superpowers@openai-curated，但官方新目录为 openai-curated-remote/superpowers/7.0.1，当前会话可见该版本；旧同名缓存为 5.1.3，旧报告错误输出 PIN_NOT_INSTALLED / RESULT PASS。

保持明确启用声明作为前提；仅对已观测的官方 marketplace 身份建立闭集目录映射，严格核对新目录元数据，保留旧布局回退。缓存不能独立推导启用；多版本不能猜最新版。只读文件安装证据不等于 fresh-session 行为验收。

## 范围与非目标

检查器、对应回归测试、本票文档，以及03要求的本票审查索引记录。保持平台 pin 7.0.0、适配记录和两侧插件不变。没有 Claude 更新、插件安装、配置修改、网络调用、凭据读取、全局技能更新、部署或自动合并。

## 判级与状态

triage：bug / ready-for-agent；公开开放 Issue 只有无关的 #417，无重复票。没有 .out-of-scope 拒绝记录。本票按 external-contract 强制 complex，R3/codex。实际标签投影和执行证据见 verification。

T01 done；最终代码已通过完整smoke、Codex双轴及Claude Code claude-fable-5-1/high独立交叉审查（08ef62fcc41f6b2876d92dbe11e55a70219c9fd1，PASS，0阻断）。用户2026-10-25明确授权的源码外发审查已执行；3条非阻断备注已在verification登记并补证。确认点2候选为0db380f97b9a6622686c8c32c634305efb678171，Codex双轴与Claude最终复核均PASS。用户2026-10-25确认提交本票唯一最终PR并跟进CI；该候选已经broker普通fast-forward push，pushed_head逐字匹配，并创建PR #431。本提交仅回填summary的PR地址、状态与上述授权事实；实现代码和测试不变。后续核验最终HEAD的required CI，全部通过后停在READY_FOR_REVIEW等待人工审核合并。
