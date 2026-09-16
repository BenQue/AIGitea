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
status: verified
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
| Mac `sudo bash codex/install-host-access-broker.sh` | PASS | `source checkout: /Users/benque/MyDocs/AISoftPlatform` / `source commit: e5ed35e (level with origin/main)` / `source operations: 36` / `installed host-access-broker/v1 candidate` / `no credential, Git config, project profile, token, service, timer, VM, merge, or deployment mutation was performed` |
| VM `orb -m gitea-ci sudo bash /mnt/mac/Users/benque/MyDocs/AISoftPlatform/codex/install-host-access-broker.sh` | PASS | `source checkout: /mnt/mac/Users/benque/MyDocs/AISoftPlatform` / `source commit: e5ed35e (level with origin/main)` / `source operations: 36` / `installed host-access-broker/v1 candidate` |
| VM 同一条命令**第二次**执行（幂等证明）| PASS | `host-access-broker/v1 candidate already current (no-op)`；两次都打印 `no credential, Git config, project profile, token, service, timer, VM, merge, or deployment mutation was performed` |

### G. 重装之后的读回

| Command / check | Result | Evidence |
|---|---|---|
| Mac `grep -c pushed_head /usr/local/lib/aisoft-host-access/aisoft_host_access/broker.py` | PASS | `1`（重装前为 `0`）|
| Mac `ls /usr/local/lib/aisoft-host-access/` | PASS | `aisoft_change_name.py  aisoft_gitea_governance  aisoft_host_access  aisoft_worktree_owner.py`；`-rw-r--r-- root wheel 12614 Sep 16 21:50 aisoft_worktree_owner.py`。`diff -q` 对源码：`broker.py` 与 `aisoft_worktree_owner.py` 均**完全一致**。已安装 manifest `operations` 计数 `36`，与仓库一致 |
| 已安装 runtime（wrapper），`AISOFT_SESSION_ID=not-the-owner-0000` | PASS（正确拒绝） | `{"code": "WORKTREE_OWNER_MISMATCH", "message": "worktree is owned by session ca740375-6b30-4296-8250-3370ceb61f01, not not-the-owner-0000; the owning session pushes its own branch, another session notifies or hands back", "status": "BLOCKED_EXTERNAL"}` |
| 已安装 runtime（wrapper），marker 暂时移走后以正确 session 调用 | PASS（正确拒绝） | `{"code": "WORKTREE_UNCLAIMED", "message": "change worktree has no ownership marker at .../worktrees/issue-304-reinstall-worktree-owner-gate/aisoft-owner.json; claim it with: ... claim-worktree --branch <change/N-slug> --session <session id>", "status": "BLOCKED_EXTERNAL"}`。marker 随即复原，内容不变 |
| 已安装 runtime，正确 session 推送本分支（AC-2）| PASS | `{"checkout": "/private/tmp/issue-304-reinstall-worktree-owner-gate", "identity": "aisoft-platform-agent", "operation": "git.push.change", "previous_head": "e5ed35e860f0ae080ce605b29dc4d698df9ada75", "pushed_head": "d75952cce257d986719b219f765ae23b4d0b8929", "session": "ca740375-6b30-4296-8250-3370ceb61f01", "status": "PASS"}`。推送前 `git rev-parse HEAD` = `d75952cce257d986719b219f765ae23b4d0b8929`，与 `pushed_head` 相同。marker 随即写入 `"last_push_head": "d75952cc..."` 与 `"last_push_at": "2026-09-16T22:43:29+08:00"`（重装之前同一字段在推送后仍是 `null`，见 C 段）|
| Mac `host.access.audit` | PASS | `"status": "PASS"`；protection `main` / `["CI / verify (pull_request)"]` 不变 |
| Mac 既有 typed 操作回归抽样 | PASS | `host.onboarding.check` / `orbstack.vm.status` / `orbstack.runner.status` / `vm.profile.read-back` 均 `"status": "PASS"`；`gitea.repo.read` / `gitea.protection.read` / `gitea.labels.read` 均返回完整载荷、exit `0`（这三个返回裸载荷而非 status 信封，`gitea.labels.read` 是裸数组）；`gitea.issue.read --number 304` 读回 `open` + `['complexity/small', 'needs-analysis', 'type/maintenance']` |
| VM `grep -c pushed_head /usr/local/lib/aisoft-host-access/aisoft_host_access/broker.py` | PASS | `1` |
| VM `ls /usr/local/lib/aisoft-host-access/` | PASS | `__pycache__  aisoft_change_name.py  aisoft_gitea_governance  aisoft_host_access  aisoft_worktree_owner.py` |
| VM `host.access.audit` | PASS | `"status": "PASS"`；载荷与 Mac 一致（同样的 identities / token_scopes / protection / `routine_merge.enabled: false`）|
| VM 侧 typed 信号（由 Mac broker 在 VM 内执行，重装后复核）| PASS | `vm.profile.read-back` = `read-back` / `orbstack.vm.status` / `orbstack.runner.status` 均 `PASS` |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 两台已安装 `broker.py` 含 `pushed_head` 且 lib 目录含 `aisoft_worktree_owner.py` | **PASS** | Mac：`grep -c` `0` → `1`，`aisoft_worktree_owner.py` 存在且与源码 `diff -q` 一致，manifest `operations` = 36。VM：`grep -c` = `1`，`ls` 含 `aisoft_worktree_owner.py`，installer 打印 `source commit: e5ed35e (level with origin/main)` / `source operations: 36` |
| AC-2 正常路径返回 `pushed_head` 且等于 `git rev-parse HEAD` | **PASS** | `pushed_head` = `d75952cce257d986719b219f765ae23b4d0b8929` = 推送前的 `git rev-parse HEAD`；返回体同时带回 `session` 与 `previous_head`，marker 的 `last_push_head` 被真正写入 |
| AC-3 反向证明：`WORKTREE_OWNER_MISMATCH` 与 `WORKTREE_UNCLAIMED` | **PASS** | 重装后在 **Mac 已安装 runtime**（wrapper）上取得两条 exact 异常码，见 G。两次拒绝期间本地 `HEAD` = `d4e2811` 而远端 ref 仍为 `e5ed35e`，证明拒绝发生在凭据解析之前、未产生网络写。**只在 Mac 上验**：change worktree 只存在于 Mac，VM 不承载 change worktree，该闸门在 VM 上没有可触发的输入 |
| AC-4 两台 `host.access.audit` 均 `PASS`，既有 typed 操作无回归 | **PASS** | Mac 与 VM 重装后 `host.access.audit` 均 `"status": "PASS"`，两边载荷一致且与 Mac 重装前基线（D 段）逐字段相同。Mac 另抽样 7 个既有 typed 操作全部正常 |

## 遗留风险与未完成项

- **VM 侧的读回由人代跑**：没有任何 typed 操作能读 VM 上的文件内容，`orb` 裸 shell 在 broker 契约
  之外，所以 VM 的 `grep` / `ls` / `host.access.audit` 三条由人在 VM 内执行、输出原样抄录在 G 段。
  这是能力边界，不是本次遗漏。
- **VM 侧 `host.access.audit` 没有重装前基线**：本会话在重装之前只跑了 Mac 侧 audit。VM 那条
  重装后为 `PASS` 且与 Mac 载荷一致，可以证明「重装后正常」，但严格说不能证明「重装没有改变它」。
  下次同型运维应在重装前先取两台基线。
- **没有任何机制会主动报告「已合并但未安装」**：本 Issue 的整个存在就是人事后发现的。
  drift 检测需要独立验收标准，按 `issue-session-flow` 的判据属于新 Issue，收尾时开。
- 回滚方式：installer 为每个被覆盖文件留 `.previous` 备份；回滚是复原 `.previous`，
  或从上一个 commit 重跑 installer。仓库侧回滚是 revert 本 PR（纯文档）。
