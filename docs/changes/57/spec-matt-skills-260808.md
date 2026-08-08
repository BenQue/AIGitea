---
issue: 57
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/57
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
  - shared-core
depends_on: []
status: approved
branch: change/57
pr_url:
created: 2026-08-08
updated: 2026-08-08
---

# Matt skills development orchestration spec

## Problem Statement

AISoftPlatform 需要减少 GSD、Superpowers 与平台 skills 的开发编排重叠，同时保留已经验证的 Issue
主键、合同校验、确定性 CI/部署和人工合并边界。直接复制或修改 Matt skills 会破坏上游完整性与更新能力；
直接让 Matt 流程控制 Gitea 生命周期、push 或 merge，又会绕过平台治理。

现有 change 文档使用固定 basename。跨项目搜索和编辑器标签无法快速区分主题，而且 runtime、模板、
skills 和测试对这些名字存在硬编码。新命名必须从本 Issue 起生效，同时不得破坏历史合同与链接。

## Solution

完整保存并固定 Matt Pocock skills 的上游 snapshot、版本、commit、文件 hash 和 license；平台 adapter
通过少量稳定接口完成标签投影、spec/plan 发布和 ticket 执行。Matt skills 负责开发方法，Controller
负责平台 preflight、post-validation、push、PR、CI 和状态管理。

新文档使用 `<role>-<short-slug>-<YYMMDD>.md`，由 summary front matter 的 `documents` 映射声明真实
文件。`required_docs` 在新合同中保存语义角色；旧 summary 没有映射时，仅识别既有四个固定 basename。

## User Stories

- 作为 Issue 作者，我可以使用 `$triage` 得到完整的 Matt 分类与下一处理者建议，同时不把
  `ready-for-agent` 误当成平台 `approved`。
- 作为规格维护者，我可以用 `$to-spec` 把已确认内容发布到当前 Issue 的 spec 文件，不创建另一套合同。
- 作为计划维护者，我可以用 `$to-tickets` 把垂直切片与依赖图写入当前 Issue 的 plan 文件。
- 作为实现 Agent，我可以用 `$implement` 完成 ticket、测试、review 和原子 commit，但不能 push、开 PR、
  merge 或 deploy。
- 作为平台管理员，我可以安全更新完整 Matt snapshot；兼容更新走 maintenance，流程或权限变化走 complex。
- 作为审阅者，我在全项目搜索时可以仅从短文件名识别文档角色、主题和创建日期。

## Acceptance criteria

- [ ] **AC-1** Issue #57 及其后的新 change 文档使用
  `<summary|spec|plan|verification>-<short-slug>-<YYMMDD>.md`；slug 为 2–4 个小写英文
  `kebab-case` 词，优先不超过 24 字符、硬上限 32 字符，完整 basename 不超过 64 字符。
- [ ] **AC-2** 文件名日期等于该文件首次创建日期；普通更新只改变 `updated`，不得重命名；同一 Issue
  的 active 文档共用一个锁定 slug，每个角色最多一个 active 文件。
- [ ] **AC-3** 新 summary 使用 `documents` 角色映射和语义 `required_docs`；解析器只读取显式映射，验证
  basename、角色、slug、日期、目录边界、重复角色和 front matter，不通过无约束 glob 猜测文件。
- [ ] **AC-4** Issue #57 之前的 `00-summary.md`、`01-spec.md`、`02-plan.md`、`03-verification.md`
  继续可读；新模板、analyzer 和 adapter 不再生成旧名称，也不重命名历史文件。
- [ ] **AC-5** `triage/bug|enhancement` 与五个 `triage/*` state 作为正交标签投影；每个已 triage Issue
  恰好一个 Matt category 和 state；`triage/ready-for-agent` 永远不能单独启动 Loop，平台仍只认
  通过合同校验的 `approved`。
- [ ] **AC-6** `$to-spec` 与 `$to-tickets` 保持 Matt 原流程，通过 Gitea tracker adapter 分别更新当前
  Issue 的 spec 与 plan；默认不创建子 Issue，只有 complex spec 显式授权才允许多 Issue 模式。
- [ ] **AC-7** plan 保留 vertical slice、`blocked_by`、frontier task 和 expand-contract，并以 `T01` 起的
 稳定 ID 映射每条 AC、验证方式和非合同性的 expected touch points。
