---
issue: 75
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/75
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - authorization
  - external-contract
  - shared-core
  - platform-governance
depends_on: []
status: approved
branch: change/75-readable-change-names
pr_url:
created: 2026-08-10
updated: 2026-08-10
---

# Readable issue-scoped Change naming implementation plan

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | live baseline、semantic contract、bootstrap/fresh-run handoff | - | complete |
| T02 | shared ChangeName + document/controller/worktree vertical slice | T01 | pending |
| T03 | broker + PR + duplicate/legacy fail-closed vertical slice | T02 | pending |
| T04 | governance/docs/templates + full verification + governed PR handoff | T02, T03 | pending |

## T01 — Contract and safe handoff

- 用 installed project-scoped broker 串行读取 Issue #75 与 fresh `origin/main`，查重 remote branch/open PR，不访问
  `ci-bot` 或 credential contents。
- 从 exact main 创建隔离 `change/75-readable-change-names` worktree；canonical checkout 与用户 `.DS_Store`
  保持不变。
- 建立唯一 mapped semantic summary/spec/plan/verification，收敛 grammar、reserved words、immutability、legacy
  evidence、duplicate handling、PR exact closure、candidate bootstrap 与 post-merge install/rollback。
- 当前 run 不修改 governing root `AGENTS.md`；T02 必须由 fresh implementation run 重新读取并验证本合同后开始。

## T02 — Shared ChangeName, documents, controller and worktree

- 先在 `codex/runtime/tests/test_change_name.py`（或等价 shared test）写 parser/formatter RED matrix：valid、leading
  zero、uppercase/Unicode/separator/length/word count/all-numeric/reserved、wrong N/slug 与 full-match negatives。
- 新增 shared `aisoft_loop.change_name` 值对象；analysis summary filename、contract/document resolver、document
  publisher、controller prompt/state/required-doc links 与 Gitea adapter 全部改用它，不保留平行正则。
- 重构 analyzer wrapper：先只读产生并验证 `document_slug`，再创建 `issue-N-slug` worktree、
  `change/N-slug` 与 `docs/changes/N-slug/`；remote existing readable branch 必须精确复用。
- legacy resolver/controller 只消费 remote/history evidence；new writer/creation path 拒绝 pure N。覆盖 legacy readable/
  numeric directory conflict、multiple readable directories、front matter/document basename mismatch。
- 更新 controller/worktree/state tests、analysis/contract/documents/Gitea unit tests与 shell fixtures，保持 provider
  branch/commit/ancestry/clean rules。

## T03 — Broker, PR and duplicate gates

- 扩展 `aisoft_host_access.contract` Change branch parser；public CLI 仍只有 typed `branch`，不新增 slug/legacy/
  URL/remote/refspec/path argument。
- 在 real temp canonical + linked worktree tests 覆盖 readable fetch/push、wrong issue/slug、main、force/delete、
  dirty/detached/merge/non-FF/cross-project 与 exact same-name refspec。
- 在 first push/PR 前从 manifest-fixed remote/Gitea 查同 Issue refs/open PR：0 或 exact self 继续，legacy/readable/
  multiple conflict 返回 sanitized `CHANGE_NAME_CONFLICT`。legacy pure ref 仅在 operation 前已存在时允许维护。
- 收紧 broker/controller Gitea PR body validation：exact head、exact one-line `Closes #N`、exact mapped summary path，
  拒绝 substring、第二个 closure、wrong/duplicate slug；保留 historical batch-close parser read compatibility。
- 更新 runner/helper/installer/fresh-session/security negative tests，证明无 generic Git/curl/Keychain/`ci-bot`、
  merge/credential/permission/protection/deployment surface。

## T04 — Governance, verification and delivery

- 在 fresh run 按 spec 明确授权更新 root `AGENTS.md`、`codex/global-AGENTS.md`、README、03/04/06/08、agent
  shell comments/messages、skills、templates、onboarding/private-access examples；历史文档不批量改写。
- 更新 `codex/tests/smoke.sh` 与 cleanup/deployment fallback tests，确保新 creation examples readable，legacy
  history parser 仍可读；任何硬编码 pure `change/N` 的 active writer 必须消除或明确 compatibility-only。
- 运行 focused Python/shell/real Git tests，再运行 full smoke；修改 shell 执行 `bash -n`、ShellCheck（若可用），
  加 strict JSON、document resolver、Secret/cache scan、`git diff --check`。
- 自审 exact branch、base ancestry、commit subjects `#75 Txx`、touch points 与 clean tree。候选 source broker 只
  typed push本 readable branch，创建/更新唯一 `Closes #75` PR，读取 protection/final-head status后停在人工 merge。
- 人工 merge 后才从 exact protected main 安装，执行 second no-op、byte readback 与 rollback availability；下游
  项目迁移另立 Issue，本 Change 不部署。

## Expected touch points

- `docs/changes/75-readable-change-names/`。
- `codex/runtime/aisoft_loop/{change_name,analysis,contract,documents,controller,gitea}.py` 与 CLI/public exports。
- `codex/runtime/aisoft_host_access/{contract,broker,runner}.py`、config/installer/wrapper（仅必要处）。
- `codex/agent/{common,analyze-codex,analyze-claude,loop-controller,*-provider}.sh`。
- `codex/runtime/tests/`、`codex/tests/test-host-access-broker.sh`、`codex/tests/smoke.sh` 及相关 fixtures。
- root `AGENTS.md`、`codex/global-AGENTS.md`、README、03/04/06/08、skills、templates 与 onboarding references。
- `codex/tools/mark-deployed-issues.sh`、cleanup tool 仅在 parser/read compatibility 必要时修改。

以上是 scope guidance。root `AGENTS.md` 只允许 T04 的 fresh implementation run 修改；不授权 Secret、credential、
permission/protection、VM/service、Docker、数据库、部署、生产、自动 merge 或历史 cleanup。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | shared parser unit/public CLI matrix；所有 formatter round-trip 与 branch/docs/worktree/front matter full-match |
| AC-2 | new writer/first-push denial + remote/history-derived legacy resolver/maintenance tests；确认无 caller legacy flag |
| AC-3 | temp Git/Gitea duplicate refs/dirs/PR matrix；same slug different Issue positive；conflicts fail closed |
| AC-4 | analyzer-before-mutation、`issue-N-slug` worktree/state reuse、immutable slug、provider commit/clean/ancestry tests |
| AC-5 | host-access public seam + real linked-worktree fetch/push positive/negative matrix；exact argv/refspec spies |
| AC-6 | controller/broker PR create/update/read exact regex/path tests；`#N0`、multi-Closes、wrong slug/PR negatives |
| AC-7 | fresh-run review of AGENTS/global rules、README/03/04/06/08、skills/templates/onboarding；smoke grep assertions |
| AC-8 | focused unittest + shell/real Git + full smoke + bash-n/ShellCheck/JSON/Secret/diff gates |
| AC-9 | source broker exact branch push/readback、unique PR/protection/status；merge/install/downstream按 PASS/NOT RUN 分层 |

## 部署与回滚

本 Change 不部署。candidate 回滚为 normal PR revert。human merge 后 host installation 使用 exact-main bytes，
保留 `.previous`，必须 second no-op/readback；失败时恢复 `.previous` 并停止新 Change creation。禁止自动清理或
rename 任何历史 branch/worktree/docs。
