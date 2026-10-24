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
updated: 2026-10-24
---

# 验证记录

## 来源与边界

change_base：08aac8d5b9af4d334c53bcf34029870f09e50bf0；writer：01a16b94-fd7f-7842-852c-af5e58c3f9df；provider：Codex；执行入口 Matt implement v1.3.1。本机目录/配置只读，凭据不读取。

## Before

旧 main 的实际输出：SUPERPOWERS codex PIN_NOT_INSTALLED enabled=superpowers@openai-curated marketplace=unregistered cached=5.1.3 pinned=7.0.0；RESULT PASS，exit 0。
配置明确 enabled=true；当前会话可见插件的元数据为 superpowers / 7.0.1，路径位于 openai-curated-remote/superpowers/7.0.1。

## 执行与核验

T01 尚未启动。定向测试、smoke、实机 After、独立审查：NOT RUN。
远端 CI、安装、插件升级、fresh-session、PR、merge：NOT RUN。

## Findings

fixed / residual / new：待审查后记录。

