---
issue: 352
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/352
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
  - shared-core
  - rollback
  - external-contract
depends_on: []
status: approved
branch: change/352-matt-skills-upgrade
created: 2026-10-07
updated: 2026-10-07
---

# #352 实施计划

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 固定四角色治理合同、来源和授权证据；文档验证、本地 commit 后 STOP | - | completed |
| T02 | fresh run 完成 v1.3.1 完整 source、隔离安装/回滚、术语兼容和技能来源适配 | T01 | completed |
| T03 | PR 候选接入真实前后证据、回滚/影响范围，保留现有机器硬门 | T02 | completed |
| T04 | 整体验证、完整 spec review 与唯一最终 PR 候选 | T03 | pending |

## Expected touch points

- T01 只写本目录 `summary/spec/plan/verification` 与 `evidence/`。本轮不得添加 vendor、修改 runtime、脚本、Agent source 或当前 AGENTS.md。
- T02 使用 spec 明确授权的 vendor、installer、Matt snapshot、受影响 fixture、workflow adapter、domain/tracker 模板、GLOSSARY 与 README/04/08。沿用已有安装/快照入口，不建立另一套更新器；保留旧 release 和独立 Claude 插件。
- T03 修改 Controller 的 PR 正文/候选数据通路和对应测试，按需适配既有 verifier/provider 证据。依赖、唯一 Closes 行、summary、授权 marker 与第二确认必须回归。
- T04 只修范围内问题并回填真实验收，形成 exact Issue #352 / branch / manual 的提交卡；此时才请求 PR 第二确认。

T01 的停止用于满足治理合同与 runtime 的 fresh-run 隔离，用户的范围批准持续有效。下一轮核对工作区归属、当前 HEAD、合同、Issue 有效评论与 fresh main 后从 T02 开始，不重新调查上游方向，也不再次请求同一范围的启动批准。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | 固定 tag/commit 的 Git tree blob 校对；`python3 -m aisoft_loop.matt_snapshot verify`；`tests.test_matt_snapshot` |
| AC-2 | 通过隔离 HOME fixture 运行真实 installer：首次、升级、重复、故障注入、N-1 回滚、冲突归属与旧入口；受影响 `test-agent-runtime.sh` 和 installed-drift fixture |
| AC-3 | domain 模板与仓库配置比较、链接检查、glossary 人工语义审查；legacy fixture 验证规则/ADR 保留 |
| AC-4 | Controller PR fixture 与现有 Gitea/授权正文校验测试；对 Before/After、SHA、NOT RUN、回滚和影响范围逐项断言 |
| AC-5 | 两 provider 的元数据/显式入口/重名检测检查；真实 fresh-session conformance 独立记录，不以 static 通过替代 |
| AC-6 | adapter 与 spec 范围审查，确认只有既有 Controller dispatch；retro 仅建议、无自动写入授权 |
| AC-7 | `bash codex/tests/smoke.sh`；变更脚本 `bash -n` 和 ShellCheck；`python3 -m aisoft_loop.cli check-change-documents --repo .`；相关 focused tests |
| AC-8 | mapped verification 分层记录；最终 exact head/base/CI 的人工 PR 卡；实际安装保持独立目标验收 |

T01 本轮执行：四文档 resolver/required-docs、真实 Issue 的 load_contract、Ticket graph、文档相对链接、精确范围与 diff 检查；旧 vendor/installed/candidate 的哈希证据。没有改 shell/runtime，本轮不以其测试冒充 T02/T03 验收。

## 部署与回滚

本期 source 工作无应用部署。隔离 fixture 验证安装与回滚是 T02 的交付要求；真实 Mac/VM/Claude 插件不执行。本地治理 commit 可恢复；后续 source 合并不等于已安装。最后的现场安装卡必须绑定 exact pin、目标清单、原状态备份、失败回滚和 fresh-session 读回。
