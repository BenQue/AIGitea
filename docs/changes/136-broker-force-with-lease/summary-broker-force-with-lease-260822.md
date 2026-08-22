---
issue: 136
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/136
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - agent-governance
  - shared-core
depends_on: []
status: analyzed
branch: change/136-broker-force-with-lease
pr_url:
created: 2026-08-22
updated: 2026-08-22
reason: 修改 host-access broker 的 Git 写路径推送语义，属治理写路径核心行为变更，且需要重装 installed broker 才生效
required_docs:
  - summary
  - spec
  - plan
  - verification
override_reason: ''
documents:
  summary: summary-broker-force-with-lease-260822.md
  spec: spec-broker-force-with-lease-260822.md
  plan: plan-broker-force-with-lease-260822.md
  verification: verification-broker-force-with-lease-260822.md
---

## 问题/需求总结

`git.push.change` 的三条约束互相锁死，使**任何已推送的 change 分支在 `main` 前进后永久无法再推送**。
`codex/runtime/aisoft_host_access/broker.py` 的推送路径同时要求：

| 约束 | 检查 | 失败码 |
|---|---|---|
| 基线新鲜 | `git merge-base --is-ancestor origin/main HEAD` | `BASE_BRANCH_STALE` |
| 线性历史 | `git rev-list --min-parents=2 origin/main..HEAD` 为空 | `MERGE_COMMIT_DENIED` |
| 实际推送 | 裸 `git push remote refs/heads/X:refs/heads/X` | —— |

`main` 前进后，第一条要求 rebase；rebase 重写 commit 对象使推送变成 non-fast-forward，
第三条的裸 push 执行不了；改用 merge 引入 `main` 又被第二条拒绝。三条互锁，没有出路。

唯一出路是人工到 Gitea UI 删除远端分支——broker 的 typed 操作清单里没有 branch delete，
而绕过 broker 直接 `git push --delete` 是治理禁止的。

## 影响范围

- `codex/runtime/aisoft_host_access/broker.py` 的 `git.push.change` 执行路径与 `ls-remote` 解析。
- `codex/runtime/tests/test_host_access.py` 中断言推送 argv 形状的既有用例。
- 所有接入 broker 的项目（aisoft-platform、LocalWMS、NewEMaint 等）的 change 分支再推送能力。
- installed broker（Mac 与 gitea-ci VM 的 `/usr/local/libexec/aisoft/host-access-broker`）——source 合并不等于生效。

触发条件是「分支已推送 + `main` 前进 + 分支还需再推」。单条 Issue 串行推进时几乎碰不到；
**并行 Issue 一多就成为常态**——任一 PR 合并都会让其余在途分支进入该状态。
现象还具有误导性：使用者看到的是 `HOST_COMMAND_FAILED: structured host operation failed`，
既不提 non-fast-forward，也不提 rebase。

## 初步方案与建议

`git.push.change` 改用 `--force-with-lease=refs/heads/<branch>:<remote-sha>`，
`<remote-sha>` 取自推送前已经执行的 `git ls-remote --heads`（`_remote_change_names`
本来就在读这份数据用于 change name 唯一性判定，只是丢掉了 sha）。

远端分支不存在时使用**空 expectation**（`refs/heads/<branch>:`），git 的语义是
「该 ref 必须仍不存在」：首推正常创建，而若在读取与推送之间被别人抢先创建则拒绝。
这比「不存在就省略 lease」更强——后者在首推竞态下会退化成无保护的裸 push。

推送被 lease 拒绝时返回新的可辨识错误码 `REMOTE_BRANCH_MOVED`，取代无信息量的
`HOST_COMMAND_FAILED`。

## 风险

- **force 的作用面**：由治理合同已有的两层夹住——`change_branch()` 已把可推送 refspec
  限定为 `change/*`，且 `main` 的 branch protection 有 `enable_force_push: false`
  并由 `host.access.audit` 持续核对。force 够不到 `main`。
- **并发写同一分支**：change 分支与 Issue 一一绑定，`select_change_name` 强制唯一，
  正常路径下单写者。异常路径由 lease 本身兜住——远端被动过就拒绝而非覆盖。
- **误吞真实故障**：lease 命中时 force 必定成功，所以推送失败中出现 `stale info`
  只可能是租约不符，不会与凭据、网络故障混淆。
- **生效滞后**：合并 source 不改变 installed broker 的字节。两台主机重装前，
  本问题依然存在——包括本变更自己的分支。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 修改 host-access broker 的 Git 写路径推送语义，属治理写路径核心行为变更，且需要重装 installed broker 才生效
risk_flags:
  - platform-governance
  - agent-governance
  - shared-core
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- `change_type: platform` 属 `FORCED_COMPLEX_TYPES`，`platform-governance`、
  `agent-governance`、`shared-core` 三项均属 `FORCED_COMPLEX_RISKS`：强制 complex，无 small 候选空间。
- `aisoft-platform` 在 `codex/config/gitea-governance.json` 未声明 `change_control`，
  按 Issue #134 的默认按 `production` 处理，`spec`/`plan` 不可省。
- 变更引入新推送语义与新错误码 `REMOTE_BRANCH_MOVED`，不是纯粹恢复既有行为，
  故 `contract_effect: change` 而非 `restore`。
- 变更只有在两台主机重装 installed broker 后才生效，具备部署影响，因此追加 `verification`，
  终态为 `deployed` 而非 `completed`。

### 缺失的 acceptance criteria 或决策

- 无。Issue #136 正文已给出六条可测验收标准与精确的行号定位。
