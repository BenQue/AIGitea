---
issue: 292
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/292
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - security
  - platform-governance
  - shared-core
depends_on: []
status: spec-drafting
branch: change/292-github-main-relay
created: 2026-09-11
updated: 2026-09-15
---

# GitHub main relay 合同（已被原生 Push Mirror 取代）

## 状态声明（2026-09-15）

本 spec 原定义的自研 fast-forward-only relay 已被用户 2026-09-12 的裁决取代：本机 Gitea 是唯一源，
指定私有 GitHub 仓库是可覆盖镜像，使用 Gitea 原生 Push Mirror。**下文 AC-1 至 AC-10、受保护文件允许
清单与 T02–T05 授权全部停止，不再构成任何实现、安装或调度授权。** 保留原文只为追溯当时批准过什么。

## 现行验收边界（由 NewEMaint #80 承载，本票不交付）

| 项 | 内容 | 责任 | 本票状态 |
|---|---|---|---|
| M-1 | 核对唯一源与指定私有目标，确认目标独有成果无需保留 | 用户 | 已确认 |
| M-2 | 在 Gitea 界面手工配置原生 Push Mirror，目标仓库专用凭据，不降低源 main 保护、不回推 | 用户 | NOT RUN |
| M-3 | 首次同步成功后独立读回目标 main 与源 SHA 一致，核对 branch/tag 范围与目标 workflow 影响 | 用户 | NOT RUN |
| M-4 | 后续已批准源更新经原生触发或周期同步到目标，读回一致 | 用户 | NOT RUN |
| M-5 | 公司按原入站/PR/CI/人工审核流程消费；镜像覆盖许可不延伸到公司 main | 公司流程 | NOT RUN |
| M-6 | 停用镜像只停止未来同步，不自动恢复历史 | 用户 | 边界声明 |

本票关闭条件：四份映射文档如实反映上述取代关系并经唯一最终 PR 人工合并。M-2 至 M-5 的完成与否不阻塞
本票关闭，其证据归 NewEMaint #80。

## 非目标（现行）

- 不实现、不安装、不调度任何自研 relay、helper、pre-push gate 或 PAT 审核回执体系。
- 不修改 `sync/` 入站组件、broker 操作表、installer、source guard、`AGENTS.md` 或 CI。
- 不授权强推本机 Gitea、公司 Gitea 或指定目标以外的任何仓库。
- 不配置、读取或核验镜像凭据；不代替 #80 记录现场证据。

## 未决问题

无。收口方式已由用户裁决为提交文档后关闭本票。

---

## 历史合同（2026-09-11 至 2026-09-12，已停止，不构成授权）

### 目标与原因

把已在开发侧受保护main合并的提交单向传输到显式绑定的私有GitHub中继，让公司入站同步消费同一Git来源。同步不是合并或部署。

### Acceptance criteria（已停止）

- [ ] AC-1：typed plan/reconcile/status仅接受manifest project，源从现有项目合同派生，目标来自受保护的显式项目relay绑定。GitHub hostname限定github.com、private目标、refs/heads/main固定；不存在/未知/未opt-in/绑定漂移拒绝。调用方不能传URL、Git参数、脚本、refspec或credential path。
- [ ] AC-2：plan只读网络，不写远端/凭据/工作区；输出source SHA、destination SHA、祖先关系、plan动作和缺口的脱敏字段。源码为空、目标main缺失、非共同历史、目标不为源祖先、源历史相对上次成功倒退均拒绝。相同SHA是no-op。
- [ ] AC-3：reconcile先获取项目独占锁，在隔离bare工作区fetch精确main所需对象，读回当前源与目标，固定本轮source/target OID；只发送单一sourceSHA:refs/heads/main更新。不使用force、force-with-lease、mirror、prune、delete、tags、all，也不修改目标其它refs或本机源refs。
- [ ] AC-4：必须校验Git push实际协商的目标旧OID。使用版本化且调用方不可替换的pre-push gate或等效原子机制，仅允许一个main更新，广告旧OID必须非零并与本轮校验值一致，local OID必须等于本轮pin。预检查后远端推进/删除/换历史应拒绝；hook后再推进由Git receive-pack旧OID匹配拒绝。不得声称普通merge-base预检查单独消除竞态，不得用任何force选项实现CAS。
- [ ] AC-5：源端复用既有Gitea项目最小身份；GitHub采用独立、仅目标仓库的fine-grained PAT认证绑定；其单仓库范围、权限和有效期由人核验，以绑定token指纹的受保护非Secret审核回执作为scope信任来源，工具另外在线核验身份和目标仓库。回执缺失、无效、过期、指纹或项目/目标绑定不匹配，以及元数据/身份/scope不足或凭据缺失必须单独BLOCKED，不自动provision、不fallback到shared bot、管理员或全局gh/Git凭据。禁止credential/token值进入argv、URL、日志、Git配置、receipt、Git objects或公共合同。
- [ ] AC-6：Git子进程隔离全局Git config、继承hook/credential/helper、redirect、transport和代理注入；具体allowlist与既有broker兼容，目标URL校验先于凭据调用。固定protocol与项目路径，阻止symlink、任意command/helper、未验证hook替换。失败只返回类别/rc等脱敏信息，不回显原始远端错误。
- [ ] AC-7：成功后独立读取GitHub main等于本轮源pin，原子保存source/destination/prev OID、时间、结果、工具版本和绑定摘要receipt；失败不写成功。相同SHA重跑无远端mutation。status只返回脱敏最近receipt和调度状态，历史PASS不能代替新鲜plan。
- [ ] AC-8：提供版本化项目专用macOS调度入口，默认10分钟周期，只调用同一typed reconcile，锁防重叠。install候选不创建/复制凭据、不启用任务。实际安装必须通过现有source provenance guard，配置/启用只针对获批项目，disable停止后续运行且不回退/删除任何GitHub ref。不改现有入站timer及其它项目任务。
- [ ] AC-9：确定性测试覆盖成功FF、两次执行update→no-op、分叉、missing ref、源码倒退、目标在plan后推进/删除、凭据/身份/绑定拒绝、并发、receipt失败与脱敏，并断言其它branch/tag完全不变。测试使用临时repo/fakes，禁止触碰真实网络/凭据。
- [ ] AC-10：最终源码PR人工合并后，验证installed字节，再由用户完成必要专用认证。实际pilot执行一次FF、一次no-op，远端独立读回一致，并证明至少一次调度触发执行；真实数据的故意失败不得改远端，可使用本地受控故障路径。未发生则对应项NOT RUN。

