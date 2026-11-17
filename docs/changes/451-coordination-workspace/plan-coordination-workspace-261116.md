---
issue: 451
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/451
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
depends_on: []
branch: change/451-coordination-workspace
created: 2026-11-16
updated: 2026-11-16
---

# Plan：跨项目协调工作区的平台最小适配

## 全局约束与接口

- 唯一执行合同是本 plan 的 Txx。provider 为 claude，路由 R3：frontier/max、spec-plan、full+reverse-proof、cross-provider、confirm 2，具体 skills 为 to-spec, to-tickets, executing-plans, verification-before-completion。
- exact worktree、owner、change_base `c14a86d4ad0d1fd5938ab31343f8d72acd486a71`、全部 git_scope 与冻结候选见 spec。同一时刻只有一个写者，按依赖 frontier 执行，不 reset、不重写历史、不进入别的会话的 worktree（包括 #450 的 `/private/tmp/issue-450-engineering-principles`）。
- 负责人已确认的 D1–D6 与 Home 参数是合同输入，执行中不再询问。ticket、测试命令、本地 commit 与普通修复都不是确认点；合同冲突或范围扩张按既有规则升级。
- T01 是治理步骤：独立 commit 后 STOP。T02 必须由 fresh run 重读批准合同、治理 diff、当前规则与 owner/branch/HEAD 后恢复；同一线程里的普通工具调用或上下文压缩不算 fresh run。
- Txx 是唯一任务身份；`prepare-ticket` 生成的 Task N 只是派生视图。SP 路径不承担 Matt 的逐票双轴审查，最终整批交叉审查保留。
- 最终独立审查由未参与实现的 Codex 只读会话承担，经 Herdr 官方 CLI 在可见的独立会话里进行，模型 GPT-6-Astra、推理强度 high，记录实际生效的型号、强度、BASE/HEAD 与完成状态。审查者不写 worktree。登录、信任与权限提示由负责人处理。Herdr 或权限不可用时报告具体障碍，不改用不可见的会话。
- 隔离导出只写本票新建的临时目录，不碰真实 HOME，不安装，不 adopt。远端只走 broker；确认点 2 之前不 push、不建 PR。
- required CI 以 governance manifest 的 `CI / verify (pull_request)` 为准；本地 smoke 不代表远端 CI 通过。

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 合同钉子测试先红后绿，冻结文字精确应用，使用包追加一个版本，形成可回退的治理候选并停止 | - | done |
| T02 | fresh run 完成整批验证、隔离导出比对、反向证明、判级投影、独立交叉审查与证据，形成最终 PR 候选 | T01 | pending |

## T01：受控应用冻结文字与发布登记

- **交付/范围**：在 `codex/runtime/tests/test_session_contract.py` 增加一组钉子并看它失败；应用本票冻结补丁到四份技能文件；用现有工具在 `usage/bundle.json` 追加版本；记录证据。不改模板、适配器、runtime、安装面或 spec 不纳入清单里的任何文件。
- **blocked_by**：无。
- **AC**：AC-1、AC-2、AC-3、AC-4、AC-5、AC-6，以及 AC-7 的发布登记部分、AC-8 的受控治理步骤部分。
- **接口/约束**：开始前运行 `bash codex/tools/aisoft prepare-ticket 451 T01 --provider claude`，记录 ticket_base 与起始状态，按返回的派生视图调用 executing-plans。先核实 approved 合同、owner 与四份文件的基线 SHA-256；任一基线不符或补丁不能干净应用就停止分析。钉子只写进已有测试类，断言新小节标题存在、小节内含「不授予任何访问权」「对其他项目缺省只读」「待建票」，并断言 `greenfield-planning` 不含「已登记、已采用」、`aisoft-matt-workflow` 不含「exact manifest project, protected」。
- **验证**：
  1. 写入钉子后、应用补丁前：`cd codex/runtime && python3 -m unittest tests.test_session_contract`，新增用例失败，原有 13 个用例仍通过。
  2. `git apply --check docs/changes/451-coordination-workspace/proposals/coordination-workspace.patch`，通过后才应用。
  3. 应用后四份文件的 SHA-256 等于 spec 表中的值；`git apply --reverse --check` 同一补丁成功。
  4. 重跑第 1 步命令，全部通过。逐条临时删掉一个被钉短语重跑，对应用例必须失败，随后还原并确认 SHA-256 回到固定值。
  5. `bash codex/tools/usage-bundle.sh --release 1.25.0 --today <实施日> --compatibility minor --notes '跨项目协调工作区成为调度协调的可选合法位置；自主采用入口两处表述对齐 ADR 0003（#451）'`。版本被占用时按 spec 顺延。
  6. `bash codex/tools/usage-bundle.sh --verify --baseline-ref c14a86d4ad0d1fd5938ab31343f8d72acd486a71`；比较 bundle 成员集合与既有 releases 前缀不变。
  7. `python3 -B codex/tests/check-project-leak.py`，`git diff --check`，`bash codex/tools/aisoft check-change-documents --porcelain`；逐项审议 spec 的场景与反例；确认没有范围外路径。
