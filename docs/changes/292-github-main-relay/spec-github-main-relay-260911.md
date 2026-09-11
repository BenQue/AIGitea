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
status: approved
branch: change/292-github-main-relay
created: 2026-09-11
updated: 2026-09-11
---

# GitHub main relay 合同

## 目标与原因

把已在开发侧受保护main合并的提交单向传输到显式绑定的私有GitHub中继，让公司入站同步消费同一Git来源。同步不是合并或部署。

## Acceptance criteria

- [ ] AC-1：typed plan/reconcile/status仅接受manifest project，源从现有项目合同派生，目标来自受保护的显式项目relay绑定。GitHub hostname限定github.com、private目标、refs/heads/main固定；不存在/未知/未opt-in/绑定漂移拒绝。调用方不能传URL、Git参数、脚本、refspec或credential path。
- [ ] AC-2：plan只读网络，不写远端/凭据/工作区；输出source SHA、destination SHA、祖先关系、plan动作和缺口的脱敏字段。源码为空、目标main缺失、非共同历史、目标不为源祖先、源历史相对上次成功倒退均拒绝。相同SHA是no-op。
- [ ] AC-3：reconcile先获取项目独占锁，在隔离bare工作区fetch精确main所需对象，读回当前源与目标，固定本轮source/target OID；只发送单一sourceSHA:refs/heads/main更新。不使用force、force-with-lease、mirror、prune、delete、tags、all，也不修改目标其它refs或本机源refs。
- [ ] AC-4：必须校验Git push实际协商的目标旧OID。使用版本化且调用方不可替换的pre-push gate或等效原子机制，仅允许一个main更新，广告旧OID必须非零并与本轮校验值一致，local OID必须等于本轮pin。预检查后远端推进/删除/换历史应拒绝；hook后再推进由Git receive-pack旧OID匹配拒绝。不得声称普通merge-base预检查单独消除竞态，不得用任何force选项实现CAS。
- [ ] AC-5：源端复用既有Gitea项目最小身份；GitHub采用独立、仅目标仓库的认证绑定。元数据/身份/scope不足或凭据缺失必须单独BLOCKED，不自动provision、不fallback到shared bot、管理员或全局gh/Git凭据。禁止credential/token值进入argv、URL、日志、Git配置、receipt、Git objects或公共合同。
- [ ] AC-6：Git子进程隔离全局Git config、继承hook/credential/helper、redirect、transport和代理注入；具体allowlist与既有broker兼容，目标URL校验先于凭据调用。固定protocol与项目路径，阻止symlink、任意command/helper、未验证hook替换。失败只返回类别/rc等脱敏信息，不回显原始远端错误。
- [ ] AC-7：成功后独立读取GitHub main等于本轮源pin，原子保存source/destination/prev OID、时间、结果、工具版本和绑定摘要receipt；失败不写成功。相同SHA重跑无远端mutation。status只返回脱敏最近receipt和调度状态，历史PASS不能代替新鲜plan。
- [ ] AC-8：提供版本化项目专用macOS调度入口，默认10分钟周期，只调用同一typed reconcile，锁防重叠。install候选不创建/复制凭据、不启用任务。实际安装必须通过现有source provenance guard，配置/启用只针对获批项目，disable停止后续运行且不回退/删除任何GitHub ref。不改现有入站timer及其它项目任务。
- [ ] AC-9：确定性测试覆盖成功FF、两次执行update→no-op、分叉、missing ref、源码倒退、目标在plan后推进/删除、凭据/身份/绑定拒绝、并发、receipt失败与脱敏，并断言其它branch/tag完全不变。测试使用临时repo/fakes，禁止触碰真实网络/凭据。
- [ ] AC-10：最终源码PR人工合并后，验证installed字节，再由用户完成必要专用认证。实际pilot执行一次FF、一次no-op，远端独立读回一致，并证明至少一次调度触发执行；真实数据的故意失败不得改远端，可使用本地受控故障路径。未发生则对应项NOT RUN。

## 本轮批准范围与受保护文件授权

用户已明确批准实现#292、完成本地测试和PR材料；本轮禁止实际推送GitHub、配置或provision凭据、安装或启用定时任务、触碰公司服务器及旧服务。此前对未来自动同步目标的批准，不替代本轮明确禁止项。T02/T03可实施代码并在临时目录验证；T04仅本地回归和PR材料，实际提交/合并另守原有人工门；T05为后续NOT RUN阶段。

