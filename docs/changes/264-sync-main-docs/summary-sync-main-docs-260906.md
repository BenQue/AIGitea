---
issue: 264
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/264
change_type: docs
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: unchanged
reason: 把 README、AGENTS.md 目录节、08、onboarding-runbook 与 04 同步到 2026-09-05 合并批次（#222/#223/#225/#228/#243/#250/#252/#254）之后的仓库现状，只补目录、状态条目、入口与字段说明，不改任何判级规则、命名元组、单闸门、broker 路径或 routine merge 条件（contract_effect=unchanged）。但范围触及根 AGENTS.md 目录节与安装到两侧 skill 的 onboarding-runbook，命中 Agent/平台治理强制规则，effective complexity=complex；change_control=production 需 spec+plan
risk_flags:
  - agent-governance
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-sync-main-docs-260906.md
  spec: spec-sync-main-docs-260906.md
  plan: plan-sync-main-docs-260906.md
  verification: verification-sync-main-docs-260906.md
confidence: high
override_reason: ''
depends_on: []
status: analyzed
branch: change/264-sync-main-docs
pr_url:
created: 2026-09-06
updated: 2026-09-06
---

## 问题/需求总结

2026-09-06 的平台仓盘点发现主文档落后于 09-03 之后合并的八个 Issue（#222/#223/#225/#228/#243/#250/
#252/#254）：这些变更只在 `06` 踩坑集留下痕迹，总纲 README 与根 `AGENTS.md` 目录节没有跟上。Issue #264
正文逐条列出 7 项漂移，本 summary 以它为合同、不扩范围：

1. `AGENTS.md` 目录节缺 `company-delivery/`、`skill-for-claude/`、`templates/project/` 三个真实目录。
2. `AGENTS.md` 目录节 installer 一行只列 `codex/install-*.sh` 四个，实际 8 个 installer 共用
   `codex/lib/install-source-guard.sh`；`codex/skills/` 一行漏 `issue-session-flow`。
3. `README.md` 版本头与 §1 日期停在 2026-09-03，§1 状态条目未反映上述八个 Issue。
4. `README.md` §5 的 06 一行写「17 条实证踩坑」，06 实际到 27 条并新增 §1.0.1/§1.0.2。
5. README 与 `08` 没有 Claude 侧 `skill-for-claude/install.sh` + `check-drift.sh` 入口。
6. onboarding-runbook §2 未提 `templates/project/ci/`。
7. `analysis_provider` 三个取值（`codex`/`claude`/`none`）没有一处文档定义。

Issue 正文明确不改：`docs/changes/*/summary` 的 `status: pr-open`（文档层终态）与 `09` 第 526 行
「14 条踩坑」（历史规划表原文）。

## 影响范围

- 根 `AGENTS.md`：**只改「目录」节**（补三个目录行、installer 行、`codex/skills/` 行），工作原则节一字不动，
  独立原子 commit（#233 T04 先例）。
- `README.md`：版本头日期、§1 标题日期与状态条目、§5 导航 06 一行、§5 或 §6 新增一处 Claude 侧 skill 安装入口。
- `08-双工具共存与实施.md`：§5 初始化段补 `skill-for-claude/install.sh` + `check-drift.sh`，与
  `codex/install-skills.sh` 并列；`analysis_provider` 取值定义放 `04` §4 Analyzer（唯一定义处），`08` 只引用。
- `04-Agent编排与定时任务.md`：§4 Analyzer 增加 `analysis_provider` 三个取值的定义段。
- `skill-for-codex/references/onboarding-runbook.md` §2：提到 `templates/project/ci/`；该 references 同时装进
  Claude 侧 `aisoft-platform` skill，改后需 `bash skill-for-claude/install.sh` 重装并让 `check-drift.sh` 回 CLEAN。

不改：`codex/skills/*/SKILL.md` 正文（Issue 验收第 6 条）、`03`、`06`、`09`、`codex/runtime/`、`codex/tools/`、
`codex/config/`、`templates/`、`docker-release/`、`architecture/`、`company-delivery/`、任何 manifest。

