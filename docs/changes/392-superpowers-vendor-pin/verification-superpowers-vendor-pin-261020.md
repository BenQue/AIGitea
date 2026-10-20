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
status: pending
branch: change/392-superpowers-vendor-pin
created: 2026-10-20
updated: 2026-10-20
---

# #392 验证记录

## 基线与范围

- Commit SHA: 实现 head `448a652`（T04）；最终候选 head 见确认点 2
- 基线：`origin/main` = `0192a8e`
- 环境: macOS 本机（bash 3.2）；Claude Code 2.1.228；Codex CLI 0.161.0；Cursor CLI `cursor-agent`
- 本记录负责证明的 acceptance criteria: AC-1–AC-6

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| `git ls-remote https://github.com/obra/superpowers 'refs/tags/v7*'` | PASS | `7f043e5e… refs/tags/v7.0.0`、`bb92a777… refs/tags/v7.0.0^{}` |
| `git clone --depth 1 --branch v7.0.0`，`git rev-parse HEAD` | PASS | `bb92a77741419a4ab5f06e711a283343f1ada0c3` |
| `diff -r <clone>/skills ~/.claude/plugins/cache/claude-plugins-official/superpowers/7.0.0/skills`；`cmp` LICENSE/README.md/RELEASE-NOTES.md | PASS | 无输出，`SKILLS_IDENTICAL`；三个文件 same |
| `python3 -m aisoft_loop.matt_snapshot verify --pack superpowers <snapshot> <manifest>` | PASS | `skill_count 15`、commit `bb92a77…` |
| `python3 -m unittest tests.test_matt_snapshot tests.test_matt_install` | PASS | 20 + 原有用例 OK；Matt 安装用例未改 |
| `bash codex/tests/test-usage-bundle.sh` | PASS | `test-usage-bundle: PASS`（含第 18 节 vendor 用例） |
| `bash codex/tools/usage-bundle.sh --verify --baseline-ref origin/main` | PASS | `VERIFIED 1.3.0 sha256:2dbfa5eb…` |
| `bash codex/tests/test-external-skill-versions.sh` | PASS | `external skill versions tests passed` |
| `bash codex/tests/test-installed-drift.sh` | PASS | exit 0（`matt_snapshot.py` 指纹已同步） |
| `bash codex/tests/smoke.sh` | 见下 | 见「smoke」 |

### 三端读回（AC-4）

`bash codex/tools/check-external-skill-versions.sh --repo <临时检出>`，临时检出 = `usage-bundle.sh --build` 产物 `git init` 后的会话 scratch 目录（未提交到任何项目仓，项目采用归 R11）：

```
CLI claude 2.1.228
CLI codex 0.161.0
SUPERPOWERS claude PIN_CLEAN installed=7.0.0 commit=pinned pinned=7.0.0
SUPERPOWERS codex PIN_NOT_INSTALLED enabled=superpowers@openai-curated marketplace=unregistered cached=5.1.3 pinned=7.0.0
MATT claude PIN_CLEAN
SUPERPOWERS cursor PIN_CLEAN skills=15 cache=6.1.1 pinned=7.0.0
MATT cursor PIN_CLEAN skills=37 cache=1.2.0 pinned=1.3.1
RESULT PASS
```

Claude 插件记录的 `gitCommitSha` 与 Cursor 检出的目录哈希都对应 `bb92a77`。Codex 端如实为 `PIN_NOT_INSTALLED`：配置启用的 `superpowers@openai-curated` 来源未注册，缓存 5.1.3；`openai-curated-remote` 缓存 6.4.2。按负责人确认点 1 的决定，本票不改 Codex 来源。

### Codex fresh 会话（AC-5）

`codex debug prompt-input 'hi'` 在临时检出内运行（只读，不起模型回合）：可见技能 259 个，技能根含项目级 `.agents/skills`（18 个去重后来自项目的入口：平台技能与 Matt）；名字或路径含 superpowers 的条目 0 个，`brainstorming`、`using-superpowers`、`systematic-debugging` 都不在列。结论：Codex 当前不加载任何 superpowers，与版本核对一致；项目级 `.agents/skills` 按设计不放 superpowers，没有形成第二来源。

### Cursor fresh 会话（AC-5）

`cursor-agent -p --mode ask --trust` 在临时检出内：NOT RUN，CLI 未登录（`Error: Authentication required. Please run 'agent login' first`），已请负责人登录。

### smoke

- 第 1 次（head `448a652`）：exit 1，唯一失败是 `check-change-documents` 报本文件缺失（smoke 吞掉其输出，`bash -x` 定位）；其余 867 个 runtime 单测 OK，`project-leak` PASS。
- 第 2 次（head `5fa9633`，补本文件后）：exit 0，`Codex platform static smoke checks passed.`
- 审查修复后的结果见「Codex 交叉审查」。

