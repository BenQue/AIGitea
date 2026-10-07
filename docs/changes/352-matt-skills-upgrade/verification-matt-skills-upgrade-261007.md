---
issue: 352
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/352
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
  - shared-core
  - rollback
  - external-contract
depends_on: []
status: in-progress
branch: change/352-matt-skills-upgrade
created: 2026-10-07
updated: 2026-10-07
---

# #352 验证记录

## 基线与范围

- 日期：2026-10-07（Asia/Tokyo）。
- 基线：fresh `origin/main` 与主工作区 HEAD 均为 `11628709e659dac48f5cb66bade81f1617974546`。
- 单写者：`01a11682-fafc-70c1-80f2-a5d0d470bca1`；worktree 为 `/private/tmp/issue-352-matt-skills-upgrade`。
- 本轮只证明 T01 合同、归属、来源、范围和文档校验，不证明新版 runtime、CI 或安装。
- 批准来自本会话用户的“批准你的建议”；前一轮审查卡明确 v1.3.1、术语兼容、PR 证据、人工 retro、保留 Controller。

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| sandbox broker issue.list / repo.read | BLOCKED_EXTERNAL | 原错误为 TRANSPORT_ERROR；不据此判断凭据或对象 |
| 同操作 host retry | PASS | issue.list：开放 Issue 0；repo.read：admin/aisoft-platform、main、未归档 |
| broker git.fetch.main | PASS | manifest remote 为 origin；exact main 如上 |
| broker gitea.protection.read | PASS | enable_push=false、enable_force_push=false、仅 admin merge、required CI 为 CI / verify (pull_request) |
| broker gitea.issue.create | PASS | #352，needs-analysis 在创建时写入 |
| exact worktree / claim-worktree | PASS | issue=352，branch/session/worktree 一致，last_push_head=null |
| 当前平台 v1.2.2 snapshot / 本机 35 个受管目录 | PASS | 本轮重新运行 verify_snapshot 与目录哈希校对；35/35 匹配，仅证明旧安装完整性 |
| v1.3.1 隔离候选 provenance / classify_update | PASS | 本轮重新校对 37 技能、109 个 exact commit blob；分类 complex |
| T01 文档 resolver / required-docs / 仓库文档审计 | PASS | 四角色映射完整；check-change-documents：changes=161、pass=2、gap=0 |
| T01 contract / graph / 相对链接 / 归属 / 精确范围 | PASS | 真实 #352 读回加载 8 项 AC；T01 完成后 frontier=T02；仅本 Change 文档及 evidence；见本地提交前收据 |
| Issue classification / lifecycle 投影与读回 | PASS | apply-classification --apply 后独立 --verify；broker 读回 approved、complexity/complex、type/platform |
| v1.3.1 installer、runtime、PR fixture、完整 smoke | NOT RUN | 后续 T02/T03/T04 |
| 新 provider session、全局/VM 安装、Claude 插件更新 | NOT RUN | 未执行；各层独立验收 |
| push / PR / CI / merge | NOT RUN | 未取得最终 PR 第二确认 |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | PARTIAL | 仅隔离候选来源通过；新 vendor 尚未写入仓库 |
| AC-2 | NOT RUN | installer 与回滚尚未实施 |
| AC-3 | NOT RUN | 新模板/词汇表与迁移兼容尚未实施 |
| AC-4 | NOT RUN | PR 正文通路尚未实施 |
| AC-5 | NOT RUN | provider 实际加载与重名消歧尚未验收 |
| AC-6 | PARTIAL | 已固定禁止越权的合同；source adapter 待实现 |
| AC-7 | NOT RUN | 本轮文档检查不替代后续 source 完整测试 |
| AC-8 | PARTIAL | 证据层次和人工门已固定，最终交付未发生 |

## 遗留风险与未完成项

当前实际安装仍为 v1.2.2。独立 Claude 插件记录为 v1.2.3，不在本次自动更新范围。gstack retro 与旧 skills.sh 记录的归属风险必须由 T02 处理。

本地提交前检查及版本哈希收据保存在 [T01 evidence](evidence/t01-preflight.json)。本提交只封存治理合同；最终 commit SHA 和 clean 读回在 Issue 与会话 handoff 中记录，避免把未生成的 SHA 写成本提交的证据。

T01 治理文档已经完成，本地提交成功后按治理规则 STOP。下一 fresh run 继续 T02；同一批准范围不再确认。source 未完成，不请求 push/PR，也不将本轮文档 commit 描述为升级完成。

## T02 源码与隔离安装验收（2026-10-07）

已引入完整 v1.3.1 的 109 个经固定 Git blob 校对的上游文件及 manifest，保留 v1.2.2。
真实 installer 在隔离 HOME 中通过首次、升级、重复、退役入口、失败恢复和 N-1 回滚验证；
新旧快照、旧锁文件、gstack 和独立 Claude 插件均按 ownership 边界处理。

| 验证 | 结果 |
|---|---|
| Matt snapshot/install 与 repository adapter focused tests | PASS，20 tests |
| installed-drift 八安装面 fixture | PASS，35 tests |
| install-skills shell / agent-runtime mock | PASS |
| bash-n / ShellCheck（3 个变更 shell） | PASS |
| source-only drift / 文档 audit | PASS，8 surfaces / 161 Changes |
| 新版真实 provider 会话 / 全局与 VM 安装 | NOT RUN |
| 默认完整 smoke | NOT RUN，T04 执行 |

初次失败已保留在 [T02 收据](evidence/t02-source-validation.json)：失败注入未命中临时目录别名，
已改用 canonical path；漂移检查曾把 Python helper 混入八个 installer 集合，导致
`installer-set-mismatch`，已拆分 helper pin，完整集合与字节硬门保持。两项均重新验证通过。

安装器提取了 Python 激活逻辑，因此既有 drift checker 同步固定 helper/installer/manifest 的 hash，
并验证旧受管链接退役；该维护服务于 AC-2/AC-7，不引入新安装面或扩大主机权限。
GLOSSARY 和 CONTEXT 兼容规则经人工审查，未迁移任何下游文档；两 provider 静态元数据与加载路径
可核验，真实会话发现/执行仍为 GAP/NOT RUN。T03 将继续 PR 证据生成。