## 初步方案与建议

1. 先以 `ls -d */`、`ls */install*.sh codex/install*.sh`、`grep -l install-source-guard`、`06` 表格最大编号、
   `contract.py` 的 provider 允许集合作为事实源，spec 逐条给出「文件:位置 → 现状 → 改后」清单。
2. `AGENTS.md` 目录节单独一张 ticket、单独一个 commit；其它文档改动按文件分 ticket。
3. `analysis_provider` 在 `04` §4 定义一次（`codex`/`claude`/`none` 各一句含义：该 VM profile 上 analyzer 使用的
   模型运行时；`none` 表示该项目不跑自动 analyzer），`08` 与 runbook 只引用，不重复定义。
4. 验证：`bash codex/tests/smoke.sh` 全绿；`skill-for-claude/install.sh` 重装后 `check-drift.sh` 回 CLEAN；
   `check-change-documents` 保持 PASS；Issue 验收标准的 grep 逐条自证。

## 风险

- 治理文件：根 `AGENTS.md` 只改目录节，由 spec 显式授权，独立 commit；本 run 不修改工作原则节，也没有依赖
  该目录节的 runtime 实施。
- 守卫：`smoke.sh` 对 `AGENTS.md`/README 有多处 `grep -Fq` 字面量钉子；`codex/runtime/tests` 钉住 README 的
  「两台公司」「本地 OrbStack」「exact `docker-release/v2` bytes」「Architecture declaration/lock」。改动只增不删
  这些短语。
- references 漂移：改 onboarding-runbook 后本机 Claude 侧 skill 立即 DRIFT；本 Issue 内用 `skill-for-claude/install.sh`
  重装回 CLEAN（该脚本经 source guard，只装 checkout 内源）。Codex 侧 `~/.agents/skills` 由人在 Codex 会话另行自查。
- 数字漂移：README §5 的踩坑条数用 06 表格最大编号（27）而不是行数，避免再次落后。

## AI 判级

```yaml
change_type: docs
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: unchanged
reason: 把 README、AGENTS.md 目录节、08、onboarding-runbook 与 04 同步到 2026-09-05 合并批次（#222/#223/#225/#228/#243/#250/#252/#254）之后的仓库现状，只补目录、状态条目、入口与字段说明，不改任何判级规则、命名元组、单闸门、broker 路径或 routine merge 条件（contract_effect=unchanged）。但范围触及根 AGENTS.md 目录节与安装到两侧 skill 的 onboarding-runbook，命中 Agent/平台治理强制规则，effective complexity=complex；change_control=production 需 spec+plan
risk_flags:
  - agent-governance
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

- Issue 正文备注自述「触碰 `AGENTS.md` 目录节，属治理文件，按 #233 T04 先例走 complex 并在 spec 显式授权该改动」。
- 根 `AGENTS.md` 工作原则：「Agent 或平台治理变更一律按 complex 处理」；「只有 complex 变更映射的 `spec` 明确授权时，
  才能修改 `AGENTS.md`」。`skill-for-codex/references/onboarding-runbook.md` 由 `skill-for-claude/install.sh` 与
  `codex/install-skills.sh` 复制为两侧 Agent 行为源。
- `contract_effect: unchanged`：七项全部是目录、日期、状态条目、入口链接与字段说明的补齐；Issue 验收标准以
  grep/ls 可核，没有任何合同规则被改写。
- `verification` 的声明依据是 `03` §3：`check-drift.sh` 改前 DRIFT/重装后 CLEAN 的前后观测、`ls -d */` 与目录节的
  一一对照、06 最大编号核对都是 required CI 不复现的一次性观测。

### 缺失的 acceptance criteria 或决策

- 无。两项解读待确认点 1 认可：（a）`analysis_provider` 定义放 `04` §4（Issue 允许 04 或 08 任一）；（b）Claude 侧
  skill 安装入口在 README 放 §5 导航表之后的「技能安装」一段，与 `08` §5 初始化段并列。
