---
issue: 342
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/342
change_type: security
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - security
  - rollback
depends_on:
  - 337
  - 339
branch: change/342-hsdb-login-recovery
created: 2026-10-05
updated: 2026-10-05
reason: 仅恢复现有账号登录flag，认证权限及失败恢复风险强制complex/manual；未知禁用来源必须在具体批准中接受。
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-hsdb-login-recovery-261005.md
  spec: spec-hsdb-login-recovery-261005.md
  plan: plan-hsdb-login-recovery-261005.md
  verification: verification-hsdb-login-recovery-261005.md
override_reason: ''
status: analyzed
pr_url:
---

# #342 · HSDB账号恢复合同准备

**AWAITING_EXACT_ACCOUNT_CHANGE_APPROVAL**。当前只获准只读核验、唯一Issue跟踪与本地合同准备；账号写入未批准。
唯一owner=`01a10c83-389d-7ab3-b364-59e108f1ca46`；worktree=`/private/tmp/issue-342-hsdb-login-recovery`。
拟仅UID5/hsdb-agent Disable Sign-In true→false；安全风险complex/type-security/manual，无runtime/安装变更。
细节见[spec](spec-hsdb-login-recovery-261005.md)、[plan](plan-hsdb-login-recovery-261005.md)、[verification](verification-hsdb-login-recovery-261005.md)。
external卡、Issue正文/文档manifest及机读handoff位于 `/Users/benque/.codex/visualizations/2026/10/05/01a10c83-389d-7ab3-b364-59e108f1ca46/hsdb-account-recovery`。

## 证据层与前置

| 层 | 当前证据 | 边界 |
|---|---|---|
| source | 本owner typed `git.fetch.main` PASS 后平台 HEAD=origin/main=c9b5ef4e74592cbc68d6bdc6219568a1d51b6853 | 没有runtime/脚本/AGENTS/manifest修改 |
| doc | 本票独立四文档、本地合同提交；exact doc head和逐文件SHA256见外部handoff | 不等于source main、PR或CI |
| installed | 总调度/#339已独立核验Mac+gitea-ci同pin安装、幂等、真实恢复、同pin再安装PASS | 本owner未重验安装、不复用installer窗口；helper:null不证明轮换能力 |
| credential | 本轮固定typed读操作内部认证；未手工读/散列/打印/复制Secret | 现有PAT有效性/撤销状态NOT VERIFIED；不提供grant |
| live before | fresh UI UID5停用、UID3未停用，exact HSDB ACL，typed protection PASS | 下表是before；账号写入/after均NOT RUN |
| access before | Mac hsdb repo.read/audit/onboarding均exit20 HTTP_401 | manager-audit protection单独PASS；manager-mutation根因NOT VERIFIED |
| UAT/部署 | NOT RUN | HSDB adoption/应用/公司现场仍由独立owner负责 |

#337已人工合并；#339技术安装退出门已独立PASS，文档最终PR/归档仍由#339 owner负责。summary的depends_on保留两票，不能借技术PASS宣称#339已closed，也不能绕过日后Controller的依赖门。
T02 owner保持 `01a1073b-42e6-7491-89d1-212d8b19636a`；本票不改变HSDB数字命名规则，不创建HSDB Issue/分支，不重置/rebase其本地main。
HSDB fresh remote main=`6114c912310bbaf281bbfe77743abd8cff99087d`；本地main=`8e7f5d19c0e7cdc627907dc0962f7285025fb860`来自总调度/T02，本owner未改动。

## 历史安全意图与Gitea版本行为

只读发现[#252 spec](../252-offboard-five-projects/spec-offboard-five-projects-260905.md) AC-12 与
[verification](../252-offboard-five-projects/verification-offboard-five-projects-260905.md) H-6 明确把
`hsdb-agent`列入退管待停用账号，但H-6仍NOT RUN；H-4撤销PAT亦NOT RUN。存在明确的历史退管安全意图，
而当前flag的实际设置人、时间、原因及该历史动作是否执行仍 **NOT VERIFIED**。不能由历史NOT RUN推断PAT仍有效或已撤销。
#337恢复source注册但明确不解除停用；本票将拟解除历史退管对象的单一flag作为独立安全决定请求具体批准。

当前pin的manifest/contract/bootstrap/strict identity verifier未发现`expected prohibit_login=true`：
`codex/tools/bootstrap-gitea-service-account.sh:314-341`创建bot并独立处理MustChangePassword；
`codex/runtime/aisoft_host_access/broker.py:2843-2864`仍验exact login与non-site-admin；
#219 spec AC-3允许`prohibit_login`作typed metadata，不把其值当权限决策。未修改或解除任何安全门。
这项结论限所查source/已发布合同，不等于当前停用原因已证实。

Context7 `/go-gitea/gitea`返回main分支概览；精确版本另以既有公开模块缓存
`/private/tmp/issue-316-build/gopath/pkg/mod/code.gitea.io/gitea@v1.26.4`只读核对，并交叉读官方
[Gitea v1.26.4 API source](https://github.com/go-gitea/gitea/blob/v1.26.4/routers/api/v1/api.go#L836-L855)。
该版本PAT解析先获得user；已signed user的IsActive/ProhibitLogin检查拒绝API请求（此分支403），
apiAuth认证错误路径401。故本轮HTTP401与禁用flag同时存在，**不能证明禁用是唯一故障原因**。
恢复false可能使仍有效的既有PAT重新获得既有Write能力；不重新签发、不承诺可用，不测试密码登录。

## AI 判级

```yaml
change_type: security
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
reason: 仅恢复现有账号登录flag，认证权限及失败恢复风险强制complex/manual；未知禁用来源必须在具体批准中接受。
risk_flags:
  - security
  - rollback
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

判级证据：恢复已有通道的目标明确，账号登录状态决定existing PAT/Write能力可用性，故即使单字段可逆仍强制complex。
当前只投影type/security与complexity/complex，triage/needs-triage保留；不写approved。
最终文档PR policy固定manual，本轮未请求提交PR；本票现有允许scope仅合同准备。
