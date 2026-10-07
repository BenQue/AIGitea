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

## 当前源码验收结果（T04，2026-10-07）

T01–T04 的 source 实施和本地验证已完成，唯一最终 PR 候选等待第二确认。Issue 仍为 `approved`，尚未 push 或创建 PR。完整默认 smoke 检查对象为代码 SHA `a0731966350cb20ea4805623298ecd22004776f1`；之后仅回填本 Change 的文档和证据，最终 HEAD 在提交卡与 Issue 状态读回中记录。

| 验证 | 结果与范围 |
|---|---|
| `bash codex/tests/smoke.sh`（host 执行，无缩减参数） | PASS，exit 0；runtime 1,241 tests、installed-drift 35 tests、release 197 tests 及默认 shell/安装 fixture 全部通过 |
| `PYTHONPATH=codex/runtime python3 -m unittest tests.test_controller` | PASS，48 tests；人工门、唯一 PR、正文证据、空 report 和 optional failure 均覆盖 |
| `PYTHONPATH=codex/runtime python3 -m unittest tests.test_matt_install` | PASS，9 tests；真实安装入口、升级/幂等/回滚、所有权冲突、故障恢复和参数拒绝 |
| 变更 shell 的 `bash -n` / ShellCheck | PASS；完整 smoke 同时执行原有 shell 硬门 |
| 固定上游 blob / manifest / 旧 release 与 AGENTS 范围 | PASS；109 个上游文件、37 个技能；旧 v1.2.2 与 AGENTS.md 无改动 |
| provider 静态调用策略、明确来源及重名检查 | PASS；Codex 元数据与 Claude front matter 分别检查；不等于实际会话执行 |
| 真实 HOME 只读安装预检与旧受管目录哈希 | PASS，仅只读；current=v1.2.2，35/35；独立 Codex/Claude plugin metadata 均为 v1.2.3 |
| final Issue 分类读回 | PASS，`projected`：type/platform、complexity/complex；approved 保持 |
| fresh main / PR namespace / protection | PASS；main=`11628709e659dac48f5cb66bade81f1617974546`，开放 PR 为空；禁直推/force、required CI 与人工 merge 保持 |
| 新版真实 provider fresh session | GAP / NOT RUN；source 静态策略不证明会话实际发现或调用 |
| push / PR / required CI / merge / 真实全局或 VM 安装 / live | NOT RUN；不由本地 smoke 推导 |

完整 smoke 最初在 sandbox 中因本地 HTTP fixture 的 `s.bind(("127.0.0.1", 0))` 报 `PermissionError: [Errno 1] Operation not permitted` 而退出 1，记录为环境阻塞。原默认命令经 host 权限重跑后 PASS，未删测试或添加 skip。收尾检查另发现单独传入 `--rollback` 可能被解释成目标目录，已显式拒绝并添加无写入断言，随后完整 smoke 验证上述最终代码 SHA。详细收据见 [T04 evidence](evidence/t04-final-validation.json)。默认 smoke 内既有 real Docker/现场 E2E 未运行边界照实保留，不作为本票真实部署证据。

## Before

- T01 核验的 main 为 `11628709e659dac48f5cb66bade81f1617974546`。平台固定 v1.2.2，真实受管安装的 35/35 目录哈希匹配；这是旧版本完整性证据。
- 该基线的 Controller PR 正文经 source inspection 确认缺少具体 Before/After、回滚和影响范围；未运行一个旧版失败测试来冒充基线结果。
- domain 配置仍采用 CONTEXT，根目录没有 glossary；旧锁文件和独立 gstack retro 需要明确归属。只读观察详见 T01/T02 收据。

## After

- v1.3.1 的固定 commit 为 `24fe0ef7737efae15c87225755e9f6f5965e4888`，完整 37 技能；新上游原文字节不变，旧 v1.2.2 保留。
- 隔离 HOME 中真实 installer 验证首次安装、升级、重复、入口退役、故障恢复与 N-1 回滚；不覆盖独立 gstack/Claude fixture，不改旧锁文件。普通异常恢复已验证，不宣称进程强杀或掉电事务恢复。
- Controller 使用真实 report 与 SHA 生成候选；缺少 Before、空 report、optional failure 均诚实显示，授权 marker、唯一 Closes、人工门和现有 schema 保持。
- GLOSSARY/旧 CONTEXT 兼容、Matt retro 显式来源与人工会话范围、implement-spec 写入编排禁用均落入平台 adapter/模板。未批量迁移下游文件。
- full smoke 覆盖的代码 SHA 为 `a0731966350cb20ea4805623298ecd22004776f1`。真实主机仍为旧安装；source/local 与 CI/installed/live 分开验收。

