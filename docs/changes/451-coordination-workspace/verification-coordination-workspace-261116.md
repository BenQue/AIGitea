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
status: pending
branch: change/451-coordination-workspace
created: 2026-11-16
updated: 2026-11-16
---

# Verification：跨项目协调工作区的平台最小适配

## 基线与范围

- Commit SHA：T01 治理提交 `3f4b6a6282bdd653fad18b54c9484cc2f1f45081`；ticket_base `443d8983f5b0c88c48c034b4f1286a651e3e0984`；change_base `c14a86d4ad0d1fd5938ab31343f8d72acd486a71`。T01 交回 HEAD `638def252e487ef58087242552b46b5610c9e71e`；fresh run 的 T01 完成记录提交 `1bf0dcbfc262f0df547fae25b0a2304848a947c9`，也是 T02 的 ticket_base。
- 基线：`origin/main` = `c14a86d4ad0d1fd5938ab31343f8d72acd486a71`（2026-11-16 broker `git.fetch.main` 返回 PASS 后读取；fresh run 于 2026-11-16 与 2026-11-17 各 fetch 一次，读回不变）。
- 环境：Mac 平台检出 `/Users/benque/MyDocs/AISoftPlatform`；change worktree `/private/tmp/issue-451-coordination-workspace`。
- 本记录负责证明的 acceptance criteria：AC-1 至 AC-8。T01 已执行到治理 STOP，并由 fresh run 补齐完成判定；T02 由 fresh run 执行。
- 执行会话：T01 为 Claude Code 会话 `0a9bf32d-…`，会话元数据读回 model `claude-opus-5-5`、effort `medium`。T02 为 fresh run 会话 `7f3a1416-3cf0-4e14-8d1c-6f9aa2546590`，读回 model `claude-opus-5-5`、effort `xhigh`。路由为 max，两次偏离都记入 summary `override_reason`，待负责人裁决。实际加载的 superpowers 插件路径为 7.0.2，平台 pin 为 7.0.0；`executing-plans` 由该插件提供，Txx 仍是唯一合同。T02 的派生视图 `.superpowers/aisoft/451/issue-451-0a099e7c…-174020f8….md` 与台账 `.superpowers/sdd/issue-451-0a099e7c…-174020f8…/progress.md` 只是缓存。

## 准备阶段记录（不是实施验收）

| 检查 | 结果 | 证据 |
|---|---|---|
| #451 最新状态读回 | 已读 | 2026-11-16 23:26（北京时间）broker `gitea.issue.read --number 451`：open，标签仅 `needs-analysis`，comments 0，`updated_at` 2026-11-15T17:45:15+08:00 |
| 既有分支、worktree 与 owner | 无 | `git worktree list` 与 `git branch -a` 没有 #451 条目；本会话 `claim-worktree` 返回 `result: created` |
| 方案与审核材料 | 已读 | 方案 v2.1 SHA-256 `5f306c6a6a75c29e13845cde0d14f625509a6b9c894c5cf93e7e93c295ea8573`；校准附录 `18ff6a2656f49810a1e3155ab112ee3fde52c6d5c4b1aa3a12d70c7046346c7b`；R2 报告 `d1d189f56f6885f2ebb71c4c0fbb9488a3b04726d88497fd61788ed7f0258c8a`。后两份留在仓库外，未重新启动历史审核 |
| 冻结补丁可应用 | 通过 | 相对基线 `git apply --check` 成功；补丁 SHA-256 `d2352ae89d3c4709c394f693ca821d7ba3c4d2b6de60d4edcbea9c3451b1a7c3` |
| 候选对现有钉子的影响 | 通过 | 候选临时写入 worktree 时 `python3 -m unittest tests.test_session_contract` 13 个用例通过，smoke 对 `issue-session-flow` 的四个标题钉子仍命中；随后 `git checkout -- skills` 还原，基线 SHA-256 复核一致 |
| 技能来源 | 已记录 | Claude Code 会话没有 `to-spec`、`to-tickets` 的可调用入口（上游声明 `disable-model-invocation`）。本会话直接读取平台检出 `codex/vendor/mattpocock/v1.3.1/skills/engineering/` 下的两份 SKILL.md，产物按平台适配写进映射 spec 与 plan。Claude 侧 Matt 插件的实际版本未读回 |
| `admin/AISoftHome` 是否存在 | NOT RUN | 没有 typed 路由；匿名 404 不构成证据。留给建仓前由有权人员核对 |

