---
issue: 162
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/162
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - platform-governance
depends_on: []
status: approved
branch: change/162-installer-staleness-gate
pr_url:
created: 2026-08-24
updated: 2026-08-24
reason: 给 broker installer 增加一条 fail-closed 前置闸门并改变其成功输出契约；installer 是平台治理组件的安装面，属平台/部署脚本变更，强制 complex
required_docs:
  - summary
  - spec
  - plan
override_reason: ''
documents:
  summary: summary-installer-staleness-gate-260824.md
  spec: spec-installer-staleness-gate-260824.md
  plan: plan-installer-staleness-gate-260824.md
---

## 问题/需求总结

`codex/install-host-access-broker.sh` 在**陈旧 checkout** 上安装旧内容，并且成功输出与
装对了完全一样。

2026-08-23 实测（#161 合并后，两台同时踩中）：

| 位置 | 执行 | 输出 | 实际装入 |
|---|---|---|---|
| Mac | `sudo bash codex/install-host-access-broker.sh` | `installed host-access-broker/v1 candidate` | 29 操作（旧） |
| gitea-ci VM | 同一脚本，经 `/mnt/mac/` | `installed host-access-broker/v1 candidate` | 29 操作（旧） |

根因不在 installer 的比对逻辑，而在**它比对的是哪两个东西**：

- `install_versioned()` 用 `cmp -s "$source" "$target"` 比较 **checkout 里的文件** 与
  **已安装的文件**。这个比对本身是对的，`CHANGED=1` / `already current (no-op)` 也都是真的。
- 但操作人问的是另一个问题：「我装的是不是**已合并的合同**」。当 checkout 的本地 `main`
  落后 `origin/main` 3 个 commit（PR #161 已合并、checkout 未 fast-forward）时，
  installer 忠实地装了 checkout 里那份 29 操作 manifest，并如实报告「装了」。
- 两个问句的答案在正常情况下重合，所以偏差不可见。**幂等证据在这里是假阳性**：
  `already current (no-op)` 证明 `installed == checkout`，不证明 `installed == merged`。

VM 经 `/mnt/mac/Users/benque/MyDocs/AISoftPlatform` 挂载的是**同一份 checkout**，
所以「两台都装」这个既有防线（`06` 踩坑 18/20 的对策）对这一种失败形态完全无效——
两台读同一个陈旧源，一起装错。

下游症状极具误导性：新 typed 操作返回
`{"code": "REQUEST_DENIED", "message": "requested operation is not allowlisted"}`，
读起来像身份或 ACL 问题。`06` 踩坑 20 已经覆盖「忘记重装」，但没有覆盖
「**装了、装的是旧的**」——后者更难认，因为人明明执行过，且拿到了成功输出。

本次运行现场即是活证据：本仓库 `codex/config/host-access-broker.json` 是 30 操作，
而本机 `/usr/local/share/aisoft/host-access-broker.json` 仍是 29，
缺的正是 #160 新增的 `gitea.issue.labels.classify`。

## 影响范围

改动（新增闸门与输出，不改既有安装语义）：

1. `codex/install-host-access-broker.sh` —— 安装前新增 **source provenance 输出**
   （AC-1）与 **staleness fail-closed 闸门**（AC-2）。闸门位于任何 `install_versioned`
   调用之前，拒绝时不产生任何文件系统变更。
2. `codex/tests/test-install-host-access-broker.sh` —— 新增（AC-3）。用本地 bare 仓库
   构造 behind / level / no-remote / detached / non-git 五种源状态，全部离线。
3. `codex/tests/smoke.sh` —— 注册新测试的 `bash -n`、`shellcheck` 与执行（AC-4）。
4. `06-运维手册与踩坑集.md` —— 踩坑 20 补记这一种失败形态与判别方法（AC-5）。

**不改动**：broker 的操作表与任何 typed 操作（`contract.py`、`broker.py`、`runner.py`、
`codex/config/host-access-broker.json`）、`install-vm.sh` / `install-host-role.sh` /
`architecture/install.sh` / `docker-release/install.sh` 等其它 installer、
`AGENTS.md`、CI workflow、部署脚本、凭据与 profile 绑定面。

## 初步方案与建议

**闸门比对的是本地已有的 remote-tracking ref，不联网。** 依据：

- installer 以 `sudo` 运行。让它发起网络 I/O 会新增一条以 root 身份触达远端的路径，
  而平台合同规定 remote 访问只走 broker typed 操作（`git.fetch.main` / `git.fetch.change`）。
