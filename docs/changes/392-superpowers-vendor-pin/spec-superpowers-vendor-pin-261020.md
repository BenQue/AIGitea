---
issue: 392
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/392
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
depends_on:
  - 389
status: approved
branch: change/392-superpowers-vendor-pin
created: 2026-10-20
updated: 2026-10-20
git_scope:
  - 08-双工具共存与实施.md
  - README.md
  - codex/config/external-skill-adaptation.json
  - codex/runtime/aisoft_loop/matt_snapshot.py
  - codex/runtime/tests/test_matt_snapshot.py
  - codex/tests/smoke.sh
  - codex/tests/test-external-skill-versions.sh
  - codex/tests/test-usage-bundle.sh
  - codex/tools/check-external-skill-versions.py
  - codex/tools/check-installed-drift.py
  - codex/tools/usage-bundle.py
  - codex/vendor/superpowers/v7.0.0/LICENSE
  - codex/vendor/superpowers/v7.0.0/README.md
  - codex/vendor/superpowers/v7.0.0/RELEASE-NOTES.md
  - codex/vendor/superpowers/v7.0.0/manifest.json
  - codex/vendor/superpowers/v7.0.0/skills/brainstorming/SKILL.md
  - codex/vendor/superpowers/v7.0.0/skills/brainstorming/builder-check-prompt.md
  - codex/vendor/superpowers/v7.0.0/skills/brainstorming/scripts/frame-template.html
  - codex/vendor/superpowers/v7.0.0/skills/brainstorming/scripts/helper.js
  - codex/vendor/superpowers/v7.0.0/skills/brainstorming/scripts/server.cjs
  - codex/vendor/superpowers/v7.0.0/skills/brainstorming/scripts/start-server.sh
  - codex/vendor/superpowers/v7.0.0/skills/brainstorming/scripts/stop-server.sh
  - codex/vendor/superpowers/v7.0.0/skills/brainstorming/visual-companion.md
  - codex/vendor/superpowers/v7.0.0/skills/diagnosing-superpowers/SKILL.md
  - codex/vendor/superpowers/v7.0.0/skills/diagnosing-superpowers/prompts/analyst-common.md
  - codex/vendor/superpowers/v7.0.0/skills/diagnosing-superpowers/prompts/cost-and-time.md
  - codex/vendor/superpowers/v7.0.0/skills/diagnosing-superpowers/prompts/plan-adherence.md
  - codex/vendor/superpowers/v7.0.0/skills/diagnosing-superpowers/prompts/quality-evidence.md
  - codex/vendor/superpowers/v7.0.0/skills/diagnosing-superpowers/prompts/repeated-work.md
  - codex/vendor/superpowers/v7.0.0/skills/diagnosing-superpowers/prompts/request-conflicts.md
  - codex/vendor/superpowers/v7.0.0/skills/diagnosing-superpowers/prompts/scrub-audit.md
  - codex/vendor/superpowers/v7.0.0/skills/diagnosing-superpowers/prompts/scrub.md
  - codex/vendor/superpowers/v7.0.0/skills/diagnosing-superpowers/prompts/similar-session.md
  - codex/vendor/superpowers/v7.0.0/skills/diagnosing-superpowers/prompts/skill-timeline.md
  - codex/vendor/superpowers/v7.0.0/skills/diagnosing-superpowers/prompts/stumbles.md
  - codex/vendor/superpowers/v7.0.0/skills/diagnosing-superpowers/references/context-safety.md
  - codex/vendor/superpowers/v7.0.0/skills/diagnosing-superpowers/references/github-issues.md
  - codex/vendor/superpowers/v7.0.0/skills/diagnosing-superpowers/references/redaction-policy.md
  - codex/vendor/superpowers/v7.0.0/skills/diagnosing-superpowers/references/session-discovery.md
  - codex/vendor/superpowers/v7.0.0/skills/diagnosing-superpowers/templates/bundle-README.md
  - codex/vendor/superpowers/v7.0.0/skills/diagnosing-superpowers/templates/case.md
  - codex/vendor/superpowers/v7.0.0/skills/diagnosing-superpowers/templates/issue.md
  - codex/vendor/superpowers/v7.0.0/skills/diagnosing-superpowers/templates/report.md
  - codex/vendor/superpowers/v7.0.0/skills/dispatching-parallel-agents/SKILL.md
  - codex/vendor/superpowers/v7.0.0/skills/executing-plans/SKILL.md
  - codex/vendor/superpowers/v7.0.0/skills/executing-plans/scripts/task-done
  - codex/vendor/superpowers/v7.0.0/skills/executing-plans/scripts/task-start
  - codex/vendor/superpowers/v7.0.0/skills/finishing-a-development-branch/SKILL.md
  - codex/vendor/superpowers/v7.0.0/skills/receiving-code-review/SKILL.md
  - codex/vendor/superpowers/v7.0.0/skills/requesting-code-review/SKILL.md
  - codex/vendor/superpowers/v7.0.0/skills/requesting-code-review/code-reviewer.md
  - codex/vendor/superpowers/v7.0.0/skills/subagent-driven-development/SKILL.md
  - codex/vendor/superpowers/v7.0.0/skills/subagent-driven-development/implementer-prompt.md
  - codex/vendor/superpowers/v7.0.0/skills/subagent-driven-development/re-review-prompt.md
  - codex/vendor/superpowers/v7.0.0/skills/subagent-driven-development/scripts/review-package
  - codex/vendor/superpowers/v7.0.0/skills/subagent-driven-development/scripts/sdd-workspace
  - codex/vendor/superpowers/v7.0.0/skills/subagent-driven-development/scripts/task-brief
  - codex/vendor/superpowers/v7.0.0/skills/subagent-driven-development/task-reviewer-prompt.md
  - codex/vendor/superpowers/v7.0.0/skills/systematic-debugging/CREATION-LOG.md
  - codex/vendor/superpowers/v7.0.0/skills/systematic-debugging/SKILL.md
  - codex/vendor/superpowers/v7.0.0/skills/systematic-debugging/condition-based-waiting-example.ts
  - codex/vendor/superpowers/v7.0.0/skills/systematic-debugging/condition-based-waiting.md
  - codex/vendor/superpowers/v7.0.0/skills/systematic-debugging/defense-in-depth.md
  - codex/vendor/superpowers/v7.0.0/skills/systematic-debugging/find-polluter.sh
  - codex/vendor/superpowers/v7.0.0/skills/systematic-debugging/root-cause-tracing.md
  - codex/vendor/superpowers/v7.0.0/skills/systematic-debugging/test-academic.md
  - codex/vendor/superpowers/v7.0.0/skills/systematic-debugging/test-pressure-1.md
  - codex/vendor/superpowers/v7.0.0/skills/systematic-debugging/test-pressure-2.md
  - codex/vendor/superpowers/v7.0.0/skills/systematic-debugging/test-pressure-3.md
  - codex/vendor/superpowers/v7.0.0/skills/test-driven-development/SKILL.md
  - codex/vendor/superpowers/v7.0.0/skills/test-driven-development/writing-good-tests.md
  - codex/vendor/superpowers/v7.0.0/skills/using-git-worktrees/SKILL.md
  - codex/vendor/superpowers/v7.0.0/skills/using-superpowers/SKILL.md
  - codex/vendor/superpowers/v7.0.0/skills/using-superpowers/references/antigravity-tools.md
  - codex/vendor/superpowers/v7.0.0/skills/using-superpowers/references/claude-code-tools.md
  - codex/vendor/superpowers/v7.0.0/skills/using-superpowers/references/codex-tools.md
  - codex/vendor/superpowers/v7.0.0/skills/using-superpowers/references/gemini-tools.md
  - codex/vendor/superpowers/v7.0.0/skills/using-superpowers/references/hermes-tools.md
  - codex/vendor/superpowers/v7.0.0/skills/using-superpowers/references/muse-tools.md
  - codex/vendor/superpowers/v7.0.0/skills/using-superpowers/references/pi-tools.md
  - codex/vendor/superpowers/v7.0.0/skills/verification-before-completion/SKILL.md
  - codex/vendor/superpowers/v7.0.0/skills/writing-plans/SKILL.md
  - codex/vendor/superpowers/v7.0.0/skills/writing-skills/SKILL.md
  - codex/vendor/superpowers/v7.0.0/skills/writing-skills/anthropic-best-practices.md
  - codex/vendor/superpowers/v7.0.0/skills/writing-skills/examples/CLAUDE_MD_TESTING.md
  - codex/vendor/superpowers/v7.0.0/skills/writing-skills/graphviz-conventions.dot
  - codex/vendor/superpowers/v7.0.0/skills/writing-skills/persuasion-principles.md
  - codex/vendor/superpowers/v7.0.0/skills/writing-skills/render-graphs.js
  - codex/vendor/superpowers/v7.0.0/skills/writing-skills/testing-skills-with-subagents.md
  - docs/adr/0002-deterministic-development-flow.md
  - docs/changes/392-superpowers-vendor-pin/plan-superpowers-vendor-pin-261020.md
  - docs/changes/392-superpowers-vendor-pin/spec-superpowers-vendor-pin-261020.md
  - docs/changes/392-superpowers-vendor-pin/summary-superpowers-vendor-pin-261020.md
  - docs/changes/392-superpowers-vendor-pin/verification-superpowers-vendor-pin-261020.md
  - docs/governance/remediation-roadmap.md
  - skills/aisoft-platform/SKILL.md
  - usage/CONTRACT.md
  - usage/bundle.json