### AC-5 已批准的权限证明方式（已停止）

2026-09-12，用户在既有实施任务同意：人工核验fine-grained PAT仅选择目标仓库、所授权限和有效期，形成绑定该token指纹的受保护非Secret审核回执。该回执是人工审核证据；工具在线核验身份与目标仓库，不将目标仓库GET成功或push成功解释为token仅限单仓库的在线证明，也不引入额外GitHub App或管理员审计权限。该决定随自研路线一并停止。

### 本轮批准范围与受保护文件授权（已停止）

用户曾批准实现#292、完成本地测试和PR材料，并禁止实际推送GitHub、配置凭据、安装/启用定时任务、触碰公司服务器及旧服务。以下 exact 文件允许清单已随 T02–T05 停止而失效，保留只为追溯：

| Ticket | Exact files | 原授权与验证 |
|---|---|---|
| T02 | `codex/runtime/aisoft_host_access/broker.py`、`codex/runtime/aisoft_host_access/contract.py`、`codex/runtime/aisoft_host_access/cli.py`、`codex/config/host-access-broker.json` | 新typed relay路由与封闭绑定 |
| T02 | `codex/runtime/aisoft_host_access/github_relay.py`、`codex/config/github-relay-binding.schema.json`、`codex/tools/github-relay-pre-push.sh`、`codex/tools/github-relay-credential.sh` | 专用relay、binding schema和固定进程入口 |
| T02 | `codex/runtime/tests/test_host_access.py`、`codex/runtime/tests/test_github_relay.py`、`codex/tests/test-host-access-broker.sh` | AC-1–AC-7/AC-9 回归 |
| T03 | `codex/install-host-access-broker.sh`、`codex/install-github-main-relay.sh`、`codex/runtime/aisoft_host_access/github_relay_scheduler.py`、`codex/templates/launchd/com.aisoft.github-main-relay.plist` | 版本化安装/默认disabled调度 |
| T03 | `codex/tests/test-install-host-access-broker.sh`、`codex/tests/test-install-github-main-relay.sh`、`codex/runtime/tests/test_github_relay_scheduler.py`、`codex/tests/smoke.sh` | installer/scheduler 回归 |
| T03 | `codex/lib/install-source-guard.sh` | source-guard inventory 登记 |
| T03/T04 | `README.md`、`06-运维手册与踩坑集.md` | relay 操作与边界说明 |
| T01–T04 | `docs/changes/292-github-main-relay/` 四份映射文档 | 合同与证据更新 |

上述清单中没有任何文件在本票分支上被实际修改；本次收口 PR 只触及最后一行的四份文档。

### 接口、数据与兼容性影响（历史）

建议操作名github.relay.plan、github.relay.reconcile、github.relay.status。未实现，broker 操作表无变化。

### 风险与回滚约束（历史）

安装回滚恢复上一版本化工具，调度关闭阻止新运行；已推进的GitHub main保持。未实施。