### 一次性副本预演

为了在确认点 1 之前发现范围外的钉子，本会话在 scratchpad 里从 `origin/main` 建了一个 detached 副本，应用冻结补丁并用现有工具登记 1.25.0，然后跑完整 smoke。副本没有提交、没有推送，用后移除；它不在 change worktree 里，不是 T01 的应用，也不算本票的执行证据。

| 预演步骤 | 结果 |
|---|---|
| 副本上应用冻结补丁 | 干净应用，改动只有四份技能文件 |
| `usage-bundle.sh --release 1.25.0 --today 2026-11-16 --compatibility minor` | `RELEASED 1.25.0 sha256:8e0e15405bb6adac945943e7bc267bcd57c20659e8c25e6900e1b284421e43c8`，只多出 `usage/bundle.json` |
| `usage-bundle.sh --verify --baseline-ref c14a86d4…` | `VERIFIED 1.25.0`，摘要同上 |
| `AISOFT_USAGE_BASELINE_REF=c14a86d4… LC_ALL=C bash codex/tests/smoke.sh` | 退出码 0，末行 `Codex platform static smoke checks passed.` |

预演没有包含 T01 的合同钉子，也没有本目录的文档，所以它只说明四份技能文件加发布登记不会撞到范围外的钉子。正式的 T01、T02 验证仍是 NOT RUN。实施时的发布摘要会因实施日期与当时的 `main` 而不同，不以预演的摘要为准。

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| `prepare-ticket 451 T01 --provider claude` | prepared | ticket_base `443d8983…`，起始状态为空，回执 `.superpowers/aisoft/451/T01.json` |
| T01 钉子先红：写入两个新用例后、应用补丁前运行 `python3 -m unittest tests.test_session_contract` | 按预期失败 | `Ran 15 tests`，`FAILED (failures=2)`，失败的是 `test_coordination_workspace_grants_no_access_and_stays_read_only` 与 `test_adoption_entry_points_follow_adr_0003`，原有 13 个通过 |
| T01 `git apply --check` 后应用冻结补丁 | 通过 | 补丁 SHA-256 `d2352ae8…a7c3` 与 spec 一致；应用前四份文件 SHA-256 等于 spec 基线值，应用后等于 spec 固定值 |
| T01 `git apply --reverse --check` | 通过 | 同一补丁可反向匹配 |
| T01 钉子转绿 | 通过 | `Ran 15 tests`，`OK` |
| T01 删短语反证 | 按预期失败后还原 | 临时删掉「不授予任何访问权」、「对其他项目缺省只读」各一次，`test_coordination_workspace…` 失败；删掉「它的项目目录不是第三种访问来源」，`test_adoption_entry_points…` 失败。每次还原后四份文件 SHA-256 回到固定值。「待建票」一条没有手工删，由用例内的 mutation 断言覆盖 |
| T01 `usage-bundle.sh --release 1.25.0 --today 2026-11-16 --compatibility minor` | 通过 | 发布前 broker `git.fetch.main` 读回 `origin/main` 仍为 `c14a86d4…`，最新版本 1.24.1；`RELEASED 1.25.0 sha256:8e0e15405bb6adac945943e7bc267bcd57c20659e8c25e6900e1b284421e43c8` |
| T01 `usage-bundle.sh --verify --baseline-ref c14a86d4…` | 通过 | `VERIFIED 1.25.0`，摘要同上；成员集合与基线相同，既有 31 个 release 前缀不变，只多 1 个 |
| T01 `python3 -B codex/tests/check-project-leak.py` | 通过 | `PASS: project-leak (4 baseline files, 12 hits; site 7 files, 29 hits)` |
| T01 `git diff --check` 与 `check-change-documents --porcelain` | 通过 | 无空白错误；`change-documents PASS`、`change-pr-url PASS` |
| T01 场景与反例审议 | 已做 | spec 七个场景逐条对到新小节的角色、远端写入、任务书、版本不一致、依赖、缺席与恢复、不授权各条，没有发现文字允许被排除的误读。这是作者自审，不是独立审查 |
| fresh run 接管 | PASS | 新 Claude Code 会话 `7f3a1416-3cf0-4e14-8d1c-6f9aa2546590`（会话元数据读回 model `claude-opus-5-5`、effort `xhigh`）。核对 branch、HEAD `638def252e487ef58087242552b46b5610c9e71e`、工作树干净，重读 summary、spec、plan、verification、AGENTS.md、`issue-session-flow`、`execution-adapter` 与治理 diff `c14a86d4..638def25`；`claim-worktree --takeover` 返回 `taken-over`，owner 由 `0a9bf32d-…` 改为本会话。broker `git.fetch.main` 两次读回 `origin/main` 仍为 `c14a86d4…` |
| `prepare-ticket 451 T01 --provider claude --resume` | REFUSED（按设计） | 返回 `resume identity/semantic contract mismatch`。plan 语义摘要在 `3f4b6a62`、`638def25` 与当前工作树均为 `174020f8…`，差异只在 owner；runtime 规定未完成票只许原 owner resume，继任者只能消费已完成的依赖票。没有手改 owner 文件。负责人 2026-11-17 在本票线程回复「授权」，授权本 fresh run 写入 T01 完成记录；改为复跑可只读复现的 T01 检查，写入下方机器可读记录，再由 `prepare-ticket 451 T02` 的依赖校验判定 T01 |
| T01 完成判定（fresh run 复跑） | PASS | 在 HEAD `638def25` 上：`tests.test_session_contract` 15 个 OK；补丁 SHA-256 等于 spec，在从 `c14a86d4` 取出的 `skills/` 副本上 forward `--check` 通过，在 HEAD 上 `--reverse --check` 通过；四份文件 SHA-256 等于 spec 固定值；bundle `--verify` 为 `VERIFIED 1.25.0 sha256:8e0e1540…`，既有 31 条 release 与 `contract_version`、`lock_path`、`members` 均与 `c14a86d4` 相同；泄漏守卫计数不变；`check-change-documents` 两项 PASS。AC 的 PASS 只指 T01 负责的部分，AC-2、AC-3、AC-4 的独立审议与 AC-7 的三端导出、AC-8 的 smoke、判级与交叉审查由 T02 承担 |
| T01 删短语反证复核（fresh run） | 按预期失败后还原 | 在 worktree 外用 `git archive 638def25` 导出副本操作，不碰 worktree。逐条删掉「不授予任何访问权」「对其他项目缺省只读」「目标还没有 Issue 时写「待建票」，不编造编号」与小节标题，`test_coordination_workspace…` 各失败一次；删掉「它的项目目录不是第三种访问来源」，或把「已登记、已采用」「exact manifest project, protected」加回去，`test_adoption_entry_points…` 各失败一次。7 次变异 7 次失败，还原后 OK，四份文件 SHA-256 回到固定值 |
| 全分支 `git diff --check c14a86d4..HEAD` | FAIL（仅冻结补丁） | 12 处 trailing whitespace 全部在 `proposals/coordination-workspace.patch`：unified diff 把空行上下文写成单个空格。T01 只对工作树跑过无范围的 `git diff --check`，所以没有暴露。排除该文件后同一命令退出 0。补丁 SHA-256 钉在 spec，T01 的 apply 命令也不带 `--unidiff-zero`，改成零上下文格式（#425 的做法）会改动冻结合同并使 T01 回执失效，所以不改补丁、如实记录。CI 与 smoke 都不运行这项检查 |
| T02 完整 smoke | NOT RUN | 待执行 |
| `prepare-ticket 451 T02 --provider claude` | prepared | 依赖校验确认 T01 完成；ticket_base `1bf0dcbfc262f0df547fae25b0a2304848a947c9`，起始 staged、unstaged、untracked 均空，语义摘要 `174020f8…` 不变，回执 `.superpowers/aisoft/451/T02.json` |
| T02 `bash codex/tools/usage-bundle.sh --build <本票新建的隔离目录>` | PASS | 目录为本会话 scratchpad 下新建的 `build-451-t02`，不是真实 HOME，不是安装。输出 `BUILT 1.25.0 sha256:8e0e15405bb6adac945943e7bc267bcd57c20659e8c25e6900e1b284421e43c8`，与 `--verify` 摘要相同 |
| T02 三端字节比对 | PASS | `cmp` 逐个比较 `project/.agents`、`project/.claude`、`project/.cursor` 下的 `skills/issue-session-flow/SKILL.md`、`skills/aisoft-platform/SKILL.md`、`skills/aisoft-platform/references/greenfield-planning.md` 与源码，9 个文件全部相同。`aisoft-matt-workflow` 只导出到 `.agents`（Claude、Cursor 两端没有这个技能目录），该落点 1 个文件与源码相同 |
| T02 `classify --apply` 与 `--verify` | NOT RUN | 待执行 |
| required CI `CI / verify (pull_request)` | NOT RUN | PR 之后才有 |
| Mac 技能重装与漂移读回 | NOT RUN | 合并后由负责人执行，不在本票授权内 |
| 任何 provider 会话实际加载新文字 | NOT RUN | 本次未取得证据 |

