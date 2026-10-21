---
issue: 408
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/408
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
  - shared-core
  - artifact
depends_on:
  - 392
  - 402
status: approved
branch: change/408-peer-review-evidence
created: 2026-10-21
updated: 2026-10-21
git_scope:
  - 03-Issue-Spec-Plan与单闸门开发流程.md
  - 08-双工具共存与实施.md
  - codex/config/change-template-sync.json
  - codex/runtime/aisoft_main_integration.py
  - codex/runtime/tests/test_main_integration.py
  - codex/runtime/tests/test_session_contract.py
  - codex/tests/smoke.sh
  - codex/tests/smoke-pin-baseline.json
  - codex/tests/test-aisoft-entry.sh
  - codex/tests/test-external-skill-versions.sh
  - codex/tools/aisoft
  - codex/tools/check-external-skill-versions.py
  - docs/changes/408-peer-review-evidence/plan-peer-review-evidence-261021.md
  - docs/changes/408-peer-review-evidence/spec-peer-review-evidence-261021.md
  - docs/changes/408-peer-review-evidence/summary-peer-review-evidence-261021.md
  - docs/changes/408-peer-review-evidence/verification-peer-review-evidence-261021.md
  - docs/governance/platform-e2e-acceptance.md
  - docs/governance/remediation-roadmap.md
  - docs/governance/review-evidence-index.md
  - skills/aisoft-platform/SKILL.md
  - skills/aisoft-platform/references/onboarding-runbook.md
  - skills/gitea-development-loop/SKILL.md
  - skills/issue-session-flow/SKILL.md
  - templates/docs/changes/_template/plan.md
  - templates/docs/changes/_template/spec.md
  - templates/docs/changes/_template/verification.md
  - usage/CONTRACT.md
  - usage/bundle.json
---

# R15 对等最小能力集读回、审查证据索引与轮换、Cursor 使用层首次验收

## 目标与原因

「Claude、Codex、Cursor 用同一套能力」要能一条命令读回，每端缺什么写得出原因；交叉审查要有统一、可复核的记录；
Cursor 要在使用层真实走完一个 Issue；每批固定出现的仪式性提交要收掉。来源：复审 P1-5、P2-3、P2-7，计划 R15。

现状（2026-10-21 读回，`origin/main` = `38ddc920`）：

- `check-external-skill-versions.sh` 只报 superpowers 与 Matt 的 pin，没有平台技能、只读审查、smoke 可跑三项，也没有每端一行结论。
  本机读到 Claude superpowers `PIN_CLEAN`、Codex superpowers `PIN_NOT_INSTALLED`（官方市场缓存 5.1.3，未提供 7.0.0）、Cursor 无 `--repo` 时 `NOT_CHECKED`。
- 审查证据：R0–R3 的 PR 正文没有交叉审查记录；R4 只在 PR 正文里（Codex 审 `78a3237`，PASS-WITH-NITS）；R5、R6、R6b 只记了修复 head，缺首轮 head；
  R7、R8、#385、#387 每轮有 head。四种写法互不相同，实现方从未作为字段记录。
- 确认点 1 的提交改 summary、spec、plan 三处 `status`（例：`f1707474`）。代码里只有 broker 推送闸门
  `aisoft_main_integration.py` 的 `scope()` 读 spec 状态（要求 `approved`），plan 与 verification 的状态无人读。
- 建 PR 后要手工跑 `backfill-pr-url`、提交、再推一次（例：`2c43b08f`）。
- SFM 没有 Cursor 落点（无 `.cursor/`），R11 的采用 Issue SFM #184 默认只采用 claude、codex 两端。本机 `cursor-agent` 已登录。

## 设计

### 1. 最小能力集与读回

`08` §7.1 新增「最小能力集」表，行是能力，列是 Claude、Codex、Cursor，每格写读回来源：

| 能力 | Claude | Codex | Cursor（使用层，项目级落点） |
|---|---|---|---|
| 平台技能 | `skill-for-claude/install` 读回 | `install-skills` 读回 | `--repo` 下 `.cursor/skills` 与发布包导出逐字节一致 |
| Matt pin | `check-plugin-pin.sh` | 安装的 vendor 快照版本 | `--repo` 下 Matt 技能哈希 |
| superpowers pin | 已有读回 | 已有读回 | `--repo` 下 superpowers 技能哈希 |
| 只读审查 | `claude` CLI 可执行 | `codex` CLI 可执行（`codex exec -s read-only`） | `cursor-agent` 可执行且已登录（`--mode ask`） |
| smoke 可跑 | 维护层：`bash`、`python3`、`jq`、`rg`、`git` 齐全 | 同左 | 不适用（Cursor 不进维护层） |

