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
status: contract-drafting
branch: change/370-ci-download-cache
created: 2026-10-20
updated: 2026-10-20
---

# CI 下载缓存（#370）

## 目标与原因

平台仓必需检查不再因为 runner 访问 GitHub、`go.dev`、`proxy.golang.org` 的间歇断线而失败。缓存命中时这三处都不访问；缓存未命中时有限重试；所有缓存内容在每次使用前都按既有 pin 校验。

## 方案

1. **checkout**：本站 Gitea 建公开组织 `actions`，把 `https://github.com/actions/checkout` 拉取镜像为 `actions/checkout`（负责人在界面操作一次）。`ci.yml` 改为
   `uses: http://gitea-ci.orb.local:3000/actions/checkout@11d5960a326750d5838078e36cf38b85af677262`（即 GitHub 上 `v4` 现指的 `v4.4.0`）。钉 40 位 commit SHA，镜像同步时 GitHub 断线不影响已有对象，内容由 git 对象哈希保证。
2. **Go 工具链**：`test-gitea-pat-helper-linux.sh` 新增可选环境变量 `AISOFT_CI_DOWNLOAD_CACHE`。设了就先从 `<cache>/go-toolchain/<archive>` 复制到私有临时目录，复制件按 `build-lock.json` 的 sha256 与既有 tar 安全检查验证；校验失败就删掉缓存件（`TOOLCHAIN_CACHE_EVICTED`）改为下载。下载加 `--retry 3 --retry-all-errors --retry-delay 5`，校验通过后原子写回缓存。不设该变量时行为与现在相同（只多了重试）。
3. **Go 模块**：设了缓存时 `GOMODCACHE=<cache>/go-mod`（调用方自己给了 `GOMODCACHE` 则尊重调用方）。构建前先 `GOPROXY=off go mod download all` 试命中，失败才联网下载，最多 3 次；随后 `go mod verify`，之后 `build.py`、`go test` 全部在 `GOPROXY=off` 下运行。`GOCACHE` 仍是私有临时目录，不持久化。
4. **workflow**：PAT helper 步骤传 `AISOFT_CI_DOWNLOAD_CACHE="$HOME/.cache/aisoft-ci"`。`$HOME` 由 `act_runner.service` 设为 runner 用户家目录，不在仓里写站点路径。workflow 名、job key、事件三者不变，required context 不变。

## Acceptance criteria

- [ ] AC1 checkout 与 PAT helper 步骤在缓存命中时不访问 GitHub、`go.dev`、`proxy.golang.org`：checkout 日志显示从本站镜像取 action；helper 日志出现 `TOOLCHAIN_CACHE_HIT` 与 `GO_MODULE_CACHE_HIT`，且构建/测试在 `GOPROXY=off` 下通过。冷缓存首跑仍需外网，as-built 写明。
- [ ] AC2 不放宽任何 pin：checkout 钉 40 位 SHA；工具链在命中与下载两条路径都校验 `build-lock.json` 的 sha256 与归档路径；模块经 `go.sum` 与 `go mod verify` 校验；gates 测试证明被篡改的缓存件被驱逐、从不被解包使用。
- [ ] AC3 `01` §4 写明缓存位置、镜像、回滚步骤；在 runner 上真实验证：同一 PR 至少两次 CI 运行，第一次填充、第二次命中，日志摘录写进 verification。

## 接口、数据与兼容性影响

- 新增脚本环境变量 `AISOFT_CI_DOWNLOAD_CACHE`（可选）与输出标记 `TOOLCHAIN_CACHE_HIT`、`TOOLCHAIN_CACHE_EVICTED`、`GO_MODULE_CACHE_HIT`、`GO_MODULE_CACHE_FILLED`。
- runner 持久状态新增 `$HOME/.cache/aisoft-ci/{go-toolchain,go-mod}`，属主 runner 用户，预计约 1 GiB。
- 本站 Gitea 新增公开组织 `actions` 与镜像仓 `actions/checkout`。
- 各应用项目的 workflow 与 `templates/project/ci/` 不改，发布包不动。

## 风险与回滚约束

- 回滚：revert 本 PR 即恢复每次实时下载；缓存目录可留可删（删除由负责人以 runner 用户执行 `rm -rf /opt/act-runner/.cache/aisoft-ci`）；镜像仓留着不影响任何项目。
- act_runner 若不接受完整 URL 的 `uses:`，实现停在这一步上报，候选改法（runner `github_mirror` 或 Gitea `DEFAULT_ACTIONS_URL`）都是站点级变更，需另行确认。
- 工作流中的站点 Gitea 地址与 R13 站点外置守卫存在交集，PR 前与 R13 的守卫规则对齐。

## 非目标

- 不改各应用项目的 CI、不改 `templates/project/ci/`。
- 不改 act_runner `config.yaml`、systemd 单元或 Gitea `app.ini`。
- 不持久化 `GOCACHE`，不引入 Go 模块代理服务。

## 未决问题

- 无。镜像组织名 `actions` 与缓存位置是默认取法，确认点 1 可改。
