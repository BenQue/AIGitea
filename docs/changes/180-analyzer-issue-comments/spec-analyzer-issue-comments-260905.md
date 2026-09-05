---
issue: 180
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/180
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - shared-core
  - agent-governance
  - external-contract
depends_on: []
status: approved
branch: change/180-analyzer-issue-comments
created: 2026-09-05
updated: 2026-09-05
---

# Spec · get-issue payload 带上 Issue 评论内容，analyzer 输入合同显式消费评论

## 目标与原因

让判级流水线「看全」Issue：`aisoft_loop.cli get-issue` 产出的 Issue JSON 除 Gitea 原始 Issue 对象外，
再带上完整评论线程；analyzer prompt 与 `gitea-analyze-change` skill 明确评论对范围的优先级；wrapper 对
没有评论字段的 payload fail-closed。这是 Issue #180 正文「方向 1」与 2026-09-05 平台裁定评论的落地。
Issue 正文与裁定评论是合同源；本 spec 把它们落成可观察结果，不扩张。

## 术语

- **Issue JSON / ISSUE_FILE**：`python3 -m aisoft_loop.cli get-issue N FILE` 写出的 JSON 对象；两个
  wrapper（`analyze-codex.sh`、`analyze-claude.sh`）先把它整份喂给 analyzer，再喂给 `render-analysis`。
- **`comments`**：Gitea Issue 对象自带的整数计数，保留不动。
- **`issue_comments`**：本变更新增的列表字段；每项恰有四键 `id`（int）、`author`（login 字符串）、
  `created_at`（字符串）、`body`（字符串），按 Gitea 返回顺序（创建时间升序）排列；与 broker
  `gitea.issue.comments.read` 的投影同形。
- **凭据路径**：`load_agent_env` 从 `GITEA_TOKEN_FILE` 读入的 project-agent token，经 `GITEA_TOKEN`
  环境变量进入 `GiteaClient`；本变更不新增任何凭据来源或 owner 例外。
- **fixture**：`codex/tests/fixtures/classification/issue-comment-overrides-body.json`，正文含
  `## 验收标准` 且带 `complexity/small` 标签、自称局部 bug 修复；`issue_comments` 中一条后续评论把范围
  改为新增 schema 迁移（新增表与数据回填）。

## Acceptance criteria

- [ ] **AC-1 payload 含评论内容、计数保留**：`GiteaClient.list_issue_comments(n)` 以 `limit=50` 分页
  GET `/issues/{n}/comments`，最多 100 页，超界抛 `GiteaError`；每项 schema 不符抛 `GiteaError`；
  token 只出现在 Authorization header。`get-issue` 输出对象同时含原始 `comments` 整数与
  `issue_comments` 列表，且 `len(issue_comments)` 与真实评论数一致（单测用 FakeTransport 断言
  端点、分页次数、投影四键与计数保留）。`get_issue()` 方法与 Controller 调用次数不变。
- [ ] **AC-2 wrapper 知道自己不全**：`render-analysis` 读到的 Issue JSON 若 `issue_comments` 不是 list，
  以 `AnalysisError` 退 2 并打印明确原因；带空列表或非空列表都正常渲染，summary 内容不因评论变化
  （评论只进 analyzer，不进 summary 模板）。单测覆盖三种输入。
- [ ] **AC-3 analyzer 输入合同显式消费评论**：`codex-analyzer.sh` 与 `claude-analyzer.sh` 的 prompt
  各新增一行同义规则：`issue_comments` 是按时间顺序的完整评论线程，后出现的修订/收窄/推翻正文
  范围的评论对判级优先于正文，且必须在 `evidence` 中引用所依据的评论。
  `codex/skills/gitea-analyze-change/SKILL.md` 第 1 步补充同一规则与字段名；两份 analyzer 脚本
  的其余行逐字不变。
