---
issue: 339
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/339
change_type: security
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
  - 337
status: approved
branch: change/339-install-hsdb-broker
created: 2026-10-05
updated: 2026-10-05
---

# #339 Verification · Revision 2 新窗口完整安装/恢复/再安装

# #339 Revision 2 安装与真实恢复验收结果

**INSTALLED_ACCEPTANCE_PASS**。source pin/current main：c9b5ef4e74592cbc68d6bdc6219568a1d51b6853；provider保持none。唯一owner 01a10bea-8743-7d12-bd55-addf317088bc；branch/worktree change/339-install-hsdb-broker / /private/tmp/issue-339-install-hsdb-broker。

人类直接批准Revision2增量范围及新窗口；同时fresh读回总调度原始“确认批准”和绑定的卡/旧文档head/body。采用更早T0=2026-10-05T22:44:23+09:00，计划截止23:29:23，限定意外恢复截止23:44:23。实际root闭环及最终读取完成22:55:38，未使用延长。
两端source root clean main/upstream/完整pin、即时baseline、helper/receipt和新snapshots均PASS；VM→Mac首次/第二次installer exit0，第二次no-op；独立26目标/root mode-owner/receipt/七仓38/三VM profiles/已批准policy变化均PASS。
planned restore于22:55:17开始，尚余2045.90052秒（34分05.9秒）≥30分钟。Mac/VM分别22:55:28真实恢复并清除已核本候选新建的八目标；独立读取原字节/mode/uid/gid/previous链/absence、六仓36、原SFMDigitalBoard字段absence和原HSDB unknown全部PASS。随后同pin VM→Mac再安装，22:55:37最终26目标/receipt/七仓38全部PASS，与第二次安装状态完全一致。

| 结果层 | 结论 | 限制 |
|---|---|---|
| source/current main | PASS | final installed typed fetch后HEAD=origin/main=pin、clean；源码未改，本票文档不冒充source main |
| 两端installed 26目标与receipt | PASS | 全SHA/mode/root uid-gid、source_sha、merged_main=true、四公开目标摘要、helper:null |
| 同pin两次/no-op | PASS | 两端second output及独立字节/权限/previous链相同 |
| 真实baseline restore | PASS | 新快照真实root恢复；63/75 inventory路径、34/43归档文件；absence/previous链完整 |
| 同pin再安装/最终七仓38 | PASS | 最终与second-install状态相同，精确三VM profiles，HSDB vm_profile:null |
| HSDB注册解析 | PASS | 两端installed三个typed只读操作不再unknown-project |
| repo/access/onboarding | GAP | 两端各三操作均exit20 HTTP_401 / Gitea returned HTTP 401，不把它写成access PASS |
| account/PAT根因 | GAP | HTTP401不足以区分账号停用/过期或无效token；未fallback/启用/替换/轮换 |
| rotation helper capability | NOT VERIFIED | helper:null，无PAT helper artifact，无rotation/grant调用 |
| previous installed source SHA | NOT VERIFIED | 真实snapshots证明observed-byte基线，不反推历史merged SHA |
| 应用部署/UAT/公司现场 | NOT RUN | 不属本票 |
| #339 push/PR/CI/manual merge | NOT RUN | 文档最终PR仍需独立既定门禁 |

本窗口VM snapshot SHA256：bda1e3a2c66b54c79e84860455dfe990dd1abd21d21890336b8feea136b30218；Mac：755cd5c241684b58c10f99f0e4312a4dba6b66688912b7e84ae00406356677cb。均为本窗口新归档，没有复用旧压缩包。
凭据metadata与baseline相同，未手工读取/输出值；固定installed broker仅在授权只读验收中内部使用受保护credential。没有Secret/账号/helper/grant/profile/protection/binding/labels/service/timer/provider/routine/其它installer/应用部署变更，没有push/PR/merge，没有恢复暂停监控。

机读handoff及全部phase原始证据：/Users/benque/.codex/visualizations/2026/10/05/01a10bea-8743-7d12-bd55-addf317088bc/t01b-install-execution/window-2/handoff-339.json、phases.jsonl、两端install-1/install-2/restore/reinstall.json、before/restored/final.json、final-acceptance.json和registration-final*.json。原窗口STOP和获批Revision2文本分别完整保留，不将历史失败写成通过。
T01B安装技术AC-1至AC-6 PASS；AC-7总调度fresh独立核验PASS，已于2026-10-05T23:08:43+09:00单独激活T02。本owner只回填其证据，不实施T02；本票文档交付、最终PR与收尾尚未完成。

