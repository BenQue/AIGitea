---
issue: 309
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/309
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 在三仓共用的 gitea-ci runner 主机上新增平台提供的 Flutter 工具链合同，并更正 01 文档 4.1 的 act-runner as-built；触及共享 CI 基础设施与主机侧持久状态，按强制规则判为 complex。
risk_flags:
  - ci-integration
  - shared-core
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-flutter-runner-preinstall-260918.md
  spec: spec-flutter-runner-preinstall-260918.md
  plan: plan-flutter-runner-preinstall-260918.md
  verification: verification-flutter-runner-preinstall-260918.md
confidence: high
override_reason: ''
depends_on: []
status: analyzed
branch: change/309-flutter-runner-preinstall
pr_url:
created: 2026-09-18
updated: 2026-09-18
---

## 问题/需求总结

NewEMaint #158 要给 required CI 增加 `mobile-verify` job，但 gitea-ci runner 上没有 Flutter SDK，
job 内也无法自行获得：Flutter 官方 Linux 归档只发 x64，runner 主机是 aarch64，arm64 只能 `git clone`
tag 后自举，而自举解压 `dartsdk-linux-arm64` 需要 `unzip`/`bsdtar`/`7z`，主机上一个都没有。
即便解决了解压，冷启动 clone 约 1 GiB 也很可能撞满 `timeout: 20m` 并占死唯一执行位。

因此 Flutter 必须由平台侧预装成 runner 主机的持久能力，而不是每个 job 自己准备。

同一份只读核对还发现 `01-基础设施-VM-Gitea-Runner.md` §4.1 的 as-built 段已经与实际不符，
本次一并更正（详见「影响范围」）。

## 影响范围

**主机侧（gitea-ci VM，`role=scm-ci`）**

- 新增 `/opt/flutter/3.32.8`（Flutter `3.32.8`、revision `edada7c56edf4a183c1735310e123c7f923584f1`），
  对 `gitea-runner` 用户可读可执行。
- 新增 APT 包 `unzip`（Dart SDK 自举与 `pub` 解压所需）。
- 新增 provenance marker `/opt/flutter/3.32.8/.aisoft-runtime-source`，格式沿用主机上既有的
  `/opt/node24.18.0/.aisoft-runtime-source`（`contract=gitea-runner-node-runtime/v1`）。
- 新增持久 pub 缓存 `/opt/act-runner/.pub-cache`（`gitea-runner` 属主，与既有 `.npm` 同级）。
- **修改共享 CI 服务配置**：`/opt/act-runner/config.yaml` 新增 `runner.envs`
  （`PUB_CACHE` 与含 `/opt/flutter/3.32.8/bin` 的 `PATH`），需重启 act_runner 生效。

**仓库侧**

- 新增幂等安装脚本与其单元测试，并登记进 `codex/tests/smoke.sh` 的静态闸门清单。
- `01-基础设施-VM-Gitea-Runner.md`：新增「Flutter SDK（runner 预装）」小节；三处 as-built 更正
  （`config.yaml`、`ExecStart -c`、`/opt/node24.18.0`）。

**不触及**：act_runner 版本、`capacity`、`timeout`、systemd unit 与既有 `10-config.conf` drop-in、
Gitea 配置、任何项目仓 workflow、任何部署链路。

范围 1 于 2026-09-18T21:24:23+08:00 由调度会话追加持久 `PUB_CACHE` 与 runner 作业环境写入
（来源：NewEMaint #158 回报 pub.dev 是新的外部依赖、pub 侧没有 Verdaccio 等价物）。
该追加项越出了 Issue 原授权闸门 1 的边界，spec 因此把闸门拆成 3 条逐条授权；
其中闸门 3（改 `config.yaml` 并重启 act_runner）影响三个仓库的全部 CI job，单独授权。

### `01` 文档 as-built 的三处漂移（本次只读实测，2026-09-18）

| 文档现写 | 实测 | 证据 |
|---|---|---|
| `/opt/act-runner/config.yaml` 不存在 | 存在，`gitea-runner:gitea-runner 644`，mtime `2026-09-05 22:46:24 +0800` | `stat` + `cat`：`runner.capacity: 1`、`runner.timeout: 20m` |
| `ExecStart` 没有 `-c`，走 3h 内置默认 | `ExecStart` 已含 `-c /opt/act-runner/config.yaml`，服务自 `2026-09-15 20:38:48 CST` 起以该配置运行 | `systemctl show act_runner -p ExecStart` |
| （文档无任何记载） | `/opt/node24.18.0` 已装 Node `24.18.0` + npm `11.19.0`，`root:root 755`，213 MiB，marker `installed_at=2026-08-07`，目录 mtime `2026-08-07 22:36:37 +0800` | `cat .aisoft-runtime-source`、`stat`、`bin/node --version`、`bin/npm --version` |

前两处说明 #228 记为「应用方式（人工，尚未执行）」的那一段实际已经执行过，as-built 停在了执行之前的
快照。第三处是另一种漂移：主机装了东西而文档里零记录——这正是本次 Flutter 安装必须同时落文档的理由。

