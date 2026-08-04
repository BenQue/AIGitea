---
issue: 27
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/27
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - schema-change
  - security
  - external-contract
  - shared-core
  - ci-change
  - artifact
  - deployment
  - compatibility
  - rollback
  - platform-governance
depends_on: []
status: verified-local
branch: change/27
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/30
created: 2026-08-04
updated: 2026-08-04
---

# Verification

## 结论

当前结果为 **LOCAL PASS / REAL CONTAINERD E2E PASS / CLASSIC REJECTED**。Issue #27 的
schema、runtime、strict archive/inventory、capability matrix、fake tests、安装合同、文档和
disposable E2E harness 已在 platform worktree 完成。两个独立 OrbStack disposable VM 的真实
Engine 29 containerd E2E 已覆盖 Registry push/pull、release-scoped tag、save/load、离线 Registry
pull 拒绝、Compose `--pull never --no-build`、运行身份/健康和 exact cleanup，并生成只读 evidence。
因此 `engine-29-containerd-linux-amd64` row 固定为 `supported`。Classic 没有同等级真实证据，仍为
`rejected + evidence:null`。这些结果不是 NewEmaint、AppServer、database 或 production 部署证据。

## 环境与基线

- Live Issue：开始实现前以已认证 Gitea API 回读为 `open + approved + complexity/complex +
  type/platform`；批准评论精确绑定下列 baseline 与 `docs/changes/27/{00-summary,01-spec,02-plan}.md`。
- Approved baseline / 当前未提交实现的 parent：
  `a75181cd72097bb0183b6b8f909da2965d5bb4b8`。
- 开始时 live `origin/main`：`8d5dae9569b6e61e88b40490ae04941614c62f8d`。
- 最终集成的 live `origin/main`：`951fa6e3a9f7d21ea2e1ab1d7cf1931f191734b2`（已合并 Issue #26 / PR #29）；
  按批准 plan 合入后，新增 architecture transition 与 release capability ordering 的交叉回归已修复并重跑。
- Worktree：显式 `change/27`，upstream `origin/change/27`；编辑前 HEAD 等于 approved baseline、
  divergence `0/0`、worktree clean。未在 detached HEAD、`main` 或 `codex/*` 分支编辑/提交。
- Runtime：Python `3.14.4`；ShellCheck `/opt/homebrew/bin/shellcheck`。
- Disposable VM：经用户单独授权创建 `aisoft-27-producer` 与 `aisoft-27-consumer`；均为
  OrbStack isolated `ubuntu:24.04`、`linux/amd64`、2 CPU、3 GiB memory、24 GiB disk。既有
  `AppServer`、`gitea-ci` 与 OrbStack 内置 Docker 未被修改、重启或清理。
- Disposable Docker：两台 VM 均为 Engine `29.7.1`、containerd `2.2.6`、Compose `2.40.3`，
  `Driver=overlayfs` 且 `DriverStatus=[["driver-type","io.containerd.snapshotter.v1"]]`。实际 daemon
  ID 分别为 `6ac62e06-761b-4014-9d78-fb1a56896544` 与
  `6d3c1c6e-c4b6-4466-ac54-3ccef0d0ee34`；data root 都显示 `/var/lib/docker`，但位于不同 VM。
- Cgroup remediation：经用户精确授权，两台专用 daemon 的 `/etc/docker/daemon.json` 只设置
  `exec-opts=[native.cgroupdriver=cgroupfs]`；配置先由 `dockerd --validate` 验证，再只重启这两台
  Docker service。重启后均为 cgroup v2 + `cgroupfs`，daemon ID、containerd marker 与资源基线不变。
  既有 OrbStack Docker、`AppServer` 和 `gitea-ci` 未被切换或重启。
- Fixture baseline / post-cleanup：producer 仅预载
  `registry@sha256:a3d8aaa63ed8681a604f1dea0aa03f100d5895b6a58ace528858a7b332415373`
  (`linux/amd64`)；consumer 保持 0 images。两边均 0 containers、0 volumes，仅有默认
  `bridge/host/none` networks；loopback port `5001` 未监听。最终 PASS 后逐项回读仍与此基线一致。
