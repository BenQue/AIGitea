---
issue: 237
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/237
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - ci-guard
depends_on:
  - 233
status: verified
branch: change/237-deproject-company-delivery
created: 2026-09-03
updated: 2026-09-03
---

# Verification · 去项目化收尾

## 基线与范围

- Commit SHA: T00 `c0c322b`、T01 `44e0641`、T02 `8244ef2`、T03 `c1c8672`、T04 `cdd4064`（HEAD `cdd4064` 时观测）；本记录与 `smoke.sh` 守卫随 T05 提交，SHA 见 PR
- 基线：`origin/main` = `c98b2e5`（Merge PR #236，#233 prune-stale-docs）
- 环境: Mac 本机 checkout（`/Users/benque/MyDocs/AISoftPlatform`，worktree
  `/private/tmp/issue-237-deproject-company-delivery`）
- 本记录负责证明的 acceptance criteria: AC-1～AC-6（spec 同名条目）

## 基线观测（改动前，只能在此刻留下）

| Command / check | Result | Evidence |
|---|---|---|
| `grep -rci NewEmaint company-delivery/ \| grep -v ':0$'` | 合计 23 | `README.md` 9、`runbook.md` 8、`compatibility/newemaint-company-pilot-v1.json` 1、`schema/inventory-v1` 2、`inventory-v2` 1、`inventory-v3` 1、`templates/handoff-manifest.example.json` 1（与 Issue 正文 23 处一致） |
| `find company-delivery -type f \| wc -l` | 19 | 与 spec 判定表 D-01～D-19 一一对应 |
| `grep -n '新项目默认' *.md` | 2 处 | `07…md:141`（§5.1 标题，本 Issue 范围）、`01…md:106`（「不再接受为新项目默认」——否定句，不把任何形态当默认，不在范围） |
| `grep -rn -i 'newemaint' codex/runtime/aisoft_company_delivery/` | 4 处 | `bundle.py:33` `COMPATIBILITY_PATH`、`contract.py:49`/`:357`、`collector.py:350` timer unit 名（runtime 绑定标识符，非目标） |
| `grep -n 'newemaint-prod' codex/runtime/tests/test_company_delivery.py` | 1 处 | `:2926` 测试钉住 runbook 短语 `aisoft-docker-release-gate <action> newemaint-prod <full-sha>` |
| `bash codex/tests/smoke.sh`（worktree = `origin/main`） | PASS，rc=0 | `Ran 651 tests … OK` + `Codex platform static smoke checks passed.` |
| `bash skill-for-claude/check-drift.sh` | CLEAN，rc=0 | 两份 SKILL.md 与源码一致（#233 references 已在本会话之外重装） |

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| `grep -n '新项目默认' 07-*.md` | 空，rc=1 | 无输出（`01…md:106` 的否定句不在范围，基线已说明） |
| `grep -c '平台不设默认' 07-*.md` | 1 | §5.1 首句「交付形态由项目 `AGENTS.md`「项目事实」与 architecture 声明，平台不设默认」 |
| `git diff -U0 origin/main...HEAD -- 07-*.md \| grep '^@@'` | 8 个 hunk | `-88,2`（P-04）、`-141`（P-01）、`-143`（P-02）、`-170,11`（P-03）、`-208`、`-219`、`-222,2`（P-05，含相邻 `:208` 一句）、`-256`（P-06）；§5.1 bullets（145–167）无 diff |
| `find company-delivery -type f \| wc -l` | 19 | 与 spec 判定表 D-01～D-19 逐行对照，处置结果见下表 |
| `grep -rci NewEmaint company-delivery/ \| grep -v ':0$'` | 合计 9（基线 23） | `README.md` 0、`runbook.md` 0；`compatibility/newemaint-company-pilot-v1.json` 1（D-04）、`schema/inventory-v1` 3、`inventory-v2` 2、`inventory-v3` 2（D-06～D-08：原 enum 各 +1 条 `$comment`）、`templates/handoff-manifest.example.json` 1（D-13） |
| `jq -r '."$comment"' company-delivery/schema/inventory-v{1,2,3}.schema.json \| grep -c 历史证据` | 各 1 | 三份 schema 顶层 `$comment` 均以「历史证据：」开头并指向 archive 与 runtime 绑定位置；`jq empty` 通过 |
| broker `gitea.issue.create --project newemaint` | `number: 75`，state open | http://gitea-ci.orb.local:3000/admin/NewEMaint/issues/75 「承接平台 company-delivery pilot 归属：compatibility matrix、newemaint-prod target 与公司两 VM Stage 进度（平台 #237）」；正文列出承接清单 4 项与验收 4 条；NewEmaint 仓文件零改动 |
| `git diff --stat origin/main...HEAD` | 14 files（T05 前）+ `smoke.sh` + 本记录 | 全部为平台仓路径；无下游仓改动 |
| `grep -c '原路径' archive/company-delivery-pilot-历史-20260903.md` | 1 | 「原路径链接兼容说明」段：`company-delivery/` 各路径不变 |
| `git diff origin/main...HEAD -- archive/README.md \| grep -c '^+\|'` | 1 | 新增一行索引 |
| 守卫反向证明（`ROOT=<临时副本>` 单独执行守卫块，runbook 副本追加 `参照 NewEMaint 的旧 profile。`） | 报红，rc=1 | 打印 `…/company-delivery/runbook.md:269:参照 NewEMaint 的旧 profile。` + `company-delivery 文档不得出现具体项目名（#237 AC-4）` |
| 同一守卫块对真实 worktree 执行 | `guard did not fire`，rc=0 | 真实 README/runbook 计数 0 |
| `bash -n codex/tests/smoke.sh`；`shellcheck -S warning codex/tests/smoke.sh` | 通过 | 无告警 |
| `git diff -U0 origin/main...HEAD -- codex/runtime/tests/test_company_delivery.py \| grep '^@@'` | 4 个 hunk（`-2931` 与 `-2978`、`-2989`、`-2992,3`） | `:2926→2931` 钉住短语 `newemaint-prod` → `<fixed-target-id>`（±1 行）；`CompanyDeliveryTopologyDocsTests.test_authoritative_docs_link_two_vm_newemaint_override` → `test_authoritative_docs_link_two_vm_reference_runbook`（项目中立断言）；其余断言不变 |
| 首次全量 `bash codex/tests/smoke.sh`（T02–T04 + 守卫，测试未同步前） | FAILED，rc=1 | `Ran 651 tests … FAILED (failures=2)`：`test_authoritative_docs_link_two_vm_newemaint_override` 对 `README.md`（要求含 `NewEmaint`）与 `07`（要求含 `Stage 00–50`、`legacy migration/phase-out`）报红——该测试钉住的正是本 Issue 迁出的 pilot 事实，按 Issue 验收第 4 条同步改为项目中立断言（spec AC-4 已补记） |
| `PYTHONPATH=codex/runtime python3 -m unittest tests.test_company_delivery`（同步后） | PASS | `Ran 76 tests … OK` |
| `bash codex/tests/smoke.sh`（含新增守卫、测试同步、T02–T05 全部改动） | PASS，rc=0 | `Ran 651 tests in 34.456s … OK` + `Codex platform static smoke checks passed.`（基线同为 651 tests OK；新增守卫块在真实树静默） |
| `git diff --stat origin/main...HEAD -- codex/tests/test-company-delivery-real-release-harness.sh codex/tests/integration codex/runtime/aisoft_company_delivery` | 空 | harness、integration 与 runtime 包零 diff |
| `bash codex/tests/integration/test-company-delivery-real-release.sh` | NOT RUN（默认边界） | `NOT RUN: Issue #124 exact real-release regression requires explicit --execute.`；`--execute` 本 Issue 未运行（无 exact release bytes，Issue 非目标） |
| 链接检查（`check-md-links.py` 对 README、07、12、13、company-delivery/*.md、archive/README.md、archive 新文件） | `links=80 broken=0` | 脚本逐个相对链接检查目标存在；本次范围内无 install-time 断链 |
| `grep -n 'NewEmaint 公司交付 runbook\|NewEmaint 两台公司 VM 人工' README.md 07-*.md` | 空，rc=1 | README §5 主表行与 07 §9 入口已改为「公司两 VM …（参考实现）」 |
| `grep -c 'company-delivery/runbook.md' 12-Linux*.md 13-*.md` | 3 / 2 | 12/13 引用保持原样，链接目标存在 |
| `git diff --stat origin/main...HEAD -- docker-release/ architecture/ codex/runtime/aisoft_company_delivery codex/runtime/aisoft_loop codex/config codex/tools templates AGENTS.md skill-for-codex skill-for-claude codex/skills 12-*.md 13-*.md` | 空 | 非目标路径未改 |
| `bash skill-for-claude/check-drift.sh`；`bash codex/check-drift.sh` | CLEAN，rc=0 | 本 Issue 不改任何技能源 |
| `PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli check-change-documents --repo <worktree>` | `pass=2 gap=0` | `PASS: change-documents`、`PASS: change-pr-url` |
| `codex/tools/apply-classification-labels.sh 237` → `--apply` → `--verify 237` | `projected` | plan `applied:false`；apply `result:updated`；verify `result:projected`，`type/platform` + `complexity/complex` |
| `grep -ci newemaint 07-*.md` | 6（基线 11） | 剩余 `:3`（状态句）、`:26–27`（§1 第 9 条）、`:41`、`:61`（组件图）、`:261`（§9 尾句）——spec 非目标（#233 F 组判定 07/12/13 正文保留），列入遗留项 |

### 判定表处置结果（AC-2）

| # | 文件 | 判定 | 处置结果 | 改后计数 |
|---|---|---|---|---|
| D-01 | `README.md` | 通用 | 已改写（定位句、拓扑表、compatibility 指针、示例路径、#124 历史证据措辞） | 0 |
| D-02 | `VERSION` | 通用 | 保留 `1.2.0` | 0 |
| D-03 | `bin/aisoft-company-delivery` | 通用 | 未改 | 0 |
| D-04 | `compatibility/newemaint-company-pilot-v1.json` | 专属 → 迁项目仓 | 字节与路径不改（runtime 绑定）；归属由 NewEmaint #75 承接；README 改为指针 | 1 |
| D-05 | `runbook.md` | 通用框架 + 专属事实 | 已改写（标题、role 描述、approval tuple、`<fixed-target-id>` ×3、§2 历史证据措辞）；pilot 事实迁 archive + #75 | 0 |
| D-06 | `schema/inventory-v1.schema.json` | 通用 | 保留 + `$comment` | 3 |
| D-07 | `schema/inventory-v2.schema.json` | 通用 | 保留 + `$comment` | 2 |
| D-08 | `schema/inventory-v3.schema.json` | 通用 | 保留 + `$comment` | 2 |
| D-09～D-12 | `schema/evidence-v1`、`gitea-transition-v1/v2`、`handoff-v1` | 通用 | 未改 | 0 |
| D-13 | `templates/handoff-manifest.example.json` | 通用 | 保留（`matrix_path` 与 runtime 常量绑定） | 1 |
| D-14～D-19 | `templates/` 其余 6 个 | 通用 | 未改 | 0 |

命令与输出照实抄；改动前的基线观测见上一节。

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 07 §5.1 措辞 | PASS | `新项目默认` 为空；`平台不设默认` = 1；§5.1 bullets 无 diff |
| AC-2 判定表覆盖与去项目名 | PASS | 19 文件逐行处置；README/runbook = 0；合计 9 全部落在 D-04/D-06/D-07/D-08/D-13，schema 三处均有「历史证据」`$comment` |
| AC-3 专属内容归属 | PASS | NewEmaint #75 已创建并写入本记录与 archive；diff 只含平台仓路径；archive 新文件含原路径兼容说明；`archive/README.md` +1 行 |
| AC-4 测试与守卫 | PASS | 守卫反向证明报红/真实树静默；测试两处钉住文档内容的断言同步（首轮 smoke 红→同步后绿）；harness/integration/runtime 包零 diff；smoke 651 tests OK rc=0；integration `--execute` NOT RUN |
| AC-5 引用一致 | PASS | `links=80 broken=0`；README/07 不再把 runbook 描述为某项目的 runbook；12/13 链接目标存在 |
| AC-6 非目标守卫 | PASS | 非目标路径 diff 为空；两侧 check-drift CLEAN |

## 遗留风险与未完成项

- **runtime 绑定标识符**（D-04 compatibility 路径与文件、D-06～D-08 `aisoft-inbound-sync@newemaint.timer`、D-13 `matrix_path`）：
  本 Issue 保留并标注；删除平台副本与参数化由衍生平台 Issue 处置（收尾时创建，编号在收尾报告）。
- `07` 其余 6 处项目名（§1 第 9 条、组件图、状态句、§9 尾句）与 `12`/`13` 正文：spec 非目标（#233 F 组判定
  保留为参考记录）；如需彻底去项目化另开 Issue。
- integration `test-company-delivery-real-release.sh --execute`：NOT RUN（需 exact release bytes，Issue 非目标）。
- NewEmaint #75 的落地由该仓自己的 Issue 会话完成；本 Issue 不改该仓。
- operator bundle 字节随 README/runbook/schema 改写而变化，`VERSION` 保持 `1.2.0`；任何正式搬运包按 runbook §2
  从 protected `main` exact SHA 重新生成并重新批准。

合格标准：每条 acceptance criterion 都有一条真实执行过的命令或一次真实观测支撑；
不得把 `NOT RUN` 改写为通过；不可达的环境与未执行项在此显式写明。
