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
reason: 本机共享 system broker 安装和完整恢复涉及安全、共享核心及平台运维，强制 complex/manual。
override_reason: ''
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-mac-broker-install-acceptance-261017.md
  spec: spec-mac-broker-install-acceptance-261017.md
  plan: plan-mac-broker-install-acceptance-261017.md
  verification: verification-mac-broker-install-acceptance-261017.md
pr_url:
---

# #362 Mac system broker 固定版本安装与验收

当前运维结果 **INSTALLED_ACCEPTANCE_PASS**。本人终端P0–P6全部通过，原owner已完成既定有界独立核验；最终停在固定pin一致的新版本。根调度已逐一RELEASE并取得全员ACK，05:08:37 UTC解除完成；当前准备唯一manual文档PR，本票未发表。

唯一owner/session `01a1457e-699f-7372-8b6a-7a21d613d407`；branch `change/362-mac-broker-install-acceptance`，WT `/private/tmp/issue-362-mac-broker-install-acceptance`；claim last_push_head=null。

## 问题/需求总结

#360/PR361已交付canonical模板scope修复，原Mac system broker仍有2模块及公开metadata未更新。本票执行直接人类已批准的独立工具运维整包，安装来源固定为已合并 `06afadfca2a950ad6ebee4b90a22e9d950bc72fa`，不消费本票文档HEAD。

## 影响范围

既有 `codex/install-host-access-broker.sh`，SHA256 `485ea19514c5f4b72c84d6cc9576fe0c2b65c34d084e74c8f80e2d6ad6f10897`。
受控闭包为27静态文件、1公开metadata、有限previous/absence及目录/临时metadata。没有installer/runtime/manifest/权限政策或AGENTS修改；本票Git提交仅四语义文档及runbook，附属证据在本会话artifact。

## 已完成的实际验收

- human:benque在同一私密Mac终端以原生sudo完成P0–P6；根调度及已识别调用者实际ACK/HOLD，没有以marker声称OS隔离。
- 27文件字节、root:wheel、mode/type/link、metadata exact pin/helper=null、完整previous/absence通过。P1=P3=P5=当前独立读回的完整记录。
- 同pin真实no-op通过；完整restore与写前43文件/13absence/10目录owner-mode-type相等，旧资格返回BROKER_SURFACE_GAP。
- 同pin再安装后actual canonical HSDB、holder=True、context.verify通过；broker-only focused drift为39 operations /27 files /0 GAP。
- F1/F2原实测2项PASS，独占fixture根已清理；未对真实系统单文件造故障、调用live mutation验闸门或安装依赖。

真实总回执 `manual-execution-receipt.json` SHA256 `941a0871b522de091ae5a08d3d85df27898957acdc5207b6858f791ed6b380c7`。
独立验收 `independent-acceptance-362.json` 位于 `/Users/benque/.codex/visualizations/2026/10/16/01a1457e-699f-7372-8b6a-7a21d613d407/issue-362/`；证据层次与方法见[verification](verification-mac-broker-install-acceptance-261017.md)。

Snapshot保留：`/usr/local/share/aisoft/backups/tools-362-20261017T013941Z/baseline.tar.gz`，SHA256 `00ea2f364a7778e49984791dce5ca5f7784a7434a705e4ab6dc6d7830abefd35`，43公开成员。root归档由本人固定root helper读回，owner比较公开回执并核当前公开目标，不越过root目录权限。
协调保持开始01:13:11 UTC；实际首写01:39:41 UTC；修正后重试开始05:02:53.510354 UTC，终端阶段完成05:03:13.251131 UTC（均2026-10-17）。根调度逐一RELEASE及全员ACK完成时间05:08:37 UTC，公开回执见artifact release-all-acks-362.json。

## 首次失败、恢复和修正

首次P1实际PASS，P2辅助脚本错误硬编码holder=False，和固定canonical默认True矛盾，触发完整恢复PASS。原始失败回执/脚本/分阶段结果在artifact `attempt-20261017T013941Z-failed-p2/` 完整保全；原总回执将P1/P2分组记为NOT RUN与实际P1 JSON PASS的差别如实记录。
只修本票辅助validator和runbook为严格holder=True；错误holder/URL仍拒绝，有限回归通过。同一HOLD窗口只复用原exact snapshot，再次fresh核source/root/baseline后完成P1–P6。本次成功不覆盖第一次失败记录。
[runbook](runbook-mac-broker-install-acceptance-261017.md)保留实际执行版本及其当时说明，SHA256 `ac4338ffe2730f838f189fe11725e53dce949d5118998c8639ca656350a4ba5c`；当前结果以本summary和verification为准。

## 风险与保留边界

Mac user Loop沿用原卡GAP、VM installed NOT READ且当前路径NOT REQUIRED、architecture/lock GAP保留。没有HSDB采用/T04、live/UAT、VM安装、业务服务启停、DB/迁移、Secret/权限、provider/monitor或公司部署。
HSDB#15固定OID/全部资源继续冻结，#32/T06 PAUSED，IMPLEMENT_PROVIDER=none；RELEASE不增加业务授权。#360保持closed/completed，不恢复旧WT/branch/claim。
本票未push/PR/merge。正式classification此前读回projected：type/platform、complexity/complex；RELEASE后最终判级已fresh读回projected，main保护/required CI保持；manual提交确认与人类merge仍保留。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 本机共享 system broker 安装和完整恢复涉及安全、共享核心及平台运维，强制 complex/manual。
risk_flags:
  - security
  - shared-core
  - deployment
  - rollback
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

本机共享工具真实root安装和恢复，属于强制complex/manual；不把本票文档或source/CI当作installed证明，installed由本人执行和原owner独立有界核验分证。

### 缺失的 acceptance criteria 或决策

无新业务决策。全部运维AC已完成；协调RELEASE已完成；最终本地候选验证后一次请求manual最终PR提交确认。

## 最终PR候选边界

Policy manual；Issue保持open/approved，尚无本票push/PR/merge。RELEASE后formal source/main仍为固定pin，classification fresh readback projected；main push/force禁用、merge allowlist仅admin、required CI为 `CI / verify (pull_request)`。PR未创建，因此PR CI为NOT RUN；本地文档检查不冒充CI。
