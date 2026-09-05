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
status: verified
branch: change/180-analyzer-issue-comments
created: 2026-09-05
updated: 2026-09-05
---

# Verification · get-issue payload 带上 Issue 评论内容，analyzer 输入合同显式消费评论

## 基线与范围

- Commit SHA: `4cfdc8d`（approved 合同文档）、`075d099`（T01 runtime）、`45bc931`（T02 analyzer 输入合同与 fixture）；本记录随 T03 提交，SHA 见 PR
- 基线：`origin/main` = `07084de`（Merge PR #242，#241 platform-ops-neutral）
- 环境: Mac 本机 worktree `/private/tmp/issue-180-analyzer-issue-comments`；`claude` 2.1.228 可用；
  `codex-cli 0.147.0` 本机可执行但被配置模型/账号限制挡住（见 AC-4）；真实 `rg`、`shellcheck` 可用；
  python 3.14
- 本记录负责证明的 acceptance criteria: AC-1～AC-6（spec 同名条目）

## 基线观测（改动前，只能在此刻留下）

| Command / check | Result | Evidence |
|---|---|---|
| `origin/main` 的 `get-issue` 路径 | 只 dump `get_issue()` | `cli.py:402-412` 原样写出 Gitea Issue 对象；`gitea.py` 无任何 `/comments` GET |
| 旧 prompt + 去评论 fixture（`old-claude-analyzer.sh` = `origin/main` 版本，输入为 fixture `del .issue_comments`） | rc=0，2m35s | 判级 `assessed_complexity: needs-human-decision`、`contract_effect: unclear`、`requested_complexity: small`；reason 写明「the Issue also records 1 comment whose content is absent from the analyzer input, so a scope-revising comment cannot be ruled out」；override_reason 要求人确认评论线程 |
| 旧 prompt + 去评论 fixture（`old-codex-analyzer.sh`） | rc=1，NOT RUN | Codex CLI 400：配置模型 `gpt-6-astra` 要求更新 CLI；`CODEX_MODEL=gpt-5.4`、`gpt-5-codex` 均报「not supported when using Codex with a ChatGPT account」 |
| `bash codex/check-drift.sh`（改动前状态由改动后输出反推） | 改动后 DRIFT 两项 | `gitea-analyze-change/SKILL.md`（本次）与 `gitea-platform-ops/SKILL.md`（#241 合并后尚未重装，非本次引入） |

基线对照的结论：旧流水线对该 fixture 没有判 `small`，而是因为看见 `comments: 1` 却读不到内容而停在
needs-human-decision——盲区真实存在，只是这一次模型选择了保守停下而不是静默按不全信息判级。
spec AC-4 已预先声明「若基线不判 small 照实记录，不算失败」。

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| `PYTHONPATH=codex/runtime python3 -m unittest tests.test_gitea tests.test_issue_payload`（T01 实现前） | 红：failures=4 errors=10 | `list_issue_comments` 缺失、`render-analysis` 对缺键 payload 退 0 |
| 同上（T01 实现后） | `Ran 22 tests … OK` | 4 条客户端用例 + 4 条 payload/守卫用例全绿 |
| `PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests -t codex/runtime` | `Ran 668 tests in 36.6s OK` | 基线 660 + 新增 8 |
| `bash codex/tests/smoke.sh`（T02 后，rc 见右） | rc=0 | 末行 `Codex platform static smoke checks passed.`，含 unittest 668、`check-change-documents` `pass=2 gap=0`、analyzer heading 守卫、token/argv 守卫、skill 项目名/交付形态守卫 |
| `bash -n` + `shellcheck -S warning codex/agent/codex-analyzer.sh codex/agent/claude-analyzer.sh` | rc=0，无输出 | 两份脚本各只 +1 行 printf 参数 |
| `git diff origin/main --numstat -- codex/agent/*-analyzer.sh` | `1 0` × 2 | AC-3 逐字对照：新增行为同一句英文规则 |
| `grep -c issue_comments` 两份 analyzer 脚本与 `gitea-analyze-change/SKILL.md` | 各 1 | 字段名进入 prompt 与 skill |
| 新 prompt + 带评论 fixture：`env -u CLAUDECODE AISOFT_LOOP_RUNTIME_DIR=codex/runtime bash codex/agent/claude-analyzer.sh <fixture> <out> .` | rc=0，2m15s，经 `extract-json` + `validate-analysis` | 见下方 AC-4 原始输出 |
| 新 prompt + 带评论 fixture：`codex-analyzer.sh` 同参 | rc=1，NOT RUN | 三次尝试同一根因（CLI 0.147.0 与 `gpt-6-astra`、账号不放行 `gpt-5.4`/`gpt-5-codex`），按「同一根因三次」规则停止 |
| `git diff origin/main -- codex/config codex/runtime/aisoft_host_access AGENTS.md codex/install-*.sh` | 0 行 | AC-6 |
| `gitea.py` 中 `"POST"|"PATCH"|"DELETE"|"PUT"` 计数 now vs `origin/main` | 3 vs 3 | 新增代码只发 GET |
| `grep -rn source_credential_owner codex/config` | 与 `origin/main` 逐字相同（`"benque"`） | `vm_profile_policy` 未动 |
| `grep -c "get_issue(" controller.py` now vs main | 2 vs 2 | Controller 调用不变 |
| `check-drift.sh` | DRIFT 两项，rc=1 | 见基线观测；重装由用户独立执行 |

