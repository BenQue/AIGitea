---
issue: 362
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/362
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - security
  - shared-core
  - deployment
  - rollback
  - platform-governance
depends_on:
  - 360
status: approved
branch: change/362-mac-broker-install-acceptance
created: 2026-10-17
updated: 2026-10-17
---

# #362 已批准运维合同

## 目标与原因

恢复已合并 source→Mac system 的实际资格闭包，按原卡完整验收；不改变工具源码或权限政策。
直接人类批准原文及 #362 正文独立读回在 `/Users/benque/.codex/visualizations/2026/10/16/01a1457e-699f-7372-8b6a-7a21d613d407/issue-362/fresh-typed.json` 与调度输入目录。
权威审阅卡：`/Users/benque/.codex/visualizations/2026/10/14/01a13b2a-e69a-78e2-9c6f-a00284afda90/scope360/install-review-261016/独立工具安装与验收审阅卡-261016.md`，SHA256 `3c67a0c6a3d085735d4e20aead4fd951ead4eeb716ac41323719bff85d3ed8d9`。
本合同继承其 P0–P6/F1/F2，无新增安装面。

## Acceptance criteria

- AC1：唯一 #362/session/branch/docs/WT/claim；full pin/sourceguard/27源文件/installer/guard正确，fresh baseline、root/interpreter和真实协调窗口有效。
- AC2：27文件字节、root:wheel、mode/type/link与 pin 一致，metadata exact pin/helper=null，manifest相同。
- AC3：本 session fresh pure qualification、canonical repository/holder/context.verify；不构造 GitRepository、不访问HSDB#15 WT/scope/history。
- AC4：同 pin 二次安装 no-op；全部 target/previous/absence/owner/mode/link 独立不变。
- AC5：完整 snapshot restore，43存在/13absence及目录权限与 observed baseline 一致；旧资格负例；同 pin 再安装并重做 AC2/AC3。
- AC6：原卡 F1/F2 两项封闭 fixture 通过并清理；保留外部 GAP，不安装依赖，不对真实系统造坏。
- AC7：真实命令/退出码/完整 SHA、snapshot/restore/no-op/资格/剩余GAP分层留证；未运行如实 NOT RUN。

## 接口、数据与兼容性影响

Source pin `06afadfca2a950ad6ebee4b90a22e9d950bc72fa`；canonical checkout `/Users/benque/MyDocs/AISoftPlatform`。
只执行它的既有 `codex/install-host-access-broker.sh`；SHA256 `485ea19514c5f4b72c84d6cc9576fe0c2b65c34d084e74c8f80e2d6ad6f10897`。
本票文档不修改正在遵循的 AGENTS，也没有治理 runtime 实施步骤。

| exact target | mode（root:wheel） |
|---|---|
| `/usr/local/lib/aisoft-host-access/aisoft_gitea_governance/__init__.py` | 0644 |
| `/usr/local/lib/aisoft-host-access/aisoft_gitea_governance/cli.py` | 0644 |
| `/usr/local/lib/aisoft-host-access/aisoft_gitea_governance/client.py` | 0644 |
| `/usr/local/lib/aisoft-host-access/aisoft_gitea_governance/contract.py` | 0644 |
| `/usr/local/lib/aisoft-host-access/aisoft_gitea_governance/reconcile.py` | 0644 |
| `/usr/local/lib/aisoft-host-access/aisoft_gitea_governance/service_policy.py` | 0644 |
| `/usr/local/lib/aisoft-host-access/aisoft_host_access/__init__.py` | 0644 |
| `/usr/local/lib/aisoft-host-access/aisoft_host_access/application_preflight.py` | 0644 |
| `/usr/local/lib/aisoft-host-access/aisoft_host_access/broker.py` | 0644 |
| `/usr/local/lib/aisoft-host-access/aisoft_host_access/cli.py` | 0644 |
| `/usr/local/lib/aisoft-host-access/aisoft_host_access/contract.py` | 0644 |
| `/usr/local/lib/aisoft-host-access/aisoft_host_access/credential_rotation.py` | 0644 |
| `/usr/local/lib/aisoft-host-access/aisoft_host_access/dependencies.py` | 0644 |
| `/usr/local/lib/aisoft-host-access/aisoft_host_access/profiles.py` | 0644 |
| `/usr/local/lib/aisoft-host-access/aisoft_host_access/runner.py` | 0644 |
| `/usr/local/lib/aisoft-host-access/aisoft_change_name.py` | 0644 |
| `/usr/local/lib/aisoft-host-access/aisoft_worktree_owner.py` | 0644 |
| `/usr/local/lib/aisoft-host-access/aisoft_main_integration.py` | 0644 |
| `/usr/local/share/aisoft/host-access-broker.json` | 0644 |
| `/usr/local/share/aisoft/gitea-governance.json` | 0644 |
| `/usr/local/share/aisoft/gitea-labels.json` | 0644 |
| `/usr/local/libexec/aisoft/host-access-broker` | 0755 |
| `/usr/local/libexec/aisoft/git-credential-aisoft-host` | 0755 |
| `/usr/local/libexec/aisoft/project-profile-migration` | 0755 |
| `/usr/local/libexec/aisoft/bootstrap-gitea-service-account` | 0755 |
| `/usr/local/libexec/aisoft/rollback-gitea-routine-pilot` | 0755 |
| `/usr/local/libexec/aisoft/rotate-gitea-service-account` | 0755 |

另含公开 `/usr/local/share/aisoft/credential-rotation-source.json`（0644）、以上28目标各自有限 `.previous`、原卡10目录的metadata及installer实际 `.rotation-source.XXXXXX`。
完整 exact 清单由原卡 `prospective-backup-manifest.json` 给出，当前 fresh 43存在/13缺失/10目录；不是未来覆盖漂移许可。
retired `keychain-acl-audit`/`.previous` 及 Mac PAT helper 必须保持缺失；任一未知出现即STOP。

## 风险与回滚约束

固定原生 `/usr/bin/sudo`；sudo不可用即停止，不切身份/AppleScript或改sudoers。
固定环境、PATH、interpreter/import及root safe.directory仅瞬时设置，详见 runbook。
共享写入窗口由owner本人协调，source/target任一漂移、未知并发/额外文件/链接停止；不以本地marker证明安全排他。
Snapshot exact `/usr/local/share/aisoft/backups/tools-362-<窗口UTC>/` root:wheel/0700；先 fresh 验证，native tar只归档显式43公开文件。
恢复native tar还原完整previous链；仅删除本次可证新建且仍符合预期字节的 exact `aisoft_main_integration.py.previous`，不glob删除。
恢复后全量比较原baseline；snapshot保留。失败按同窗口恢复；恢复失败保全现场STOP，不修改installer来绕失败。

## 非目标

VM/其他7 installer/user Loop修复、Secret/PAT/身份/权限/DB/迁移/服务启停、HSDB采用/T04、provider/monitor、公司部署和push/PR/merge。
#360保持closed/completed，不恢复其WT/branch/claim；#358按A，architecture/lock GAP保留。
HSDB#15 OID `82a5aba9e46a002b78e3aca9896ef9a26e4aa5cd`及所有资源停写；声明4–44、52行/7版本及样本/旧附件/日期/历史结果保留。

## 未决问题

合同无未决业务问题。本人私密终端root认证与解释器核验已通过；共享工具窗口尚未协调，P0未完整通过，执行状态BLOCKED_EXTERNAL。Agent执行上下文认证没有重探测。
