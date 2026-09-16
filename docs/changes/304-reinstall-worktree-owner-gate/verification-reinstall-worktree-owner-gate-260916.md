---
issue: 304
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/304
change_type: maintenance
requested_complexity: auto
assessed_complexity: small
effective_complexity: small
contract_effect: unchanged
confidence: high
risk_flags:
  - host-runtime-install
depends_on: []
status: pending
branch: change/304-reinstall-worktree-owner-gate
created: 2026-09-16
updated: 2026-09-16
---

# Verification · Issue #304 两台主机重装 broker 使 #298 归属闸门生效

## 基线与范围

- Commit SHA: 见本分支 `git log`
- 基线：`origin/main` = `e5ed35e860f0ae080ce605b29dc4d698df9ada75`
- 环境：Mac（`/usr/local/lib/aisoft-host-access/`）与 gitea-ci VM（OrbStack machine `gitea-ci`）
- 本记录负责证明的 acceptance criteria：Issue #304 正文四条（AC-1..AC-4）
- 本次变更**不部署任何制品**，因此没有 `## 部署验收` 一节。声明 `verification` 的原因是
  四条验收标准全部是主机读回，diff review 与 required CI 都复现不了。

## 执行结果

### A. 重装之前的基线证据（Mac，2026-09-16）

| Command / check | Result | Evidence |
|---|---|---|
| `grep -c pushed_head /usr/local/lib/aisoft-host-access/aisoft_host_access/broker.py` | PASS（观测到缺陷） | `0` |
| `ls /usr/local/lib/aisoft-host-access/aisoft_host_access/` | PASS（观测到缺陷） | `__init__.py broker.py cli.py contract.py profiles.py runner.py` 及各自 `.previous`；**没有** `aisoft_worktree_owner.py` |
| `grep -c pushed_head codex/runtime/aisoft_host_access/broker.py`（源码） | PASS | `1` |
| `ls codex/runtime/aisoft_worktree_owner.py`（源码） | PASS | 存在 |
| `diff -q` 已安装 vs 源码 `broker.py` | PASS（观测到缺陷） | `Files ... differ` |
| 主 checkout `git status -sb` / `git log -1` | PASS | `## main...origin/main`（无 ahead/behind，工作区干净）/ `e5ed35e` |

结论：两个 installer（`codex/install-host-access-broker.sh:58`、`codex/install-vm.sh:60`）都已收录
`aisoft_worktree_owner.py`，源码侧闸门完整。缺陷仅仅是主机未重装。

### B. 重装之前的反向证明（源码 runtime，证明闸门代码本身是好的）

调用形态：`PYTHONPATH=codex/runtime python3 -B -m aisoft_host_access.cli --access-manifest
codex/config/host-access-broker.json --governance-manifest codex/config/gitea-governance.json
--label-manifest codex/config/gitea-labels.json broker --project aisoft-platform --operation
git.push.change --branch change/304-reinstall-worktree-owner-gate`，cwd 为本 change worktree。

| Command / check | Result | Evidence |
|---|---|---|
| 源码 runtime，`AISOFT_SESSION_ID=not-the-owner-0000` | PASS（正确拒绝） | `{"code": "WORKTREE_OWNER_MISMATCH", "message": "worktree is owned by session ca740375-6b30-4296-8250-3370ceb61f01, not not-the-owner-0000; ...", "status": "BLOCKED_EXTERNAL"}` |
| 源码 runtime，未设 `AISOFT_SESSION_ID` | PASS（正确拒绝） | `{"code": "WORKTREE_OWNER_MISMATCH", "message": "AISOFT_SESSION_ID is not set; this worktree is owned by session ca740375-...", "status": "BLOCKED_EXTERNAL"}` |

### C. 重装之前，已安装 runtime 的同一次调用（缺陷的一手复现）

| Command / check | Result | Evidence |
|---|---|---|
| `/usr/local/libexec/aisoft/host-access-broker ... --operation git.push.change --branch change/304-...`，`AISOFT_SESSION_ID=not-the-owner-0000` | **未拒绝** | `{"checkout": "...", "identity": "aisoft-platform-agent", "operation": "git.push.change", "project": "aisoft-platform", "remote_name": "origin", "status": "PASS"}` —— 无 `pushed_head`、无 `session`、无 `previous_head` |
| 该次调用后 `git dir` 内 `aisoft-owner.json` | PASS（观测到缺陷） | `"last_push_head": null` —— `record_push()` 从未被调用 |
| `git.fetch.change` 后 `git rev-parse refs/remotes/origin/change/304-...` | PASS | `e5ed35e860f0ae080ce605b29dc4d698df9ada75` |

