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
git_scope:
  - docs/governance/review-evidence-index.md
  - codex/tools/check-external-skill-versions.py
  - codex/tests/test-external-skill-versions.sh
  - docs/changes/429-codex-plugin-layout/summary-codex-plugin-layout-261024.md
  - docs/changes/429-codex-plugin-layout/spec-codex-plugin-layout-261024.md
  - docs/changes/429-codex-plugin-layout/plan-codex-plugin-layout-261024.md
  - docs/changes/429-codex-plugin-layout/verification-codex-plugin-layout-261024.md
---

# Codex 插件安装目录识别

## 目标与原因

恢复“报告本机已启用插件的可核验安装版本”这一既有合同，避免把新版官方目录漏判为未安装。不扩大到插件管理或自动升级。

## Acceptance criteria

- [x] AC-1：启用 superpowers@openai-curated 或 superpowers@openai-curated-remote 时，识别 openai-curated-remote/superpowers/<version>/.codex-plugin/plugin.json；单一有效版本与 pin 相等为 PIN_CLEAN，不同为 PIN_DRIFT / REVIEW_NEEDED / exit 1。输出实际布局来源和版本。新版明确存在时不用旧缓存 5.1.3 覆盖它。
- [x] AC-2：无配置、未启用或禁用时，不凭残留新缓存推导已启用；不受支持的 marketplace 保持旧逻辑。新目录不存在时保持原布局兼容。未启用项不因无关旧缓存制造失败。
- [x] AC-3：新路径父目录、版本目录、元数据目录/文件的符号链接和异常类型、缺少/错误名称或版本、目录/元数据版本不一致、重复 JSON key、多个候选版本、不可读或畸形内容一律 UNKNOWN，并汇总到失败退出；不读取链接外文件、不选最大版本。
- [x] AC-4：保留 Claude、Cursor、Matt、CLI 状态与既有结果汇总语义；不改 pin、插件配置或全局安装，不读 Secret，不网络访问，不写入 HOME 或 pyc。
- [x] AC-5：新真实缺陷 fixture 在旧实现先失败，修复后新/旧回归、bash -n、ShellCheck、完整 smoke 通过。实机只读报告准确给出 Codex 7.0.1 对平台 7.0.0 的 PIN_DRIFT；这证明诊断修复，不代表版本差异消失。独立审查覆盖完整固定 BASE..HEAD。

## 实现决定、接口与兼容性

沿用现有命令及 --home 测试边界。官方目录映射只接受观测到的 openai-curated / openai-curated-remote 身份，目标目录固定 openai-curated-remote。保留显式 enabled=true 要求和现有多启用声明歧义拒绝。先验证 config 结构，不能用新缓存掩盖坏配置。

新布局由闭集身份及有效目录联合识别，不要求它另出现在旧 marketplaces 表。路径逐级 lstat，不穿过符号链接。有效候选必须是一个目录名与 plugin.json version 完全一致的 dotted numeric version，name 恰为 superpowers。若新目录缺失，调用现有旧布局逻辑；若新目录存在但坏掉，则 UNKNOWN，不降级回旧缓存获得 PASS。没有活动版本清单时，多版本保留 UNKNOWN。

实机目录另含官方安装标记 .codex-remote-plugin-install.json（schema_version、remote_plugin_id）。它必须是常规文件，只按文件类型排除出版本候选，不解析内容、不作为活动版本证据；链接或目录形式仍为 UNKNOWN。测试包含该实际目录结构。

## 验证边界

沿用已有 fabricated HOME、fake CLI、隔离 PATH 的顶层命令测试；覆盖主问题、旧布局、禁用、残留、多版本、错名/版本/JSON、链接与读错及零写入。实机核验仅运行候选只读脚本，不把候选安装进全局环境。

## 风险与回滚

官方目录布局可能再变：未知格式明确 UNKNOWN。只改诊断，源码可由后续受控 revert 恢复；无数据迁移和环境写入。不要修改真实插件造反向证据，反例仅在临时 fixture。

## 非目标与未决问题

不升级任何包、pin 或适配记录；不修旧布局之外的独立问题；不改 Agent 技能或治理规则；不创建新后台任务。无影响实现方向的未决问题。
