---
issue: 171
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/171
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - platform-governance
depends_on: []
status: pr-open
branch: change/171-installer-source-guard
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/185
created: 2026-08-24
updated: 2026-08-24
reason: 把 #162 的 fail-closed 前置闸门与 provenance 输出抽成共用库，并接到另外四个 installer 上（第五个 docker-release/install.sh 被 #65 evidence gate 挡住，切出 #182）；installer 是平台组件的安装面，属平台/部署脚本变更，强制 complex
required_docs:
  - summary
  - spec
  - plan
override_reason: ''
documents:
  summary: summary-installer-source-guard-260824.md
  spec: spec-installer-source-guard-260824.md
  plan: plan-installer-source-guard-260824.md
---

## 问题/需求总结

#162（PR #165，合并为 `c58ba1b`）只修了 `codex/install-host-access-broker.sh` 一个。
它的正文把其它 installer 显式排除，并写明「若同因，另开 Issue」。收尾核对确认**同因**，
本 Issue 就是那条另开。

实测（2026-08-24，`main` `208b2bf`；本次运行在 `5faffa7` 上复核，结论不变）：

| 脚本 | 取源 | `grep -c 'rev-list --count'` | staleness 闸门 |
|---|---|---|---|
| `codex/install-vm.sh` | `$ROOT`（源 checkout） | 0 | 无 |
| `codex/install-host-role.sh` | `$ROOT` | 0 | 无 |
| `codex/install-skills.sh` | `$root` | 0 | 无 |
| `architecture/install.sh` | `$ROOT` | 0 | 无 |
| `docker-release/install.sh` | `$repo_root` | 0 | 无 |

失败形态与 #162 完全同构：checkout 的本地分支落后 remote 时，installer 忠实地装了那份
旧内容并如实报成功，**成功输出对「装了新的」与「装了旧的」完全一样**。
二次运行的幂等输出证明的是 `installed == checkout`，不是 `installed == 已合并的合同`。

放大因素同样存在：gitea-ci VM 经 `/mnt/mac/` 挂载的是**同一份 checkout**，
所以「Mac 与 VM 两台都装」这条既有防线对这一种失败形态无效，两台一起装错
（`06` 踩坑 18 是「只装一台」，踩坑 20 是「装了、装的是旧的」）。

**比 #162 更难归因**：broker 那次至少有 `REQUEST_DENIED` 这一个统一信号，
这五条没有。下游症状按 installer 各不相同——host-role guard 用旧 capability 表、
architecture lock 用旧 schema、docker-release 用旧 capability gate、skills 装旧版本、
loop runtime 用旧模块——每一种都指向别处，不指向「源陈旧」。

## 影响范围

改动（新增前置闸门与输出，不改任何安装内容、目标路径与幂等语义）：

1. `codex/lib/install-source-guard.sh` —— **新增**。把 #162 落在
   `install-host-access-broker.sh` 里的实现抽成共用 sourceable 库（AC-3）。
2. `codex/install-host-access-broker.sh` —— 用共用库替换内联实现。
   **外部行为逐字节不变**（AC-3 的硬约束）。
3. `codex/install-vm.sh`、`codex/install-host-role.sh`、`codex/install-skills.sh`、
   `architecture/install.sh` —— 各调用一次共用库，在第一次文件系统写入之前（AC-1、AC-2）。
4. `codex/tests/test-installer-source-guard.sh` —— 新增（AC-4）。一份离线构造的
   checkout，按 level → behind → no-remote 三段改写其 git 状态，每段跑全部**五个**
   接入的 installer。
5. `codex/tests/smoke.sh` —— 注册新库与新测试的 `bash -n`、`shellcheck` 与执行（AC-5）。
6. `06-运维手册与踩坑集.md` 踩坑 20 —— 覆盖范围从 broker installer 扩到全部 installer（AC-6）。

**不改动**：各 installer 的安装内容、目标路径与幂等语义；broker 的操作表与任何 typed
操作；`sync/install.sh`（取源方式不同，Issue 正文列为范围外）；`AGENTS.md`；
CI workflow；部署脚本；凭据与 profile 绑定面。

**切出**：`docker-release/install.sh`。实现已完成并验证过，但
`codex/tests/integration/test-docker-release-v2-lifecycle-e2e.sh:455` 把 `docker-release/`
相对 Issue #65 delivery base `7ef7fa2` 的 diff **钉死为两个文件**
（`README.md` 与 `compatibility/image-stores-v1.json`）；接上闸门后 `install.sh` 成为第三个，
`smoke.sh` 红在 `FAIL: docker-release differs outside the Issue #65 evidence-gated scope`。
那是一条刻意的 name-only 语法闸门，正因为它是语法的，「我这个改动无害」不构成通过理由；
扩它的 allowlist 落在 **#65 的授权边界**内，本 spec §5 没有授权。
因此该 installer 切给 **#182**，连同「怎么处理 #65 的 pin」一起决定。

## 初步方案与建议

**共用库而不是五份副本（AC-3 的核心）。** #162 的实现里只有两处是 installer 特定的：
WARNING/ERROR 前缀里的 **installer 名字**，和那条「装的是哪一版」的**可读量**
（broker 是 `source operations: 30`）。其余——git 探测、四种降级、输出格式、拒绝消息与
补救命令——逐字相同。因此库的接口就是这两个参数：

```
aisoft_install_source_guard <installer-name> <source-root> [<label> <value>]...
```

`<label> <value>` 成对可变长，让每个 installer 自己决定打印哪些可读量；
库不认识任何一个 installer 的数据文件，也不引入 `jq`/`python3` 的硬依赖
（取值失败一律降级为 `unknown`，与 #162 同）。

