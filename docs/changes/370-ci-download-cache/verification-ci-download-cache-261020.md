---
issue: 370
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/370
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - ci-change
  - rollback
  - platform-governance
depends_on: []
status: verified
branch: change/370-ci-download-cache
created: 2026-10-20
updated: 2026-10-21
---

# Verification

## 基线与范围

- Commit SHA: runner 证据取自 `dd58deb902d83e93101c1697ba7a4afc3866288e`（run 2040）与 `886fc6912a4b3edc45511b5fdfb6b6ba8a481c0b`（run 2041）；之后只集成了 R16（#397）的 main 并回填本记录。
- 基线：`origin/main` = `86821cfe4c48fb792c595c6eac719671c77aa6e1`（两次运行时合并预览读到的 base 尖端）
- 环境: 平台 VM 上的 act_runner v1.0.7（host 模式，aarch64，`gitea-ci-runner`）；另有 Mac 本机与 Linux arm64 容器（debian:stable）
- 本记录负责证明的 acceptance criteria: AC1、AC2、AC3

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| PR 401 run 2040（job 2319，head `dd58deb`，冷缓存） | PASS | 全部 6 步 success；日志 `workflow prepared` 之后直接 `Run Main Check out`，没有任何 action 克隆；`GO_MODULE_CACHE_FILLED`、`all modules verified`；PAT helper 步骤 126s；合并预览 `PR head = dd58deb…`、`已检出 SHA = dd58deb…` |
| PR 401 run 2041（job 2320，head `886fc69`，热缓存） | PASS | 全部 6 步 success；`TOOLCHAIN_CACHE_HIT`、`GO_MODULE_CACHE_HIT`、`all modules verified`；PAT helper 步骤 83s；合并预览 `PR head = 886fc69…`、`已检出 SHA = 886fc69…` |
| 两次运行的 `Remove checkout credential` | PASS | `always()` 步骤 success；日志里 token 均为 `[redacted]` |
| `bash codex/tests/smoke.sh`（Mac，集成 R10b 后的 `dd58deb`） | PASS | exit 0 |
| `bash codex/tests/test-gitea-pat-helper-linux-gates.sh` | PASS | 校验和、路径、命中、驱逐、符号链接、目录 6 个场景；变异检查：命中路径不置位、写回改删除、拒绝改 `|| true` 三种退化分别报 `FAIL: hit…`、`FAIL: evict…`、`FAIL: link: wrong refusal` |
| `python3 -m unittest discover -s codex/tools/gitea-pat-helper -p test_build.py` | PASS | 12 tests OK |
| Linux 容器冷跑 / 热跑（同一缓存卷） | PASS | 冷跑 132s `GO_MODULE_CACHE_FILLED`；热跑 86s `TOOLCHAIN_CACHE_HIT`、`GO_MODULE_CACHE_HIT`；三次产出二进制 sha256 均为 `a9b002e8…735a` |
| Linux 容器 `--network none` 热跑 | PASS | `curl https://go.dev/dl/` 报 `Could not resolve host`；脚本仍 exit 0 并打印两条 HIT |
| Linux 容器篡改缓存中 `golang.org/x/crypto@v0.52.0` 一个文件 | 按设计失败 | exit 1，`dir has been modified`；恢复文件后复原 |
| 手写 checkout 本机模拟（bare 仓、干净与半途合并的复用工作区） | PASS | 两种状态都检出 exact head、`status --porcelain` 为空，之后合并预览通过 |
| Codex 只读交叉审查 | PASS | 第 1 轮（`0f4b3ac`）一条 P2 已修；第 2 轮（`dd58deb`）PASS；记录在项目库 `codex-review-370.md` |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC1 | PASS | run 2041：checkout 只访问本站 Gitea（没有 action 克隆），工具链与模块两处 HIT，构建与测试在 `GOPROXY=off` 下通过；容器在 `--network none` 下同样通过。冷缓存首跑仍需外网（run 2040），已写进 `01` §4.4 |
| AC2 | PASS | 工具链命中与下载两条路径都校验 `build-lock.json`；不符的缓存件被驱逐，符号链接与目录被拒（gates）；模块经 `go.sum`、`go mod verify` 与 `go.mod`/`go.sum` 字节守卫，篡改实测被拒；checkout 检出事件给出的 exact head |
| AC3 | PASS | `01` §4.4 写明缓存位置、checkout 做法、恢复与回滚；runner 两次真实运行：run 2040 填充、run 2041 命中，PAT helper 步骤 126s → 83s |

## 遗留风险与未完成项

- 缓存被删或 runner 重建后第一次运行仍需外网，这是设计如此，as-built 已写明。
- 模块缓存被改过时 job 失败，不会自愈，需要按 `01` §4.4 删除 `go-mod` 后 Re-run。
- 应用项目的 CI 与 `templates/project/ci/` 仍用 `actions/checkout@v4`，不在本 Issue 范围内。
- runner 上的「外网真正中断」没有人为制造；离线能力由 `GOPROXY=off` 下通过、无 action 克隆、容器 `--network none` 三项共同支撑。