- [ ] **AC-8** Controller 显式调用 `$implement Issue #N ticket Txx`；Agent 只可在当前 `change/N`
  修改授权文件并创建包含 `#N` 与 `Txx` 的原子 commit，不得 push、开 PR、merge、rebase、force-push
  或 deploy。
- [ ] **AC-9** Controller 在 push 前验证 exact branch、旧 head ancestry、无 merge commit、授权路径、
  Secret 扫描、clean worktree 和确定性 tests；失败通过追加修复 commit 处理，不默认 amend 审计历史。
- [ ] **AC-10** 每个 Issue 最终只有一个 `Closes #N` PR；Controller 可 fast-forward push、创建/更新 PR、
  等待 CI 和投影状态，但最终 merge 必须由人工操作，部署保持独立授权。
- [ ] **AC-11** Matt snapshot 保持完整且不修改上游文件；manifest 固定 source、tag、exact commit、skill
  清单、hash、license 与 adapter contract。skill 增删/改名、主流程、权限、工具、网络或 Git 副作用变化
  必须升级为 complex，不能直接推广。
- [ ] **AC-12** 文档、模板、skills、runtime 和 tests 一致更新；focused tests、完整 Python suite、
  `bash codex/tests/smoke.sh`、相关 `bash -n`、ShellCheck（可用时）和 `git diff --check` 通过。

## Implementation Decisions

- 上游 Matt 内容使用只读 vendor snapshot；AISoftPlatform adapter 单独维护，不 fork `SKILL.md`。
- 平台接口收敛为 label reconciliation、spec publication、plan publication 和 ticket execution。
- 新旧格式由 summary 是否存在显式 `documents` 映射区分；不得用 Issue 编号推断新旧格式。
- `triage/*` 表示 Matt category/state；现有 `type/*`、`complexity/*`、lifecycle 继续是平台权威。
- Agent 拥有本地 commit，Controller 拥有远端 mutation；人工拥有 merge。
- 当前运行遵守现有根 `AGENTS.md`，本 Change 不在执行中自修改该文件；根规则更新留给合并后的独立治理步骤。

## Testing Decisions

- 文档解析 seam：以临时仓库 fixture 覆盖新映射、legacy fallback、非法路径、多个 active 角色、slug/date
  不匹配和 64 字符上限。
- LabelProjector seam：使用 mock Gitea transport 验证两个 triage 维度与现有三维标签互不覆盖。
- Git seam：使用临时 Git repository 验证 Agent commit 的 branch、ancestry、message、path 与 clean tree。
- Update seam：使用固定 snapshot fixture 验证 manifest hash、skill 增删和重大合同变化会 fail closed。
- 所有 network/live Gitea/全局 skill 安装测试默认 synthetic；未运行不得写成 live PASS。

## Interface, Data and Compatibility

- summary front matter 新增一个一级 `documents` mapping，key 仅允许 `summary`、`spec`、`plan`、
  `verification`，value 必须是同目录安全 basename。
- 新合同的 `required_docs` 值为上述语义角色；legacy 合同继续接受旧 basename，但两种模式不能混用。
- `Contract.required_docs` 对外返回解析后的实际 basename，保持 PR 链接与 Controller 使用简单确定。
- 旧 Issue、PR 评论和历史分支不改名；没有映射的非 legacy 自定义文件 fail closed。

## Risks and Rollback

- 解析器先兼容 legacy，再启用新 writer；回滚代码不会损坏历史文件，但 #57 新文档需要保留在分支中等待
  修复，不能被旧 Controller 启动。
- Matt adapter 或 manifest 验证失败时停止更新并保留已发布 snapshot；支持原子恢复 N-1。
- Git post-validation 失败时不 push；人工 merge gate 始终保留。

## Out of Scope

- 不删除或批量更新本机 GSD、Superpowers、Matt 或 Claude 插件。
- 不自动迁移历史 Issue、业务仓库或全局用户配置。
- 不修改生产、公司内网、数据库或部署环境。
- 不在本次正在遵循根 `AGENTS.md` 的运行中修改该文件。

## Further Notes

普通 Matt 上游文字与内部质量改进在 adapter contract 不变且 conformance 全通过时可作为 maintenance；
任何新增 skill 或平台可见语义变化都必须创建新的 complex Issue。

## 未决问题

无。用户已批准命名、兼容、编排、commit、PR 与人工 merge 边界。
