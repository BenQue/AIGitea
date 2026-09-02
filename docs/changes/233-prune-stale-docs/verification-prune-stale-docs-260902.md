---
issue: 233
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/233
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: unchanged
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
depends_on:
  - 231
  - 232
status: verified
branch: change/233-prune-stale-docs
created: 2026-09-02
updated: 2026-09-03
---

# Verification · 清除过时文档与概念

## 基线与范围

- Commit SHA: `be27e54`（T01 `31be7af`、T02 `ad5349e`、T03 `fb241ca`、T04 `be27e54`；`ae154eb` 为 approved 合同
  文档提交；本记录与 `smoke.sh` 守卫随 T05 一并提交，SHA 见 PR）
- 基线：`origin/main` = `0df92177497c1b4b16d9ed0c0bc5780849d7e7fb`（Merge PR #235，#232 deploy-env-guidance）
- 环境: Mac 本机 checkout（`/Users/benque/MyDocs/AISoftPlatform`，worktree
  `/private/tmp/issue-233-prune-stale-docs`）；本机两侧 skills 已按 #232 合并后的源重装（基线 CLEAN）；
  本机 `rg`、`shellcheck` 可用
- 本记录负责证明的 acceptance criteria: AC-1～AC-8（spec 同名条目）

## 基线观测（改动前，只能在此刻留下）

