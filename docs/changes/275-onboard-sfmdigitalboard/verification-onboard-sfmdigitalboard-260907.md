---
issue: 275
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/275
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - agent-governance
  - security
  - shared-core
depends_on: []
status: contract-drafting
branch: change/275-onboard-sfmdigitalboard
created: 2026-09-07
updated: 2026-09-07
---

# Verification 重新接入 SFMDigitalBoard

实现 commit：`7741336`。基线：`origin/main` = `a2dc131`。

## Acceptance criteria 结果

| AC | 结果 | 证据 |
|---|---|---|
| AC-1 | PASS | `projects[]` = `[aisoft-platform, localwms, myapp, newemaint, sfm-digital-board, smoke-test]`；`repositories[]` = `[aisoft-platform, LocalWMS, myapp, NewEMaint, SFMDigitalBoard, smoke-test]`；rsdesign/hsdb/wmpda/saptable 四个字符串在两份 manifest 中均不出现 |
| AC-2 | PASS | `validate` → `{"status":"PASS","project_count":6,"operation_count":36,"merge_operation_count":1}` |
| AC-3 | PASS | 见下节「封印重算」 |
| AC-4 | PASS | `git diff --stat origin/main -- codex/runtime/aisoft_host_access/contract.py codex/runtime/aisoft_gitea_governance/contract.py` 输出为空 |
| AC-5 | PASS | `bash codex/tests/smoke.sh` → `EXIT=0`，收尾行 `Codex platform static smoke checks passed.` |
| AC-6 | PASS | `git diff origin/main -- codex/tests/smoke.sh` 输出为空 |
| AC-7 | PASS | 见下节「回滚演练」 |
| AC-8 | PASS | 人工交接项清单见下节，未执行项全部 NOT RUN |
| AC-9 | NOT RUN | 需要人工重装，不由源码推断 |
| AC-10 | NOT RUN | PR 尚未创建 |

## 封印重算（AC-3）

算式（与 #252 同款，取自 `aisoft_gitea_governance/contract.py:71`）：

```python
repository_declarations_sha256(repositories, exclude_name='NewEMaint')
# json.dumps(..., ensure_ascii=False, sort_keys=True, separators=(",",":")) 的 sha256
```

| | 取值 |
|---|---|
| 旧值（#252 pin） | `d64ccb588cecb6219b7d1b8c43caa13857ce4aaee42063045c53e052c69426c2` |
| 新值（本 commit 现算） | `4969422f72782de90155881cc4a92720dfd1ee5f468e940bd30ac7a666b0df85` |

落盘后回读自校验通过（重新读文件现算 == 文件中记录值）。保留仓库的声明内容未被
调整——本次 `repositories[]` 的唯一变化是新增一条 SFMDigitalBoard。

## 回滚演练（AC-7）

```
改后树           validate → project_count: 6
git revert --no-commit HEAD → project_count: 5
git revert --abort          → project_count: 6，工作树 0 个改动
```

## 实测发现：五处花名册耦合断言

Issue 正文与 spec 起草时只预见了 `project_count` 一处。实跑 `smoke.sh` 后逐一显形：

| # | 位置 | 原取值 | 处理 |
|---|---|---|---|
| 1 | `codex/tests/test-host-access-broker.sh` jq | 除 `newemaint` 外任何项目不得 `has("git_remote_name")` | 改写为「声明该键的项目 == `[newemaint, sfm-digital-board]` 且取值全为 `gitea`」 |
| 2 | `codex/tests/test-host-access-broker.sh` jq | `.project_count == 5` | → 6 |
| 3 | `codex/runtime/tests/test_host_access.py:86` | `len(projects) == 5` | → 6 |
| 4 | `codex/runtime/tests/test_host_access.py:107` | `gitea_remote_projects = {"newemaint"}` | 加 `sfm-digital-board` |
| 5 | `codex/runtime/tests/test_gitea_governance.py:189,198` | `len(repositories) == 5`；private == `{LocalWMS, NewEMaint}` | → 6；加 `SFMDigitalBoard` |