---

# #392 superpowers vendor pin 与三端落点

## 目标与原因

D6（2026-10-20）裁定三端用同一套外部技能包。负责人在确认点 1（2026-10-20 11:22Z）修正：Claude 与 Codex 都有官方 marketplace 可以直接同步 superpowers，这条来源不变，单独使用 Claude 或 Codex 时用户照样能用；平台 pin 7.0.0 是三端核对的基准，vendor 快照只供项目级（Cursor）导出。本票结束「三端版本不齐但没人报」的状态，并把 #355「superpowers 不自建 pin」改为「平台 pin 作基准、三端核对同版」。

pin 的事实：`https://github.com/obra/superpowers` tag `v7.0.0`，tag object `7f043e5eaf3522dc19178c673b76328de9b0c355`，commit `bb92a77741419a4ab5f06e711a283343f1ada0c3`（`git ls-remote` 2026-10-20 读取），与本机 Claude 插件 `superpowers@claude-plugins-official` 记录的 `gitCommitSha` 一致。

现状（2026-10-20 只读核对）：Codex 配置启用 `superpowers@openai-curated`，该缓存是 5.1.3 且未加载（`codex debug prompt-input` 可见技能里没有 superpowers）；`openai-curated-remote` 缓存是 6.4.2。Codex 官方来源当前给不到 7.0.0。