- Compose controller：为保持 exact version contract，官方 `v2.40.3` macOS arm64 plugin 仅放在
  `/private/tmp/aisoft-27-docker-config`；实际 SHA-256
  `8cd7eb5f95bacb536cc407111662e2c205d67d9abfea5dcb8400be8418db60d1` 与官方
  `checksums.txt` 一致。未修改用户 `~/.docker`。
- Execute toolchain：官方 Go `1.26.5` macOS arm64 archive 仅解压到
  `/private/tmp/aisoft-27-go1.26.5`；SHA-256
  `efb87ff28af9a188d0536ef5d42e63dd52ba8263cd7344a993cc48dd11dedb6a` 与 Go 官方 live download
  metadata 一致，未修改 Homebrew 或系统目录。

## Primary documentation evidence

2026-08-04 通过 Context7 与 official primary source 固定核对：

- Docker Docs `d1eaa21fd5d7466c698fe7ef11d00bbaab33165e` 的 `docker image save/load` 只承诺
  保存/恢复 images 与 tags，不承诺 offline load 后恢复 canonical digest reference/`RepoDigests`。
- 同一 Docker Docs commit 的 containerd image-store 文档说明 Engine 29 fresh install 默认
  containerd，而 upgrade 保留 classic，并给出 `DriverStatus` snapshotter marker；因此 runtime
  同时读取 Engine、Compose、driver 与 structured `DriverStatus`，不按 Engine major 猜 store。
- Moby `6719bc3c8d675b3ac60a2fd78c630a066177e20d` 的 classic
  `daemon/internal/image/tarexport/save.go` 与 containerd `daemon/containerd/image_exporter.go`
  支持“显式创建 release-scoped tag 后按 tag save”的设计判断。源码结论不计为 real E2E PASS。

固定 URL 与语义摘要位于 `docker-release/README.md`；未使用滚动文档结论替代运行证据。

## Platform-local 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=codex/runtime python3 -B -m unittest discover -s codex/runtime/tests -p 'test_release_*.py' -v` | PASS | 合入 latest main/#26 后 58 项 release schema/parser/capability/transport/runner/TOCTOU/safety/integration tests 通过 |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=codex/runtime python3 -B -m unittest discover -s codex/runtime/tests -p 'test_architecture_*.py' -v` | PASS | 合入 latest main/#26 后 34 项 canonical architecture/transition regression 通过 |
| `bash codex/tests/test-docker-release-install.sh` | PASS | 临时 install root 连续安装两次 byte-identical；V2 schemas/matrix/runtime path 完整，未调用 Docker |
| `bash codex/tests/test-docker-image-store-e2e-harness.sh` | PASS（fake） | default 零 Docker call；授权 marker 下 fake read-only preflight `mutations:0`，回读 daemon ID/data root；安全 `ssh://user@host` positive 与 credential-bearing SSH negative；同 daemon endpoint pair fail closed |
| `bash -n`（全部修改 shell） | PASS | installer、smoke、fake harness 与 real harness 语法通过 |
| `shellcheck`（全部修改 shell） | PASS | ShellCheck 可用且零 finding |
| `PYTHONDONTWRITEBYTECODE=1 bash codex/tests/smoke.sh` | PASS | 合入 latest main/#26 后 197 项 Python tests、全部 shell mocks/installers、fake harness 与 static checks 通过 |
| Latest main/#26 integration | FAIL → FIXED → PASS | 首轮 focused test 发现 transition positive path 的旧期望缺少 #27 capability event；更新为严格要求 `capability → config` 后，58+34 focused 与 197-test full smoke 均通过 |
| `git diff --check` | PASS | 当前 platform-local candidate 无 whitespace error |
| `codex/tests/integration/test-docker-image-store-e2e.sh --preflight` | PASS（real read-only） | 两个 SSH endpoint 回读 exact Engine/Compose/store/daemon ID/data root；输出 `PASS_READ_ONLY` 与 `mutations:0`；该模式本身没有执行 Docker mutation |
| `codex/tests/integration/test-docker-image-store-e2e.sh --execute` attempt 1 | FAIL（real，已修复） | producer 首个 Registry container 在 systemd cgroup scope 创建阶段失败，错误为 `Failed to determine whether process is a kernel thread: Inappropriate ioctl for device`；自动 cleanup 恢复基线且未生成 evidence。经授权切换两台专用 daemon 为已验证的 `cgroupfs` 并重启 |
| 同一 `--execute` attempt 2 | FAIL（real，已修复） | Registry、save/load 与 Compose create 已执行，64 MiB fixture web container 在 amd64 emulation 下退出 `137`；Docker event 明确为 `oom`。Exact cleanup 后识别并逐个删除 5 个本次 legacy builder dangling intermediate images，没有运行 prune；fixture memory 调整为 256 MiB，并补全 image-ID baseline cleanup 与失败诊断测试 |
| 同一 `--execute` attempt 3 | **PASS（real containerd）** | 两个不同 daemon 上完成 Registry push/pull、tag/save/load、offline pull rejection、Compose `--pull never --no-build`、health/identity 与 exact cleanup；写出 evidence `issue-27-containerd-a75181cd7209` |
| Evidence schema/mode/checksum | PASS | `/private/tmp/aisoft-27-containerd-a75181cd7209.evidence.json` exact-key/值校验通过，mode `0444`，SHA-256 `781c9413e2a3948e2b654a28b95248d01bd0fa7d4381fc3d02e880b292f2f694` |

