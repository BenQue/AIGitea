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
status: approved
branch: change/171-installer-source-guard
created: 2026-08-24
updated: 2026-08-24
---

# Spec · installer source guard（#171）

## 1. 目标与原因

让每一个**可改的** installer 的成功输出足以回答「我刚才装进去的是什么」，并在源
checkout 落后于它自己的远端时拒绝安装，而不是安装旧内容后报成功。
`docker-release/install.sh` 是唯一的例外，原因与去向见 §4。

原因见 summary：#162 已经在 broker installer 上确认了这条失败形态，并在正文里预留了
「若同因，另开 Issue」；收尾核对确认其余五个 installer 同因。它们比 broker 那次**更难
归因**，因为没有 `REQUEST_DENIED` 这种统一信号，下游症状按 installer 各不相同。

同时，五份复制粘贴的实现本身就是下一个缺陷（AC-3），所以本次一并把 #162 的实现抽成
共用库。

## 2. 行为契约

### 2.1 共用实现（AC-3）

新增 `codex/lib/install-source-guard.sh`：一份 **sourceable** shell 库，只定义函数，
**自身不安装任何东西、不执行任何动作**。

公开接口：

```
aisoft_install_source_guard <installer-name> <source-root> [<label> <value>]...
```

- `<installer-name>`：出现在 WARNING/ERROR 前缀里的可读名字（如 `install-vm`）。
- `<source-root>`：被探测 git 状态、并被打印为 `source checkout:` 的绝对路径。
- `<label> <value>`：成对、可变长、可为空。每对打印一行 `source <label>: <value>`。
  库**不认识**任何 installer 的数据文件；取值由调用方负责。

附带的取值辅助函数（失败一律得 `unknown`，绝不致命）：

| 函数 | 用途 |
|---|---|
| `aisoft_install_source_json_count <file> <key>` | `len(json[key])` |
| `aisoft_install_source_json_value <file> <key>` | `str(json[key])` |
| `aisoft_install_source_file_count <path>...` | 参数中实际存在的常规文件数（供 glob 展开） |

前两个用 `python3`，与 #162 相同且**不引入 `jq` 等新的安装期依赖**；
`python3` 不可用或文件不可读时得 `unknown`，不影响安装。

接入的 installer 一律 `source` 这一份库，不得复制其中任何一段逻辑。

### 2.2 Source provenance（第一次文件系统写入之前，无条件输出）

向 stdout 打印，至少两行，之后是调用方给的每一对：

```
source checkout:   <source-root 的绝对路径>
source commit:     <short SHA> (<sync 状态短语>)
source <label>:    <value>
```

约束：

- **无条件**——变更路径与 no-op / 幂等路径都打印。`no-op` 是 #162 点名的假阳性来源。
- 取不到的字段打印 `unknown`，各字段独立降级，不因此失败。
- 每个 installer 既有的结果行与边界声明行（如 `installed ... candidate`、
  `no credential, ... was performed`）**文本与相对位置不变**，provenance 是前置新增行。
- 对齐固定为 `printf 'source %-11s %s\n'`，即所有值起于第 20 列（label 超过 11 字符时
  退化为单空格分隔）。这一条是为了让 #162 已验收的三行输出**逐字节不变**。

### 2.3 各 installer 的可读量（AC-1）

| installer | 打印的 `<label>: <value>` | 取自 |
|---|---|---|
| `codex/install-host-access-broker.sh` | `operations: N` | `codex/config/host-access-broker.json` 的 `.operations` 长度 |
| `codex/install-vm.sh` | `runtime modules: N`、`operations: N` | 三个 runtime 包的 `*.py` 加 `aisoft_change_name.py`；同上 manifest |
| `codex/install-host-role.sh` | `capabilities: N` | `codex/config/host-capabilities.json` 的 `.capabilities` 长度 |
| `codex/install-skills.sh` | `skills: N`、`matt snapshot: vX.Y.Z` | `codex/skills/*/` 目录数加 `skill-for-codex`；脚本内的 `matt_version` |
| `architecture/install.sh` | `catalog revision: R`、`components: N` | `architecture/catalog.json` 的 `.revision` 与 `.components` 长度 |
| ~~`docker-release/install.sh`~~ | ~~`matrix revision: R`、`schemas: N`~~ | 切出 #182，见 §4 |