**这次调用产生了一个非预期的副作用，如实记录**：闸门尚未生效，所以这次「期望被拒绝」的调用
**真的把分支推上了远端**。推上去的 ref 等于 `origin/main`（零自有 commit，无 PR），随后被本
change 的真实推送 fast-forward 覆盖，无数据损失。教训已固化为 `06` 踩坑 30：闸门未生效时，
在已安装 runtime 上做反向证明不是空操作；重装之前只在源码 runtime 上做。

### D. 既有 typed 操作基线（重装之前）

| Command / check | Result | Evidence |
|---|---|---|
| Mac `host.access.audit` | PASS | `"status": "PASS"`，protection / token_scopes / routine_merge 均正常 |
| Mac `host.onboarding.check` | PASS | `"status": "PASS"`，`"binding": "PASS"` |
| `git.fetch.main` | PASS | `"status": "PASS"` |
| `orbstack.vm.status` | PASS | `machine gitea-ci` |
| `orbstack.runner.status` | PASS | `act_runner.service` active/running |
| `vm.profile.read-back` | PASS | `"result": "read-back"`，说明 VM 侧 root-scoped 安装面存在（见 `06` 踩坑 18） |

### E. 仓库侧回归

| Command / check | Result | Evidence |
|---|---|---|
| `bash codex/tests/smoke.sh` | PASS | `Ran 962 tests in 92.795s` / `OK` / `Codex platform static smoke checks passed.`，exit `0`（含 `tests.test_worktree_owner` 全部用例） |

### F. 重装（由人执行，需要 `sudo`）

| Command / check | Result | Evidence |
|---|---|---|
| Mac `sudo bash codex/install-host-access-broker.sh` | NOT RUN | 待填写（含 `source commit` / `source operations` 两行） |
| VM `orb -m gitea-ci sudo bash /mnt/mac/.../codex/install-host-access-broker.sh` | NOT RUN | 待填写（含 `source commit` / `source operations` 两行） |

### G. 重装之后的读回

| Command / check | Result | Evidence |
|---|---|---|
| Mac `grep -c pushed_head` 已安装 `broker.py` | NOT RUN | 待填写 |
| Mac `ls` 已安装 lib 目录含 `aisoft_worktree_owner.py` | NOT RUN | 待填写 |
| 已安装 runtime，错误 `AISOFT_SESSION_ID` | NOT RUN | 待填写 |
| 已安装 runtime，未 claim 的 worktree | NOT RUN | 待填写 |
| 已安装 runtime，正确 session 推送本分支 | NOT RUN | 待填写 |
| Mac `host.access.audit` | NOT RUN | 待填写 |
| VM `host.access.audit` | NOT RUN | 待填写 |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 两台已安装 `broker.py` 含 `pushed_head` 且 lib 目录含 `aisoft_worktree_owner.py` | NOT RUN | 待 F/G |
| AC-2 正常路径返回 `pushed_head` 且等于 `git rev-parse HEAD` | NOT RUN | 待 G |
| AC-3 反向证明：`WORKTREE_OWNER_MISMATCH` 与 `WORKTREE_UNCLAIMED` | 源码 runtime 已证（B，仅 MISMATCH 两型）；**已安装 runtime NOT RUN** | 待 G |
| AC-4 两台 `host.access.audit` 均 `PASS`，既有 typed 操作无回归 | Mac 重装前基线 PASS（D）；**重装后两台 NOT RUN** | 待 G |

## 遗留风险与未完成项

- **VM 侧已安装 `broker.py` 的版本无法从 Mac 读取**：没有任何 typed 操作能读 VM 上的文件内容。
  该台 AC-1 的证据只能取自 installer 自己打印的 `source commit` / `source operations` 两行，
  以及重装后 VM 侧 `host.access.audit` 的 `PASS`。这是能力边界，不是本次遗漏。
- **没有任何机制会主动报告「已合并但未安装」**：本 Issue 的整个存在就是人事后发现的。
  drift 检测需要独立验收标准，按 `issue-session-flow` 的判据属于新 Issue，收尾时开。
- 回滚方式：installer 为每个被覆盖文件留 `.previous` 备份；回滚是复原 `.previous`，
  或从上一个 commit 重跑 installer。仓库侧回滚是 revert 本 PR（纯文档）。
