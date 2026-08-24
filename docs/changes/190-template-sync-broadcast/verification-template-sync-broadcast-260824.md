---
issue: 190
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/190
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - platform-governance
  - ci-change
depends_on: []
status: pr-open
branch: change/190-template-sync-broadcast
created: 2026-08-24
updated: 2026-08-24
---

# Verification：change 模板的上游同步广播

## 基线与范围

- Commit SHA：`change/190-template-sync-broadcast`（rebase 到最新 `main` 之后）
- 基线：`origin/main` = `01d8fa7`（含刚合并的 #191/PR #195，它把 rsdesign-new 的
  `mac_checkout` 指向真实 checkout）。本记录的 AC-8 在该基线上重跑过一次，见下方注记。
- 环境：Mac，worktree `/private/tmp/issue-190-template-sync-broadcast`；
  bash 3.2.57、shellcheck 已安装、jq 与 python3 可用
- 本记录负责证明：AC-1 … AC-9 全部九条

本记录之所以存在（`03` §3 第二行）：验收标准四要求的证据是**跨 6 个真实下游 checkout
的扫描**与**改动前后对比**——required CI 里没有任何下游 checkout，这两类证据它都不跑。

## 执行结果

| # | Command / check | Result | Evidence |
|---|---|---|---|
| 1 | `bash codex/tests/test-change-template-sync.sh` | PASS | `PASS: change-template-sync (17 cases)`，退出码 0 |
| 2 | `PYTHONPATH=codex/runtime python3 -m unittest tests.test_vendored_change_templates` | PASS | `Ran 5 tests in 0.005s` / `OK` |
| 3 | `shellcheck codex/tools/change-template-sync.sh codex/tests/test-change-template-sync.sh codex/tests/smoke.sh` | PASS | 无输出，退出码 0 |
| 4 | `bash codex/tests/smoke.sh` | PASS | `Ran 530 tests` / `OK` / `Codex platform static smoke checks passed.` |
| 5 | `PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli check-change-documents --repo $PWD` | PASS | `result: changes=86 pass=2 gap=0` |
| 6 | `PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli resolve-documents 190 --repo $PWD` | PASS | 四个角色全部解析到真实 basename |
| 7 | `bash codex/tools/aisoft-project-check.sh --repo /Users/benque/Projects/LocalWMS --kind software` | PASS | `PASS: change-templates`；`result: pass=6 gap=0 skip=2`——`change-templates` 的语义未被本次变更改动 |
| 8 | AC-8 真实模板改动三步（下方逐字抄录） | PASS | 见「### AC-8：一次真实的模板改动」 |
| 9 | `git status --porcelain`（模板与 digest 回滚后） | PASS | `templates/` 无改动；`codex/config/change-template-sync.json` 内容等于回滚前 |
| 10 | 平台 CI（PR #197，run 654，`934a8c2`） | FAIL → 已修 | 见「### CI 抓到的 bash 可移植性缺陷」 |
| 11 | `docker run --rm alpine:3.20 …bash codex/tests/test-change-template-sync.sh`（bash 5.2.26） | PASS | `PASS: change-template-sync (17 cases)` |
| 12 | 同容器内 `change-template-sync.sh`（无任何下游 checkout 的主机） | PASS | 9 个 holder 全部 `unverified`、`result: … unverified=9`、退出码 0 |

### AC-8：一次真实的模板改动

**第一步——改模板，平台 CI 这一步必须变红。**

```
$ printf '\n<!-- AC-8 真实模板改动验证 -->\n' >> templates/docs/changes/_template/summary.md
$ bash codex/tools/change-template-sync.sh --verify-digest
digest 漂移：templates/docs/changes/_template 的内容与 codex/config/change-template-sync.json 钉住的值不一致。
  pinned:   sha256:84356c58e0e4321feb89174dec62a41ca9e359ff00b9ba804921c544e1447073
  computed: sha256:0bbf8509a31b0d80fcd3a543439b2dedc5846e8918b2e256627b2c9512761c18
改动模板的这次变更必须同时刷新 digest 并广播下游：
  bash codex/tools/change-template-sync.sh --refresh-digest
exit=3
```

