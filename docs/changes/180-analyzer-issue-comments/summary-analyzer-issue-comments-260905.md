---
issue: 180
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/180
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 按 2026-09-05 平台裁定采用方向 1，让 aisoft_loop.cli get-issue 的 payload 带上评论内容（新增 issue_comments 列表，保留 comments 计数），并让 analyzer prompt、gitea-analyze-change skill 与 render-analysis 显式消费该字段。改动落在 codex/runtime/aisoft_loop 共享核心（gitea 客户端与 cli）与 analyzer 输入合同（codex/agent 两个 analyzer prompt、Agent 行为文件 SKILL.md），属共享核心组件与 Agent 行为合同变更，强制 complex；平台仓 change_control 缺省 production，需 spec 与 plan
risk_flags:
  - shared-core
  - agent-governance
  - external-contract
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-analyzer-issue-comments-260905.md
  spec: spec-analyzer-issue-comments-260905.md
  plan: plan-analyzer-issue-comments-260905.md
  verification: verification-analyzer-issue-comments-260905.md
confidence: high
override_reason: ''
depends_on: []
status: approved
branch: change/180-analyzer-issue-comments
pr_url:
created: 2026-09-05
updated: 2026-09-05
---

## 问题/需求总结

判级流水线（`codex/agent/analyze-codex.sh:18`、`analyze-claude.sh:18`）只把
`python3 -m aisoft_loop.cli get-issue` 写出的 Issue JSON 喂给 analyzer；该 payload 是 Gitea
`GET /issues/{n}` 的原样返回，其中 `comments` 只是整数计数，没有评论正文。而
`codex/skills/gitea-analyze-change/SKILL.md` 第 1 步要求读「Issue 标题/正文/评论」，
`04` §5 也要求 controller 从「Issue、有效评论、summary」重算合同。对「正文之后由评论修订/收窄/推翻
范围」的 Issue，analyzer 判级依据不全且不知道自己不全。analyzer 在 VM 上以 `coder` 身份补读 broker
被 `CREDENTIAL_OWNER_INVALID` 正确挡住，那条边界不能放宽。

平台裁定（Issue #180 评论，2026-09-05）：采用方向 1——`get-issue` 带上评论内容，走
`aisoft_loop.gitea` 已持有的 `GITEA_TOKEN_FILE`（project-agent token）同一条只读路径；不放宽
`vm_profile_policy.source_credential_owner`，`coder` 不获得新的写权限；保留 `comments` 计数；盘点并
回归全部消费者。验收沿用 Issue 正文。本 summary 只做判级与路由，合同细节见映射的 spec 与 plan。

## 影响范围

- `codex/runtime/aisoft_loop/gitea.py`：新增 `GiteaClient.list_issue_comments(number)`，分页读
  `/issues/{n}/comments`，投影为 `id/author/created_at/body` 四字段（与 broker
  `_issue_comments` 同形，schema 校验、有界扫描）。`get_issue` 本身不变——Controller 与
  `apply-analysis`/`publish-*` 仍只需 Issue 对象。
- `codex/runtime/aisoft_loop/cli.py`：`get-issue` 在 Issue 对象上追加 `issue_comments` 列表；
  `render-analysis` 对缺少 `issue_comments` 的 Issue JSON fail-closed（wrapper 从此「知道自己不全」）。
- `codex/agent/codex-analyzer.sh`、`codex/agent/claude-analyzer.sh`：prompt 增加一句评论优先级规则。
- `codex/skills/gitea-analyze-change/SKILL.md`：第 1 步说明自动化运行中评论以 `issue_comments`
  形式随 Issue JSON 提供，`comments` 只是计数。
- `codex/runtime/tests/test_gitea.py`、新增 `test_get_issue_payload`（名称以 plan 为准）：端点、分页、
  schema、token 不泄漏、payload 组合、render-analysis 守卫。