## Acceptance criteria 结果

| AC | Result | Evidence / boundary |
|---|---|---|
| AC-1 | PASS（local） | Manifest schema/runtime 区分 Registry reference/digest、transport tag、runtime tag 与 content image ID；tag 由 lower owner/repo、service、完整 SHA 确定，unsafe source/service 拒绝 |
| AC-2 | PASS（fake + real producer） | V2 bundle/inventory exact fields；digest inspect → tag → repeated ID/platform inspect → tag-only save 顺序已覆盖；真实 containerd producer 的 tag/save 与 consumer load 已 PASS |
| AC-3 | PASS（local/fake） | Legacy Registry manifest 保持可读/按 digest pull且不 retag；legacy offline、mixed、unknown field 在 load 前稳定拒绝；README 只允许重新 publish V2 |
| AC-4 | PASS（fake + real） | Fixed argv 读取 exact Engine/Compose/linux-amd64/driver/`DriverStatus`；missing/conflict/duplicate marker、wrong store、range/row/evidence/date 错误 fail closed；真实 E2E 绑定两个不同 containerd daemon 与 supported evidence |
| AC-5 | PASS（fake） | Checksums、strict inventory、path traversal、extra member、RepoTags/config/layer/OCI allowlist 在 load 前验证；load 一次后按 runtime tag 检查 ID/platform，允许空 RepoDigests；migration/up 顺序与 post-start identity 已覆盖 |
| AC-6 | PASS（fake + real parity） | Registry digest/RepoDigest/tag 与 offline load 对同一 runtime tag/image ID/Compose/architecture/release/container identity 的路径已覆盖；真实 Registry push/pull 与 offline save/load 均收敛到同一 image ID |
| AC-7 | **PASS（real containerd E2E）** | 双 daemon、digest-pinned Registry fixture、Registry push/pull、tag/save/load、consumer offline Registry pull rejection、Compose `--pull never --no-build`、health/identity 与 exact cleanup 全部通过；immutable evidence 已校验 |
| AC-8 | PASS（rejection branch） | Classic committed row 为 `rejected + evidence:null`，preflight 在 mutation 前拒绝；同等级 classic real E2E `NOT RUN`，没有写 PASS |
| AC-9 | PASS（fake） | Archive/inventory/digest/tag/ID/platform/service/Compose/architecture/release/wrong-store/TOCTOU 负例 fail closed；pre-load mutation 0，post-load failure 不 migration/up，post-start mismatch 走 previous-container rollback且不 restore DB |
| AC-10 | PASS（Issue #27 required scope） | NewEmaint V2 synthetic fixture、58+34 tests、双 installer、fake harness、bash-n、ShellCheck、197-test smoke、diff check 与 real containerd E2E 通过；classic 和 external deployment 项保持真实 `REJECTED`/`NOT RUN` |

## Fake / real / external evidence matrix