读回扩展现有 `check-external-skill-versions.py`，不新建脚本：加 `--capabilities`（必须同时给 `--repo`），保留现有各行，末尾每端加一行
`CAPABILITY <tool> <PASS|KNOWN_EXTERNAL|GAP> <逐项状态>`，此时最后的 `RESULT` 由这三行决定；不带 `--capabilities` 时输出与退出码不变。

- `PASS`：该端每项都满足。
- `KNOWN_EXTERNAL`：唯一的不满足项属于登记过的外部原因，行内写原因。首个登记项是 Codex superpowers
  `PIN_NOT_INSTALLED`（官方市场尚未提供 7.0.0，#392 负责人决定不由平台安装）。登记表是脚本常量 `KNOWN_EXTERNAL`（适配记录的 schema 是逐键锁死的，不扩它）。
- `GAP`：其余任何不满足，含 `UNKNOWN` 与 `PIN_DRIFT`。

只读审查一项只检查 CLI 可执行与登录状态，不发起模型回合；模型回合能否跑通由交叉审查本身证明，记入审查记录。
脚本仍然只读、不安装、不联网。

### 2. 审查记录与索引

- `templates/docs/changes/_template/verification.md` 新增固定节 `## 交叉审查`，表头
  `| 轮次 | 实现方 | 审查方 | exact head | 结论 | 发现与处置 |`，`exact head` 写 40 位 SHA。
  项目仓不适用平台交叉审查时整节删除（与「部署验收」同一写法）。
- 新建 `docs/governance/review-evidence-index.md`：每批一行，列「批次、Issue、PR、merge SHA、实现方、审查方、审查 head、各轮结论、来源」，
  回填 R0–R8（含 R6b）、#385、#387，另加 #370（Claude 实现、Codex 审）。仓内与 PR 正文都没有的，格子写「未记录」，不补造；
  R0–R3 写「未做交叉审查」并给 PR head。缺首轮 head 的（R5、R6、R6b）若项目库 `codex-review-*.md` 也没有，就写「未记录」。
  此后每个平台 complex 批次合并后追加一行，由收尾步骤负责。
- `03` §7「交叉审核」改写：实现方 ≠ 审查方；每批在 verification 的固定表和索引里记录实现方与审查方。具体方向按未决问题 1 的决定写。

### 3. approval 只写 summary（P2-7）

- 确认点 1 只改 summary 的 `status: approved`。spec、plan 模板去掉 `status` 字段；已有文档里的 `status` 照旧合法，不批量改写。
- `aisoft_main_integration.py` 的 `scope()` 不再要求映射 spec `status: approved`，summary 的 `approved`/`pr-open` 仍是闸门，
  spec 的 issue、branch 绑定检查保留。canonical 模板 git scope 合同（`03` §3）里「spec 必须 `approved`」同步改为由 summary 决定。
- 反向证明：summary 不是 `approved`/`pr-open` 时推送照样被拒；spec 写成别的 Issue 照样被拒。
- 生效需要两台重装 broker；合并前旧闸门仍在，本批自己的文档保留 spec `status: approved` 以通过旧闸门。

### 4. 一步建 PR（P2-7）

新增 `aisoft open-pr N --title <标题> --body-file <文件>`，确认点 2 之后由会话调用一次：

1. 核对 exact 分支、worktree 归属、干净工作树与 summary 状态 `approved`。
2. 本地先校验正文合同（恰好一行 `Closes #N`，映射 summary 路径恰好出现一次），不合格不发任何 broker 请求。
3. broker `git.push.change` 首推；`gitea.pull.create`；从返回取 PR 编号，用已有 `backfill_pr_number` 回填 summary；
   只提交 summary；`check-change-documents`；再 `git.push.change`。
4. 任何一步失败就停在原地报告；重跑安全：`gitea.pull.create` 对同一 change 已有开放 PR 时返回原 PR，回填已是同值时不再提交。