- `codex/tests/fixtures/classification/`：新增「正文声明 small、评论改成 schema 迁移」fixture。
- `04-Agent编排与定时任务.md` §4：analyzer 输入合同补一句。
- 不改：broker、`vm_profile_policy`、`codex/config/*`、`AGENTS.md`、`controller.py`、
  `analyze-codex.sh`/`analyze-claude.sh` 调用行本身（payload 形状变化对它们透明）。

## 初步方案与建议

1. gitea 客户端加只读 `list_issue_comments`，复用 `_array` 与既有重试/redact 路径，分页 50/页、最多
   100 页、超界抛 `GiteaError`（与 broker 一致，避免「只读第一页把残缺讨论当完整」）。
2. `_get_issue` 组合：`issue["issue_comments"] = client.list_issue_comments(n)`；`comments` 计数原样保留。
3. `_render_analysis` 断言 `issue_comments` 是 list，否则 `AnalysisError` 退 2——同一 ISSUE_FILE 先喂
   analyzer 再喂 render，因此该断言等价于「analyzer 一定拿到了评论」。
4. 两个 analyzer prompt 与 skill 各加一句：`issue_comments` 按时间顺序给出完整评论线程；后出现的、修订/
   收窄/推翻正文范围的评论对判级优先于正文。
5. fixture 端到端证明：本机分别用 `claude-analyzer.sh` 与 `codex-analyzer.sh`（真实 CLI）跑 fixture，
   结果 `effective_complexity: complex` 且 `override_reason` 非空；同 fixture 去掉 `issue_comments`
   走旧形状作基线对照。这是一次性真实观测，CI 不重放，故声明 `verification`。

## 风险

- 评论数极多的 Issue 会让 prompt 变长；有界扫描上限 5000 条远超实际，prompt 长度由模型侧承担，
  不在本 Issue 引入截断策略（截断会重新制造盲区）。
- `render-analysis` fail-closed 会让任何仍用旧形状 Issue JSON 的调用方立即退 2；仓内两个调用方都用
  同一 `get-issue` 产出，VM 上 `install-vm.sh` 同步 runtime 与 agent 脚本，不存在跨版本混用；
  verification 记录 VM 重装为未执行项。
- fixture 判级依赖真实模型输出，存在非确定性；verification 照实记录两次运行原始结果，不改写。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 按 2026-09-05 平台裁定采用方向 1，让 aisoft_loop.cli get-issue 的 payload 带上评论内容（新增 issue_comments 列表，保留 comments 计数），并让 analyzer prompt、gitea-analyze-change skill 与 render-analysis 显式消费该字段。改动落在 codex/runtime/aisoft_loop 共享核心（gitea 客户端与 cli）与 analyzer 输入合同（codex/agent 两个 analyzer prompt、Agent 行为文件 SKILL.md），属共享核心组件与 Agent 行为合同变更，强制 complex；平台仓 change_control 缺省 production，需 spec 与 plan
risk_flags:
  - shared-core
  - agent-governance
  - external-contract
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- `codex/runtime/aisoft_loop/cli.py:402-412` `_get_issue` 原样 dump `get_issue()`；`gitea.py:66` 只 GET
  `/issues/{n}`，没有评论读取方法。
- `codex/agent/codex-analyzer.sh:38-49`、`claude-analyzer.sh:36-47` 把 ISSUE_FILE 全文接在 prompt 后，
  没有其它评论来源。
- `codex/skills/gitea-analyze-change/SKILL.md:8` 要求读评论；`04` §5 要求 controller 读「有效评论」。
- `codex/runtime/aisoft_host_access/broker.py:2040-2088` 已有评论投影实现可对齐形状。
- `codex/config/gitea-governance.json` 的 `aisoft-platform` 条目无 `change_control`，缺省 production。
- Issue #180 唯一评论（2026-09-05）已写明方向 1 与实施边界。

### 缺失的 acceptance criteria 或决策

- 无；如后续发现缺失则回到 awaiting-triage。
