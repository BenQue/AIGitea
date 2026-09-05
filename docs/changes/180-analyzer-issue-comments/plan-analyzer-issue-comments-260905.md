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

# Plan · get-issue payload 带上 Issue 评论内容，analyzer 输入合同显式消费评论

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | runtime：`GiteaClient.list_issue_comments` + `get-issue` 组合 `issue_comments` + `render-analysis` fail-closed 守卫；对应单测先红后绿（AC-1、AC-2） | - | pending |
| T02 | analyzer 输入合同：两份 analyzer prompt 各加一行、skill 第 1 步补字段名与规则、`04` §4 补一句；fixture JSON 落盘；`smoke.sh` 与 shellcheck 绿（AC-3、AC-5、AC-6） | T01 | pending |
| T03 | 真实 analyzer 跑 fixture（claude 与 codex 各一次）+ 去评论基线对照；填 verification（AC-4 与全部 AC 结果、未执行项） | T01, T02 | pending |

Ticket ID 固定为 `Txx`；依赖只引用本表中的 ID。T02 依赖 T01：prompt 要求读 `issue_comments` 而
payload 还没有该键会让 fixture 与 render 守卫互相矛盾。T03 依赖两者定稿：fixture 判级证明必须跑在
最终 prompt 与最终 payload 形状上。选 vertical slice，每张 ticket 独立可验证。

## Expected touch points

- **T01**：`codex/runtime/aisoft_loop/gitea.py`（新增方法）、`codex/runtime/aisoft_loop/cli.py`
  （`_get_issue`、`_render_analysis`）、`codex/runtime/tests/test_gitea.py`（新增用例）、新增
  `codex/runtime/tests/test_issue_payload.py`（`_get_issue` 组合与 `render-analysis` 守卫）。
- **T02**：`codex/agent/codex-analyzer.sh`、`codex/agent/claude-analyzer.sh`（各一行 printf 参数）、
  `codex/skills/gitea-analyze-change/SKILL.md`（第 1 步）、`04-Agent编排与定时任务.md`（§4）、
  `codex/tests/fixtures/classification/issue-comment-overrides-body.json`（新增）。
- **T03**：`docs/changes/180-analyzer-issue-comments/verification-analyzer-issue-comments-260905.md`。

这是范围提示，不授权扩大 spec：`codex/runtime/aisoft_host_access/`、`codex/config/`、
`controller.py`、`analysis.py` 的路由逻辑、`analyze-codex.sh`/`analyze-claude.sh`、`AGENTS.md`、
其它 skill 都不在 touch points 内。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 payload 含评论、计数保留 | `PYTHONPATH=codex/runtime python3 -m unittest tests.test_gitea tests.test_issue_payload -v`：端点 `/issues/8/comments?limit=50&page=1`、两页分页、schema 拒绝、token 只在 header、`comments` 与 `issue_comments` 同时存在且长度一致；`grep -c "get_issue(" codex/runtime/aisoft_loop/controller.py` 与 origin/main 相同 |
| AC-2 wrapper 知道自己不全 | 同上测试文件：缺键退 2 且 stderr 含 `issue_comments`；空列表与非空列表渲染出的 summary 逐字相同 |
| AC-3 analyzer 输入合同 | `git diff origin/main -- codex/agent/codex-analyzer.sh codex/agent/claude-analyzer.sh` 各恰好 +1 行；`grep -c issue_comments` 对两份脚本与 skill 各 ≥ 1；`bash codex/tests/smoke.sh` 中 analyzer heading 守卫仍绿 |
| AC-4 fixture 判级 complex | 本机：`AISOFT_LOOP_RUNTIME_DIR=codex/runtime bash codex/agent/claude-analyzer.sh <fixture> <out> .` 与 `codex-analyzer.sh` 同参；`python3 -c` 读 out 断言 `effective_complexity: complex`、`override_reason` 非空；基线：`jq 'del(.issue_comments)' fixture > base.json` 后同样运行并记录 |
| AC-5 既有消费者通过 | `bash codex/tests/smoke.sh; echo rc=$?` → 0；`shellcheck -S warning codex/agent/codex-analyzer.sh codex/agent/claude-analyzer.sh` |
| AC-6 权限边界不变 | `git diff origin/main --stat` review；`git diff origin/main -- codex/config codex/runtime/aisoft_host_access AGENTS.md` 为空；`grep -rn '"POST"\|"PATCH"\|"DELETE"' codex/runtime/aisoft_loop/gitea.py` 与 origin/main 相同 |

## 部署与回滚

无部署影响。回滚 = revert 唯一 PR。VM 上 runtime 与 agent 脚本的重装（`codex/install-vm.sh`）不在本
Issue 内执行，verification 记 NOT RUN；映射的 `verification` 文档只记录本机 fixture 真实运行、基线
对照与未执行项，不含「部署验收」节。
