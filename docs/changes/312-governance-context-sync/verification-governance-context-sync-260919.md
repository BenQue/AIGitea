---
issue: 312
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/312
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - shared-core
  - ci-integration
depends_on: []
status: verified
branch: change/312-governance-context-sync
created: 2026-09-19
updated: 2026-09-19
---

# Verification：#312

## 基线与范围

- Commit SHA: `a19beddf501f37383979ae090d9b20aafe4c21b6`（本记录所引 CI 证据对应的 head）。
  此后每一条只改本文件的证据 commit 都会让 PR head 再前进一次并触发自己那一轮 CI；
  合并闸门读的是合并那一刻的最后一轮，PR 页面即事实源。
- 基线：`origin/main` = `95c0f1912b4e224e6f1b37824312cdc2abb0574b`
- 环境：Mac，change worktree `/private/tmp/issue-312-governance-context-sync`；
  Gitea `http://gitea-ci.orb.local:3000`
- 本记录负责证明的 acceptance criteria: AC-1、AC-2、AC-4，以及 AC-3 的读回

**候选 runtime 验收**：Mac 的 `/usr/local` 写入需要 `sudo`，本会话的权限策略拒绝 `sudo`，
所以全部 live 读回都用**源码 runtime + 本分支 manifest** 执行
（`PYTHONPATH=codex/runtime python3 -m aisoft_host_access.cli --access-manifest …
--governance-manifest … broker …`）。它连的是同一个真实 Gitea、用的是同一套受保护凭据，
验的是本分支的代码与 manifest，只是不改变已安装状态。真正的两台重装未执行，见「遗留风险与未完成项」。

## 改动前基线（只在改动前观测得到）

| 观测 | 结果 | 证据 |
|---|---|---|
| `host.access.audit --project newemaint`（已安装 runtime） | BLOCKED | `{"code": "PROTECTION_MISMATCH", "message": "protected main does not match the governance boundary", "status": "BLOCKED_EXTERNAL"}` |
| `gitea.protection.read --project newemaint` | 两条 context | `"status_check_contexts": ["CI / verify (pull_request)", "CI / mobile-verify (pull_request)"]`；`enable_status_check: true`；`merge_whitelist_usernames: ["admin"]`（routine merger 尚未进入 allowlist，pre-apply 状态）；`updated_at: 2026-09-19T09:35:22+08:00` |
| manifest NewEMaint `status_check_contexts` | 一条 context | 改动前 `codex/config/gitea-governance.json` 仅 `CI / verify (pull_request)` |
| 只加 context、不改 `contract.py` | 整份合同拒绝加载 | scratch 副本 + `load_contract`：`ContractError routine_live_pilot requires one exact status context: NewEMaint` |
| 只改 `contract.py`/manifest 之一（装半边） | 整份合同拒绝加载 | 把 `contract.py` 还原到 `HEAD` 再跑新 manifest：`ContractError repositories[3].routine_live_pilot keys mismatch: missing=['required_context'] extra=['required_contexts']`；三个用例同时 error |

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| `load_contract` 读本分支 manifest | PASS | NewEMaint `status_check_contexts` 与 pilot `required_contexts` 均为 `('CI / verify (pull_request)', 'CI / mobile-verify (pull_request)')` |
| 反向证明：pilot 少声明一条 | PASS（正确拒绝） | `ContractError: routine_live_pilot required contexts mismatch for NewEMaint` |
| 反向证明：新用例对旧 `contract.py` | PASS（正确变红） | `test_pilot_accepts_more_than_one_context_and_pins_every_one`、`test_pilot_rejects_contexts_that_disagree_with_the_repository`、`test_newemaint_is_the_only_pilot_and_other_repositories_match_pinned_bytes` 三条一起 error |
| `python3 -m unittest tests.test_gitea_governance` | PASS | Ran 51 tests，OK |
| `python3 -m unittest tests.test_routine_merge tests.test_host_access` | PASS | Ran 207 tests，OK |
| `bash codex/tests/test-project-check.sh` | PASS | `project check tests passed (61 cases)` |
| `bash codex/tests/smoke.sh` | PASS | exit 0；`Ran 967 tests … OK`；`Codex platform static smoke checks passed.` |
| broker `git.push.change` | PASS | `pushed_head` = `8798bc3f74c9ac111128d5becc17b66040580af6`，与确认点 2 核验的 SHA 逐字相同；回填 `pr_url` 后第二次推送 `previous_head` = `8798bc3f…`、`pushed_head` = `a19beddf501f37383979ae090d9b20aafe4c21b6` |
| broker `gitea.pull.create --issue 312` | PASS | PR 314，head `8798bc3f74c9`，`mergeable: true` |
| PR final head 的 required CI | PASS | `gitea.commit.status.read --sha a19beddf501f37383979ae090d9b20aafe4c21b6`：combined `success`，唯一 context `CI / verify (pull_request)` 为 `success`（2026-09-19 16:31） |
| `apply-classification-labels.sh --verify 312` | PASS | `{"result":"projected","change_type":"platform","complexity":"complex"}`，detail `Issue #312 carries the classification its merged summary declares` |
| `aisoft-loop check-change-documents --repo .` | PASS | `PASS: change-documents` / `PASS: change-pr-url`；`changes=143 pass=2 gap=0` |
| `host.access.audit --project newemaint`（候选合同） | BLOCKED，但**不再是 PROTECTION_MISMATCH** | `{"code": "HTTP_403", …}`；请求序列显示 `branch_protections/main` 返回 200 并通过比对，audit 继续推进到 routine merger 段 |
| `host.access.audit`（候选合同，其余三仓） | PASS | `localwms`、`sfm-digital-board`、`aisoft-platform` 均正常返回完整 audit JSON |