broker 那一行与 #162 完全一致，不新增也不改名。

### 2.4 Staleness 闸门（AC-2）

比较基准固定为**当前分支的 upstream**（`@{upstream}`），落后数为
`git -C <source-root> rev-list --count HEAD..<upstream>`。

| 源状态 | 行为 |
|---|---|
| 落后 N ≥ 1 个 commit | **fail-closed**：非零退出，stderr 说明落后 N 个 commit 与补救命令，**不安装任何文件** |
| 齐平或领先 | 正常安装 |
| 当前分支无 upstream / 无 remote | 警告后安装 |
| detached HEAD | 警告后安装 |
| upstream ref 本地不可解析（离线、ref 未取回） | 警告后安装 |
| `<source-root>` 不是 git 工作区，或 `git` 不可用 | 警告后安装 |

- 拒绝必须发生在**第一次文件系统写入之前**：`install -d` 也算写入，因此闸门位于目录
  创建之前。`architecture/install.sh` 的 `--prefix` 参数校验（`exit 2`）保持在闸门之前，
  因为它不是写入。
- 警告写 stderr，前缀 `WARNING: <installer-name>:`，不影响退出码。
- 拒绝写 stderr，前缀 `ERROR: <installer-name>:`，退出码非零。
- **不提供绕过开关**（无环境变量、无 `--force`）。补救是
  `git merge --ff-only <upstream>` 或 `git rebase <upstream>`，两条都写进拒绝消息。

### 2.5 不联网

闸门只读本地已有的 remote-tracking ref，**不执行 `git fetch` 或任何网络操作**。
`install-host-access-broker.sh` 与 `install-host-role.sh` 以 `sudo` 运行，让它们联网会
新增一条 root 身份触达远端的路径；平台合同规定 remote 访问只走 broker typed 操作。

### 2.6 嵌套调用

`install-vm.sh` 内部调用 `install-skills.sh`，两者各自带闸门，因此正常路径会打印两段
provenance。这是**允许且期望**的：两段各自标注 installer 名字与各自的可读量。
behind 时 `install-vm.sh` 自己的闸门先拒，不会走到第二段。

## 3. Acceptance criteria

- [x] **AC-1** `install-vm.sh`、`install-host-role.sh`、`install-skills.sh`、
      `architecture/install.sh` 在安装前输出源 checkout 的 commit（含 upstream 同步状态）
      与 §2.3 表中对应的可读量，且在幂等 / no-op 路径上同样出现。
      `docker-release/install.sh` 切出 #182（§4）。
- [x] **AC-2** 上述四个 installer 在源 checkout 落后 upstream 时 fail-closed，且在第一次
      文件系统写入之前拒绝；消息含落后 commit 数与 fast-forward 补救。
      无 remote / detached HEAD / 取不到 remote ref / 非 git 目录一律降级为警告后正常安装。
- [x] **AC-3** 五个 installer（broker 与新接的四个）共用
      `codex/lib/install-source-guard.sh` 一份实现，不是复制五份；
      `install-host-access-broker.sh` 改为使用同一份库，其**外部行为不变**——
      `codex/tests/test-install-host-access-broker.sh` 的断言不做任何放宽即继续通过。
- [x] **AC-4** `codex/tests/test-installer-source-guard.sh` 对**五个**接入的 installer
      各覆盖三条路径：落后 → 拒绝（且安装根零写入）、齐平 → 安装、无 remote → 警告后安装。
      离线构造，不触网。`INSTALLERS` 数组用注释写明 `docker-release/install` 为何缺席
      并指向 #182，不静默少一项。
- [x] **AC-5** `bash codex/tests/smoke.sh` 全绿，新库与新测试已注册进 `bash -n`、
      `shellcheck` 与执行列表。