## Acceptance criteria 最终 source review

| AC | 结论 | 证据与边界 |
|---|---|---|
| AC-1 | PASS | 37 技能完整 manifest、109 固定 blob、tag/commit/license 校对；旧快照未改 |
| AC-2 | PASS | 9 个 installer tests 与完整 smoke；isolated HOME、owned links、普通异常恢复、N-1 回滚，不触碰真实安装 |
| AC-3 | PASS | domain 与模板一致、最小 glossary/相对引用检查、规则及 ADR 保全规则审查；没有自动迁移器或下游改写，历史规则未删除 |
| AC-4 | PASS | 48 个 Controller tests；具体正文、真实/缺失证据、SHA、回滚范围、machine fields 与确认恢复 |
| AC-5 | PARTIAL | 两 provider 静态 metadata、明确 source 路径及 gstack 消歧 PASS；真实 fresh-session conformance 为 GAP / NOT RUN，按 spec 保留独立验收 |
| AC-6 | PASS（source） | adapter/manual invocation 元数据与合同审查；既有 Controller gates 回归通过；真实 LLM 行为不由静态检查证明 |
| AC-7 | PASS | 默认完整 smoke、focused checks、bash-n/ShellCheck、resolver/audit 与 source parity；未弱化断言 |
| AC-8 | PASS（source handoff） | 逐层标注、exact branch/manual 提交卡和安装独立边界；PR/CI/merge/现场安装仍 NOT RUN |

## 遗留事项与交付边界

待用户确认提交唯一最终 PR 后，才由既有 Controller/broker 发表当前 exact branch、创建 PR 并处理合同内 CI；required CI 全绿后等待用户人工合并。平台全局受管技能实际仍为 v1.2.2，独立两个 provider plugin 为 v1.2.3。合并后的实际升级须另有固定 source/target、备份、回滚及 fresh-session 读回验收；本票当前没有安装结果。

以下 T01/T02/T03 为历史阶段记录。各阶段的 NOT RUN 或初次失败保留时间含义，当前 source 结论以上方 T04 和分层边界为准。

## T01 历史基线与范围

- 日期：2026-10-07（Asia/Tokyo）。
- 基线：fresh `origin/main` 与主工作区 HEAD 均为 `11628709e659dac48f5cb66bade81f1617974546`。
- 单写者：`01a11682-fafc-70c1-80f2-a5d0d470bca1`；worktree 为 `/private/tmp/issue-352-matt-skills-upgrade`。
- T01 当轮只证明合同、归属、来源、范围和文档校验，不证明新版 runtime、CI 或安装。
- 批准来自本会话用户的“批准你的建议”；前一轮审查卡明确 v1.3.1、术语兼容、PR 证据、人工 retro、保留 Controller。

## T01 历史执行结果

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

## T01 历史 Acceptance criteria 结果

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

## T01 历史停止点

T01 时实际安装为 v1.2.2，独立 Claude 插件记录为 v1.2.3。gstack retro 与旧 skills.sh 的归属处理当时安排在 T02。

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

## T03 PR 证据生成（2026-10-07）

Controller 的初次候选与 PR 创建都生成 Summary / Evidence / Merge Danger，保留唯一 Closes、
语义文档、依赖、authorization marker 与 policy。候选正文使用实际 verifier 结果和 exact SHA；
跨确认恢复复用已有 candidate_head_sha 的已验证事实，并明确未重跑，未新增持久 schema。
回滚与影响范围来自映射合同，缺失信息明示；不会把 optional failure 或空 report 写成全部 PASS。

`PYTHONPATH=codex/runtime python3 -m unittest tests.test_controller`：PASS，48 tests。
初次回归发现 legacy small 的 resolver 会返回尚未要求存在的可选文档；已仅载入 required 或实际存在的
映射文件，保留 required 文档硬门。回归同时覆盖人工确认的等待/恢复、routine 路径、唯一 PR、
正文防重复 Closes/marker、脱敏、真实失败与缺证显示。默认完整 smoke 和远端 CI 尚待后续阶段。