## 方案与决策

1. **快照**：`codex/vendor/superpowers/v7.0.0/` 收 `LICENSE`、`README.md`、`RELEASE-NOTES.md`、`skills/`（15 个技能全部）与 `manifest.json`。来源是对上述 tag 的浅克隆，核对 HEAD 等于 pin commit，再与 Claude 插件缓存的 `skills/` 逐字节比对。不收 hooks 与插件清单。
2. **校验模块不另起一份**：`matt_snapshot.py` 的 `verify`/`build_manifest` 增加技能包参数（`mattpocock` 默认、`superpowers`），每个包有自己的来源 URL 与关键技能集合。Matt 的 manifest、安装行为与命令行保持不变。superpowers 关键技能：`brainstorming`、`dispatching-parallel-agents`、`executing-plans`、`finishing-a-development-branch`、`subagent-driven-development`、`systematic-debugging`、`test-driven-development`、`using-superpowers`、`verification-before-completion`。
3. **Claude 与 Codex 不由平台安装 superpowers**：`install-skills.sh`、`skill-for-claude/install.sh`、`check-drift.sh` 不改，`check-installed-drift` 只同步它钉住的 `matt_snapshot.py` 指纹（安装语义不变）；两端继续从官方 marketplace 同步，平台只核对版本。
4. **发布包**：`usage/bundle.json` 新增成员模式 `vendor`，source 是快照的 `manifest.json`（它按目录哈希钉住全部技能字节，release 摘要因此覆盖快照）。`--build` 先按 manifest 校验快照再导出：superpowers 只到 `.cursor/skills/<名>/`（项目级 `.agents/skills` 会与 Codex 官方插件形成第二来源，所以不导出）；Matt 到 `.agents/skills/<名>/` 与 `.cursor/skills/<名>/`（Matt 在 Codex 本来就走 vendor pin）。都不导出 `.claude/skills/`。发布包 1.2.0 → 1.3.0。
5. **版本核对**：`check-external-skill-versions.sh` 对 superpowers 输出与 Matt 同形的 `PIN_CLEAN` / `PIN_DRIFT` / `PIN_NOT_INSTALLED`：Claude 看插件记录的版本与 commit；Codex 看已启用且已加载的官方插件版本，启用了但来源未注册或未缓存记 `PIN_NOT_INSTALLED`（附注原因），不再有 `NOT_LOADED`；Cursor 只有项目级落点，新增 `--repo <检出>` 按 manifest 目录哈希读该检出 `.cursor/skills/`（两包都报），不给 `--repo` 时写 `NOT_CHECKED`，用户级缓存版本降为附注。`PIN_DRIFT` 的含义是「该端版本与平台 pin 不同，先过 `08` §5 适配清单」，作为 `REVIEW_NEEDED` 计入 RESULT；`PIN_NOT_INSTALLED` 只报告。适配记录 `external-skill-adaptation.json` 的版本必须等于 pin 版本，issue 改为 392。
6. **治理文件**：`08` §5 与 `aisoft-platform` 技能「外部技能包边界」改为「Claude/Codex 跟随官方 marketplace，平台 pin 7.0.0 作基准三端核对，Cursor 项目级由发布包导出」，加 `dispatching-parallel-agents`（只读调查可并行）、`subagent-driven-development`（顺序派发、一次一个写者）两行三端通用约束；`README.md` 两句同步。单独 commit 后停止，重读再改 runtime。路由表本身不动（R10b）。