第三处由调度会话在 2026-09-18 并入本 Issue 范围 3 与 AC-4（Issue 正文
`updated_at: 2026-09-18T21:20:41+08:00`），理由是它与前两处同属 `01` 文档 as-built 漂移、
只改文档不改主机、不需要独立验收标准，且落在本 PR 已触碰的同一个文件。

## 初步方案与建议

1. 安装动作固化为一个幂等脚本，带只读 `--check` 模式：已装且 revision 一致即 no-op 退出，不重复 clone。
2. 用 `git clone --depth 1 --branch 3.32.8` 取 SDK，clone 后断言 `git rev-parse HEAD` 等于钉住的 revision，
   不匹配即失败退出，避免 tag 被移动时装进未知版本。
3. 先 `apt-get install -y unzip`，再触发一次 `flutter --version` 完成 Dart SDK 自举，随后 `flutter precache --linux`
   预热，使首个 job 不再下载。
4. 目录属主 `root`、模式 `755`，`gitea-runner` 只读执行；SDK 自带的 `bin/cache` 需要对 `gitea-runner` 可写，
   否则每个 job 会尝试重新自举——这一点在 spec 里作为显式验收项。
5. 安装前后各记一次 `df -h /opt`；使用率达到或超过 80% 即停止（沿用 `12` 的磁盘告警阈值）。

## 风险

| 风险 | 处置 |
|---|---|
| 安装期间占用 runner 执行位或干扰在跑的 job | 闸门 1、2 不经 act_runner、不重启任何服务 |
| 闸门 3 重启 act_runner 会杀掉在跑的 job，影响三个仓库 | 重启前 `orbstack.runner.status` 确认 `execution.child_count == 0`，非零就等；读回不符立刻回滚 |
| `runner.envs` 的 `PATH` 覆盖掉 job 原有 `PATH` 导致既有 CI 变红 | `PATH` 值以 `/opt/flutter/3.32.8/bin` 前置、完整保留既有五段系统路径；回滚是删除 `runner.envs` 段 |
| 只证明了配置与 daemon 侧生效，未证明 job step 内生效 | AC-8 显式记为已知限制，端到端证据落在 NewEMaint #158 首次绿跑 |
| tag `3.32.8` 被上游移动，装进非预期 revision | clone 后断言 revision，等于才继续 |
| `bin/cache` 权限不当导致每个 job 重新自举 | 验收项显式要求以 `gitea-runner` 身份跑通并观察无二次自举 |
| 磁盘被 SDK + pub cache 撑满 | 安装前后 `df -h /opt` 入 verification，80% 阈值停机 |
| 回滚 | `rm -rf /opt/flutter/3.32.8` 与 `rm -rf /opt/act-runner/.pub-cache`（两者本次之前都不存在）；`config.yaml` 删除新增的 `runner.envs` 段后重启；`unzip` 保留，移除它不属于本次回滚范围 |

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 在三仓共用的 gitea-ci runner 主机上新增平台提供的 Flutter 工具链合同，并更正 01 文档 4.1 的 act-runner as-built；触及共享 CI 基础设施与主机侧持久状态，按强制规则判为 complex。
risk_flags:
  - ci-integration
  - shared-core
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- `type/platform` 属于 `FORCED_COMPLEX_TYPES`；`contract_effect=add` 与 `risk_flags` 中的
  `ci-integration`、`shared-core` 三条都独立触发强制 complex（`codex/runtime/aisoft_loop/classification.py`）。
- 主机侧只读核对：`uname -a` = `Linux gitea-ci … aarch64`，`Ubuntu 26.04 LTS`；
  `unzip`/`bsdtar`/`7z`/`7za`/`p7zip` 全部 MISSING，`python3`/`git`/`curl`/`xz` 存在。
- `git ls-remote https://github.com/flutter/flutter refs/tags/3.32.8` 返回
  `edada7c56edf4a183c1735310e123c7f923584f1`，与 Issue 正文一致。
- NewEMaint `apps/mobile/pubspec.yaml` 要求 Dart sdk `^3.8.1`，`pubspec.lock` 要求 Flutter `>=3.32.0`；
  Flutter 3.32.8 随附 Dart 3.8.1，满足约束。
- `df -h /opt`：`/dev/vdb1` 253G，已用 54G，可用 199G，使用率 22%，远低于 80% 阈值。
- `/opt/flutter` 本次之前不存在（`ls` 返回 No such file or directory），因此回滚是纯删除。
- `required_docs` 含 `verification`：主机安装与「以 gitea-runner 身份实测耗时」这两类证据只能在真实
  环境一次性观测，diff review 与 required CI 都复现不了（`03` §3「何时声明 verification」）。

### 缺失的 acceptance criteria 或决策

- 无。Issue 正文已给出 AC-1～AC-5 与唯一授权闸门，spec 在此基础上补齐可观察表述与权限验收项（AC-6）。