### Codex 交叉审查

第 1 轮：`codex exec -s read-only -C <worktree>`，head `5fa9633`，结论 `CHANGES_REQUESTED`，无 blocker。四条 should-fix 与一条 nit 及处置：

| # | 发现 | 处置 |
|---|---|---|
| 1 | `--build` 按工作树执行位导出，而 manifest 只哈希字节，同一版本可导出不同权限 | 导出权限改由字节决定（`#!` 开头 0755，其余 0644）；`test-usage-bundle.sh` 加执行位丢失用例 |
| 2 | `.cursor/skills` 根是普通文件时误报 `PIN_NOT_INSTALLED` 且通过 | 根不是目录记 `UNKNOWN` 并失败；加 `repo-file-root` 用例 |
| 3 | Matt CLI 错误文案由 `matt snapshot…` 改成了 `skill snapshot…`，违反逐字节兼容 | 缺省 Matt 恢复原文案，superpowers 用 `superpowers snapshot…` |
| 4 | Cursor 未运行、smoke 结果无落点 | 本节补齐 smoke；Cursor 仍如实 NOT RUN |
| nit | 路线图 R10c 正文与括号修正矛盾 | 改写正文 |

修复 head `e2db07f` 上 smoke 第 3 次：exit 0，`Codex platform static smoke checks passed.`；`test-usage-bundle.sh`、`test-external-skill-versions.sh`、`test_matt_snapshot`/`test_matt_install` 在本机全部通过。

第 2 轮：head `e2db07f`，结论 `VERDICT: PASS`，无 blocker、无新增 should-fix 与 nit；四条原发现逐条关闭，`check-installed-drift.py` 指纹与实算一致（`a3c924a2…`）。审查方沙箱里三个测试套件因 `mktemp` 被拒未能运行，改用静态审查与内存验证；同一组测试由实现方在本机实跑通过（上一段）。

## `08` §5 适配清单（superpowers 7.0.0，三端各一次）

| # | 检查项 | Claude（官方插件 7.0.0） | Codex（官方插件，当前未加载） | Cursor（项目级 `.cursor/skills`） |
|---|---|---|---|---|
| 1 | 技能增删 | 无影响：15 个技能，与 #375 适配时相同 | 无影响：内容同一 commit | 无影响：导出即快照全集 |
| 2 | 调用方式 | 无影响：插件 hook 注入 `using-superpowers`，其余按描述触发 | 需要注意：上游 Codex 插件 `hooks: {}`，只按描述触发；`using-superpowers/references/codex-tools.md` 给 Codex 工具映射 | 需要注意：项目级技能按描述触发，没有 `using-superpowers` 的 Cursor 专属参考，按通用说明工作 |
| 3 | 文件与目录约定 | 无影响：落点映射不变 | 无影响 | 无影响 |
| 4 | Git / PR / 并行写入副作用 | 已约束：`finishing-a-development-branch` 远端动作禁用 | 已约束：`dispatching-parallel-agents`、`subagent-driven-development` 依赖 `[features] multi_agent = true`；平台规则写成三端通用：前者只做只读调查，后者顺序派发、一次一个写者 | 同 Codex 两行约束 |

两条新约束已写进 `08` §5 映射表与 `aisoft-platform` 技能（T01）。brainstorming 定级不替代平台判级一条本来就是三端共用的平台技能文本。

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | PASS | snapshot verify、`diff -r` 对插件缓存、`test_matt_snapshot` 新增 5 例 |
| AC-2 | PASS | `--verify` 1.3.0；`test-usage-bundle.sh` 第 18 节：落点、篡改失败、非法成员、同名冲突 |
| AC-3 | PASS | `test-external-skill-versions.sh`：三端 `PIN_CLEAN` / `PIN_DRIFT` / `PIN_NOT_INSTALLED`，无 `NOT_LOADED`/`BEHIND` |
| AC-4 | PASS（Codex 如实未装） | 上文三端读回 |
| AC-5 | 部分：Codex 已记录；Cursor NOT RUN | 上文 |
| AC-6 | PASS | smoke 第 3 次 exit 0（`e2db07f`）；Codex 第 2 轮 `VERDICT: PASS` |

## 遗留风险与未完成项

- Codex 端到 7.0.0 之前持续 `PIN_NOT_INSTALLED`（或注册来源后 `PIN_DRIFT`），需负责人决定 Codex 来源；不在本票。
- 合并后照常重装两侧技能（`aisoft-platform` 文本变了）并读回 `check-installed-drift`。