| Command / check | Result | Evidence |
|---|---|---|
| Issue 验收第 2 条 grep（活文档） | 5 处命中 | `README.md:164`（导航行 Codex-first / Claude parity 条件）、`08…md:147`（§8 Claude Code 接入条件）、`04…md:147`（§10 Codex-first 验证顺序）、`skill-for-codex/SKILL.md:26`（After AISoftPlatform Issue #35）、`skill-for-codex/references/onboarding-runbook.md:97`（Legacy ci-bot collaborator gate） |
| `bash check-md-links.sh <origin/main 树>`（脚本见 AC-3 节） | `links=113 broken=3`，rc=1 | 3 条均为 `skill-for-claude/aisoft-platform/SKILL.md -> references/{onboarding-runbook,project-align,private-gitea-access}.md`（install-time 链接，`skill-for-claude/install.sh` 复制后才存在；基线即存在，非本 Issue 引入） |
| `rg -ni '<#231 AC-1 pattern>' skill-for-codex/references/*.md` | 2 处 | `private-gitea-access.md:10`（NewEmaint's `gitea`）、`onboarding-runbook.md:3`（rsdesign-new 历史试点） |
| `bash codex/tests/smoke.sh`（worktree = `origin/main`） | PASS，rc=0 | `Ran 651 tests in 35.248s … OK` + `Codex platform static smoke checks passed.` |
| `bash codex/tools/aisoft-project-check.sh --repo <worktree> --kind docs` | `result: pass=2 gap=2 skip=4` | `GAP: pointer-sections`、`GAP: change-templates`（平台仓结构性 GAP）；`PASS: change-documents`、`PASS: change-pr-url` |
| `bash skill-for-claude/check-drift.sh` / `bash codex/check-drift.sh` | CLEAN，rc=0 | 基线已安装副本与源一致 |
| `grep -n 'AISOFT_ONBOARDING_MODE=software-repository' codex/tests/smoke.sh` | `465` | 断言对象是 `skill-for-codex/SKILL.md:48` 退役 gate 块 |
| `grep -c -E 'override_reason\|needs-human-decision' codex/runtime/tests/test_classification.py` | 6 | A-06 改写依据：classifier case 已由 runtime tests 固化 |
| `docs/changes/213-routine-live-pilot/verification-*.md` AC 表 | live layers 全部 NOT RUN | C-08 并入 README:23 的 #208 约束仍为现状 |

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| Issue 验收第 2 条 grep：`grep -rn -E 'Codex-first\|Claude parity 条件\|Claude Code 接入条件\|After AISoftPlatform Issue #35\|Legacy .?ci-bot.? collaborator gate' --exclude-dir=archive --exclude-dir=.git --exclude-dir=vendor . \| grep -v -E '^(\./)?docs/changes/'` | 空，rc=1 | 无输出（去掉 `docs/changes/` 过滤时只命中本 Issue 与 #231 的 change 文档，属排除范围） |
| `bash check-md-links.sh <worktree>` | `links=117 broken=3`，rc=1 | `BROKEN` 集合与基线完全相同（3 条 install-time 链接）；新增 4 条链接（README §1 历史链接、`08` §4 历史链接、`archive/README.md` 索引、`archive/平台状态历史` 回指 README）全部解析 |
| `grep -rn '08-Codex双工具共存与实施.md' --include='*.md' . \| grep -c '\]('` | 0 | 旧文件名只剩 `archive/10`、`docs/changes/*` 的代码跨度（含本 Issue 文档引用旧名）；`archive/11:5` 链接已改指新名 |
| `rg -ni '<#231 AC-1 pattern>' skill-for-codex/references/*.md` | 空，rc=1 | B-05、B-10 清掉后为空 |
| `bash codex/tests/smoke.sh`（含新增 references 守卫、已删陈旧断言） | PASS，rc=0 | `Ran 651 tests in 35.290s … OK` + `Codex platform static smoke checks passed.`（与基线同为 651 tests） |
| `bash -n codex/tests/smoke.sh`；`shellcheck -S warning codex/tests/smoke.sh` | PASS | 无告警 |
| 守卫反向证明 | 报红，rc=1 | 把 `skill-for-codex/references/*.md` 复制到临时目录并向 runbook 副本追加 `参照 NewEMaint 的旧 profile。`，以 `ROOT=<临时目录>` 单独执行守卫块 → 打印命中行 `onboarding-runbook.md:386:参照 NewEMaint 的旧 profile。` + `共享 references 不得出现具体项目名（#233 G-01）` 并退出 1；同一块对真实 worktree 执行 → `guard did not fire`，rc=0；真实 runbook `grep -c -i NewEMaint` = 0 |
| `grep -n 'AISOFT_ONBOARDING_MODE=software-repository' codex/tests/smoke.sh` | 空，rc=1 | 陈旧断言已删除 |
| `bash codex/tools/aisoft-project-check.sh --repo <worktree> --kind docs` | `result: pass=2 gap=2 skip=4` | 与基线逐行一致：`GAP: pointer-sections`、`GAP: change-templates`、`PASS: change-documents`、`PASS: change-pr-url` |
| `bash codex/tests/test-install-claude-skills.sh` | PASS | `claude skill install tests passed` |
| `bash codex/tests/test-project-check.sh` | PASS | `project check tests passed (37 cases)` |
| `PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli check-change-documents --repo <worktree>` | `pass=2 gap=0` | `PASS: change-documents`、`PASS: change-pr-url`；`resolve-documents 233` 返回四个映射 basename |
| `git diff --stat origin/main...HEAD -- 03-*.md` | 空 | 判级规则与命名元组定义分册无 diff |
| `git diff -U0 origin/main...HEAD -- AGENTS.md \| grep '^@@'` | `@@ -38 +38 @@`、`@@ -57 +57 @@` | 只改目录段两行；工作原则、初始化与开发编排、Git 三段无 diff |
| `git diff -U0 origin/main...HEAD -- README.md \| grep '^@@'` | 行 3、11、14–35（§1）、164（§5 导航行） | §3（81–95）与 §4（96–142）无 diff |
| `git diff -U0 origin/main...HEAD -- skill-for-codex/SKILL.md \| grep '^@@'` | `-26,2`、`-44,27`、`-79,2` | `:86–99`（命名元组、判级、单闸门）无 diff |
| `git diff -U0 origin/main...HEAD -- skill-for-codex/references/onboarding-runbook.md \| grep '^@@'` | `-3`、`-19`、`-43,3`、`-97`、`-99,28`、`-258` | `:36–41`（routine 条件）、`:51–68`（broker 接入步骤）、`:260–262`（routine merger）无 diff |
| `git diff -U0 origin/main...HEAD -- 04-*.md \| grep '^@@'` | `-37,2`、`-46,0`、`-147`、`-156`、`-160` | §9 终态（含 routine hard gate 句）无 diff |
| `git diff -U0 origin/main...HEAD -- 09-*.md \| grep '^@@'` | `-6,0`、`-48,0`、`-510` | §16（#208 routine 合同）无 diff |
| `git diff -U0 origin/main...HEAD -- 06-*.md \| grep '^@@'` | `-70`、`-196`、`-232`、`-399` | 四处「发布后」措辞；§1.0 broker 段其余无 diff |
| `git diff --stat origin/main...HEAD -- docker-release/ architecture/ codex/runtime codex/tools codex/config templates company-delivery` | 空 | 非目标路径未改 |
| `git diff --stat -M origin/main...HEAD -- archive/` | 3 项 | `11-…md`（+1/−1，仅链接目标）、`README.md`（+1 索引行）、`平台状态历史-20260902.md`（新建 41 行）；无删除 |
| `git diff --stat -M origin/main...HEAD` | 24 files（T04 头 +632/−154；T05 含本记录与守卫后 +770/−154） | 全部为平台仓路径；无下游仓改动 |
| `bash skill-for-claude/check-drift.sh`（改动后、未重装） | DRIFT，rc=1 | `DRIFT: aisoft-platform/references/onboarding-runbook.md`、`DRIFT: aisoft-platform/references/private-gitea-access.md` |
| `bash codex/check-drift.sh`（改动后、未重装） | DRIFT，rc=1 | `DRIFT: gitea-platform-ops/SKILL.md`、`aisoft-platform/references/onboarding-runbook.md`、`aisoft-platform/references/private-gitea-access.md`、`aisoft-platform/SKILL.md` |
| 重装后 `check-drift.sh` CLEAN | NOT RUN | Issue 非目标：本 Issue 不安装或更新全局 skills；合并后独立执行 |
| `codex/tools/apply-classification-labels.sh 233` → `--apply` → `--verify 233` | `projected` | plan `applied:false`；apply `applied:true, result:updated`；verify `result:projected`，`detail: Issue #233 carries the classification its merged summary declares`，`type/platform` + `complexity/complex` |