- 实测失败形态正是「已 fetch、未 fast-forward」：`origin/main` 在本地已经是新的，
  只有工作分支落后。`git rev-list --count HEAD..@{upstream}` 不需要任何网络就能测出它。
- 因此闸门能回答的是「checkout 是否落后于**它自己看到的**远端」。
  「remote-tracking ref 本身陈旧」（从未 fetch）不在闸门覆盖范围内——
  这一层由 AC-1 的 commit 输出兜底：操作人拿到 commit SHA，可与已合并的 PR 对照。
  spec §4 把这条边界写成显式非目标，而不是留作隐含假设。

**三种「测不出来」必须降级为警告而不是拒绝**（AC-2 明确要求）：无 remote/upstream、
detached HEAD、upstream ref 本地不可解析。理由是闸门必须能区分「落后」与「无从判断」；
两者都拒绝会让 tarball 安装、CI 沙箱和裸 checkout 全部装不上，
把一条安全网变成一条硬依赖。非 git 目录与 `git` 不可用同理走警告路径。

**不提供绕过开关。** 与平台既有姿态一致（`AGENTS.md`：调用方不能用 `legacy` 开关绕过
evidence-derived compatibility；#160 对已关闭 Issue 同样不提供 override）。
补救动作是一条命令 `git merge --ff-only <upstream>`，代价远低于一个能让本闸门静默失效的开关。

**AC-1 的输出必须在 no-op 路径上也打印。** Issue 正文点名 `already current (no-op)`
是假阳性来源；如果 provenance 只在 `CHANGED=1` 时打印，第二次运行就又回到不可读状态。
因此 provenance 在安装动作之前无条件打印。

`required_docs` 取 `[summary, spec, plan]`，不含 `verification`：本变更改的是安装脚本的
前置校验，不是应用部署链路，没有「两次幂等 + 一次故意失败回滚」的部署验收对象。
这与最接近的先例 #160（同为「治理工具 + 测试 + 文档」）一致。
反例是 #138——它声明了 `verification`，于是 `mark-completed-issues.sh` 跳过它，
而没有部署链路去写 `deployed`，至今一个标签都没有。

## 风险

- **误报挡住合法安装**：工作分支跟踪 `origin/main` 时，`main` 前进就会让该分支「落后」。
  从本闸门的目的看这不是误报——checkout 确实缺少已合并的 commit，装出去的可能就是旧合同。
  缓解：拒绝消息同时给出 `merge --ff-only` 与 `rebase` 两条补救，并打印 upstream 名字与落后数，
  让操作人一眼看出该走哪条。
- **首次运行的输出契约变化**：既有调用方（`06` §1.0 自检、#18/#20 的对策步骤）只 grep
  `installed`/`no-op` 两行。缓解：这两行原样保留、位置不变，provenance 是**前置新增行**，
  不改既有行文本。
- **闸门覆盖不到「从未 fetch 的 checkout」**：见「初步方案」。缓解：AC-1 的 commit 输出 +
  `06` 踩坑 20 的判别方法补记，把这一层交给可读证据而不是假装闸门覆盖了它。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 给 broker installer 增加一条 fail-closed 前置闸门并改变其成功输出契约；installer 是平台治理组件的安装面，属平台/部署脚本变更，强制 complex
risk_flags:
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
confidence: high
override_reason: ''
```

### 判级证据

- `AGENTS.md`：「CI/制品/部署/回滚，以及 Agent 或平台治理变更一律按 complex 处理」——
  `install-host-access-broker.sh` 是 host-access broker 的**安装面**，是平台所有 typed
  能力上线的必经路径。
- `03` §9 行 87：「改变平台行为或治理合同的 `type/platform` 强制 complex」——
  本变更让 installer 新增一条会**非零退出**的路径，改变了它对调用方的外部行为。
- `contract_effect: add`：staleness 闸门与 provenance 输出都不存在，是新增的外部可观察契约，
  不是恢复既有行为。因此不满足 small 的 `restore`/`unchanged` 前提。
- 触及 `AGENTS.md` 点名需 spec 显式授权的「CI/部署脚本」类文件，授权见 spec §5。

### 缺失的 acceptance criteria 或决策

- 无。Issue 正文 AC-1..AC-5 完整且可测。AC-2 未指定「落后」的比较基准与是否允许绕过，
  由 spec §2 固定为 `@{upstream}` 且不提供绕过开关，理由见「初步方案与建议」。