- **Expected**：钉子先红后绿，反向删短语时再红；冻结文字精确应用且可反向匹配；已发布历史不变，新版本摘要与源码一致；泄漏基线不增。这里不证明任何会话实际加载了新文字，也不证明安装、项目采用或远端 CI。
- **停止条件**：治理文件应用后在一个独立本地 commit 里提交（主题以 `#451 T01` 开头），记录 exact HEAD、验证结果与未完成核验，立即 STOP。T01 的完成判定由 fresh run 补齐；证据不齐时不写成 complete，也不提前启动 T02。冻结文字、范围或合同需要实质改变时先升级。

## T02：fresh run 核验与最终候选

- **交付/范围**：fresh run 接回同一 claimed worktree，先完成 T01 的候选核验与真实完成判定，再执行本票。只补本目录的证据与状态、`docs/governance/review-evidence-index.md` 的本票一行，形成最终候选。
- **blocked_by**：T01。
- **AC**：AC-1 至 AC-8。
- **接口/约束**：先按全局约束复核治理交接，用 `prepare-ticket 451 T01 --provider claude --resume` 恢复并核对语义身份；owner 因会话变化被拒时如实记录并按合同处理，不手改 owner 文件。固定 T01 的实际 HEAD，核对 ticket_base 到 HEAD 的内容以及 staged、unstaged、untracked 遗漏。T01 证据完整后再 `prepare-ticket 451 T02 --provider claude`。真正覆盖同一范围的既有验证可以复用，不因技能名再叠加轮次。
- **验证**：
  1. `AISOFT_USAGE_BASELINE_REF=c14a86d4ad0d1fd5938ab31343f8d72acd486a71 LC_ALL=C bash codex/tests/smoke.sh`。开跑前 broker `git.fetch.main`；`origin/main` 已前进时先把它集成进本分支再跑。
  2. `bash codex/tools/usage-bundle.sh --build <本票新建的隔离目录>`；逐个比较导出的 `.agents`、`.claude`、`.cursor` 下四份对应技能文件与当前源码字节相同（`aisoft-matt-workflow` 只在它实际导出的落点比较）。记录实际目录与比较结果，不称为安装。
  3. 反向证明：补丁反向匹配与全文摘要复核；确认完整 smoke 里已含的 bundle 未发版、成员漂移与已发布历史不可变等负向夹具确实执行；复核 T01 的删短语反证记录。
  4. 记录全部必要本地结果后固定 candidate_head，确认 `change_base..HEAD` 全批只含 git_scope 内的路径，检查 staged、unstaged、untracked 遗漏。经 Herdr 由未参与实现的独立 Codex 审查整个固定范围；有修复就追加 commit、重验并审新 HEAD。治理返修仍独立提交并 STOP、fresh run。
  5. 在本票 verification 的交叉审查表与 `review-evidence-index` 记录实际 BASE/HEAD、提供者、型号、强度、结论与 findings。只有证据提交改变 HEAD 时，审实际证据 diff 并记录新的范围覆盖，不冒用旧 PASS。
  6. `bash codex/tools/aisoft classify --apply 451`，再单独 `bash codex/tools/aisoft classify --verify 451` 读回 `projected`；`check-change-documents --porcelain`、`git diff --check c14a86d4ad0d1fd5938ab31343f8d72acd486a71..HEAD` 与范围核对通过。
