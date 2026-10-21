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
status: approved
branch: change/370-ci-download-cache
created: 2026-10-20
updated: 2026-10-21
git_scope:
  - docs/changes/370-ci-download-cache/summary-ci-download-cache-261020.md
  - docs/changes/370-ci-download-cache/spec-ci-download-cache-261020.md
  - docs/changes/370-ci-download-cache/plan-ci-download-cache-261020.md
  - docs/changes/370-ci-download-cache/verification-ci-download-cache-261020.md
  - .gitea/workflows/ci.yml
  - 01-基础设施-VM-Gitea-Runner.md
  - codex/tests/test-gitea-pat-helper-linux.sh
  - codex/tests/test-gitea-pat-helper-linux-gates.sh
---

# CI 下载缓存（#370）

## 目标与原因

平台仓必需检查不再因为 runner 访问 GitHub、`go.dev`、`proxy.golang.org` 的间歇断线而失败。缓存命中时这三处都不访问；缓存未命中时有限重试；所有缓存内容在每次使用前都按既有 pin 校验。

## 方案

1. **checkout**（2026-10-21 修订）：不再使用 `actions/checkout`。`ci.yml` 的 Check out 步骤只和本 job 已在使用的 Gitea（`$GITHUB_SERVER_URL`）通信：`git fetch` 全部分支与 `refs/pull/*/head`（最多 3 次），先中止残留合并并 `reset --hard`/`clean -ffdx`，再检出事件给出的 exact PR head。job token 写入本地 `http.<server>/.extraheader` 供合并预览取 base，末尾 `always()` 步骤删除。原「站点镜像 + 完整 URL」方案因 R13（#396）站点值守卫禁止 `ci.yml` 出现站点地址而作废。
2. **Go 工具链**：`test-gitea-pat-helper-linux.sh` 新增可选环境变量 `AISOFT_CI_DOWNLOAD_CACHE`。设了就先从 `<cache>/go-toolchain/<archive>` 复制到私有临时目录，复制件按 `build-lock.json` 的 sha256 与既有 tar 安全检查验证；校验失败就删掉缓存件（`TOOLCHAIN_CACHE_EVICTED`）改为下载。下载加 `--retry 3 --retry-all-errors --retry-delay 5`，校验通过后原子写回缓存。不设该变量时行为与现在相同（只多了重试）。
3. **Go 模块**：设了缓存时 `GOMODCACHE=<cache>/go-mod`（调用方自己给了 `GOMODCACHE` 则尊重调用方）。构建前先 `GOPROXY=off go mod download all` 试命中，失败才联网下载，最多 3 次；随后 `go mod verify`，之后 `build.py`、`go test` 全部在 `GOPROXY=off` 下运行。`GOCACHE` 仍是私有临时目录，不持久化。
4. **workflow**：PAT helper 步骤传 `AISOFT_CI_DOWNLOAD_CACHE="$HOME/.cache/aisoft-ci"`。`$HOME` 由 `act_runner.service` 设为 runner 用户家目录，不在仓里写站点路径。workflow 名、job key、事件三者不变，required context 不变。

## Acceptance criteria

- [ ] AC1 checkout 与 PAT helper 步骤在缓存命中时不访问 GitHub、`go.dev`、`proxy.golang.org`：checkout 只访问本站 Gitea；helper 日志出现 `TOOLCHAIN_CACHE_HIT` 与 `GO_MODULE_CACHE_HIT`，且构建/测试在 `GOPROXY=off` 下通过。冷缓存首跑仍需外网，as-built 写明。
- [ ] AC2 不放宽任何 pin：checkout 检出事件给出的 exact head SHA；工具链在命中与下载两条路径都校验 `build-lock.json` 的 sha256 与归档路径；模块经 `go.sum`、`go mod verify` 校验，且填充不得改动 `go.mod`/`go.sum`；gates 测试证明不符的缓存件被驱逐、从不被解包使用。
- [ ] AC3 `01` §4 写明缓存位置、checkout 做法、回滚步骤；在 runner 上真实验证：同一 PR 至少两次 CI 运行，第一次填充、第二次命中，日志摘录写进 verification。

## 接口、数据与兼容性影响

- 新增脚本环境变量 `AISOFT_CI_DOWNLOAD_CACHE`（可选）与输出标记 `TOOLCHAIN_CACHE_HIT`、`TOOLCHAIN_CACHE_EVICTED`、`GO_MODULE_CACHE_HIT`、`GO_MODULE_CACHE_FILLED`。
- runner 持久状态新增 `$HOME/.cache/aisoft-ci/{go-toolchain,go-mod}`，属主 runner 用户，预计约 1 GiB。
- checkout 凭据的生命周期与 `actions/checkout` 默认一致（写入本地 git 配置、job 末尾删除）。
- 各应用项目的 workflow 与 `templates/project/ci/` 不改，发布包不动。

## 风险与回滚约束

- 回滚：revert 本 PR 即恢复每次实时下载；缓存目录可留可删（删除由负责人以 runner 用户执行 `rm -rf /opt/act-runner/.cache/aisoft-ci`）；镜像仓留着不影响任何项目。
- 手写 checkout 需要自己处理 host 模式工作区复用；已在本机用 bare 仓模拟干净与半途合并两种复用状态，并跑通合并预览。

## 非目标

- 不改各应用项目的 CI、不改 `templates/project/ci/`。
- 不改 act_runner `config.yaml`、systemd 单元或 Gitea `app.ini`。
- 不持久化 `GOCACHE`，不引入 Go 模块代理服务。

## 未决问题

- 无。缓存位置是默认取法。