第 1 项是唯一有语义风险的一处：**删掉 SFM 的 `git_remote_name` 也能让测试变绿**，
但 SFM checkout 的 `origin` 指向 `https://github.com/BenQue/SFMDigitalBoard.git`，
删键后 broker 会按默认 `origin` 把 change 分支推到 GitHub。故改断言而非改数据，
且新写法把「只有一个项目可以有非默认 remote」升级为「有非默认 remote 的项目
精确列举 + 取值必须是 gitea」——强度提高。

第 3/4/5 项不在 Issue §治理文件修改授权 的逐条清单内，属 AC-5「smoke 全绿」的
机械后果，未改变任何断言语义强度，如实记录于此。

### 定位手法（值得复用）

`jq -e` 与 `grep -Fq` 失败时**不打印任何内容**，`smoke.sh` 因此静默 exit 1。
定位靠两步：① 在干净 `origin/main` 上跑同一套取基线（exit 0 / 944 行）；
② 比对两次输出，改后树的 30 行恰是基线的前 30 行，第 31 行即失败点。
「输出量差一个数量级」比退出码更早提示问题所在。

## 对 #252 交接清单的事实修正

#252 verification 把 H-1/H-2/H-3/H-6 标为 `NOT RUN`，但 2026-09-07 实测：

| #252 项 | 实测 |
|---|---|
| H-1 停用 `aisoft-agent@sfm.timer` | 已执行（VM 上 `systemctl list-timers 'aisoft-agent@*'` 返回 0 timers）|
| H-2 删除三份 VM profile env 与 token | 已执行（`/home/coder/.config/aisoft/projects/` 只剩 aisoft-platform / emaintenance / localwms）|
| H-3 两台重装 | Mac 侧已执行（`/usr/local/share/aisoft/host-access-broker.json` 的 `projects[]` 为退出后的五条）|
| H-6 停用 Gitea 账号 | 已执行（`sfm-board-agent` `prohibit_login: true`，仍是 collaborator）|

即那些动作已完成，只是文档停在 PR 时刻未回写。

## 人工交接项（PR 合并后，需 sudo 或无 typed 操作）

**顺序与 #252 的退出顺序相反**：退出是「先清理后重装」，接入是「先重装拿回通道
再补凭据」。

| 编号 | 动作 | 状态 |
|---|---|---|
| H-1 | Mac 重装 broker 与 host-role。**重装前先 `git -C <checkout> status -sb` 确认无 `behind`** | NOT RUN |
| H-2 | Gitea 解除 `sfm-board-agent` `prohibit_login`，重发 token（`write:issue,write:repository,read:user`），确认 collaborator 为 write | NOT RUN |
| H-3 | token 落到 Mac 凭据根 `projects/sfm-digital-board/project-agent.token`，mode 600 | NOT RUN |
| H-4 | `mac.git.bind` 后 `host.onboarding.check` 回读（对应 AC-9） | NOT RUN |

H-1 的前置检查不是形式：2026-09-07 起草本变更时实测该 checkout 落后 `origin/main`
13 个 commit（#270/#271），经 diff 确认未触及治理文件后已 ff 同步。installer 从
checkout 取源，落后时会忠实装旧内容并报成功（06 踩坑 20 变体）。

H-4 补充：SFM checkout `.git/config` 中退出前 `mac.git.bind` 写入的三行已于
2026-09-07 由 SFM 侧会话移除以恢复 keychain fetch。**不必手工补回**，
`mac.git.bind` 会重写，`host.onboarding.check` 对 repo-local helper drift fail-closed。

`sfm-board-routine-merger` 保持停用，本次不恢复。

## #112 处置翻转（须记录）

#252 的 H-7 曾要求「关闭 SFMDigitalBoard #112」，理由是该仓已出平台范围。本次接入
后该理由消失，**#112 应保留并执行**。

另：#112 正文的「缺口②（`block_on_outdated_branch`）由人在 Gitea 界面打开」已过期
——2026-09-07 实测 `admin/SFMDigitalBoard` 的 `main` 分支保护该项已为 `true`。
