---
issue: 222
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/222
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - functional-change
  - external-contract
  - shared-core
  - authorization
  - platform-governance
depends_on: []
status: approved
branch: change/222-issue-list-state-set
created: 2026-09-05
updated: 2026-09-05
---

# Implementation plan · #222

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | `gitea.issue.list`：合同、manifest、dispatch、投影分页、runner 方法、测试 | - | pending |
| T02 | `gitea.issue.state.set`：合同、manifest、dispatch、写路径与幂等、runner 方法、测试 | - | pending |
| T03 | 文档：`06` §1.0 精确集合语义与两条命令，踩坑表新增一行 | T01, T02 | pending |
| T04 | 候选 manifest 实机验收与 verification 文档 | T01, T02, T03 | pending |
| T05 | 两份 issue-session-flow skill 的清扫枚举改用 gitea.issue.list | T01 | pending |

T01 与 T02 各自触碰同样的六个同步点，串行执行以免两次改同一处计数互相覆盖。

## Expected touch points

**T01 / T02（每个操作都要走完踩坑 20 的六处）**

1. `codex/runtime/aisoft_host_access/contract.py` — `EXPECTED_OPERATIONS` 增条目；
   注释写清为什么是这个 route、这个 mutating 值与这组 arguments。
2. `codex/runtime/aisoft_host_access/broker.py` — `_gitea()` 增 dispatch 分支；
   新增 `_issue_list()` 与 `_set_issue_state()` 两个投影 helper（分页约定抄 `_issue_comments`）。
3. `codex/runtime/aisoft_host_access/runner.py` — `GovernedHostRunner.issue_list()` 与
   `issue_state_set()`。
4. `codex/config/host-access-broker.json` — operations 表两条。
5. `codex/runtime/tests/test_host_access.py` — 新用例，并把两项加进既有
   `test_governed_issue_and_pull_operations_have_exact_typed_fields` 的表。
6. `codex/tests/test-host-access-broker.sh` — `operation_count == 36` 与
   `[.operations[].name] | length == 36` 两处，加两条 arguments 断言。

**不动**：`codex/runtime/aisoft_host_access/cli.py`。`--number` 与 `--state` 已存在，
因此踩坑 20 的第七处（`test_cli_exposes_only_typed_issue_and_pull_fields` 逐字钉死的
`execute()` kwargs）不受影响。

**T03**：`06-运维手册与踩坑集.md` §1.0（两条命令 + 精确集合语义段落）与踩坑表第 26 行。
加行前重新 `gitea.pulls.read --state open` 核对没有别的 PR 也在占 26 号（踩坑 22）。

**T04**：`docs/changes/222-issue-list-state-set/verification-issue-list-state-set-260905.md`。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | `codex/tests/test-host-access-broker.sh` 的 arguments 断言；`test_governed_issue_and_pull_operations_have_exact_typed_fields` |
| AC-2 | `test_host_access.py` 新用例断言 PATCH 方法与 body；实机 `host.access.audit` 读回 project-agent 的 `repository_permission` 与 scope |
| AC-3 | `test_host_access.py` 断言 `--state all` 抛 `ARGUMENT_INVALID` 且零 HTTP 请求 |
| AC-4 | `test_host_access.py` 多页 fake transport 用例；实机候选 manifest 调用读回真实条数 |
| AC-5 | `test_host_access.py` 混入 `pull_request` 非空条目，断言 `issues` 不含它且 `pull_requests_excluded` 计数正确 |
| AC-6 | `bash codex/tests/smoke.sh` |
| AC-7 | diff review：`06` §1.0 与踩坑表第 26 行 |
| AC-9 | diff review 两份 SKILL.md；`bash codex/tests/smoke.sh` 的 governance-set 与清扫段守卫 |
| AC-8 | `PYTHONPATH=codex/runtime python3 -m aisoft_host_access.cli --access-manifest codex/config/host-access-broker.json --governance-manifest codex/config/gitea-governance.json broker --project aisoft-platform --operation gitea.issue.list --state open`，输出抄进 verification |

## 未执行项（人工交接）

两台（Mac 与 gitea-ci VM）`sudo bash codex/install-host-access-broker.sh` 重装，
合并后由人执行。未重装前 `/usr/local/libexec/aisoft/host-access-broker` 对这两个操作
返回 `REQUEST_DENIED`，那是安装期操作表陈旧，不是权限问题（踩坑 20）。
