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
status: contract-drafting
branch: change/292-github-main-relay
created: 2026-09-11
updated: 2026-09-11
---

# 实施计划

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 独立合同步骤：本票四份映射文档与范围对齐，无runtime修改 | - | completed |
| T02 | typed main relay plan/reconcile/status、绑定与协商OID门、确定性测试 | T01 | pending |
| T03 | 版本化安装与项目调度、脱敏receipt及失败关闭回归 | T02 | pending |
| T04 | 完整回归、一次最终PR与人工合并 | T03 | pending |
| T05 | exact merged install、必要用户认证、两次live执行及调度验收 | T04 | pending |

## Expected touch points

T01：docs/changes/292-github-main-relay/{summary,spec,plan,verification}-github-main-relay-260911.md。

T02：codex/runtime/aisoft_host_access/{broker,contract,cli}.py，新增github_relay.py及固定pre-push验证入口，codex/config/host-access-broker.json，必要严格relay binding schema，codex/runtime/tests/test_host_access_broker.py及新增test_github_relay.py。先核实际测试文件路径，不因提示路径不同另建重复测试体系。Gitea访问复用现有broker；GitHub的独立adapter只可从typed路由进入。

T03：codex/install-host-access-broker.sh及其测试、versioned macOS launchd模板/installer与tests、必要source-guard inventory、README与06相关小节。template内容不能使用任意shell/script参数，默认不启用。允许新增专用安装入口，但必须受相同provenance guard、无凭据副作用；不得新增第二套通用权限broker。

T04：仅范围内smoke/回归与文档验证修复，不修改AGENTS.md、既有workflow、CI context、其它项目配置、inbound runtime或其它历史证据。PR manual最终门不可由本票授权代替。

T05：仅merged exact source实际安装与绑定/项目调度，凭据由人本地输入；私有现场回执留项目私有总控，平台仅汇总非敏感结果。若需新权限超出目标仓库Contents写入须停止，而不是扩大token。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1/2/5/6 | 新relay unittest与broker strict-contract/credential regression |
| AC-3/4/9 | 临时真实bare repos与阻塞/竞态fixture，验证push协商OID gate、无非main变化 |
| AC-7 | 原子receipt、readback失败、脱敏测试 |
| AC-8 | installer source provenance及调度disabled默认/stop幂等测试 |
| AC-10 | merged工具hash→现场FF→no-op→调度触发元数据与独立GitHub读回 |

改shell必须bash -n与ShellCheck（如可用）；执行bash codex/tests/smoke.sh。按仓库现有方式运行Python全部相关单元测试及check-change-documents、git diff --check。测试命令在实施确认工具入口后写入verification，不宣称未跑PASS。

## 部署与回滚

此为开发侧版本化工具/调度安装，不是公司应用部署。两次live reconcile及一次本地拒绝故障证明对应AC-9/10。需要人工合并后才能安装；自动同步操作范围已获批，不重复启动确认。仅缺失认证输入或明确范围扩张时请求一次具体动作。停用scheduler后读取disabled且无新执行，保持所有远端refs。