- **Expected**：本地必需回归通过；三端导出同字节；独立审查覆盖全部实际变更与 AC，新文字没有引入新的权限来源、确认点或必经入口；判级与路由读回一致；未执行的 CI、安装、采用如实标注。这些证据不能证明 Home 可用或任何试点结论。
- **停止条件**：形成 `AWAITING_PR_CONFIRMATION` 候选后停下，等确认点 2。之后的 push、唯一 PR、required CI、人工合并与合并后收尾按原合同。本计划不授权真实安装、项目采用、建 Home 仓或部署。

## Expected touch points

- T01：四份技能文件、`codex/runtime/tests/test_session_contract.py`、`usage/bundle.json`，以及本目录的执行证据区。冻结补丁不因应用方便而改写。
- T02：本目录 plan 的执行证据与状态、verification、必要的 summary 状态，以及 `docs/governance/review-evidence-index.md` 的本票一行。任何修改不得超出 spec 的十三个 exact 路径。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | 冻结补丁应用检查、四份全文 SHA-256、反向 apply check |
| AC-2 | 合同钉子、diff 与 spec 场景审议、独立交叉审查 |
| AC-3 | diff 审议确认未触及确认点、路由、单写者、合并与部署条文；`tests.test_session_contract` 原有用例通过 |
| AC-4 | 合同钉子的两条否定断言、对照 ADR 0003 的 diff 审议 |
| AC-5 | `check-project-leak.py` 与完整 smoke 里的泄漏守卫 |
| AC-6 | 应用前红、应用后绿、删短语再红的三次真实运行记录 |
| AC-7 | bundle verify、历史前缀与成员集合比较、隔离 build 三端字节比对 |
| AC-8 | 文档与 scope 检查、完整 smoke、STOP 与 fresh run 记录、classify 读回、实际候选的 cross-provider 审查 |

## 执行证据

<!-- execution-evidence:start -->
2026-11-16：只完成合同准备。T01、T02 未开始；ticket_base、治理 candidate_head、正式 smoke、隔离 build 与实际补丁交叉审查均 NOT RUN。准备阶段的只读核对与一次性副本预演见映射 verification，预演不是本票的执行证据。
2026-11-16：负责人在本票线程回复「确认」，合同获批。summary 记为 approved（提交 `443d8983f5b0c88c48c034b4f1286a651e3e0984`），Issue 生命周期标签经 broker 由 `needs-analysis` 改为 `approved`。会话 `0a9bf32d-69b7-4d4e-a676-2bc1eb8df9ed` 运行 `prepare-ticket 451 T01 --provider claude`，回执 status=prepared，ticket_base `443d8983f5b0c88c48c034b4f1286a651e3e0984`，起始 staged、unstaged、untracked 均空。钉子先红、冻结补丁精确应用、钉子转绿并做删短语反证、bundle 追加 1.25.0；治理提交 `3f4b6a6282bdd653fad18b54c9484cc2f1f45081` 只含四份技能文件、测试文件与 bundle，随后 STOP。T01 状态保持 pending：真实完成判定由 fresh run 以 `--resume` 恢复后补齐；T02 未开始。逐条结果见映射 verification。
2026-11-17：fresh run 会话 `7f3a1416-3cf0-4e14-8d1c-6f9aa2546590` 以 `claim-worktree --takeover` 接手（HEAD `638def252e487ef58087242552b46b5610c9e71e`，工作树干净，`origin/main` 仍为 `c14a86d4…`）。`prepare-ticket 451 T01 --provider claude --resume` 因 owner 变化被拒（语义摘要未变）；经负责人在本票线程授权，fresh run 复跑 T01 可复现的检查并在映射 verification 写入 `aisoft-execution` 完成记录（base `443d8983…`，head `638def25…`），T01 标为 done，由 `prepare-ticket 451 T02` 的依赖校验确认。
<!-- execution-evidence:end -->

## 部署与回滚

无部署、全局安装或项目采用。本地候选与合并后的回退按 spec「风险与回滚约束」，已发布的 bundle 历史只追加。最终 PR 由人确认提交并人工合并。