### 四项目 audit 状态

| 项目 | 改动前（已安装旧合同） | 改动后（候选合同） |
|---|---|---|
| `newemaint` | BLOCKED_EXTERNAL / **PROTECTION_MISMATCH** | BLOCKED_EXTERNAL / **HTTP_403**（换了根因，见下） |
| `localwms` | PASS | PASS |
| `sfm-digital-board` | PASS | PASS |
| `aisoft-platform` | PASS | PASS |

`myapp` 与 `smoke-test` 是 manifest 里的占位项目，无凭据绑定，改动前后都是
`CREDENTIAL_UNAVAILABLE`，与本次无关。

### newemaint 那条 HTTP 403 是先于 #312 就存在的独立缺陷

只读请求序列（源码 runtime，transport 加 trace）：

```text
200 GET /api/v1/user                                   ×3   身份核验
403 GET /api/v1/notifications                          ×3   token scope 探针，403 是设计中的
200 GET /api/v1/repos/admin/NewEMaint/collaborators/aisoft-platform-manager/permission
200 GET /api/v1/repos/admin/NewEMaint/collaborators/newemaint-agent/permission
200 GET /api/v1/repos/admin/NewEMaint/branch_protections/main     ← 本次修好的那一步，现已通过
200 GET /api/v1/users/newemaint-routine-merger                    帐号存在、非 site admin
403 GET /api/v1/user                                              ← 用 routine merger 自己的 token
```

即：分支保护比对现在通过了，audit 因此第一次推进到 routine merger 段，随后用
`newemaint-routine-merger` 的凭据调 `/api/v1/user` 拿到 403。

**与本次改动无关的证明**：用**已安装的 pre-#312 runtime 与 manifest**
（`PYTHONPATH=/usr/local/lib/aisoft-host-access`，manifest 取 `/usr/local/share/aisoft/`，读回
contexts 确认是旧的单条声明）单独解析同一个 routine 凭据并调用 `_verify_identity`：

```text
installed NewEMaint contexts: ('CI / verify (pull_request)',)
routine identity: newemaint-routine-merger
identity verify -> HTTP_403
```

凭据是否可用与 required context 集合毫无关系。它先于 #312 就坏了，只是
`PROTECTION_MISMATCH` 在更前面中止了整条检查链，把它挡住了。连续两次调用结果相同，不是抖动。

这条按会话合同只回报、不由本会话立案；调度会话已立为平台 **#313**
（`security(newemaint): newemaint-routine-merger 凭据调 /api/v1/user 返回 403，routine 自动合并路径不可用`，入口标签 `needs-analysis`，阻塞于 #312 合并与两台重装）。

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | **部分达成** | 「`gitea.protection.read` 的 contexts 与 manifest 声明逐字相同」已达成：两者都是 `["CI / verify (pull_request)", "CI / mobile-verify (pull_request)"]`，且 audit 的分支保护比对实测通过（请求序列里 `branch_protections/main` 之后仍在继续）。「返回非 BLOCKED」**未达成**，被上面那条先于本 Issue 存在的 routine merger 凭据 403 挡住，已立 #313，不在本次范围内 |
| AC-2 | 达成 | `smoke.sh` exit 0，967 单测 OK，61 个 project-check case 通过；新增用例 `test_pilot_accepts_more_than_one_context_and_pins_every_one` 与 `test_pilot_rejects_contexts_that_disagree_with_the_repository`（8 个子用例）分别钉住多 context 与两处声明不一致拒绝加载 |
| AC-3 | 达成 | `06-运维手册与踩坑集.md` §1.2 新增「增删 required status context 的顺序（顺序不能反，#312）」四步与反向后果；踩坑表新增第 32 条，写明 2026-09-19 本例、症状、根因与定案 |
| AC-4 | 达成 | 上面的四项目 audit 表；`check-change-documents` PASS（`changes=142 pass=2 gap=0`）；`apply-classification-labels.sh --verify 312` 读回 `projected`，两个维度分别为 `type/platform` 与 `complexity/complex` |

## 遗留风险与未完成项

- **两台重装 NOT RUN**。`sudo` 在本会话被权限策略拒绝，`/usr/local` 不可写。合并后需要负责人在
  Mac 与 gitea-ci VM **两台**执行：

  ```bash
  sudo bash codex/install-host-access-broker.sh
  ```

  重装前 checkout 必须已 fast-forward 到含本 PR 的 `origin/main`，否则 installer 的 staleness
  闸门会 fail closed。**两台必须一起装**：manifest 与 `aisoft_gitea_governance` 是一对，只装一边
  会让那一边加载合同失败——本记录「改动前基线」表的最后一行就是这个形态的实测。
  已安装状态目前**完全未被触碰**，仍是合并前的旧合同，因此平台当下行为与会话开始时相同。
- **幂等与回滚 NOT RUN**，同一原因。回滚路径：checkout 回到不含本 PR 的 `origin/main` 后重跑同一
  installer，预期 audit 回到 `PROTECTION_MISMATCH`。
- **NewEMaint routine merger 凭据 403** 未修，见上节，已立 **#313**。它使 NewEMaint 的 routine
  自动合并路径当前不可用（`host.access.audit` 仍 BLOCKED）；manual PR 与 typed 写操作不受影响。
  凭据签发是负责人动作，#313 阻塞于本 PR 合并与两台重装，不在本次范围内。
- 06 踩坑编号 32 是跨 PR 共享的可变状态，并行会话可能同时取 32；撞号由合并者改。