本complex spec将plan既定touchpoints收敛为以下exact文件允许清单。允许为AC-1–AC-9修改或新增以下文件；只按需要触及，不要求全部修改，不授权同目录其它文件：

| Ticket | Exact files | 授权与验证 |
|---|---|---|
| T02 | `codex/runtime/aisoft_host_access/broker.py`、`codex/runtime/aisoft_host_access/contract.py`、`codex/runtime/aisoft_host_access/cli.py`、`codex/config/host-access-broker.json` | 新typed relay路由与封闭绑定；broker/contract回归，原操作语义与权限不变 |
| T02 | `codex/runtime/aisoft_host_access/github_relay.py`、`codex/config/github-relay-binding.schema.json`、`codex/tools/github-relay-pre-push.sh`、`codex/tools/github-relay-credential.sh` | 专用relay、binding schema和固定进程入口；临时真实Git/协商OID/凭据脱敏/严格参数测试 |
| T02 | `codex/runtime/tests/test_host_access.py`、`codex/runtime/tests/test_github_relay.py`、`codex/tests/test-host-access-broker.sh` | 复用真实现有测试路径，覆盖AC-1–AC-7/AC-9；不得删除或放宽既有安全断言 |
| T03 | `codex/install-host-access-broker.sh`、`codex/install-github-main-relay.sh`、`codex/runtime/aisoft_host_access/github_relay_scheduler.py`、`codex/templates/launchd/com.aisoft.github-main-relay.plist` | 版本化安装/默认disabled调度；只在临时安装根与fake scheduler验证，无真实安装/launchctl enable |
| T03 | `codex/tests/test-install-host-access-broker.sh`、`codex/tests/test-install-github-main-relay.sh`、`codex/runtime/tests/test_github_relay_scheduler.py`、`codex/tests/smoke.sh` | installer/scheduler幂等与disabled默认、source provenance及全套回归 |
| T03 | `codex/lib/install-source-guard.sh` | 仅既定必要source-guard inventory/新installer登记；不得改变provenance/staleness拒绝规则，完整source-guard回归 |
| T03/T04 | `README.md`、`06-运维手册与踩坑集.md` | 仅新增relay操作与边界说明，不扩展凭据/部署授权；文档与链接检查 |
| T01–T04 | `docs/changes/292-github-main-relay/summary-github-main-relay-260911.md`、`docs/changes/292-github-main-relay/spec-github-main-relay-260911.md`、`docs/changes/292-github-main-relay/plan-github-main-relay-260911.md`、`docs/changes/292-github-main-relay/verification-github-main-relay-260911.md` | 映射合同和真实证据更新；check-change-documents与diff检查 |

禁止修改AGENTS.md、现有workflow/CI context、controller实现、Gitea治理权限manifest、其它项目配置、入站sync实现与历史证据。需要清单外受保护文件时先向Controller报告具体必要差异，不推导为同目录授权。新入口文件basename在本次收敛时固定，以免worker猜测范围；不新增功能。

回滚授权限于开发分支上的本票代码回退，以及测试临时安装根的隔离恢复；不回退GitHub refs、不卸载/替换已安装工具、不更改真实调度。后续已合并工具的安装与停用计划仍按AC-8/10单独验收。本轮本地验证必须覆盖non-main refs不变、失败拒绝、两次临时FF/no-op、竞态、secret不泄漏与source-guard完整性。

## 接口、数据与兼容性影响

建议操作名github.relay.plan、github.relay.reconcile、github.relay.status，最终实现可在同一语义范围选择一致名字但须同步所有schema/CLI/help/tests。新增relay binding使用受保护的项目命名空间，不能复用Gitea token；不开放任意目的地址写入。不得改现有操作语义或减少安全校验。receipt与状态位于独立项目relay namespace，不复用入站state。

## 风险与回滚约束

安装回滚恢复上一版本化工具，调度关闭阻止新运行；已推进的GitHub main保持。出现目标人工提交或分叉停止，交给人解决，不允许强推修复。source main保护、required CI和公司审批不变。

## 非目标

全仓镜像、其它refs、GitHub PR/Issue镜像、公司bootstrap旧SHA改写、公司CI/部署、Secret生成/扩权、source或destination分支保护调整、Docker/数据库/旧服务操作。

## 未决问题

无会改变已批准行为的未决项。凭据实际可用性和安装/live属于实施后的现场验收，不伪装为已通过。