命令与输出照实抄；改动前的基线观测见上一节。

### AC-3 链接检查脚本

```bash
#!/usr/bin/env bash
# AC-3 (#233): every relative Markdown link to a .md target inside the repository must resolve.
# Inline code spans (`...`) are stripped first: quoted link text inside backticks is not a link.
# Usage: bash check-md-links.sh <repo-root>
set -euo pipefail
root="${1:-.}"
cd "$root"
total=0; broken=0
while IFS= read -r line; do
  file="${line%%:*}"; rest="${line#*:}"
  rest="$(printf '%s' "$rest" | sed -E 's/`[^`]*`//g')"
  while IFS= read -r target; do
    [[ -z "$target" ]] && continue
    case "$target" in http://*|https://*|mailto:*) continue ;; esac
    target="${target%%#*}"; [[ -z "$target" ]] && continue
    total=$((total+1))
    dir="$(dirname "$file")"
    if [[ ! -f "$dir/$target" ]]; then
      broken=$((broken+1)); printf 'BROKEN %s -> %s\n' "$file" "$target"
    fi
  done < <(printf '%s\n' "$rest" | grep -oE '\]\([^)]*\.md(#[^)]*)?\)' | sed -E 's/^\]\((.*)\)$/\1/' || true)
done < <(grep -rn --include='*.md' -E '\]\([^)]*\.md' . --exclude-dir=.git --exclude-dir=vendor)
printf 'links=%d broken=%d\n' "$total" "$broken"
[[ "$broken" -eq 0 ]]
```

基线（`git archive origin/main` 解包后运行）与改动后的 `BROKEN` 集合均为同 3 条 install-time 链接；
`skill-for-claude/aisoft-platform/SKILL.md` 的 `references/` 目录由安装脚本从 `skill-for-codex/references`
复制生成（`skill-for-claude/install.sh` 第 7、15 行），仓库源树中不存在，属既有设计，不在本 Issue 范围内。

## 清单处置结果（AC-1）

行号为改动后（HEAD = T04 `be27e54` + T05 工作树）。

| # | 处置 | 结果 / 改写后位置 |
|---|---|---|
| A-01 | 改名 + 同步引用 | `git mv` → `08-双工具共存与实施.md`（T01 rename 检测为同一文件）；`README.md:154`、`AGENTS.md:38`、`09…md:528`、`archive/11…md:5` 已指新名 |
| A-02 | 改为现在时 | `08:3` `更新：2026-09-03` |
| A-03 | 改为中性 | `08:14–15` 去括注；`08:24` 「两个 adapter 等价、可互换，由 `IMPLEMENT_PROVIDER` 显式选择」 |
| A-04 | 迁 archive + 改写 | `08:48` `## 4. 当前 provider 基础`；`08:50–62` 合并后的 source baseline 清单；`08:64–65` 仍未完成 + 历史链接；原 `50–56`、`66–72` 逐字收录于 `archive/平台状态历史-20260902.md` §「来源：`08` §4」 |
| A-05 | 改为中性 | `08:102` `## 7. Provider 验证矩阵`；`08:114` provider 无权部署生产 |
| A-06 | 改为现在时 | `08:128` 「这些 classifier case 由 `codex/runtime/tests`（`test_classification.py` 等）固化为合同测试」 |
| A-07 | 删除 | §8「Claude Code 接入条件」已删；`08:130` `## 8. 部署边界`、`08:136` `## 9. 回滚` |
| A-08 | 改为现在时 | `08:138` |
| A-09 | 改为中性 | `08:140` |
| A-10 | 改为现在时 | `08:141` |
| A-11 | 改为中性 | `04:37–38` 去括注；`04:47` 等价句 |
| A-12 | 改为中性 | `04:149` `## 10. Provider 验证矩阵`；`04:158` 第 8 条 |
| A-13 | 改写 | `README.md:154` |
| A-14 | 改写（T04 独立 commit） | `AGENTS.md:38` |
| A-15 | 改名同步 | `09…md:528` |
| B-01 | 改为现在时 | `skill-for-codex/SKILL.md:26–27` |
| B-02 | 删除 + 一句退役说明 | `skill-for-codex/SKILL.md:44–46`（原 44–66 删） |
| B-03 | 改写 | `skill-for-codex/SKILL.md:48–49`；「Retire `ci-bot` only after…」句已删 |
| B-04 | 改为现在时 | `skill-for-codex/SKILL.md:58` |
| B-05 | 改为中性 | `onboarding-runbook.md:3` |
| B-06 | 改为现在时 | `onboarding-runbook.md:19` |
| B-07 | 改为现在时 | `onboarding-runbook.md:43`、`:45` |
| B-08 | 删除 + 三句退役说明 | `onboarding-runbook.md:97–100` `### 1.2 共享 ci-bot gate（已退役）`（原 97–126 删）；`ensure-gitea-collaborator.sh` 字面量保留，`smoke.sh` 断言仍成立 |
| B-09 | 删除该句 | `onboarding-runbook.md:232` 现以「二者均不给 merge。」结尾 |
| B-10 | 改为中性 | `private-gitea-access.md:10` |
| B-11 | 改为现在时 / 退役说明 | `gitea-platform-ops/SKILL.md:21`、`:23`；`retire-shared-bot` 字面量保留 |
| B-12 | 改为现在时 | `04:162` |
| B-13 | 改为现在时 | `06:70`、`:196`、`:232`、`:399` |
| B-14 / G-03 | 删除 | `smoke.sh` 不再含 `AISOFT_ONBOARDING_MODE=software-repository` |
| B 组「核实后保留」 | 保留 | `01:49`、`01:79`、`05:61`、`08:42`、`README:201–202`（原 211–212）、runbook `:39`、`:88`、`:296`（原 322）、`06` §「旧 ci-bot gate」、`skill-for-codex/SKILL.md:32` 均未改 |
| C-01 | 改为现在时 | `README.md:3`、`:11` `2026-09-03` |
| C-02、C-04～C-06、C-09～C-13 | 迁 archive | 原 `README.md:14、16、17、18、27、28、29、31、32` 逐字收录于 `archive/平台状态历史-20260902.md` §「来源：`README.md` §1」 |
| C-03 | 尾句迁 archive | `README.md:14` 去尾句；尾句作为独立 bullet 收录于 archive |
| C-07 | 合并 + 迁 archive | `README.md:16` 「✅ provider adapters：…等价、可互换…」；原 `:20`、`:24` 收录于 archive |
| C-08 | 迁 archive + 并入 | 原 `:22` 收录于 archive；`README.md:18` 尾部追加「；未获独立 live apply 授权前，现有 merge allowlist、credential 与 installed bytes 均不改变」 |
| C-14 | 新增 | `README.md:25` 📜 历史记录链接 |
| C-15 | 新建 + 索引 | `archive/平台状态历史-20260902.md`（41 行）；`archive/README.md:17` 索引行 |
| C 组保留 | 保留 | `README.md:13、14、15、17、18、19、20、21、22、23、24`（原 13、15、19、21、23、25、26、30、33、34、35） |
| D-01 | 新增 | `09…md:7` 「落地对照：2026-09-03，见 §0.2」 |
| D-02 | 新增 | `09…md:50–66` `### 0.2 落地对照（2026-09-03）` 十行表 |
| E-01 / E-02 | 改写（T04） | `AGENTS.md:38`、`:57` |
| F-01～F-06 | 保留原位 + 尾句改判定 | `02:3`、`12-Linux…:3`、`12-Windows…:3`、`13:3`、`14:3`、`15:3` 各含「#233 判定：正文保留为参考记录…」 |
| F-07 / F-08 | 不动 | `docker-release/`、`architecture/` diff 为空 |
| G-01 | 新增守卫 | `smoke.sh:489–498` references 项目名守卫块（`references_set`） |
| G-02 | 不扩展 | 交付形态名守卫仍只作用于 7 份治理集 |

`grep -c '待定'` 本表 = 0。

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 清单处置 | PASS | 上表 A-01～G-03 每条有处置与位置，无「待定」 |
| AC-2 活文档 grep 为空 | PASS | 执行结果第 1 行；基线 5 处 → 0 处 |
| AC-3 链接无悬空 | PASS | `links=117 broken=3`，`BROKEN` 集合 = 基线 3 条 install-time 链接；旧文件名无链接形式残留 |
| AC-4 测试 | PASS | smoke 651 OK；project-check 与基线一致；test-install-claude-skills、test-project-check PASS |
| AC-5 语义等价 | PASS | `03` 无 diff；AGENTS 只目录段两行；README §3/§4、SKILL.md `:86–99`、runbook `:36–41`/`:51–68`/`:260–262`、`04` §9、`09` §16 均无 diff；spec「语义对照」列逐条 |
| AC-6 守卫 | PASS | references 守卫反向证明报红/真实树静默；陈旧断言已删；shellcheck 无告警 |
| AC-7 非目标守卫 | PASS | 非目标路径 diff 为空；`archive/` 只有新建文件、索引行与一条链接目标 |
| AC-8 两侧技能安装内容随之变化 | PASS | 两侧 check-drift 如实 DRIFT（Claude 侧 2 份 references，Codex 侧 4 份）；重装后 CLEAN 记 NOT RUN |

## 判级投影

2026-09-03 在 T04 提交后、T05 提交前执行：`codex/tools/apply-classification-labels.sh 233`（plan：`applied:false, change_type:platform, complexity:complex`）→ `--apply`（`applied:true, result:updated`）→ `--verify 233`（`result:projected`，`type/platform` + `complexity/complex`）。

## 遗留风险与未完成项

- 本机 skills 重装（`skill-for-claude/install.sh`、`codex/install-skills.sh`）：NOT RUN——Issue 非目标，合并后
  独立执行；重装后 `check-drift.sh` 应 CLEAN。
- `07` §5.1「Linux 新项目默认与既有试点」标题与 `company-delivery/` 的项目专属内容不在本 Issue 范围
  （非目标），是否收敛到项目仓另开 Issue。
- `archive/10`、`docs/changes/*` 中以代码跨度出现的旧文件名 `08-Codex双工具共存与实施.md` 是历史文本，
  按 Issue 非目标不改写。

合格标准：每条 acceptance criterion 都有一条真实执行过的命令或一次真实观测支撑；
不得把 `NOT RUN` 改写为通过；不可达的环境与未执行项在此显式写明。