`backfill-pr-url` 保留为兼容与手工修复入口。broker 的发现方式与 `aisoft classify` 相同。不新增 broker 操作。

### 5. Cursor 使用层首次验收

在 SFM 开一个项目侧 small Issue，内容是为 SFM 采用 Cursor 落点（`--adopt --tools cursor`，版本跟随 SFM 当时 pin 的发布包），
由 Cursor 会话（本机 `cursor-agent`，我在 SFM 的 change worktree 里驱动）按 SFM 自己的流程走到 PR 候选；新落点生效后再开一个 fresh
Cursor 会话读回 `aisoft-platform` 技能能触发。结果写进 `platform-e2e-acceptance.md`：「采用记录」与「验收记录」两表加「工具」列，
已有行补 `Claude`。SFM PR 仍由负责人合并。依赖 SFM #184 先合并（它在途）。走法按未决问题 3 的决定。

### 6. 发布

改了 spec/plan/verification 模板与会话工具，同 PR `usage-bundle.sh --release <下一空闲版本> --compatibility minor --notes ...`
（预计 1.9.0；R12 若先合并就顺延），并 `change-template-sync.sh --refresh-digest`，下游同步清单写进 verification。

## 验收标准

- AC-1 `check-external-skill-versions.sh --repo <SFM checkout> --capabilities` 输出三行 `CAPABILITY`；三端各自是 `PASS`，或是 `KNOWN_EXTERNAL` 且原因是已登记项；
  测试覆盖三种结论，反向证明：把登记项删掉，Codex 那行变 `GAP`、`RESULT` 非 PASS。
- AC-2 `review-evidence-index.md` 覆盖 R0–R8（含 R6b）、#370、#385、#387，每行有审查 head（40 位）或明写「未记录/未做」及原因，每行有来源。
- AC-3 verification 模板有固定「交叉审查」表；`03` §7 写明实现方 ≠ 审查方与记录位置；本批 verification 用新表记录自己的审查。
- AC-4 确认点 1 之后的 approval 只改 summary 一处：broker 闸门的测试证明 spec 无 `status` 时推送可过、summary 不合法时仍拒。
- AC-5 `aisoft open-pr` 一条命令完成首推、建 PR、回填、提交与再推；测试用假 broker 覆盖正常路径、正文不合格零请求、半途失败后重跑不重复建 PR 不重复提交；本批 PR 用它开。
- AC-6 SFM 有一个由 Cursor 会话完成的 small Issue 与 PR，项目侧 verification 链接写进 E2E 表的「工具」列。
- AC-7 发布新版本，`usage-bundle.sh --verify` 与 `change-template-sync.sh --verify-digest` PASS；`bash codex/tests/smoke.sh` 全绿；未参与实现的一方只读审查 PASS。

## 风险与回滚约束

- broker 闸门放宽：只删 spec 状态一条，绑定检查不动；整 PR revert 即恢复，revert 后要重装才回到旧闸门。
- 新模板发布后，没有 pin 的项目 `change-templates` 变红，按下游同步清单各自复制。
- SFM 的 Cursor 采用是独立项目 PR，可单独 revert。

## 非目标

- 不安装或升级任何外部技能包，不替 Codex 装 superpowers 7.0.0。
- 不往 `~/.cursor` 写任何东西；Cursor 不进维护层。
- 不改路由表，不加确认点，不改 broker 操作集合。
- 不改 R12 负责的 `aisoft-project-check.sh`、`change_audit.py`、`usage-bundle.py` 的 lock 读取。

## 已决问题（确认点 1，负责人 2026-10-21 12:19Z「确认」，四项均按推荐）

1. 反向审查批次：选 a。`03` §7 写「实现方 ≠ 审查方，默认 Claude 实现、Codex 只读审查，每批记录双方」；计划中的反向批次由负责人取消，AC-3 不含反向批次。
2. 能力集：选 a。允许 `KNOWN_EXTERNAL`，原因必须是登记项。
3. Cursor 会话：选 a。SFM #184 合并后开 SFM small Issue「采用 Cursor 落点」，由本机 `cursor-agent` 完成，fresh Cursor 会话读回技能触发；平台 PR 在它出 PR 候选后再开。
4. P2-7：选 a。按 §3、§4 做全，合并后两台重装 broker。