- [ ] **AC-4 fixture 判级为 complex**：用真实 CLI 在本机 checkout 上分别运行
  `codex/agent/claude-analyzer.sh <fixture> <out> <repo>` 与 `codex/agent/codex-analyzer.sh <fixture> <out> <repo>`，
  两者经 `validate-analysis` 后 `effective_complexity: complex`、`requested_complexity: small`、
  `override_reason` 非空、`risk_flags` 含 `schema-change`（或同义稳定名）。基线对照：同一 fixture
  删除 `issue_comments` 后至少一个 analyzer 判 `small`（证明盲区真实存在）；若基线也判 complex，
  照实记录，不算失败。原始输出与命令写进 verification。
- [ ] **AC-5 既有消费者全部通过**：`bash codex/tests/smoke.sh` rc=0（含 `unittest discover` 全量、
  `check-change-documents`、token/argv 守卫）；`shellcheck -S warning` 对两份 analyzer 脚本无新增告警；
  `analyze-codex.sh`、`analyze-claude.sh` 调用行不变；`test_parity`、`test_controller` 不需改动即通过。
- [ ] **AC-6 权限边界不变**：`git diff origin/main --stat` 不含 `codex/config/`、
  `codex/runtime/aisoft_host_access/`、`codex/install-*.sh`、`AGENTS.md`；`grep -rn source_credential_owner codex/config` 输出与 `origin/main` 逐字相同；新增代码只发 GET。

## 接口、数据与兼容性影响

- **`get-issue` 输出形状**：新增顶层键 `issue_comments`，其余键原样。仓内消费者只有两个 wrapper 与
  `render-analysis`；前者透传，后者按 AC-2 变为要求该键。VM 上 runtime 与 agent 脚本由 `install-vm.sh`
  同一次安装，不存在跨版本混用；重装本身不在本 Issue 内执行。
- **HTTP 调用数**：`get-issue` 从 1 次变为 1 + ceil(评论数/50)（0 条评论也调 1 次）。`apply-analysis`、
  `publish-spec/plan`、Controller 不变。
- **Prompt 长度**：随评论线程线性增长；不引入截断（截断重造盲区），由模型上下文承担。
- **凭据**：同一 `GITEA_TOKEN`，只读 GET；`coder` 不获得任何新权限，broker owner 策略不动。

## 授权范围（治理文件）

本 spec 明确授权修改以下 Agent 行为文件，且仅限 AC-3 所述的一句规则：
`codex/skills/gitea-analyze-change/SKILL.md`、`codex/agent/codex-analyzer.sh`、
`codex/agent/claude-analyzer.sh`；另授权 `04-Agent编排与定时任务.md` §4 补一句 analyzer 输入合同。
不授权修改 `AGENTS.md`、其它 skill、controller、CI 或部署脚本。

## 风险与回滚约束

- 回滚 = revert 唯一 PR。runtime 与 prompt 在同一 PR，revert 后两侧同时回到旧形状，不会出现
  「prompt 要评论、payload 没评论」的半程状态。
- `render-analysis` fail-closed 是新的硬失败点，但只对不经 `get-issue` 生成的 Issue JSON 触发；
  仓内不存在这种调用方。
- fixture 结果依赖真实模型，verification 只记录、不改写；若某一侧 analyzer 判级不为 complex，
  停下升级给人，不调 prompt 到通过为止。

## 非目标

- 不实现方向 2（VM 侧独立评论入口）或方向 3（正文唯一契约）。
- 不给 `coder` 开 broker 通道，不改 `vm_profile_policy`、`host-access-broker.json`。
- 不改 `analyze_route` 的验收标准判定（仍只看正文 `## 验收标准`）；评论追加的验收标准是否算数是
  另一个合同问题。
- 不在 VM 上重装 runtime，不跑 VM canary。
- 不改 Controller 读评论的方式（`04` §5 的 controller 复核是另一条路径）。

## 未决问题

无。
