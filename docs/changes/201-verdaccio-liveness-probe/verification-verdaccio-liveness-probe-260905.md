---
issue: 201
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/201
change_type: reliability
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - ci-change
  - platform-governance
depends_on: []
status: verified
branch: change/201-verdaccio-liveness-probe
created: 2026-09-05
updated: 2026-09-05
---

# Verification · registry 存活断言

## 基线与范围

- 基线：`origin/main` = `00f7d53`（含 #250 合并后的第七个 installer）
- 环境：Mac 本机 checkout，只读访问 `http://gitea-ci.orb.local:4873/`
- 本记录负责证明的 acceptance criteria：AC-1 至 AC-11
- **未进入 gitea-ci VM**，全程未使用 broker 之外的任何主机访问

## 改动前基线观测

这些只在改动前才观测得到，合并后无法重放。

| 观测 | 结果 | 证据 |
|---|---|---|
| Verdaccio 根路径 | `200` | 2026-09-05 `curl -s -o /dev/null -w '%{http_code}' http://gitea-ci.orb.local:4873/` |
| Verdaccio `-/ping` | `{}` | 同日同址 |
| `fflate` packument | 58 个版本，`dist-tags.latest` = `0.8.3` | 同日；tarball 指向 `http://gitea-ci.orb.local:4873/fflate/-/fflate-0.8.3.tgz` |
| `aisoft-project-check.sh`（origin/main 版本，对本 worktree） | `result: pass=4 gap=3 skip=3` | 三个 GAP（pointer-sections、change-templates、architecture-lock）是平台仓既有的结构性差异，不由本次改动引入 |
| `bash codex/tests/smoke.sh`（改动前） | 红在陈旧闸门 | `ERROR: install-skills: source checkout is 4 commit(s) behind origin/main`；`git rebase origin/main` 后复绿。这是 checkout 落后而非本次 diff |

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| `bash -n` + `shellcheck templates/project/ci/registry-preflight.sh` | PASS | 无输出 |
| `bash -n` + `shellcheck codex/tests/test-registry-preflight.sh` | PASS | 无输出 |
| `shellcheck codex/tools/aisoft-project-check.sh` | PASS | 无输出 |
| `NPM_CONFIG_REGISTRY=http://gitea-ci.orb.local:4873/ bash templates/project/ci/registry-preflight.sh` | PASS，exit 0 | 2026-09-05 16:15:45 输出 `AISOFT_REGISTRY_PREFLIGHT_OK registry=http://gitea-ci.orb.local:4873 package=fflate@0.8.3` |
| 同上，指向死端口 `http://127.0.0.1:4899/` | FAIL，exit 1 | `AISOFT_REGISTRY_PREFLIGHT_FAIL stage=connect`，curl 退出码 7，结论含「不要往 uplink 配置、npmmirror 可达性或网络策略方向排查」 |
| 同上，`NPM_CONFIG_REGISTRY` 未设置 | FAIL，exit 1 | `AISOFT_REGISTRY_PREFLIGHT_FAIL stage=config`，明确「不猜、也不回退到 npmjs」 |
| `bash codex/tests/test-registry-preflight.sh` | PASS | `registry preflight tests passed` |
| `bash codex/tests/test-project-check.sh` | PASS | `project check tests passed (58 cases)`，改动前为 57 条 |
| `bash codex/tests/smoke.sh` | PASS，exit 0 | `Ran 671 tests ... OK` / `Codex platform static smoke checks passed.` |
| `aisoft-project-check.sh --repo <本 worktree>`（本次版本） | `result: pass=4 gap=3 skip=4` | 相对基线只多一行 `SKIP: ci-registry-preflight — 没有安装 npm 依赖的 workflow`；三个 GAP 与基线逐字相同 |

### 反向证明（证明这些断言不是空转）

每一条都先把被测对象改坏、确认变红，再恢复并确认复绿。

