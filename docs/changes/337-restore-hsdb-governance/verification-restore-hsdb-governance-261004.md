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

治理原子 commit：`2aeb5b2a69ea581a64fdbc78d93cff8f2957c0da`；parent 为合同 commit
`53078bfa0ea42ce0c7fd8ce2bd7d63eaafedb2a8`；tree=`94a045d00bd1bbf5a6173fc4d96c6bd0a813d35a`。
后续候选只同步本 Issue 的证据文档；最终 exact HEAD/parent/tree/index/claim 由外部 candidate 卡 fresh 读回，避免自引用 SHA。

| AC | 结果 | 证据 |
|---|---|---|
| AC-1 | PASS | 两份 manifest 精确七仓，仅恢复 HSDB；[scope-check](evidence/scope-check.json) |
| AC-2 | PASS | strict validate=7 projects/38 operations/1 merge operation |
| AC-3 | PASS | 同树 seal 现算匹配；其余六仓声明仅合法更新 seal；[seal-update](evidence/seal-update.json) |
| AC-4 | PASS | private/manual/CI/identity/origin/default phase 保留；HSDB VM 扩张拒绝；生产保护文件零 diff |
| AC-5 | PASS（local） | 两模块 246 项、broker shell/installer 隔离验证、bash-n/ShellCheck/document check 通过；host 完整 smoke exit 0，末段 1114 项通过；[QA](evidence/qa-results.json) |
| AC-6 | PASS（source only） | scratch clone 真实 git revert --no-commit 后 validate=6，再 git restore --source=HEAD --staged --worktree 恢复同候选字节，validate=7；[rollback](evidence/source-rollback.json)，不是 installed rollback |
| AC-7 | PASS（local candidate） | exact Issue/branch/owner；分类读回 [projected](evidence/classification-readback.jsonl)；最终 PR 提交未执行 |
| AC-8 | NOT RUN | 没有 push/PR/manual merge；平台 required context 仍为 CI / verify (pull_request) |
| AC-9 | GAP / NOT RUN | Mac/VM installed 均六仓且没有 HSDB；真实安装未执行；[VM metadata](evidence/vm-installed-metadata.json) |

完整 smoke 第一次在 sandbox 的本地临时端口绑定处 PermissionError、exit 1；同命令 host 路径重跑 exit 0。
保留失败历史，不改断言，不将 fake/isolated fixture 的 PASS 提升为真实安装或部署。
双轴只读审查：Standards=0 hard/smell findings；Spec=0 实现缺陷，审查时的 smoke/证据同步缺口已用回执解决，见 [review](evidence/review.json)。
Mac 与 VM 的安装 source receipt 均缺失，installed source SHA 为 NOT VERIFIED；不由六仓 manifest 字节反推整体安装 SHA。


## 合并后受保护安装、readback 与恢复卡

| 项 | 精确范围/门禁 |
|---|---|
| owner | 用户批准的 Mac/VM 平台 operator；本聊天仅在独立明确批准后执行 |
| target | Mac /usr/local 的 host-access broker、VM gitea-ci 的同名受管安装面；不安装 provider/业务服务 |
| pin | 尚未产生的本 Issue exact human merge SHA；不得使用 candidate、detached 未验收树或其它 Issue 的 pin |
| window | 人工 merge、required CI success 与 fresh main/read-only drift 读回后单独批准；当前 NOT RUN |
| install | 经 source guard 的 codex/install-host-access-broker.sh；两端从相同 exact merged pin、干净 current-main checkout 安装；禁用式，不创建 credential/profile/service/timer |
| source gate | 先 fresh broker git.fetch.main，核对 merge 在主干、source 状态与 staleness；clean current-main 且 exact merged pin；若 main 已前进则重算新的安装卡，不能使用 detached/unknown staleness 警告作为 PASS |
| rotation metadata 边界 | installer 会写 credential-rotation-source.json；安装前只读核对现有 helper/receipt metadata。若 #333 等独立 owner 已采用 helper，不得无 artifact 安装而清空 helper 声明；须停止、保留其既有能力，由 owner 提供绑定同一新 pin 的已验证 artifact 与独立 scope，不借用 #333 授权 |
| readback | 对 Mac/VM installed 两份 manifest 逐字节比对 merged source、权限/owner；source receipt 与 host entrypoint/runtime 分开核对；调用 installed broker --project hsdb --operation gitea.repo.read / host.access.audit / host.onboarding.check |
| expected | installed 可识别 hsdb（无 unknown project）；若停在 account/credential/ACL GAP 仍原样报告，不能写全 onboarding PASS |
| non-target | 对 aisoft-platform/localwms/newemaint/sfm 同类只读 audit 不回归；不 apply 它们的保护、标签、profile 或 token |
| rollback | 安装前保存上一已合并 pin、installed 快照/可读量；若安装失败，独立批准窗口用上一 pin 经同 installer 恢复两端，核对字节与六仓 readback；不删除/替换 credential |

## 未执行

push、PR、required PR CI、manual merge、真实安装、account/Secret/protection apply、mac binding、
HSDB canary、integration/E2E、UAT、服务器/公司部署均 NOT RUN。
总调度 T01 未完成，直到 human-merged source + installed broker registration 两项准入成立。
