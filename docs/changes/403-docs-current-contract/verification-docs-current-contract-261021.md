---
issue: 403
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/403
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - ci-change
depends_on:
  - 391
  - 395
  - 396
status: pending
branch: change/403-docs-current-contract
created: 2026-10-21
updated: 2026-10-21
---

# R14 文档现行态验证记录

## 基线与范围

- 基线：`origin/main` = `fdf93c1`（R10a、R10b、R13、R16、#370 均已合并）；度量基准 `77ad607`。
- Ticket commit：T00 `d9f13c2`（映射文档），T01 `f1533d2`（分册改写），T02 `023e2ba`（smoke 治理步骤，单独 commit 后停止并重读合同），T03 `1dcd488`（`--render-readme`）。
- 环境：Mac 平台检出，change worktree `/private/tmp/issue-403-docs-current-contract`，本机 `rg` 为真实二进制。
- 本记录负责证明 AC-1 至 AC-8。实现按 superpowers `executing-plans` 依 T01→T04 顺序内联执行，每张 ticket 前后用 `verification-before-completion` 核验。

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| AC-1 `git show 77ad607:03-… \| rg -c '#[0-9]{2,3}'` 对比 `rg -c '#[0-9]{2,3}' 03-…` | PASS | 53 → 16（开工时 57）；16 行全部是 `03` 第 590–605 行，即 `## 来历`（第 586 行）表内 |
| AC-2 01–08 第三行 `> 现行合同：` 与 `## 来历` | PASS | 8 册各 1 个；来历表 SHA 逐个 `git cat-file -e`，并与 `git log --merges --first-parent` 的 Issue→merge 映射逐行比对，0 不符 |
| AC-2 `rg -n '尚未(实施\|运行)\|尚待' 0[1-8]-*.md` | PASS | 0 命中；未实施事项集中在 README §8「未实施清单」（12 行） |
| AC-3 README 日期版本守卫 | PASS | smoke 内 python 守卫：剥掉链接目标、跳过 §5 导航表行后无 `YYYY-MM-DD`、`vN.N`、`N.N.N` |
| AC-3 反向证明 | PASS | 把 smoke 新增守卫逐字抽到隔离副本跑：README 末尾分别加「核对日期 2026-10-21」「核对日期2026-10-21更新」「版本v1.2已发布」「Gitea 1.26.4」均 rc=1；还原 rc=0。后两种无空格中文写法是 Codex 第 1 轮 F5 找出的漏检，守卫已改用 ASCII 边界 |
| AC-4 `bash codex/tools/aisoft-platform-readiness.sh --render-readme` | PASS | 输出 9 行表：源码、治理仓库 7、broker 操作 34、installer 安装面 6、规范标签 27（type/* 10）、发布包 1.7.0、Matt v1.3.1、superpowers v7.0.0、catalog 2026.09.0，每行带来源文件 |
| AC-4 `bash codex/tests/test-platform-readiness.sh` | PASS | spy broker 证明不调用 broker；在由合成夹具 manifest（#380）搭的隔离 checkout 上逐字比对整张 9 行表（值与来源列）；缺键、错类型、空版本、缺 Matt sha、缺 catalog revision、缺 superpowers commit 七种输入都 rc=1 且 stdout 为空 |
| AC-5 `grep -c 'grep -Fq' codex/tests/smoke.sh` 与 `smoke-pin-baseline.json` | PASS | 100 → 89，基线 89 |
| AC-5 反向证明 | PASS | 隔离副本 smoke 末尾加一行 `grep -Fq` rc=1（「90 行，超过基线 89」）；`04` 的 `## 来历` 改名 rc=1；`06` 第三行改为「> 状态：」rc=1；还原 rc=0 |
| AC-5 01–08/README 正文钉子清单 | PASS | 见下节；改写后 `grep -n 'grep -Fq' smoke.sh` 对 01–08/README 零命中 |
| AC-6 `01` §4.3、GLOSSARY | PASS | §4.3 标题与首段写明「按项目需求提供的 runner 能力，不是平台默认工具链」；GLOSSARY 加 11 条 ADR 0002 术语，`AWAITING_PR_CONFIRMATION`、`READY_FOR_REVIEW` 改指 `03`；README、GLOSSARY、01–08 的相对链接逐个 `os.path.exists`，0 断链 |
| AC-7 `python3 codex/tests/check-project-leak.py` | PASS | `--write-baseline` 后 site 19 文件 82 处（R13 基线）→ 10 文件 37 处，项目名 10 文件 40 → 9 文件 38；没有任何文件计数上升（收紧前检查器 PASS） |
| AC-8 `git diff --stat origin/main -- skills templates usage` | PASS | 空；被技能与模板引用的 `03` §1/§3/§8/§11/「交叉审核」、`06` §1.0/§1.1/踩坑号、`08` §5/§7.3 编号与标题保留 |
| AC-8 `bash codex/tools/usage-bundle.sh --verify` | PASS | `VERIFIED 1.7.0` |
| AC-8 `bash -n`、`shellcheck` smoke、readiness、readiness 测试 | PASS | 三个文件 0 告警 |
| AC-8 doc 相关单测 | PASS | `test_session_contract`、`test_architecture_governance`（改为钉标题）、`test_route_policy` 19 个 OK |
| AC-8 `bash codex/tests/smoke.sh` | 见说明 | T02 head `023e2ba` PASS（5:38）；T04 head `2b1c0de` **FAIL**：#380 守卫拦下 T03 测试直接读真实 manifest（`test-platform-readiness.sh:133–141`），已改为读合成夹具；修复后的 head 结果记在「交叉审查」节 |
| AC-8 Codex 只读交叉审查 | 进行中 | 第 1 轮 FAIL（6 项 P2、1 项 P3），处置见下节 |
| AC-8 `apply-classification-labels.sh --verify 403` | NOT RUN | 合并前执行 |

## smoke 正文钉子改写清单

| 原钉子（文件：短语） | 处置 |
|---|---|
| `03`：「不在任何下游项目引入阻塞式 required check」 | 改钉 `03` 标题「模板是 vendored 副本：改动必须由上游广播」；语义仍由 `downstream_required_check == forbidden` 的 jq 断言钉住 |
| `08`：「型号按工具映射，合同只写档位」 | 改钉 `08` 标题「7.3 模型档位」 |
| `03`：`type/feature`、`complexity/complex` | 改钉 `03` 标题「4. 平台三维标签与 Matt triage」 |
| `04`：`requested_complexity` | 改钉 `04` 标题「2. 判级输出」 |
| `03`：`### 衍生 Issue 的正文与认领` | 改用 `require_heading` |
| `03`：`### change worktree 的单写者归属（#298）`、`aisoft-owner.json` | 合并为 `require_heading` 「change worktree 的单写者归属」 |
| `03`：`### 交叉审核（…）`；`08`：`6. **交叉审核**` | 改用 `require_heading`；`08` 改钉「7.1 平台维护层（平台仓验收，两个 provider 对等）」 |
| `06`：`WORKTREE_OWNER_MISMATCH` | 删除；归属合同由 `03` 标题与技能侧钉子覆盖 |
| `08` 升级适配清单 11 个锚点 | 改钉 `08` 两个标题「外部技能包升级后的适配检查」「附：升级适配记录」 |
| `02`「首次部署」、`05`「READY_FOR_REVIEW」、`06`「标准故障包」、`07`「生产环境只执行…」 | 分别改钉「7. 首次部署与部署变更验收」「1. 事件覆盖（Gitea 自动发信）」「3. AI 辅助故障诊断」「7. 生产边界」 |

不在本票范围、保留原样：技能、`AGENTS.md`、`CLAUDE.md`、模板与 `docs/agents/` 上的钉子；`test_session_contract.py` 对 `08` §3 单写者条目的变异测试（`08` §3 那一条保持原文）。

## 规则未丢失的自查

每册改写只删叙事、过时状态与 Issue 归属，规则句保留；被删的内容去向：

- `03`：#136/#163/#192 等故事段与「已经错过窗口」逐 Issue 表 → 来历表一行；§6.1 PAT 轮换的 grant、store、事务顺序细节 → 指向 `06` §4.1（原文两处重复，`06` 保留全文）；#360「T02 尚未运行」与 #316「T01/T02A 分阶段」等单票授权句删除（#360 已于 `06afadf` 合并，`gitea.credential.rotate` 已在 source）。
- `06`：§1.0 的 #136 lease 历史改写为现行的普通 FF 推送语义与三个错误码表（取自 `broker.py` 当前代码）；#143/#222/#225 的故事段压成一句用途说明，规则要点保留；#340 已退役小节删除。
- `08`：§4 压成两句；§5 三张已填写的升级适配表原样移到 `## 附：升级适配记录`。
- `01`：两处「更正（#309）」块删除，as-built 表与日期保留；§4.1 Gitea 侧超时的「留给独立评估」移入未实施清单。
- README：§1 手写状态表与页首版本/核对日期/源码基线删除，改为指向 `--render-readme`；新增 §8 未实施清单。

规则是否丢失由 Codex 对照改写前原文逐节复核，见下节。

## 交叉审查

审查方 Codex（`codex exec -s read-only`），任务书与结论原文在项目库 `codex-review-403.md`。

| 轮次 | 审查的 head | 结论 | 发现与处置 |
|---|---|---|---|
| 1 | `2b1c0de` | FAIL | F1 `03` canonical 模板节误删 source/installed 一致性、`[Issue tip,main]` 整合与 tree 验证、no-op 重验等不变量 → 恢复为一句不变量清单。F2 `06` 把 `REMOTE_BRANCH_MOVED` 写成「一定没写入」，而传输失败也返回此码且可能已写入 → 改写为看回执的 `possible_write`/`write_status`/`observed_remote_head`。F3 README 未实施清单把已完成的 marketplace 注册与来源切换列为未实施（#354 verification）→ 只列 Codex 模型回合与 Claude `retro` 残余项，`08` §5 同步，`08` 来历补 #354。F4 删掉标题里的「（#360）」断了 `project-align.md` 的片段链接 → 标题前加显式兼容锚，技能仍零 diff；全仓片段链接重扫 0 断链。F5 README 守卫的 Unicode `\b` 放过「核对日期2026-10-21更新」→ 改 ASCII 边界并补反向用例。F6 `--render-readme` 缺键渲染成 0、缺 pin 渲染成 `null` 仍 rc=0 → 每个事实先校验键、类型与非空，测试覆盖七种坏输入。P3 站点基线原值应为 82 → 已更正 |