| 故意的破坏 | 结果 | 报出的原因 |
|---|---|---|
| `registry-preflight.sh` 的 `fail()` 改成 `exit 0` | 红 | `停掉 registry 之后：期望退出 1，实际 0` |
| 脚本末尾追加一行 `npm cache verify` | 红 | `断言正文不得调用 npm、进程管理器或额外运行时` |
| 删掉「不要往 uplink 配置」那句结论 | 红 | `连接被拒的结论必须显式排除 uplink 方向` |
| 从出厂 `ci.yml` 删掉 `Registry preflight` 步骤 | 红 | `case 46 expected status 0, got 1`，出厂模板判成 `GAP` |
| `aisoft-project-check.sh` 的顺序判定短路成恒真 | 红 | `case 48 expected status 1, got 0`，排在 `npm ci` 之后的断言被误判为合格 |
| 全部恢复 | 绿 | `project check tests passed (58 cases)`、`registry preflight tests passed` |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | PASS | `templates/project/ci/registry-preflight.sh` 全程 `curl`；测试第 8 组守卫断言正文不出现 `npm`/`pm2`/`systemctl` 的命令调用，也不读 `_cacache` |
| AC-2 | PASS | 五个 stage：`config`、`connect`、`transport`、`http`、`packument`、`tarball`；`connect` 一路显式写明不要往 uplink 方向排查 |
| AC-3 | PASS | 三次真实运行分别打印 `_OK`（exit 0）与 `_FAIL`（exit 1） |
| AC-4 | PASS | `git diff --no-index` 对 `name:`、`  verify:`、`  pull_request:`、`  push:` 四行零命中；当前值仍为 `name: CI` / job key `verify` / `pull_request` + `push`。必需检查 context 不变 |
| AC-5 | PASS | 新增 `ci-registry-preflight`，PASS / SKIP / GAP 三态各有用例；对平台仓真实执行落在 SKIP |
| AC-6 | PASS | 新测试覆盖健康、connect、http 500、非 packument、tarball 404、未配置 registry 六条路径；smoke 三处注册见 `codex/tests/smoke.sh` 第 61、62、141、142、231 行 |
| AC-7 | PASS（替身 registry） | 绿 → `kill` → 红（`stage=connect`）→ 重启 → 绿，同一端口同一条命令。**未清空任何 npm 缓存**；替身进程见 `codex/tests/fake-npm-registry.py` |
| AC-8 | PASS | 对真实 `http://gitea-ci.orb.local:4873/` 执行，输出见上表 |
| AC-9 | PASS | `01` §5 新增「Verdaccio 是 CI 的硬依赖」小节，含应用仓不得绕过 `NPM_CONFIG_REGISTRY` 的禁令 |
| AC-10 | PASS | `06` 踩坑集新增第 23 条，写明两层假绿与判活三件套 |
| AC-11 | PASS | 见下方交接项，逐条 NOT RUN 并附命令与预期输出 |

**AC-7 的边界要说清楚**：负向验证证明的是**断言本身**在服务消失时确实变红、恢复后确实复绿，
失败签名（`ECONNREFUSED`，curl 退出码 7）与 2026-08 那次生产故障一致。它**不是**在 gitea-ci VM 上
停一次真实的 Verdaccio——那超出会话可用手段（broker 没有对应 typed 操作，且会话不得绕过 broker 进 VM）。
VM 上那一次列为交接项 C。

## 人工交接项

| 项 | 状态 | 说明 |
|---|---|---|
| A · 停机原因一手取证 | NOT RUN | 需要 VM 侧只读日志。命令清单见 spec 交接项 A |
| B · 开机自启 | NOT RUN | 需要一次真实重启。命令与预期输出见 spec 交接项 B |
| C · 真实停机负向验证 | NOT RUN | 在 VM 上停一次 Verdaccio，确认采纳了本断言的项目 CI 变红、恢复后复绿 |
| D · 各项目采纳 | NOT RUN | 本 PR 不改任何应用仓。LocalWMS、NewEMaint 各走自己的对齐 Issue，把 `registry-preflight.sh` 放进 `scripts/ci/` 并在装依赖前加一步 |

停机原因目前只有 #84 会话的二手转述（PM2 的 `exec cwd` 指向 2026-07-19 已迁走的 Mac 路径导致
`pm2 resurrect` spawn 失败）。**本记录不把它写成已证实**；交接项 A 跑完之前，`06` 踩坑 23 里
对应句子保留「此项为二手转述，未取到 VM 侧一手日志」的限定。取不到就如实写「原因不明」。

## 遗留风险与未完成项

- **检测时机**：本断言只在有 CI 运行时生效。完全无 CI 活动的时段里，故障发现时刻推迟到下一次 CI。
  是否补一个 VM 侧周期探针另立 Issue 评估，本次明确不做（见 spec 非目标）。
- **broker 只读操作未新增**：会话仍无法自己回读 registry 探针结果。该动作留给 #228 独占，
  以免两个并行 PR 各自把 `codex/tests/test-host-access-broker.sh` 的 `operation_count`
  从 33 改成 34——那正是 `06` 踩坑 22 描述的静默错值。本次 `operation_count` 保持 33 未动。
- **探测包依赖**：默认 `fflate@0.8.3`。该版本若从 registry 消失，断言会以 `stage=tarball` 变红；
  用 `REGISTRY_PREFLIGHT_PACKAGE` 与 `REGISTRY_PREFLIGHT_VERSION` 换一个即可。
- 平台仓自身不装 npm 依赖，因此 `ci-registry-preflight` 在本仓恒为 SKIP；这条检查的真实价值
  要等交接项 D 在应用仓落地后才体现。