| Surface | Result | Notes |
|---|---|---|
| Schema/runtime/fake Docker | PASS | Platform-local；不等于 Docker daemon 行为 |
| Harness default + fake preflight | PASS（fake） | Default 零调用；fake preflight 只证明 argv、解析与 fail-closed 条件 |
| Engine 29 containerd producer + consumer | **E2E PASS / SUPPORTED** | 两个独立 daemon/data root；真实 Registry 与 offline transport、runtime identity/health、exact cleanup 通过；matrix evidence 已提交 |
| Engine 29 classic producer + consumer | NOT RUN / REJECTED | 没有同等级证据，不支持 |
| Ephemeral Registry + offline pull rejection | PASS（real） | Loopback Registry push/pull 成功；consumer 离线阶段的 Registry pull 按要求失败，随后只从已验证 archive load |
| NewEmaint synthetic consumer | PASS（synthetic） | 只消费 platform fixture；未修改 NewEmaint 仓库 |
| NewEmaint real app / Registry / Secret | NOT RUN | 不在当前授权范围 |
| AppServer / migration / database / deployment | NOT RUN | 未连接或修改 |
| Production | NOT RUN | 未触碰 |

## 故意失败与 mutation boundary

- Legacy offline、checksum/inventory/archive path、extra archive member、RepoTag/config、wrong store 与
  invalid capability matrix：PASS；均在 `docker image load`/pull/tag/migration/up 前拒绝，fake
  mutation count 为 0。
- Post-load wrong image ID/missing runtime tag：PASS；只发生一次 fake load，不执行 migration/up。
- Post-start Config.Image、container image ID 或 release label TOCTOU mismatch：PASS；走既有
  previous-container rollback，不自动执行 PostgreSQL restore。
- Harness `--preflight`：fake PASS、真实 PASS_READ_ONLY；读取实际 daemon ID/data root 并拒绝两个
  endpoint 指向同一 daemon，真实输出声明 `mutations:0`。第一次真实尝试因错误要求 execute-only
  `go` 而在 Docker probe 前终止；依赖门已按 mode 拆分并补回归测试，未产生 Docker mutation。
- Harness `--execute`：成功路径才允许 build/tag/push/save/load/up/down，并在 evidence
  写入前反向检查 exact Compose project/network、Registry container、release tag/image 均不存在。
- Attempt 1：因 `cgroup v2 + systemd driver` 在 OrbStack machine 内创建 scope 时收到
  `Inappropriate ioctl for device` 而失败；cleanup 恢复基线且未生成 evidence。修复只作用于两台
  disposable daemon，并在重启前验证 daemon config。
- Attempt 2：64 MiB web fixture 在 amd64 emulation 下 OOM（exit `137`）；cleanup 后精确移除本次
  5 个 dangling intermediate image ID，没有 prune。Harness 随后把 fixture memory 调整为 256 MiB，
  并加入 full image-ID baseline 清理与有界 OOM/health 诊断。
- Attempt 3：PASS。Evidence 记录 release
  `a75181cd72097bb0183b6b8f909da2965d5bb4b8`、Registry/runtime identity、archive/inventory/Compose/
  architecture checksums、consumer `RepoDigests`、offline pull rejection 和 cleanup。关键 identity：
  image ID `sha256:8e28b57755d737401ee7d93d81484104493d884070a69bf943b02c6283da6f07`；archive SHA-256
  `ac3dfb73341d28c5c6afb83521170b7d71fec29b91b0682ebe556908d09e6e40`；inventory SHA-256
  `4dfcdfa7dd582d75791d44c7cc6c6dbb1321cb6060b04bc280c86381e8b1c2e5`。

## Remaining Gate and rollback

Issue #27 的 platform-local 与 required real containerd acceptance 已完成。最终 PR #30 的正文
只包含 `Closes #27`，当前停在人工合并闸门；不得自动 merge 或直接关闭 Issue。Classic row 保持 rejected，
直至未来独立授权的同等级 real E2E 通过。两台 disposable VM 当前保留且 Docker service active；
未获得删除 VM 或恢复 daemon 配置的授权，因此不执行清理性基础设施变更。

授权仍不包含既有 OrbStack Docker、`AppServer`、业务 Registry/Secret、NewEmaint、database/
migration、部署或 production。平台代码回滚方式为人工 revert 最终 PR；若未来撤销 containerd
支持，必须同时把 matrix row 恢复为 `rejected + evidence:null`。Legacy bundle 不原地改写，只能从
受控 producer 重新发布 V2；database restore、AppServer 和 production 始终是独立人工 Gate。