## 总调度退出证据

本轮fresh读取总调度`调度台账.json`：T01 logical_stage_complete=true，T01B technical exit PASS，T02 status=ACTIVATED，dispatch时间2026-10-05T23:08:43+09:00。总调度独立核对两端25固定目标及receipt、root bytes/mode/owner、全部安装/恢复/再安装阶段与快照，阶段审计pass=true。本聊天未代其激活或实施T02。证据副本及原始文件hash见`/Users/benque/.codex/visualizations/2026/10/05/01a10bea-8743-7d12-bd55-addf317088bc/t01b-install-delivery/coordinator-exit-readback-339.json`；窗口内HTTP_401 GAP保留为带时间的访问证据，不反映或替代T02后续结果。

## 完整安装policy差异

## 已批准并验证的完整共享面差异

比较基线是本窗口两端真实非Secret snapshots，不是旧source SHA。Mac与VM结果相同；逐字段全量比较见 `full-installed-policy-diff.json`。

| 对象 | 实际 installed → exact pin 候选 | 影响/批准边界 |
|---|---|---|
| 原六仓 host项目项 | 仅 `sfm-digital-board/dependency_read_targets` absent → `["aisoft-platform"]` | Revision2已明确批准；installed目标字节及manifest已核验，新操作未实际调用 |
| 原36项 operations | 全部定义同字节/同字段，无删除或更改 | 既有操作声明保持 |
| 新operations | `gitea.dependency.read`：manager-audit、mutating=false、reference；`gitea.credential.rotate`：credential-operator | 安装声明；本票不调用这两项 |
| host顶层 | 新增 `credential_rotation_policy` | UID0、固定grant/receipt/helper/operator/Gitea路径和Gitea1.26.4约束；不创建grant/Secret、不启用轮换 |
| 原六仓 governance | 仅 NewEMaint `routine_live_pilot/non_target_repositories_sha256`：4969422f72782de90155881cc4a92720dfd1ee5f468e940bd30ac7a666b0df85 → d45a20abb3224a5e02b1e22c338429017c9ff88d80fd5fc597bffb97a90e9334 | HSDB加入非目标集合后的seal重pin；routine policy和启用状态不变 |
| 新项目/仓库 | host `hsdb`、governance `HSDB` | Mac-only、vm_profile:null |
| labels / 其它顶层 / 其余原六仓字段 | 全部相同 | 无其它遗漏或删除 |
| VM profiles | 精确 aisoft-platform/localwms/emaintenance；newemaint是project_id，emaintenance是profile name | HSDB不进入VM profile；保留IMPLEMENT_PROVIDER=none |

字段来源：`f98c90ee0a34aa2c90b217c1c69a29b3be8386a7`，`feat(#286 T02): resolve manifest-bound dependency references through audit reads`。它在旧source e2edb3e已存在，但两端实际installed尚未包含，所以相对旧source无变化不能推出相对installed无变化。
源码 `resolve_target()` 只允许canonical owner/受管repo及显式source→target edge；`_read_dependency()` 用manager-audit，要求精确非site-admin身份、禁止redirect、限制response大小；返回repository/number/reference/state/labels，不返回Issue正文。这个字段不增加sfm-board-agent的Gitea collaborator权限、Git写入或merge/deploy授权，但确实新增broker允许的跨仓只读边，因此不能继续宣称原六仓policy完全不变。
本窗口没有实际调用SFMDigitalBoard依赖读取，也没有调用credential rotation；上述影响来自exact pin源码和manifest，不冒充live capability验收。


## 证据层与未运行检查

源码required PR CI run1783/job1989（CI / verify (pull_request)）来自#337已合并source历史；不是#339 CI或独立main workflow。source/runtime/shell脚本零改动，本票没有重跑源码smoke或ShellCheck；已版本化installer的真实两次/root恢复/再安装和独立installed比对是本票验收。文档resolver/classification/ticket graph/diff检查与Issue正文fresh一致性另存final-checks，不提升为installed/API/UAT证明。
原窗口遗漏scope后STOP/真实恢复保留在上级目录；本窗口user明确批准Revision2后fresh重备份/执行，未静默重启旧窗口。没有将先前NOT RUN回填为历史PASS。
旧安装source SHA仍未知；当前installed receipt精确pin/merged_main成立，但helper:null仍不证明轮换capability。HTTP401原因未区分，未调用admin/备用凭据修复。