**输出格式必须逐字节保持。** #162 的三行值全部对齐到第 20 列
（`source checkout:` 后 3 空格、`source commit:` 后 5 空格、`source operations:` 后 1 空格）。
库用 `printf 'source %-11s %s\n' "<label>:" "<value>"` 复现同一对齐，因此
`test-install-host-access-broker.sh` 里 `^source commit:     [0-9a-f]+ \(` 这类断言
（含精确空格数）无需改动即继续通过。这是 AC-3「不得改变已通过 #162 验收的外部行为」的
可验证形式。

**每个 installer 的可读量按它自己的下游症状选**，而不是随便挑一个数：

| installer | 可读量 | 对应的下游症状 |
|---|---|---|
| `install-host-access-broker.sh` | `operations`（不变） | typed 操作 `REQUEST_DENIED` |
| `install-vm.sh` | `runtime modules` + `operations` | loop runtime 旧模块；它也装同一份 broker manifest |
| `install-host-role.sh` | `capabilities` | host-role guard 用旧 capability 表 |
| `install-skills.sh` | `skills` + `matt snapshot` | 装旧版本 skills |
| `architecture/install.sh` | `catalog revision` + `components` | architecture lock 用旧 catalog/schema |
| ~~`docker-release/install.sh`~~ | ~~`matrix revision` + `schemas`~~ | 旧 capability gate——切出 **#182**，见上「切出」 |

**测试用一份 checkout、三段 git 状态、五个 installer**，而不是多份 #162 测试的副本。
理由与 AC-3 同源：六份近似测试同样会漂移。构造顺序是 level → 让 remote 前进后
`reset --hard HEAD~1` 得到 behind → 拆掉 upstream 与 remote 得到 no-remote；
每段每个 installer 用独立的安装根，互不污染。全程离线（本地 `git init --bare` 当 remote）。

`required_docs` 取 `[summary, spec, plan]`，不含 `verification`：AC-1..AC-6 的验收证据
全部能由 diff review 与 required CI（`smoke.sh` 执行新测试）复现，没有只能在真实环境
执行或只能一次性观测到的证据（`03` §3 判据）。与最接近的先例 #162 一致。

## 风险

- **误报挡住合法安装**：与 #162 同一条风险，现在扩到五个脚本，触发面更大。
  缓解不变——拒绝消息给出 `merge --ff-only` 与 `rebase` 两条补救、打印 upstream 名字与
  落后数；四种「测不出来」（无 upstream、detached HEAD、ref 不可解析、非 git 目录）
  一律降级为警告。CI 与 tarball 场景多为 detached HEAD 或非 git，落在警告路径。
- **`smoke.sh` 的既有 installer 测试从真实 checkout 安装**
  （`test-install-skills.sh`、`test-install-host-role.sh`、`test-architecture-install.sh`、
  `test-docker-release-install.sh` 都跑 `bash "$ROOT/<installer>"`）。加闸门后，
  在**落后 upstream 的 checkout** 上跑 smoke 会红。这是有意的：此时安装出去的确实可能是
  旧合同。detached HEAD（CI、`git bisect`）与无 upstream（新建 change 分支）都走警告路径，
  不受影响。**不提供绕过开关**——与 #162 及 `AGENTS.md`「不得用开关绕过 evidence-derived
  compatibility」的姿态一致。
- **`install-vm.sh` 会打印两段 provenance**（它内部调用 `install-skills.sh`，后者也带闸门）。
  两段各自标注 installer 名字与各自的可读量，是真实信息而非重复噪声；
  behind 时 `install-vm.sh` 自己的闸门先拒，不会走到第二段。
- **跨目录依赖**：`architecture/install.sh` 需 source `codex/lib/`。它本来就已从
  `codex/runtime/aisoft_architecture/` 取安装源，不新增耦合方向。
- **覆盖面留了一个显式缺口**：`docker-release/install.sh` 仍无闸门，直到 #182 落地。
  缺口写在 `test-installer-source-guard.sh` 的 `INSTALLERS` 数组注释里——为什么不在列表、
  去了哪个 Issue——而不是静默少一项。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 把 #162 的 fail-closed 前置闸门与 provenance 输出抽成共用库，并接到另外四个 installer 上（第五个 docker-release/install.sh 被 #65 evidence gate 挡住，切出 #182）；installer 是平台组件的安装面，属平台/部署脚本变更，强制 complex
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
  这些脚本都是平台组件的**安装面**（host-access broker、loop runtime、skills、
  host-role guard、architecture 校验器）。
- `03` §9：改变平台行为或治理合同的 `type/platform` 强制 complex——本变更让四个
  installer 各新增一条会**非零退出**的路径，改变了它们对调用方的外部行为。
- `contract_effect: add`：闸门与 provenance 输出都不存在，是新增的外部可观察契约，
  不是恢复既有行为，因此不满足 small 的 `restore`/`unchanged` 前提。
- 触及 `AGENTS.md` 点名需 spec 显式授权的「CI/部署脚本」类文件，授权见 spec §5。
- 先例：同因同形的 #162 判为 complex（`docs/changes/162-installer-staleness-gate/`）。

### 缺失的 acceptance criteria 或决策

- 无。Issue 正文 AC-1..AC-6 完整且可测。AC-3 未指定共用实现的**形态**
  （库 / 函数 / 生成器），由 spec §2.1 固定为一份 sourceable shell 库；
  AC-1 未指定各 installer 的可读量取哪一个，由 spec §2.3 逐个钉死。
- 实现中发现 Issue 正文假定五个 installer 都可改，而 `docker-release/` 实际被 #65 的
  evidence gate 锁住。这不是 acceptance criteria 缺失，是**范围与另一条授权边界相撞**；
  处置由人决定（切出 #182），记录在「影响范围 · 切出」与 spec §4。
