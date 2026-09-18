---
issue: 309
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/309
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - ci-integration
  - shared-core
depends_on: []
status: contract-drafting
branch: change/309-flutter-runner-preinstall
created: 2026-09-18
updated: 2026-09-18
---

# Spec · gitea-ci runner 预装 Flutter 3.32.8 与 unzip

## 目标与原因

让 gitea-ci runner 主机具备**平台提供的、版本钉死的** Flutter 工具链，使任何仓库的 CI job
可以直接使用而不必在 job 内准备 SDK；同时把这条主机侧合同和既有的 act-runner as-built
一起写回 `01-基础设施-VM-Gitea-Runner.md`，消除文档与主机的漂移。

原因（只读实测，2026-09-18）：

- runner 主机是 aarch64，Flutter 官方 Linux 归档只有 x64，arm64 只能 clone tag 后自举。
- 自举要解压 `dartsdk-linux-arm64`，主机上 `unzip`/`bsdtar`/`7z` 全部缺失，自举必然失败。
- `runner.timeout` 实测为 `20m`、`capacity` 为 `1`，冷启动 clone 约 1 GiB 很可能撞超时并占死唯一执行位。

## Acceptance criteria

- [ ] **AC-1 SDK 与解压工具就位**：以 `gitea-runner` 身份执行
      `/opt/flutter/3.32.8/bin/flutter --version` 输出包含 `Flutter 3.32.8` 与 revision
      `edada7c56edf4a183c1735310e123c7f923584f1`；`/opt/flutter/3.32.8/bin/dart --version`
      输出的 Dart 版本与该 Flutter 版本随附版本一致；`command -v unzip` 非空。
- [ ] **AC-2 安装幂等**：同一条安装命令连续执行两次，第二次为 no-op——不发生 `git clone`、
      不改变 `/opt/flutter/3.32.8` 下任何文件的 mtime 集合、退出码为 0 并显式报告「已安装且 revision 一致」。
      两次执行的完整输出写入 verification。
- [ ] **AC-3 真实 job 形态可跑通且远低于超时**：在 runner 主机上以 `gitea-runner` 身份，对 NewEMaint
      `apps/mobile` 的一份干净 checkout 执行 `flutter pub get` 与 `dart analyze --format=machine .`，
      两条命令都以非 SDK 错误结束（analyze 可以报项目自身的 lint/错误条目，但不得报 SDK 缺失、
      权限拒绝或自举失败），各自耗时与合计耗时以实测秒数写入 verification，且合计远小于 `20m` job 超时。
- [ ] **AC-4 文档与主机一致**：`01-基础设施-VM-Gitea-Runner.md` 新增「Flutter SDK（runner 预装）」
      小节，写明路径、版本、revision、安装与升级方式、验证命令；§4.1 as-built 改为实测状态
      （`config.yaml` 存在、`capacity 1`、`timeout 20m`、`ExecStart` 已含 `-c`），并标注更正日期与依据。
- [ ] **AC-5 证据与闸门**：verification 记录安装前后 `df -h /opt`；
      `aisoft-loop check-change-documents --repo <checkout>` PASS；
      `bash codex/tests/smoke.sh` PASS；
      `codex/tools/apply-classification-labels.sh --verify 309` 两个维度都读回 `projected`。
- [ ] **AC-6 runner 身份可用且不重复自举**：`/opt/flutter/3.32.8` 对 `gitea-runner` 可读可执行，
      且以 `gitea-runner` 身份连续两次执行 `flutter --version` 时，第二次不再出现 Dart SDK 下载或
      自举输出——证明 `bin/cache` 的属主/权限不会迫使每个 job 重新自举。

## 接口、数据与兼容性影响

- **新增主机合同**：`/opt/flutter/<version>` 为平台提供的 Flutter 安装根，随附
  `.aisoft-runtime-source` provenance marker，字段沿用主机上既有的
  `/opt/node24.18.0/.aisoft-runtime-source`（`contract=gitea-runner-node-runtime/v1`），
  本次取 `contract=gitea-runner-flutter-runtime/v1`。
- **不修改** act_runner 的 `PATH`、systemd unit、`config.yaml` 或注册标签。消费方 job 使用绝对路径
  或自行把 `/opt/flutter/3.32.8/bin` 前置到 `PATH`；把它写进 runner 全局 `PATH` 属于另一次变更。
- **无 schema、无数据、无 API、无外部契约变化。**
- **向后兼容**：本次之前 `/opt/flutter` 不存在，没有既有消费方，因此没有兼容窗口问题。

## 风险与回滚约束

- 安装过程不经 act_runner、不重启 act_runner、不重启任何服务；开工前用
  `orbstack.runner.status` 确认 `execution.child_count == 0`。
- clone 后必须断言 `git rev-parse HEAD` 等于钉住的 revision；不等即失败退出，不继续自举。
- 磁盘闸门：安装前 `df` 使用率达到或超过 80% 即停止并报 BLOCKED（沿用 `12` 的磁盘告警阈值）。
- 回滚：`sudo rm -rf /opt/flutter/3.32.8`。该目录本次之前不存在，删除即回到安装前状态。
  `unzip` 是 APT 包，保留不构成风险，移除它不在本次回滚范围内。
- 主机侧任何写入都由 Issue 正文的唯一授权闸门管辖；未获授权则全部保持 NOT RUN，只交付脚本与文档。

## 非目标

- NewEMaint 侧 workflow 改动（属于 NewEMaint #158）。
- 公司侧 CI job image（NewEMaint 另有 Issue）。
- act_runner 升级、`capacity`/`timeout` 调整、注册标签变更。
- 把 `/opt/flutter/3.32.8/bin` 写进 act_runner 的全局 `PATH`。
- Android SDK、Gradle、Java 工具链——`flutter build apk` 不在本次验收范围，本次只保证
  `pub get` 与 `dart analyze` 这一档静态验证能力。
- 补写 `/opt/node24.18.0` 的文档缺口（同类漂移，但属于另一条 Issue）。

## 未决问题

无。
