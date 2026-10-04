---
issue: 337
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/337
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
status: approved
branch: change/337-restore-hsdb-governance
created: 2026-10-04
updated: 2026-10-04
---

# Verification 恢复 HSDB 治理注册

## 基线与授权

- 平台 source baseline：`e2edb3e08194624a6647212571c6cc866298575b`，2026-10-04 fresh broker fetch。
- Issue：#337；branch=`change/337-restore-hsdb-governance`。
- worktree=`/private/tmp/issue-337-restore-hsdb-governance`；owner=`01a10739-4622-7be1-ba10-0a92d8fc9905`。
- 用户已授权合同内立即启动；PR 提交、merge、安装、账号/Secret 与部署未授权。
- [preflight](evidence/preflight.json) 是只读 live/installed metadata；不包含 token/password/credential hash/数据库 URL。

## Fresh 发现

| 层 | 事实 | 结果 |
|---|---|---|
| 平台 access | protected main；manager=Admin、agent=Write；manual；CI / verify (pull_request) | PASS |
| HSDB source/installed 注册 | 六仓均不含 hsdb；installed broker 拒绝 unknown project | GAP |
| HSDB live protection | private；禁止 direct/force push；merge allowlist=[admin]；CI / test (pull_request)；0 approvals；admin override blocked | PASS（只读，非 adoption） |
| HSDB live identity | hsdb-agent Write、非 site-admin、prohibit_login=true；manager Admin | GAP（账号停用） |
| HSDB credential | Mac file exists/mode=0600/uid=501；content_read=false | metadata PASS；可用性 NOT RUN |
| HSDB branch baseline | local=8e7f5d19c0e7cdc627907dc0962f7285025fb860；live=6114c912310bbaf281bbfe77743abd8cff99087d | GAP（不同 SHA，未修改 checkout） |
| HSDB old tracker | open #15/#18，无 open PR | 保留，非本阶段工作 |

## 验证记录

治理实现、验证和回滚尚待执行；结果将在真实命令运行后填入。
目前 AC-1 至 AC-7 为 NOT RUN；AC-8/9 为 NOT RUN。

## 合并后受保护安装、readback 与恢复卡

| 项 | 精确范围/门禁 |
|---|---|
| owner | 用户批准的 Mac/VM 平台 operator；本聊天仅在独立明确批准后执行 |
| target | Mac /usr/local 的 host-access broker、VM gitea-ci 的同名受管安装面；不安装 provider/业务服务 |
| pin | 尚未产生的本 Issue exact human merge SHA；不得使用 candidate、detached 未验收树或其它 Issue 的 pin |
| window | 人工 merge、required CI success 与 fresh main/read-only drift 读回后单独批准；当前 NOT RUN |
| install | 经 source guard 的 codex/install-host-access-broker.sh；两端从相同 exact merged pin、干净 current-main checkout 安装；禁用式，不创建 credential/profile/service/timer |
| source gate | 先 fresh broker git.fetch.main，核对 merge 在主干、source 状态与 staleness；若 main 已前进则重算并提交新的 exact pin 安装卡 |
| readback | 对 Mac/VM installed 两份 manifest 逐字节比对 merged source、权限/owner；source receipt 与 host entrypoint/runtime 分开核对；调用 installed broker --project hsdb --operation gitea.repo.read / host.access.audit / host.onboarding.check |
| expected | installed 可识别 hsdb（无 unknown project）；若停在 account/credential/ACL GAP 仍原样报告，不能写全 onboarding PASS |
| non-target | 对 aisoft-platform/localwms/newemaint/sfm 同类只读 audit 不回归；不 apply 它们的保护、标签、profile 或 token |
| rollback | 安装前保存上一已合并 pin、installed 快照/可读量；若安装失败，独立批准窗口用上一 pin 经同 installer 恢复两端，核对字节与六仓 readback；不删除/替换 credential |

## 未执行

push、PR、required PR CI、manual merge、真实安装、account/Secret/protection apply、mac binding、
HSDB canary、integration/E2E、UAT、服务器/公司部署均 NOT RUN。
总调度 T01 未完成，直到 human-merged source + installed broker registration 两项准入成立。