- [x] **AC-6** `06-运维手册与踩坑集.md` 踩坑 20 的覆盖范围从 broker installer 扩到
      全部 installer（含 `docker-release/install` 的现状与去向），并给出逐 installer 的
      手工判别方法。

## 4. 非目标

- **不覆盖「remote-tracking ref 本身陈旧」**（checkout 从未 fetch）。闸门比对的是
  checkout 自己看到的远端；判别这一层靠 AC-1 打印的 commit 与已合并 PR 对照。
  与 #162 spec §4 同一条显式边界。
- 不改各 installer 的**安装内容**、目标路径与幂等语义（Issue 正文「范围外」）。
- 不改 broker 的操作表或任何 typed 操作（Issue 正文「范围外」）。
- **不改 `docker-release/install.sh`**——切出 **#182**。它与另外四个同因，改动也已写完
  并验证过（输出 `matrix revision: 2026.08.3` / `schemas: 8`），但
  `codex/tests/integration/test-docker-release-v2-lifecycle-e2e.sh:455` 把 `docker-release/`
  相对 Issue #65 delivery base `7ef7fa2` 的 diff 钉死为 `README.md` 与
  `compatibility/image-stores-v1.json` 两个文件；`install.sh` 会成为第三个，`smoke.sh` 红在
  `FAIL: docker-release differs outside the Issue #65 evidence-gated scope`。
  那条闸门是刻意的 **name-only 语法**判断，用途正是让「我这个改动无害」不构成通过理由；
  扩它的 allowlist 落在 **#65 的授权边界**内，本 spec 不能自授。
- 不改 `sync/install.sh`。它用 `AISOFT_SYNC_INSTALL_ROOT` 取源，方式不同，
  Issue 正文列为范围外；确认同因需另开 Issue。
- 不加脏工作区检查、不加 schema 校验、不改幂等语义、不加绕过开关。
- 不引入 `jq` 或任何新的安装期依赖。
- 不改既有的四个 installer 测试（`test-install-skills.sh`、`test-install-host-role.sh`、
  `test-architecture-install.sh`、`test-docker-release-install.sh`）的断言；
  它们从真实 checkout 安装，加闸门后自然继承闸门行为，这是有意的（summary「风险」第 2 条）。

## 5. 治理文件修改授权

本 spec 依 `AGENTS.md`「只有 complex 变更映射的 `spec` 明确授权时，才能修改 …
CI/部署脚本或其他治理文件」显式授权修改：

- `codex/lib/install-source-guard.sh`（新增，共用安装期库）
- `codex/install-host-access-broker.sh`（改用共用库，外部行为不变）
- `codex/install-vm.sh`、`codex/install-host-role.sh`、`codex/install-skills.sh`
- `architecture/install.sh`
- `codex/tests/test-installer-source-guard.sh`（新增）
- `codex/tests/test-install-host-access-broker.sh`（`make_source_tree` 补上新库；断言不变）
- `codex/tests/smoke.sh`（注册新库与新测试）
- `06-运维手册与踩坑集.md` 踩坑 20（AC-6）

**不授权**修改 `AGENTS.md`、broker runtime、typed 操作表、CI workflow、部署脚本、
`sync/install.sh`、`docker-release/` 下的任何文件、
`codex/tests/integration/test-docker-release-v2-lifecycle-e2e.sh`（Issue #65 的 evidence
gate）、凭据与 profile 绑定面，也不授权改动任何 installer 的安装内容。

## 6. 风险与回滚约束

- 回滚 = revert 本次 PR。六个 installer 都是无状态脚本，回滚后行为回到本次之前，
  已安装的内容不受影响（本变更不改变安装内容，只改变是否安装与打印什么）。
- 合并后需在 **Mac 与 gitea-ci VM 两台**重跑相应 installer 才能让新版本生效。
  这是操作前置步骤，不是部署，因此不映射 `verification` 文档。
- 触发面比 #162 大：一个落后的 checkout 现在会挡住五个安装动作而不是一个。
  这正是本 Issue 想要的效果；补救仍是一条 `git merge --ff-only`。

## 7. 未决问题

无。
