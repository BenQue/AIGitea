---
issue: 250
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/250
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - deployment
depends_on: []
status: approved
branch: change/250-sync-install-source-guard
created: 2026-09-05
updated: 2026-09-05
---

# Spec: sync/install.sh 接入共用 source guard

## 目标与原因

让 `sync/install.sh` 与其余六个 installer 在 source provenance 与 staleness 上行为一致：
安装前打印它正在装哪一份源，源落后 upstream 时在写任何文件之前拒绝。

原因是它现在无法区分「装上了」与「装的是旧的」。它从自身所在 checkout 取源，没有任何
staleness 判断，成功输出在两种情况下逐字相同。它装的是 systemd unit 与凭据 helper，
所以陈旧的后果不落在这一次命令上，而落在 VM 上此后每一次 timer 触发的同步里。

## Acceptance criteria

- [ ] AC-1 `sync/install.sh` 在第一次文件系统写入之前打印 `source checkout`、
      `source commit`（含 upstream 同步状态）和可读量，幂等重跑时同样打印。
- [ ] AC-2 源 checkout 落后 upstream 时以非零状态退出，且安装根目录完全没有被创建。
- [ ] AC-3 无 upstream、detached HEAD、取不到 remote ref、非 git 目录时降级为
      `WARNING: sync/install: ...` 并正常安装。
- [ ] AC-4 复用 `codex/lib/install-source-guard.sh`，`sync/` 下不出现第二份实现。
- [ ] AC-5 `codex/tests/test-installer-source-guard.sh` 的 `INSTALLERS` 含
      `sync/install`，末行计数从 6 installers 变 7 installers。
- [ ] AC-6 `06-运维手册与踩坑集.md` 踩坑 20 的逐 installer 可读量清单含 `sync/install`。
- [ ] AC-7 `bash codex/tests/smoke.sh` 全绿，其中包含既有的 `sync/tests/test-install.sh`。

## 接口、数据与兼容性影响

对外接口只增加了一条拒绝路径。成功路径的 stdout 在原有末行之前多出 provenance 行，
既有 `sync/tests/test-install.sh` 用 `grep -Fq` 匹配末行短语，不受影响。

安装产物、文件模式、systemd unit 内容与 timer 的 disabled/inactive 初始状态全部不变。
`AISOFT_SYNC_INSTALL_ROOT` 语义不变。

可读量取两个文件计数，来自库里已有的 `aisoft_install_source_file_count`：

| 标签 | 源 | 目标端手工核对对象 |
|---|---|---|
| `units` | `sync/systemd/` 下的 unit 文件 | `/etc/systemd/system/aisoft-inbound-sync@` 的 service 与 timer |
| `runtime scripts` | `inbound-sync.sh` 与 `git-credential-token-file.sh` | `/opt/aisoft-sync/` |

`sync/` 里没有携带版本号的 JSON，取不到 catalog revision 那类会随合同变化的标量。
版本证据由 guard 固定打印的 `source commit` 承担，文件计数承担目标端比对。

## 风险与回滚约束

风险是 installer 多一条拒绝路径，落后的 checkout 上原本会「成功」的安装现在失败。
这是本 Issue 的目的，且 guard 已给出 `merge --ff-only` 与 `rebase` 两条补救命令。

回滚是单文件 revert：移除 `sync/install.sh` 里的 source 与调用两处、测试数组里的一项、
文档清单里的一项即可，没有状态残留、没有迁移、没有已安装产物需要清理。

## 非目标

- 不改 sync 的同步语义、`inbound-sync.sh`、凭据 helper。
- 不改 systemd unit 内容与 timer 的启停行为。
- 不改共用库 `codex/lib/install-source-guard.sh` 本身。
- 不接入 `skill-for-claude/install.sh`。它是 Claude skills 的安装脚本，不在本 Issue
  正文范围内；若确认同因另开 Issue。
- 不在任何主机上执行安装。

## 未决问题

无。Issue 正文 AC-4 的「7 变 8」按 summary 记录的证据修正为 6 变 7。