**第二步——刷新 digest，机制指出所有持有过期副本的项目。**

```
$ bash codex/tools/change-template-sync.sh --refresh-digest --today 2026-08-25
digest: 已刷新 sha256:84356c58e0e4321feb89174dec62a41ca9e359ff00b9ba804921c544e1447073 -> sha256:0bbf8509a31b0d80fcd3a543439b2dedc5846e8918b2e256627b2c9512761c18
holders: 9（另有 1 个仓库声明不持有副本）
HSDB               stale       summary.md,spec.md,plan.md,verification.md
LocalWMS           stale       summary.md
myapp              unverified  本机无 checkout，必须由持有 checkout 的主机复核
NewEMaint          stale       summary.md,spec.md,plan.md,verification.md
rsdesign-new       stale       summary.md,spec.md,plan.md,verification.md
SapTableMigrate    unverified  本机无 checkout，必须由持有 checkout 的主机复核
SFMDigitalBoard    missing     缺少 docs/changes/_template
smoke-test         unverified  本机无 checkout，必须由持有 checkout 的主机复核
WMPDA              unverified  本机无 checkout，必须由持有 checkout 的主机复核
result: current=0 stale=4 missing=1 unverified=4
同步方式（每个项目一条独立的 Issue → change 分支 → PR，不在下游加任何阻塞闸门）：
  cp <平台仓>/templates/docs/changes/_template/*.md <目标仓>/docs/changes/_template/
unverified 不等于已同步：本机读不到那个 checkout，结论必须由能读到的主机给出。
exit=3
```

**决定性观察**：改动前 LocalWMS 是 `current`（它刚在 #78 同步过），改动后立刻变成
`stale summary.md`——正是这次改动新造出来的过期，被机制点名。同时 9 个 holder 一个不
少地出现在清单里，包括本机 `mac_checkout` 为 `null`、根本读不到的那 4 个。

**注记：这一轮是在 rebase 到 `01d8fa7` 之后重跑的。** 第一轮（基线 `eda2aeb`）里
rsdesign-new 报的是 `missing（checkout 停在分支 codex-rsdesign-new-phase0）`；#191/PR #195
把它的 `mac_checkout` 改指到 `/Users/benque/Projects/rsdesign-new` 之后，同一条命令读到的
是 `stale`（四份全部过期）。**这正是本工具反复声明的那条限制的真实样本**：逐项状态取自
`mac_checkout` 指向的工作树，manifest 指错或 checkout 停在别的分支时，`missing` 说的是
那个路径的状态，不是那个仓库的状态。记录以最终基线为准。

**第三步——回滚模板与 digest，闸门转绿。**

```
$ bash codex/tools/change-template-sync.sh --verify-digest
digest: pinned sha256:84356c58e0e4321feb89174dec62a41ca9e359ff00b9ba804921c544e1447073
exit=0
```

### CI 抓到的 bash 可移植性缺陷

第一次 CI（run 654）红在本次新增的行为测试上，不是环境问题：

```
/tmp/tmp.aJ4AVXvuTe/platform/codex/tools/change-template-sync.sh: line 208:
  ${#holders[@]:-0} > 0: bad substitution
FAIL: case 2 expected status 3, got 1
```

`${#array[@]:-0}` 把「取长度」和「取缺省」写在了一起：**本机 bash 3.2 接受它，CI runner
的 bash 5 判为 bad substitution**。写成那样是为了绕开另一个坑——空数组在 bash 3.2 的
`set -u` 下会报 unbound。两边都成立的写法是绕开这个构造本身：改用独立的整数计数器
（`document_count` / `holder_count`），数组长度不再参与判断。

