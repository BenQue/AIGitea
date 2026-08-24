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
created: 2026-08-24
updated: 2026-08-24
---

# Spec · installer staleness gate（#162）

## 1. 目标与原因

让 `codex/install-host-access-broker.sh` 的成功输出足以回答「我刚才装进去的是什么」，
并在**源 checkout 落后于它自己的远端**时拒绝安装，而不是安装旧内容后报成功。

原因见 summary：installer 比对的是 `checkout ↔ installed`，操作人问的是
`merged ↔ installed`；两个问句在 checkout 陈旧时分叉，而分叉不可见。
这条链路是平台每一个新 typed 能力上线的必经路径，每次新增操作都会重新暴露一次
（#108、#115、#160 各踩一次，`06` 踩坑 20）。

## 2. 行为契约

### 2.1 Source provenance（安装前无条件输出）

在任何 `install_versioned` 调用之前，向 stdout 打印三行：

```
source checkout:   <ROOT 的绝对路径>
source commit:     <short SHA> (<sync 状态短语>)
source operations: <codex/config/host-access-broker.json 的 .operations 长度>
```

约束：

- **无条件**——`CHANGED=1` 与 `already current (no-op)` 两条路径都打印。
  Issue 正文点名 `no-op` 是假阳性来源，只在变更时打印等于没修。
- 取不到的字段打印 `unknown`，不因此失败（commit、operations 各自独立降级）。
- 既有的 `installed host-access-broker/v1 candidate` /
  `host-access-broker/v1 candidate already current (no-op)` 与
  `no credential, ... was performed` 三行**文本与相对位置不变**，
  provenance 是前置新增行。既有调用方按这两行 grep，不得破坏。

`.operations` 长度用 `python3` 读取——`python3` 已经是被安装物的硬依赖
（`codex/tools/host-access-broker.sh` 直接 `exec python3`），不引入 `jq` 等新依赖。

### 2.2 Staleness 闸门

比较基准固定为**当前分支的 upstream**（`@{upstream}`），落后数为
`git -C <ROOT> rev-list --count HEAD..<upstream>`。

| 源状态 | 行为 |
|---|---|
| 落后 N ≥ 1 个 commit | **fail-closed**：非零退出，stderr 说明落后 N 个 commit 与补救命令，**不安装任何文件** |
| 齐平或领先 | 正常安装 |
| 当前分支无 upstream / 无 remote | 警告后安装 |
| detached HEAD | 警告后安装 |
| upstream ref 本地不可解析（离线、ref 未取回） | 警告后安装 |
| `ROOT` 不是 git 工作区，或 `git` 不可用 | 警告后安装 |

- 拒绝必须发生在**第一次文件系统写入之前**：`install -d` 也算写入，因此闸门位于目录创建之前。
- 警告写 stderr，前缀 `WARNING: install-host-access-broker:`，不影响退出码。
- 拒绝写 stderr，前缀 `ERROR: install-host-access-broker:`，退出码非零。
- **不提供绕过开关**（无环境变量、无 `--force`）。补救是 `git merge --ff-only <upstream>`
  或 `git rebase <upstream>`，两条都写进拒绝消息。

### 2.3 不联网

闸门只读本地已有的 remote-tracking ref，**不执行 `git fetch` 或任何网络操作**。
installer 以 `sudo` 运行，让它联网会新增一条 root 身份触达远端的路径；
平台合同规定 remote 访问只走 broker typed 操作。

## 3. Acceptance criteria

- [ ] **AC-1** installer 在安装前输出源 checkout 的 commit 与 `operations` 数量，
      两条既有结果行之外新增，且在 `installed` 与 `already current (no-op)` 两条路径上都出现。
- [ ] **AC-2** 源 checkout 落后 upstream 时 fail-closed，消息含落后 commit 数与
      fast-forward 补救；无 remote / detached HEAD / 离线取不到 remote ref 时降级为警告并正常安装。
- [ ] **AC-3** `codex/tests/test-install-host-access-broker.sh` 覆盖：落后 → 拒绝（且安装根未被写入）、
      齐平 → 安装、无 remote → 警告后安装；另含 detached HEAD、非 git 目录与二次运行 no-op。
- [ ] **AC-4** `bash codex/tests/smoke.sh` 全绿，新测试已注册进 `bash -n`、`shellcheck` 与执行列表。
- [ ] **AC-5** `06-运维手册与踩坑集.md` 踩坑 20 补记本失败形态（装了、装的是旧的）与判别方法。

## 4. 非目标

- **不覆盖「remote-tracking ref 本身陈旧」**（checkout 从未 fetch）。闸门比对的是
  checkout 自己看到的远端；判别这一层靠 AC-1 打印的 commit 与已合并 PR 对照。
  这是显式边界，不是遗漏。
- 不改 broker 的操作表或任何 typed 操作（Issue 正文「范围外」）。
- 不改 `install-vm.sh`、`install-host-role.sh`、`architecture/install.sh`、
  `docker-release/install.sh`（Issue 正文「范围外」；若同因另开 Issue）。
- 不加脏工作区检查、不加 manifest schema 校验、不改幂等语义。
- 不引入 `jq` 或任何新的安装期依赖。

## 5. 治理文件修改授权

本 spec 依 `AGENTS.md`「只有 complex 变更映射的 `spec` 明确授权时，才能修改 …
CI/部署脚本或其他治理文件」显式授权修改：

- `codex/install-host-access-broker.sh`（host-access broker 的安装面）
- `codex/tests/smoke.sh`（注册新测试）
- `06-运维手册与踩坑集.md` 踩坑 20（AC-5）

**不授权**修改 `AGENTS.md`、broker runtime、typed 操作表、CI workflow、部署脚本、
其它 installer、凭据与 profile 绑定面。

## 6. 风险与回滚约束

- 回滚 = revert 本次 PR。installer 是无状态脚本，回滚后行为回到 v1，
  已安装的 `/usr/local` 内容不受影响（本变更不改变安装内容，只改变是否安装与打印什么）。
- 合并后需在 **Mac 与 gitea-ci VM 两台**重跑 `sudo bash codex/install-host-access-broker.sh`
  才能让新 installer 生效。这是操作前置步骤，不是部署，因此不映射 `verification` 文档。
- 本机当前即处于闸门要防的状态之一的下游：installed 29 / repo 30，
  缺 `gitea.issue.labels.classify`。该重装由人执行（需 sudo）。

## 7. 未决问题

无。
