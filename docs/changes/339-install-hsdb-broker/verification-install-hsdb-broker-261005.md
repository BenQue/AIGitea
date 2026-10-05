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
status: awaiting-triage
branch: change/339-install-hsdb-broker
created: 2026-10-05
updated: 2026-10-05
---

# #339 Verification · 原窗口STOP/真实baseline恢复

## 授权与时间

人类在本聊天明确回复“同时批准完整执行卡，立即开窗”；已读取总调度聊天原始人类“确认”及其完整scope请求。授权证据在/Users/benque/.codex/visualizations/2026/10/05/01a10bea-8743-7d12-bd55-addf317088bc/t01b-install-execution/authorization-339.json。T0采用更早21:54:55+09:00，原45分钟截止22:39:55；当前窗口已STOP，不重新计时。
原卡与四份文档的获批内容已保留在本聊天approved-documents/、approved-review-card-339.md和approved-issue-body.md。修正版增加准确的installed字段影响，尚未获批准；live Issue标签没有投影approved。

## Phase结果

| Phase | Result | Evidence/边界 |
|---|---|---|
| fresh installed typed fetch | PASS | remote main=c9b5ef4e74592cbc68d6bdc6219568a1d51b6853，sandbox TRANSPORT_ERROR后同typed request host重试 |
| primary exact FF | PASS | e2edb3e08194624a6647212571c6cc866298575b→pin，clean main；没有push/reset/force |
| root source/provenance | PASS，两端 | HEAD=origin/main=pin、main/upstream、clean；子进程safe.directory，无global config |
| fresh before bytes/owner/helper | PASS，两端 | 与旧卡baseline相同；未覆盖其他owner |
| window snapshots | PASS | Mac SHA2cfa3e2623446d9fab5b3be2cd4dd95897711543dff27ffe1aef49b069bdcf62；VM SHA3aec3f3c47709f16c7e793bc2f966027a0ba3753553cc43b9f9545f1b6072af8；34/43公开文件tarheader/hash一致 |
| VM installer 1 | PASS执行 | 22:01:51，exit0，guard level/c9b5ef4/38；不等于整体AC通过 |
| Mac installer 1 | PASS执行 | 22:02:57，exit0，同guard；系统管理员认证，不读取密码 |
| 首次候选26目标/receipt字节和metadata | PASS历史phase | 两端pre-restore.json独立记录；first-install-target-verification.json核全部25目标及生成receipt的SHA/mode/root owner、receipt四摘要/pin/merged_main/helper:null；不替代最终状态 |
| 完整原六仓policy gate | FAIL / STOP | 新增SFMDigitalBoard→AISoftPlatform依赖读取边未在旧卡说明；源字段来自#286；不是runtime安装失败或外部漂移 |
| 同pin installer 2 / 候选HSDB识别 | NOT RUN | 在策略gate STOP，不继续 |
| Mac原生恢复初请求 | TIMEOUT | 60秒后fresh读回仍exact候选，未出现混合状态；随后同scope恢复 |
| Mac真实snapshot restore+八目标清除 | PASS执行 | 22:09:37请求，22:09:45完成，exit0；窗口余量≥30分钟，前45分钟内 |
| VM真实snapshot restore+八目标清除 | PASS执行 | 22:09:45请求，22:09:46完成，exit0 |
| 独立baseline恢复读回 | PASS，两端 | 22:11:31/22:11:32，原字节/mode/root owner/previous链/absence/完整manifests恢复，63/75路径；Mac credential metadata未变 |
| 恢复后installed HSDB原unknown | PASS恢复判据 | 两端exit20 REQUEST_DENIED / requested project is not explicitly managed |
| 演练后同pin再安装/最终七仓 | NOT RUN | 本窗口STOP，不再安装，不自动续期 |
| Secret/账号/helper/服务/其它installer | NOT RUN | 无值读取/修改、无轮换/部署/凭据fallback |
| #339 push/PR/CI/merge | NOT RUN | 仅本地文档及Issue正文 |

核验脚本曾有两个格式判断错误：guard显示短SHA而脚本先要求fullSHA；VM profile name被误用project_id。先有root完整pin证明，随后修正判断，没有借此放宽安装gate。真正STOP原因是上述完整policy差异。错误输出保留，不冒充installer失败。

## 完整静态差异与权限影响

## 实际 installed 与候选的完整共享面差异

比较基线是本窗口两端真实非Secret snapshots，不是旧source SHA。Mac与VM结果相同；逐字段全量比较见 `full-installed-policy-diff.json`。

| 对象 | 实际 installed → exact pin 候选 | 影响/批准边界 |
|---|---|---|
| 原六仓 host项目项 | 仅 `sfm-digital-board/dependency_read_targets` absent → `["aisoft-platform"]` | 新增受管跨仓Issue依赖只读边；原卡遗漏，必须明确纳入修正版范围 |
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

## AC与终态

| AC | Result | 限制 |
|---|---|---|
| AC-1 | 原授权PASS；Revision2增量/新窗口待批准 | 不重复原same-scope审批，不借用原批准覆盖新字段 |
| AC-2 | PASS本窗口source/root前置 | 下次须fresh，不继承永久valid |
| AC-3 | PARTIAL | 固定源/target摘要与receipt局部证据，不作最终installed PASS |
| AC-4 | FAIL / STOP | 原卡policy描述不准确，第二次installer未运行 |
| AC-5 | GAP / NOT RUN | 当前恢复六仓，HSDB unknown；候选识别/access未运行 |
| AC-6 | NOT COMPLETE | 真实安全restore子项PASS；计划两次/restore/reinstall/最终七仓闭环未完成 |
| AC-7 | NOT RUN | T01B未complete，T02仍WAITING_DEPENDENCY |

当前source primary clean main pin；两端installed均恢复baseline六仓36，无helper/receipt/新增operator，原previous链和absence匹配。previous installed source SHA仍NOT VERIFIED。#337保持closed，#333/#327/#336归属不动；provider=none，不恢复任何暂停监控。
下一步仅提交Revision2给总调度审阅；新45分钟窗口尚未开启。新事实/新main需重审，不在旧窗口自动重试。证据目录：/Users/benque/.codex/visualizations/2026/10/05/01a10bea-8743-7d12-bd55-addf317088bc/t01b-install-execution。