本机没有 bash 5，因此修复后额外在容器里复跑（命令 11、12），不靠「CI 应该会过」这种推断。
命令 12 顺带覆盖了一个此前没有真实样本的分支：在一台**没有任何下游 checkout** 的主机上，
9 个 holder 全部报 `unverified`、退出码 0——机制不会把「读不到」误报成「有问题」，也不会
把它说成「已同步」。

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 裁决落文 | PASS | summary「### 方向裁决」逐方向给出采用/不采用与理由；`03` §3 新节落为合同 |
| AC-2 holder 是声明 | PASS | 命令 2：缺省 `True`、平台仓库声明 `False`、非布尔取值（`""`/`"false"`/`0`/`1`/`None`/`[]`）全部 fail-closed |
| AC-3 模板有版本号 | PASS | 命令 1 case 1/2/10；digest 覆盖文件名与内容——第 10 例移走 `plan.md` 后是硬错而不是「少一份也一样」 |
| AC-4 不广播过不了 CI | PASS | AC-8 第一步退出码 3；smoke 在 `--verify-digest` 这一步消费同一个退出码（命令 4） |
| AC-5 清单不依赖 checkout | PASS | AC-8 第二步：4 个无 checkout 的项目在清单里且标 `unverified`；命令 1 case 5/6/8 用合成 fixture 钉住同一行为 |
| AC-6 逐项状态可分辨 | PASS | AC-8 第二步同时出现 `stale`（列出差异文件）与 `missing`；第一轮 rsdesign-new 的行尾标注了非 `main` 分支，见上方注记 |
| AC-7 非阻塞被钉住 | PASS | 命令 1 case 10/11：`downstream_required_check` 改成 `required` 后 plan 与 `--verify-digest` 都退出 1；smoke 另有 `jq -e` 断言与 `03` 约束句 `grep` |
| AC-8 真实模板改动验证 | PASS | 上方三步逐字抄录 |
| （回归）跨 bash 版本 | PASS | 命令 11/12：bash 5.2 下 17 例全过；CI 抓到的 bad substitution 已修 |
| AC-9 不改下游 | PASS | 命令 9 与 diff review：全部改动落在平台仓库；未新增任何下游 CI context、未产生任何下游提交 |

## 遗留风险与未完成项

1. **首跑暴露的既存缺口不在本次范围内，也未修复。** HSDB（仍是 pre-#57 的
   `00-summary.md` 一代）、NewEMaint（停在 #67 的回补）、rsdesign-new（四份全部过期）、
   SFMDigitalBoard（`main` 上没有 `docs/changes/_template/`）各需一条独立 Issue，
   走各自仓库的 change 分支与 PR。
2. **4 个项目本机不可达。** `myapp`、`SapTableMigrate`、`smoke-test`、`WMPDA` 在
   `host-access-broker.json` 里 `mac_checkout` 为 `null`，本机只能报 `unverified`。
   它们是不是真的持有副本、副本是不是过期，必须由能读到那些 checkout 的主机给出结论；
   本记录不替它们下结论。
3. **逐项状态取自 `mac_checkout` 指向的工作树**，不是各仓库 `main` 的状态。本次就撞上
   一次：rsdesign-new 在 #191 修正 `mac_checkout` 前后，同一条命令分别读出 `missing`
   与 `stale`。SFMDigitalBoard 的 `missing` 同样只是「那个路径上没有这个目录」。
4. **广播只覆盖平台侧的改动动作**，不构成定期核对。方向 3（非阻塞定期核对）没有实现，
   要不要挂定时任务需要独立验收标准（见 spec「## 非目标」）。
5. `skill-for-codex/references/` 两份文档有改动，本机已安装的 Claude skills 在重新执行
   `bash skill-for-claude/install.sh` 之前会与仓库源不一致（`check-drift.sh` 会如实报出）。