## Acceptance criteria

- [ ] AC-1 `matt_snapshot verify --pack superpowers` 对 vendor 快照 PASS；快照技能字节与 Claude 插件缓存 7.0.0 的 `skills/` 一致；Matt 快照校验结果与安装器行为不变。
- [ ] AC-2 `usage-bundle.sh --verify` 通过且最新版本为 1.3.0；`--build` 产物在 `.cursor/skills/` 有两包技能、`.agents/skills/` 只有 Matt、`.claude/skills/` 没有 vendor 技能；快照字节被改时 `--build` 失败。
- [ ] AC-3 `check-external-skill-versions.sh` 在夹具上三端分别给出 `PIN_CLEAN`、`PIN_DRIFT`、`PIN_NOT_INSTALLED`；不再以 `NOT_LOADED` / `BEHIND` 作为 superpowers 终态。
- [ ] AC-4 三端读回：Claude 插件、Codex 官方插件、一个用 `--build` 产物落地的项目检出的 `.cursor/skills`，各报 pin 状态；Claude 与 Cursor 为同一 commit `bb92a77`。Codex 端如实记录（官方来源当前 6.4.2/未加载，到 7.0.0 前是 `PIN_DRIFT` 或 `PIN_NOT_INSTALLED`）。
- [ ] AC-5 Cursor fresh 会话里 `aisoft-platform` 与 `brainstorming` 能触发；Codex fresh 会话的 superpowers 加载情况如实记录；三端各过一次 `08` §5 适配清单，结论写进 verification。
- [ ] AC-6 `bash codex/tests/smoke.sh` 全绿；Codex 只读交叉审查 PASS。

## 接口、数据与兼容性影响

- `matt_snapshot` 命令行新增可选 `--pack`，缺省行为与现在逐字节一致。
- 发布包合同仍是 `aisoft-usage-bundle/v1`，只追加成员模式；已发布的 1.0.0–1.2.0 不变，已 pin 旧版本的项目 `--project-status` 结果不变。
- 版本核对脚本的输出行格式变化（superpowers 状态词），调用它的只有人和测试。
- Claude、Codex 的 installed 层不变。

## 风险与回滚约束

- 回滚为 revert；没有 installed 层改动需要撤回。
- 与 R10a 的冲突面只剩 `usage/bundle.json` 版本号。后合并者 merge commit 集成并发下一版。

## 非目标

不改 Matt pin；不改路由表（R10b）；不往 `~/.cursor` 安装任何东西；不改 Claude、Codex 的 superpowers 来源与安装方式（官方 marketplace）；不改 `~/.codex/config.toml`；不让任何项目仓本票内采用新发布包（R11）。

## 未决问题

无。
