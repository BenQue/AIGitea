---
issue: 436
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/436
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - agent-governance
  - shared-core
  - external-contract
depends_on: []
status: passed
branch: change/436-spec-for-every-issue
created: 2026-10-31
updated: 2026-10-31
---

# 验证记录

## 基线与范围

- Commit SHA: 实现候选 `fb2156b4186313e1853a05d924f1308009d65f28`（之后只有本记录与审查证据提交）
- 基线：`origin/main` = `94ecd623336a80df84f1eff85c089f4f8a08d727`
- 环境: Mac 本机，平台源码 runtime；broker 只用于读 Issue、判级投影与标签
- 本记录负责证明的 acceptance criteria: AC-1 至 AC-6

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| `python3 -m unittest discover -s tests -t .`（codex/runtime） | PASS | 808 个用例；新增：small/development 缺 spec、执行入口拒绝高风险缺 plan、预检拒绝 summary 与 spec 一致写错的分支、legacy 推断的可选文档不算义务、映射文件缺失时预检与 `aisoft classify` 仍报 GAP、small spec 复杂度不符、D2 含高风险缺 plan 与有 plan、spec AC 合成 T01、development 有 plan 走 Txx、文档义务表五行与篡改 fail closed、预检四类缺口、模板产出的简版 spec 通过 `scope()` 与旧 summary-only 形状被拒 |
| `bash codex/tests/smoke.sh` | PASS | 含 test-aisoft-entry（简版 spec fixture）、test-usage-bundle、模板 digest 校验 |
| 反向证明 | PASS（各自变红） | 去掉 small 的 spec 义务 → 4 例红；去掉 D2 风险分支 → 高风险缺 plan 用例红；去掉 git_scope 覆盖检查 → 预检用例红；合成 T01 改回 Issue 正文 → T01 用例红；恢复后工作树干净 |
| `aisoft classify 436` | PASS | 打印路由行与「文档预检 #436: OK」 |
| `aisoft classify --verify 436` | PASS | `projected`（type/platform、complexity/complex） |
| `rg` 旧说法（AC-1） | PASS | 平台仓非历史文本不再有「small/development 不写 spec」类句子；剩余命中只在 `03` 来历表 #134 行、已合并 change 目录与历史 fixture |
| `usage-bundle.sh --release 1.22.0`（AC-5） | PASS | `sha256:3870be04af65769786f0afe2a613b4a36336fab4a83c92cf2e075f4eaed31e16`，notes 写迁移方式 |
| `change-template-sync.sh --refresh-digest` | PASS | digest 已刷新；4 个持有副本的项目为 stale，需各自 Issue 同步（既有广播机制） |
| typed `git.push.change` / `open-pr` 实推 | NOT RUN | 确认点 2 之后执行；守卫逻辑未改，由 `test_main_integration` 与 project-source 工具用例覆盖 |
| 下游项目采用 1.22.0 | NOT RUN | 不在本票范围 |

## 交叉审查

| 轮次 | 实现方 | 审查方 | exact head | 结论 | 发现与处置 |
|---|---|---|---|---|---|
| 1 | Claude | Codex（`codex exec -s read-only -m gpt-6-astra -c model_reasoning_effort="high"`） | `f7951980cad94f437d7f6ccfdd06b79033bd09e0` | FAIL（1 P1、4 P2） | P1 执行入口在 development 无 plan 时直接合成 T01，绕过 D2 → 执行前按文档义务校验并补用例；P2 预检只比 spec 与 summary 的 branch → 由目录名推导 exact branch；P2 legacy 推断的四份文档被当成义务 → 新增 `declared_documents`；P2 `gitea-spec-plan` 与 `AGENTS.md` 措辞漏 D2 → 改写；P2 1.22.0 迁移说明未分风险 → 重发同号分列步骤。均已修 |
| 2 | Claude | Codex（Herdr 只读窗格：`herdr tab create --workspace w6 --cwd <worktree> --label review-436 --no-focus` → `herdr agent start codex-review-436 --kind codex --pane w6:p3 -- --sandbox read-only --ask-for-approval never -m gpt-6-astra -c model_reasoning_effort=high` → `herdr agent prompt` → `herdr agent wait --until idle`） | `c98a22bf2bc946c27978280b73eb785913ed8360` | FAIL（第 1 轮 5 项全部 fixed；新 2 P2、1 P3） | P2 `aisoft-platform` 技能 superpowers 对照表仍写「small 只有 summary」→ 改为引用文档义务；P2 映射文件缺失时 `aisoft classify` 提前退出、不打印预检 → 预检先报映射缺口，classify 不再提前退出，补 CLI 用例并反向证明；P3 `gitea-spec-plan` description 仍限 production complex → 改为所有已判级 Issue。均已修，1.22.0 重发同号 |
| 3 | Claude | Codex（同一 Herdr 只读窗格 w6:p3，`herdr agent prompt` → `herdr agent wait --until idle`） | `1ce08c1e76ac47c5175ec87f9e53ff9593cff886` | PASS | 第 2 轮三项全部 fixed；新发现无。之后只有本记录与审查证据索引的提交 |
