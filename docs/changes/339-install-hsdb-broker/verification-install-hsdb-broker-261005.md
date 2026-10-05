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
status: contract-drafting
branch: change/339-install-hsdb-broker
created: 2026-10-05
updated: 2026-10-05
---

# #339 Verification

## 基线与范围

source pin：c9b5ef4e74592cbc68d6bdc6219568a1d51b6853；source PR #338 final head 45857164a29525d2921fee5beace82afeaed0af0。
本票branch=change/339-install-hsdb-broker，worktree=/private/tmp/issue-339-install-hsdb-broker，owner=01a10bea-8743-7d12-bd55-addf317088bc。
本轮只授权tracking/contract准备。IMPLEMENT_PROVIDER=none，未新增字段或配置。

## 执行结果

| Check | Result | Evidence |
|---|---|---|
| source required PR CI | PASS，继承总调度独立读回 | CI / verify (pull_request)，run1783/job1989；不是#339 CI或独立main workflow |
| fresh source pin与primary | PASS/GAP | prior final-preflight.json；primary clean e2edb3e…、未FF |
| 两端installed before-state | GAP | 各六仓/36操作；hsdb两端exit20 unknown-project；metadata/hash已fresh验证 |
| canonical credential metadata | PASS，仅metadata | projects/hsdb/project-agent.token，0600；未读值，未验证有效性 |
| account state | GAP | 上次prohibit_login=true是历史；本轮未fresh account API |
| Mac snapshot完整性/artifact回放 | PASS | SHA256 f072bca05787305d2721fcec4dc896890f3584d4e28e61045488ba51b6fc4831 |
| VM snapshot完整性/artifact回放 | PASS | SHA256 9170fec5f029680aa39eaf0b849c6a0bf37daeb3bf1f2f8c062099543543adce |
| 实际#339创建与正文合同发布 | PASS：独立fresh读取与发布body同字节 | fixed installed broker entry triage/needs-triage；不创建approved |
| 四角色文档/判级/owner checks | PASS：changes=157/gap=0，四角色resolver、Classification与Ticket graph有效，owner marker匹配 | 可解析/本地准备不是人类安装签署 |
| root installer第1/第2次 | NOT RUN | 安装未授权 |
| 真实snapshot restore/同pin再安装闭环 | NOT RUN | 无故障注入；snapshot回放不是root恢复/最终七仓 |
| #339 PR/CI/manual merge | NOT RUN | 本轮未push或开PR |
| 账号/PAT/Secret/profile/protection/部署 | NOT RUN | 未获本票授权 |

## Acceptance criteria 结果

| AC | 结论 | 限制 |
|---|---|---|
| AC-1 | GAP | actual Issue/tuple/owner已准备；具体安装scope尚未确认，执行方式/窗口是proposal |
| AC-2 | GAP / NOT RUN | source pin已fresh，但primary未FF，rootguard安装前证据未执行 |
| AC-3 | NOT RUN | 未实际安装 |
| AC-4 | NOT RUN | source不变量检查PASS，不替代installed两次验收 |
| AC-5 | GAP / NOT RUN | installed仍unknown；account/credential/onboarding未恢复 |
| AC-6 | NOT RUN | 快照完整性及artifact回放PASS，真实root恢复及同pin再安装闭环未执行 |
| AC-7 | NOT RUN | 总调度T01仍未complete，T02仍WAITING_DEPENDENCY |

## 遗留风险与未完成项

本票current pin变化、helper/receipt新声明、任何owner冲突即STOP。previous installed source SHA NOT VERIFIED，不用部分字节或旧.previous反推整套provenance。
实际operator建议由本T01B聊天执行，OS身份benque/sudo，授权者是人类用户；没有适用条款要求新增一名现场人工人名。
建议确认后45分钟，planned restore/reinstall/readback在45分钟内；演练前至少保留30分钟，不足不开始。意外baseline恢复另有≤15分钟，不能过期再安装；均未批准，确认后才记精确Asia/Tokyo时间。
安装/恢复方法、允许动作/source FF及人类确认需绑定本票；任何README/spec/CI存在不证明installed/live/UAT。

证据目录：[t01b-install-preflight](/Users/benque/.codex/visualizations/2026/10/05/01a10bea-8743-7d12-bd55-addf317088bc/t01b-install-preflight)，本轮tracking/publish/owner/文档check回执在：[t01b-install-issue](/Users/benque/.codex/visualizations/2026/10/05/01a10bea-8743-7d12-bd55-addf317088bc/t01b-install-issue)。