## 机器可读执行记录

`ticket_execution` 读取的唯一记录。T01 由 fresh run 复跑检查后判定完成（负责人 2026-11-17 在本票线程授权）；`start` 原样取自 `.superpowers/aisoft/451/T01.json`，`head` 为 T01 交回时的实际 HEAD。T02 是末票，形成 PR 候选时保持 in-progress，不写完成记录。

```aisoft-execution
{
  "change_base": "c14a86d4ad0d1fd5938ab31343f8d72acd486a71",
  "tickets": {
    "T01": {
      "start": {
        "identity": {
          "issue": 451,
          "branch": "change/451-coordination-workspace",
          "owner": "0a9bf32d-69b7-4d4e-a676-2bc1eb8df9ed",
          "worktree": "/private/tmp/issue-451-coordination-workspace",
          "provider": "claude",
          "plan_path": "docs/changes/451-coordination-workspace/plan-coordination-workspace-261116.md",
          "semantic_hash": "174020f86ccade6e144b1ccfdb31b994989efd898a9253277ce50cc6501f2dbb"
        },
        "ticket": "T01",
        "ticket_base": "443d8983f5b0c88c48c034b4f1286a651e3e0984",
        "raw_plan_sha256": "232593360f2cfbc10e9586c77ef81a0e8c1dc7c0a76d24aaa08c2a6a1e6ceea4",
        "scope": [
          "docs/changes/451-coordination-workspace/summary-coordination-workspace-261116.md",
          "docs/changes/451-coordination-workspace/spec-coordination-workspace-261116.md",
          "docs/changes/451-coordination-workspace/plan-coordination-workspace-261116.md",
          "docs/changes/451-coordination-workspace/verification-coordination-workspace-261116.md",
          "docs/changes/451-coordination-workspace/proposals/coordination-workspace.patch",
          "docs/changes/451-coordination-workspace/proposals/home-repo-proposal-v2.1.md",
          "skills/issue-session-flow/SKILL.md",
          "skills/aisoft-platform/SKILL.md",
          "skills/aisoft-platform/references/greenfield-planning.md",
          "skills/aisoft-matt-workflow/SKILL.md",
          "codex/runtime/tests/test_session_contract.py",
          "usage/bundle.json",
          "docs/governance/review-evidence-index.md"
        ],
        "initial_state": {
          "staged": {},
          "unstaged": {},
          "untracked": {}
        },
        "derived_plan": ".superpowers/aisoft/451/issue-451-aca4eca1ea671363-174020f86ccade6e.md",
        "scratch": ".superpowers/sdd/issue-451-aca4eca1ea671363-174020f86ccade6e",
        "policy_sha256": "850b91ae60b311eb6a48e52f372d0bfe1945ba60d9ff5da7bc540ff59183885d",
        "route": {
          "process": "complex-production",
          "tier": "frontier",
          "effort": "max",
          "skills": "to-spec, to-tickets, executing-plans, verification-before-completion",
          "method": "spec-plan",
          "verify": "full+reverse-proof",
          "review": "cross-provider",
          "confirm": "2"
        },
        "source_evidence": {
          "codex/vendor/mattpocock/v1.2.2/manifest.json": {
            "sha256": "a7e1ccccdc1ccc3d0c9af8ec0e7788cf3ac7bc0c308aaaa011ccc493c5d216da",
            "tag": "v1.2.2",
            "commit": "8b36d4fb2635b3c21998dcd8144439c9e5ba7302"
          },
          "codex/vendor/mattpocock/v1.3.1/manifest.json": {
            "sha256": "7cbdaa40307eed3258eddc1019db7f0927864b70d48cd382e202be1e7214e3dd",
            "tag": "v1.3.1",
            "commit": "24fe0ef7737efae15c87225755e9f6f5965e4888"
          },
          "codex/vendor/superpowers/v7.0.0/manifest.json": {
            "sha256": "ad9a021021ce607b35d6aa4e54bf3fb6ef572b148e08966bdf7200293629f692",
            "tag": "v7.0.0",
            "commit": "bb92a77741419a4ab5f06e711a283343f1ada0c3"
          }
        },
        "model_configuration": "not observed by helper; caller records actual model/effort in verification"
      },
      "base": "443d8983f5b0c88c48c034b4f1286a651e3e0984",
      "head": "638def252e487ef58087242552b46b5610c9e71e",
      "semantic_hash": "174020f86ccade6e144b1ccfdb31b994989efd898a9253277ce50cc6501f2dbb",
      "validation_sha256": "68db3cdd0c580c770848628d931bc5a4c983d836a5a2286da15d07ce5bc8620e",
      "ac": {
        "AC-1": "PASS",
        "AC-2": "PASS",
        "AC-3": "PASS",
        "AC-4": "PASS",
        "AC-5": "PASS",
        "AC-6": "PASS",
        "AC-7": "PASS",
        "AC-8": "PASS"
      },
      "checks": [
        {
          "command": "cd codex/runtime && python3 -m unittest tests.test_session_contract",
          "result": "PASS",
          "evidence": "T01 owner 0a9bf32d-69b7-4d4e-a676-2bc1eb8df9ed: before patch Ran 15 FAILED (failures=2, the two new tests), after patch Ran 15 OK; fresh run 7f3a1416-3cf0-4e14-8d1c-6f9aa2546590 2026-11-16: Ran 15 OK on HEAD 638def25; delete-phrase reverse proof on a git-archive copy of 638def25 outside the worktree: 7 of 7 mutations (3 pinned phrases and section heading in issue-session-flow, 1 phrase in aisoft-platform, re-adding both retired phrases) made the matching test FAIL, restored copy OK with spec SHA-256"
        },
        {
          "command": "git apply --check docs/changes/451-coordination-workspace/proposals/coordination-workspace.patch",
          "result": "PASS",
          "evidence": "T01 owner 0a9bf32d-69b7-4d4e-a676-2bc1eb8df9ed: exit 0 before applying; fresh run 7f3a1416-3cf0-4e14-8d1c-6f9aa2546590 2026-11-16: exit 0 against skills/ extracted from c14a86d4; patch sha256 d2352ae8…a7c3 equals spec; baseline file SHA-256 equal spec"
        },
        {
          "command": "git apply --reverse --check",
          "result": "PASS",
          "evidence": "fresh run 7f3a1416-3cf0-4e14-8d1c-6f9aa2546590 2026-11-16: git apply --reverse --check on the same patch exit 0 at HEAD 638def25; four file SHA-256 b883faf6…, 6c73263c…, b63333a0…, b008bbaf… equal spec"
        },
        {
          "command": "bash codex/tools/usage-bundle.sh --release 1.25.0 --today <实施日> --compatibility minor --notes '跨项目协调工作区成为调度协调的可选合法位置；自主采用入口两处表述对齐 ADR 0003（#451）'",
          "result": "PASS",
          "evidence": "T01 owner 0a9bf32d-69b7-4d4e-a676-2bc1eb8df9ed: ran with --today 2026-11-16, RELEASED 1.25.0 sha256:8e0e1540…; fresh run 7f3a1416-3cf0-4e14-8d1c-6f9aa2546590 2026-11-16: last release 1.25.0/minor/2026-11-16 with the planned notes, prior 31 releases equal prefix, contract_version, lock_path and members equal c14a86d4; origin/main still c14a86d4 after broker git.fetch.main, latest there 1.24.1"
        },
        {
          "command": "bash codex/tools/usage-bundle.sh --verify --baseline-ref c14a86d4ad0d1fd5938ab31343f8d72acd486a71",
          "result": "PASS",
          "evidence": "fresh run 7f3a1416-3cf0-4e14-8d1c-6f9aa2546590 2026-11-16: VERIFIED 1.25.0 sha256:8e0e15405bb6adac945943e7bc267bcd57c20659e8c25e6900e1b284421e43c8 exit 0"
        },
        {
          "command": "python3 -B codex/tests/check-project-leak.py",
          "result": "PASS",
          "evidence": "fresh run 7f3a1416-3cf0-4e14-8d1c-6f9aa2546590 2026-11-16: PASS: project-leak (4 baseline files, 12 hits; site 7 files, 29 hits) exit 0, same counts as T01"
        },
        {
          "command": "git diff --check",
          "result": "PASS",
          "evidence": "T01 owner 0a9bf32d-69b7-4d4e-a676-2bc1eb8df9ed: working tree vs index no output; fresh run 7f3a1416-3cf0-4e14-8d1c-6f9aa2546590 2026-11-16: git diff --check c14a86d4..638def25 excluding the frozen patch exit 0; the frozen patch alone reports 12 blank unified-diff context lines, recorded under T02"
        },
        {
          "command": "bash codex/tools/aisoft check-change-documents --porcelain",
          "result": "PASS",
          "evidence": "fresh run 7f3a1416-3cf0-4e14-8d1c-6f9aa2546590 2026-11-16: change-documents PASS, change-pr-url PASS exit 0"
        }
      ]
    }
  }
}
```

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | NOT RUN | 待执行 |
| AC-2 | NOT RUN | 待执行 |
| AC-3 | NOT RUN | 待执行 |
| AC-4 | NOT RUN | 待执行 |
| AC-5 | NOT RUN | 待执行 |
| AC-6 | NOT RUN | 待执行 |
| AC-7 | NOT RUN | 待执行 |
| AC-8 | NOT RUN | 待执行 |

## 交叉审查

此前的方案审核（Claude Opus 5.5，R1、R2 与校准附录，结论 APPROVE_WITH_CHANGES）审的是上一版方案，方案 v2.1 之后没有新的独立审核。它不是本票实现的交叉审查。

| 轮次 | 实现方 | 审查方 | exact head | 结论 | 发现与处置 |
|---|---|---|---|---|---|
| 1 | Claude | Codex（Herdr，GPT-6-Astra high，实际值待记录） | 待填写 | NOT RUN | 待填写 |

## 遗留风险与未完成项

- 本票合并只改变源码合同。Home 仓库的建立、采用、保护、CI、canary 与三项试点全部未执行，归 Home 自己的 Issue。
- 正式跨仓依赖的 installed/live 验收仍未完成，本票不改变这一点。
- 路由 effort 为 max，本会话的实际强度未能自证，实施前由负责人确认或裁决。
