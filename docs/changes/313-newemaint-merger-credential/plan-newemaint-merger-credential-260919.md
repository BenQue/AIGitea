---
issue: 313
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/313
change_type: security
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - security
  - authorization
  - platform-governance
  - shared-core
depends_on:
  - 312
status: contract-drafting
branch: change/313-newemaint-merger-credential
created: 2026-09-19
updated: 2026-09-19
---

# Implementation plan

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 让缺陷在测试里可见：`test_host_access.py` 的假 transport 按 token 声明的 scope 决定 `/api/v1/user` 返回 200 还是 403，并记录当前合同下的红 | - | pending |
| T02 | scope 合同与 governance runtime 校验同步补 `read:user`，T01 转绿 | T01 | pending |
| T03 | `bootstrap-gitea-service-account.sh` 的 routine PAT 读回闸门与其 shell 测试同步到新集合 | T02 | pending |
| T04 | `06-运维手册与踩坑集.md` 新增诊断条目；全量 smoke 与四套测试 | T03 | pending |
| T05 | 负责人重发 token 与两台重装之后，只读复验 AC-1 并回填 verification | T04 | pending |

T05 依赖负责人动作，是本 Issue 的授权闸门；会话在该步只做只读读回。

## Expected touch points

- **T01**：`codex/runtime/tests/test_host_access.py`（`/api/v1/user` 假 transport 分支）
- **T02**：`codex/config/gitea-governance.json` 的 `routine_merge_agent_policy.token_scopes`；
  `codex/runtime/aisoft_gitea_governance/contract.py` 的逐字校验
- **T03**：`codex/tools/bootstrap-gitea-service-account.sh` 的 routine scope 读回闸门；
  `codex/tests/test-bootstrap-gitea-service-account.sh` 的 mock 与断言
- **T04**：`06-运维手册与踩坑集.md`
- **T05**：`docs/changes/313-newemaint-merger-credential/verification-newemaint-merger-credential-260919.md`

这是范围提示，不授权扩大 spec。触碰上述之外的治理文件需要回到确认点。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | `host-access-broker --project newemaint --operation host.access.audit`，读回非 BLOCKED 且 `routine_merge.actual_token_scopes` 为两项 |
| AC-2 | verification 文档 review，确认含 403 精确位置、账号状态、scope 结论，且不含 token 值 |
| AC-3 | `git diff` review 四处集合逐字一致；`python3 -m unittest tests.test_gitea_governance` |
| AC-4 | 逐处回退的反向证明，记录 `ContractError` 或断言失败原文 |
| AC-5 | 先在未修 manifest 时跑改后的用例并记录红，再在修好后跑绿 |
| AC-6 | `06` 新条目 review |
| AC-7 | `bash codex/tests/smoke.sh`、`python3 -m unittest tests.test_host_access tests.test_routine_merge tests.test_gitea_governance`、`check-change-documents --repo <checkout>`、`apply-classification-labels.sh --verify 313` |

## 部署与回滚

无部署影响。本变更不调用 deploy，不改分支保护，不执行 merge。

安装面：合同进入 source 不等于生效，必须由负责人在 Mac 与 gitea-ci 两台重新运行
`codex/install-host-access-broker.sh`。会话没有 sudo，不执行 installer。

回滚：revert 本 PR 的 merge commit 并两台重装，scope 集合回到单条 `write:repository`，
audit 回到当前已知的 `HTTP_403`。不产生新的破坏状态。