### AC-4 原始输出（claude-analyzer，新 prompt，fixture 含评论）

```yaml
change_type: platform
requested_complexity: small
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 评论 90001 将范围推翻为治理 manifest schema 新增字段、全量 repositories 数据迁移与旧 manifest 拒绝的校验升级，命中强制 complex 规则
risk_flags:
  - schema-change
  - data-migration
  - external-contract
  - platform-governance
  - shared-core
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: 正文与 complexity/small 标签要求 small，但评论 90001 声明三项一起交付且正文验收标准作废，schema/数据迁移与治理校验变更按 AGENTS.md 强制 complex
```

evidence 第一条：`issue_comments[0]（id 90001，admin，2026-09-05T11:20+08:00）：声明范围改变为三项一起交付且正文验收标准作废，是本分类的唯一有效范围来源`——评论被引用为依据，满足 AC-3 的「evidence 必须引用所依据的评论」。

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 payload 含评论、计数保留 | PASS | `test_list_issue_comments_pages_projects_and_keeps_token_in_header`（端点 `?limit=50&page=1/2`、投影四键、token 只在 header）、`…_silent_issue_is_one_empty_page`、`…_rejects_invalid_entries_and_shapes`、`…_scan_is_bounded`（100 页后 GiteaError）；`test_get_issue_appends_the_thread_and_keeps_the_count`（`comments`=2 且 `len(issue_comments)`=2，文件 0600，调用序 issue→comments）；`test_get_issue_fails_instead_of_writing_a_thread_less_payload` |
| AC-2 wrapper 知道自己不全 | PASS | `test_payload_without_the_thread_fails_closed`（缺键、int、None 三种均 rc=2 且 stderr 含 `issue_comments`、无文件写出）；`test_empty_and_populated_threads_render_the_same_summary`（空/非空线程 summary 逐字相同，评论不进 summary） |
| AC-3 analyzer 输入合同 | PASS | 两份脚本各 +1 行、skill 第 1 步补规则、`04` §4 补一句；smoke 的 analyzer heading 守卫与治理 grep 守卫仍绿 |
| AC-4 fixture 判级 complex | PARTIAL | claude 侧 PASS（`effective_complexity: complex`、`requested_complexity: small`、`override_reason` 非空、`risk_flags` 含 `schema-change`、evidence 引用评论 90001）；codex 侧 NOT RUN（外部阻塞，见执行结果）；基线 claude 判 needs-human-decision 而非 small，照实记录 |
| AC-5 既有消费者通过 | PASS | smoke rc=0；668 单测；shellcheck 无告警；`analyze-codex.sh`/`analyze-claude.sh` 调用行 diff 为空；`test_parity`、`test_controller` 未改动即通过 |
| AC-6 权限边界不变 | PASS | 上表四条 diff/grep 对照 |

## 遗留风险与未完成项

- **codex-analyzer 端到端 NOT RUN**：本机 `codex-cli 0.147.0` 不支持 `~/.codex/config.toml` 配置的
  `gpt-6-astra`，ChatGPT 账号又不放行 `gpt-5.4`/`gpt-5-codex`。两份 analyzer 的新增 prompt 行逐字相同，
  `validate-analysis` 路径共享，但模型行为未经真实观测；升级 Codex CLI 后重跑同一命令即可补证。
- VM 重装 runtime/agent 脚本（`codex/install-vm.sh`）：NOT RUN，不在本 Issue 内；重装前 VM 上的
  `render-analysis` 仍是旧版本，不会触发新守卫，也不会读评论。
- 本机 skills 副本重装（`codex/install-skills.sh`）：NOT RUN，由用户独立执行；`check-drift.sh` 当前
  DRIFT 两项（其一为 #241 遗留）。
- 评论线程过长时的 prompt 长度未设上限（spec 非目标）。
