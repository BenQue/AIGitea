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
status: verified
branch: change/309-flutter-runner-preinstall
created: 2026-09-18
updated: 2026-09-18
---

# Verification · 309 flutter-runner-preinstall

## 基线与范围

- 基线：`origin/main` = `e1290d245553a59b47450438e1d94f0be4269e00`
- 环境：Mac 交互会话 + OrbStack VM `gitea-ci`（`Ubuntu 26.04 LTS`，`aarch64`，内核
  `7.0.14-orbstack-00380-ga7e0a2dc9535`）
- 本记录负责证明：AC-1 ~ AC-7
- **授权记录（2026-09-18）**：负责人在本会话确认点 1 批准合同，并逐条授权
  **闸门 1（装 `unzip` + 写 `/opt/flutter/3.32.8`）与闸门 2（建 `/opt/act-runner/.pub-cache`）**；
  **闸门 3（改 `runner.envs` 并重启 act_runner）未授权，保持 NOT RUN**。
  因此本次不修改 `/opt/act-runner/config.yaml`、不修改 systemd unit、不重启任何服务，
  `PUB_CACHE` 与 `PATH` 由消费方 workflow 自行声明。

## 执行结果

### 只读核对（安装前基线，2026-09-18）

| Command / check | Result | Evidence |
|---|---|---|
| `uname -a` | PASS | `Linux gitea-ci 7.0.14-orbstack-00380-ga7e0a2dc9535 … aarch64 GNU/Linux` |
| `. /etc/os-release && echo $PRETTY_NAME` | PASS | `Ubuntu 26.04 LTS` |
| `command -v unzip bsdtar 7z 7za p7zip` | PASS（确认缺失） | 五个全部 `MISSING`；`python3` `/usr/bin/python3`、`git` `/usr/bin/git`、`curl` `/usr/bin/curl`、`xz` 存在 |
| `ls /opt/flutter` | PASS（确认不存在） | `ls: cannot access '/opt/flutter': No such file or directory` |
| `ls /opt/act-runner/.pub-cache` | PASS（确认不存在） | 目录不在 `/opt/act-runner` 列表中 |
| `df -h /opt`（**安装前**） | PASS | `/dev/vdb1  253G  54G  199G  22% /`，使用率 22% < 80% 阈值 |
| `git ls-remote https://github.com/flutter/flutter refs/tags/3.32.8` | PASS | `edada7c56edf4a183c1735310e123c7f923584f1	refs/tags/3.32.8`，与 Issue 钉住的 revision 一致 |
| `id gitea-runner` | PASS | `uid=999(gitea-runner) gid=986(gitea-runner)` |
| `sudo -u gitea-runner ls /mnt/mac/Users/benque/Projects/NewEmaint/apps/mobile` | PASS | 可读，AC-3 的干净 checkout 不需要任何凭据 |
| NewEMaint `apps/mobile` SDK 约束 | PASS | `pubspec.yaml` `sdk: ^3.8.1`；`pubspec.lock` `flutter: ">=3.32.0"`，与 Flutter 3.32.8 相容 |

### §4.1 / §4.2 as-built 更正的依据（AC-4）

| Command / check | Result | Evidence |
|---|---|---|
| `stat -c '%n %U:%G %a %y' /opt/act-runner/config.yaml` | PASS | `gitea-runner:gitea-runner 644 2026-09-05 22:46:24.180971195 +0800` |
| `cat /opt/act-runner/config.yaml` | PASS | 全文两键：`runner:` / `capacity: 1` / `timeout: 20m` |
| `systemctl show act_runner -p ExecStart` | PASS | `argv[]=/usr/local/bin/act_runner daemon -c /opt/act-runner/config.yaml`，`start_time=[Tue 2026-09-15 20:38:48 CST]`，`pid=525` |
| `systemctl cat act_runner` | PASS | base unit 的 `ExecStart` 不带 `-c`；drop-in `/etc/systemd/system/act_runner.service.d/10-config.conf` 先 `ExecStart=` 清空再重设带 `-c` 的值 |
| `ls -la /etc/systemd/system/act_runner.service.d/` | PASS | 只有 `10-config.conf`，`2026-09-05 22:46` |
| `cat /opt/node24.18.0/.aisoft-runtime-source` | PASS | `contract=gitea-runner-node-runtime/v1`、`installed_at=2026-08-07`、node/npm 版本与校验值、`rollback=rename-or-remove-/opt/node24.18.0; system-node-and-/opt/node22-unchanged` |
| `stat /opt/node24.18.0` | PASS | `root:root 755`，mtime `2026-08-07 22:36:37 +0800`，与 marker 自报日期一致 |
| `/opt/node24.18.0/bin/node --version` / `npm --version` | PASS | `v24.18.0` / `11.19.0` |
| `du -sh /opt/node24.18.0` | PASS | `213M` |
| `/opt/node22/bin/node --version` | PASS | `v22.22.0`，目录 `gitea-runner` 属主，**无 marker**，安装者记为 `unknown` |
| `command -v node && node --version` | PASS | `/usr/bin/node` `v20.20.2`，系统自带，不由平台管理 |
| `act_runner generate-config` | PASS | v1.0.7 支持 `runner.envs`（`Extra environment variables to run jobs`）与 `runner.env_file`；主机上 `/opt/act-runner/.env` 不存在，`config.yaml` 未声明 `envs` |

### 主机执行（T02、T03，闸门 1、2 已授权，2026-09-18 21:48–22:05）

开工前 `orbstack.runner.status` 报 `child_count: 1`（NewEMaint task 1436 正在跑），
等到 `child_count == 0`（13:48:04Z）才开始——安装要下载约 1.2 GiB，与在跑的 job 抢带宽有把它
推向 20m 超时的风险。安装本身不经 act_runner、不重启任何服务。

| Command / check | Result | Evidence |
|---|---|---|
| 故意失败：`FLUTTER_REVISION=0000…` 跑安装脚本 | PASS | `ERROR: revision mismatch: tag 3.32.8 resolved to edada7c56edf4a183c1735310e123c7f923584f1, expected 0000…`；随后 `ls -la /opt/flutter` 只剩空目录，staging 已被 trap 清除，无半装树 |
| 正式安装（第一次） | PASS | `revision assertion passed: edada7c56edf4a183c1735310e123c7f923584f1`；Dart SDK 187.3M 下载完成；`precache --linux` 下载 Material fonts / sky_engine / linux-arm64 tools 等 11 项；`script exit=0` |
| `apt-get install -y unzip` | PASS | `Unpacking unzip (6.0-29ubuntu1)` / `Setting up unzip (6.0-29ubuntu1)` |
| 安装后 `flutter --version`（gitea-runner） | PASS | `Flutter 3.32.8 • channel [user-branch]` / `Framework • revision edada7c56e` / `Tools • Dart 3.8.1 • DevTools 2.45.1` |
| `dart --version`（gitea-runner） | PASS | `Dart SDK version: 3.8.1 (stable) … on "linux_arm64"` |
| `which unzip`（gitea-runner） | PASS | `/usr/bin/unzip` |
| 幂等第二次执行 | PASS | `已装` 分支命中：`skipping clone and bootstrap`、`skipping ownership, bootstrap and precache`、`provenance marker unchanged`；`script exit=0`；`CLONE: none`；`BOOTSTRAP: skipped` |
| 幂等的 mtime 集合比对 | PASS | `find … -printf "%T@ %m %u:%g %p" | sort | md5sum` 前后同为 `0f9fc3fa8bb953a4f236422bac16a89c`，文件数同为 `19696` |
| `--check` 只读模式 | PASS | `check: already installed and revision matches`，无写入 |
| `stat /opt/flutter/3.32.8` | PASS | `gitea-runner:gitea-runner 755`，`du -sh` = `1.1G` |
| `cat .aisoft-runtime-source` | PASS | `contract=gitea-runner-flutter-runtime/v1`、`installed_at=2026-09-18`、`flutter_revision=edada7c5…`、`runner_env=not injected…`、`rollback=remove-/opt/flutter/3.32.8; act_runner-config-and-unit-unchanged` |
| `stat /opt/act-runner/.pub-cache` | PASS | `gitea-runner:gitea-runner 755`，`du -sh` = `337M` |
| **`df -h /opt` 安装后** | PASS | `/dev/vdb1  252G  57G  195G  23% /`；安装前 22–23%，净增约 1.4 GiB，远低于 80% 阈值 |
| **未触碰 act_runner 的证据** | PASS | `config.yaml` mtime 仍是 `2026-09-05 22:46:24.180971195 +0800`；`10-config.conf` mtime 仍是 `2026-09-05 22:46:24.195971142 +0800`；`MainPID=525`、`ExecMainStartTimestamp=Tue 2026-09-15 20:38:48 CST` 与安装前一致，服务未重启；`config.yaml` 全文仍只有 `capacity: 1` / `timeout: 20m` |

#### AC-3：真实 job 形态耗时（`gitea-runner` 身份，NewEMaint `apps/mobile`）

干净 checkout 取自 `git clone /mnt/mac/Users/benque/Projects/NewEmaint`（本地克隆，不需要任何凭据），
HEAD = `6bd2da3`，`chown` 给 `gitea-runner` 后以下列环境执行：
`HOME=/opt/act-runner`、`PUB_CACHE=/opt/act-runner/.pub-cache`、`PATH=/opt/flutter/3.32.8/bin:<系统五段>`。

| 步骤 | exit | 耗时 | 说明 |
|---|---|---|---|
| `flutter pub get` | 0 | **10s** | `Got dependencies!`；`119 packages have newer versions incompatible with dependency constraints` |
| `dart analyze --format=machine .` | 3 | **11s** | 105 行输出，全部是**项目自身**的 lint 与编译错误条目，无 SDK 缺失、无权限拒绝、无自举失败 |
| **合计** | — | **21s** | 对 `timeout: 20m`（1200s）有 **57 倍**余量 |

`dart analyze` 的 exit 3 表示它找到了问题，不是 SDK 故障。前两条是编译期错误：
`lib/shared/services/sync_service.dart:130` 的 `categoryId` 与 `reasonId` 两个必填具名参数缺实参。
**这是 NewEMaint 自己的代码问题，属于 #158 的范围，本 Issue 不修。**

#### AC-3 续 / AC-7：持久缓存确实命中

同一份**另建的**干净 checkout（`/tmp/309-ac3-b`），两种 `PUB_CACHE` 对照：

| PUB_CACHE | `flutter pub get` exit | 耗时 | 缓存目录增长 |
|---|---|---|---|
| 空的临时目录（冷） | 0 | **10s** | 247 MiB |
| `/opt/act-runner/.pub-cache`（热） | 0 | **2s** | 0 |

热缓存比冷缓存快 5 倍，并且每个 job 省下 247 MiB 下载。两次都先删掉该 checkout 的 `.dart_tool`，
所以 2s 命中的是共享持久缓存，不是 checkout 自己的产物。临时冷缓存目录已删除。

### 仓库侧（T01、T04）

| Command / check | Result | Evidence |
|---|---|---|
| `bash -n codex/tools/install-runner-flutter.sh` | PASS | 无输出 |
| `shellcheck codex/tools/install-runner-flutter.sh` | PASS | 无 finding |
| `bash codex/tests/test-install-runner-flutter.sh` | PASS | `PASS: install-runner-flutter`（10 个用例：未知参数、`--check` 只读、首次安装、二次 no-op（含不重跑自举）、`--repair` 强制自举、已装态 `--check`、revision 不符 fail closed 且无残留、磁盘闸门、`--no-pub-cache`、`INSTALL_ROOT` 父目录也不存在时的磁盘探测） |
| `/bin/bash codex/tests/test-install-runner-flutter.sh`（bash 3.2） | PASS | `PASS: install-runner-flutter`，确认不依赖 bash 4+ 语法 |
| 缺陷 1 的反向证明 | PASS | 把磁盘探测改回 `df --output=pcent "$INSTALL_ROOT"`，测试 `exit=1`；恢复后 `exit=0` |
| 缺陷 2 的反向证明 | PASS | 去掉 `-c safe.directory=`，测试 `exit=1`；恢复后 `exit=0` |
| `bash codex/tests/smoke.sh` | PASS | 两次：修复前 `Ran 965 tests in 70.946s` / `OK`；两个缺陷修复后重跑 `Ran 965 tests in 87.319s` / `OK` / `Codex platform static smoke checks passed.`，均 exit 0。含新登记的 `test-install-runner-flutter.sh` |
| `aisoft-loop check-change-documents --repo <checkout>` | PASS | `PASS: change-documents` / `PASS: change-pr-url` / `changes=141 pass=2 gap=0` |
| `apply-classification-labels.sh 309`（计划） | PASS | `applied:false`、`change_type:platform`、`complexity:complex` |
| `apply-classification-labels.sh 309 --apply` | PASS | `applied:true`、`result:updated` |
| `apply-classification-labels.sh --verify 309` | PASS | `result:projected`、`detail:Issue #309 carries the classification its merged summary declares` |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 SDK 与解压工具就位 | **PASS** | `Flutter 3.32.8` + `revision edada7c56e`；`Dart SDK version: 3.8.1 … linux_arm64`；`which unzip` = `/usr/bin/unzip`。均以 `gitea-runner` 身份执行 |
| AC-2 安装幂等 | **PASS** | 第二次执行 `exit=0`、无 clone、无自举；mtime 集合 md5 前后同为 `0f9fc3fa…`，文件数同为 `19696`。两次执行输出见上 |
| AC-3 job 形态实测耗时 | **PASS** | `pub get` 10s + `dart analyze` 11s = **21s**，对 20m 超时有 57 倍余量；第二份 checkout 热缓存 `pub get` 2s vs 冷缓存 10s |
| AC-4 文档与主机一致 | **PASS** | §4.1 四处更正（`config.yaml` 存在/20m、`ExecStart -c` 已生效、drop-in 而非 `edit --full`）、新增 §4.2 预装工具链 as-built（含 `/opt/node24.18.0`）、新增 §4.3 Flutter 合同；每处标注更正日期与依据命令 |
| AC-5 证据与闸门 | **PASS** | `df -h /opt` 安装前 22% / 安装后 23%（净增约 1.4 GiB）；`check-change-documents` PASS；`smoke.sh` PASS；`apply-classification-labels.sh --verify 309` = `projected` |
| AC-6 runner 身份不重复自举 | **PASS** | 以 `gitea-runner` 连跑两次 `flutter --version`，两次输出完全一致且都不含 Dart SDK 下载或自举行 |
| AC-7 持久 pub 缓存就位 | **PASS** | `/opt/act-runner/.pub-cache`，`gitea-runner:gitea-runner 755`，`du -sh` = `337M`，与既有 `/opt/act-runner/.npm` 同级同属主 |

### 实现过程中在真实主机上发现并修掉的两个缺陷

单测在 mock 环境全绿，但真实主机跑出两个 mock 掩盖掉的 bug。两个修复都补了能反向证明的回归用例
（改回原写法测试变红，恢复后变绿，均已实测）。

| # | 现象 | 根因 | 修法 | mock 为什么没抓到 |
|---|---|---|---|---|
| 1 | 脚本在磁盘闸门处静默退出，什么都没做 | `/opt/flutter` 尚不存在时 `df --output=pcent` 失败，`set -euo pipefail` 让失败的命令替换直接终止脚本 | 新增 `disk_target()`，向上走到最近一个存在的祖先目录再测 | `df` 被 mock 成永远成功，恰好 mock 掉了会失败的那个条件。已改成「路径不存在就像真 `df` 一样失败」 |
| 2 | 已装的树被误判成「存在但不是 git checkout」，幂等失效 | 脚本以 root 运行而安装树属主是 `gitea-runner`，触发 git 2.53 的 dubious-ownership 拒绝（`exit=128`） | 读 revision 时带 `-c safe.directory=<该路径>`，作用域只限一个目录，不写全局配置 | `chown` 被 mock 成空操作，属主关系根本不存在。已改成记录属主变更并让后续读失败 |

第 2 个缺陷没有造成任何损害，是因为脚本下一道检查「目录存在但不是 git checkout」拒绝了继续——
诊断是错的，但 fail closed 的方向是对的。

另外发现一处第三方影响的行为（已写进 `01` §4.3）：第二次执行**不该**重跑自举。
`flutter --version` 会改写 `bin/cache` 下的时间戳文件，「顺手再跑一次」看着无害，
实际让 AC-2 的 mtime 集合不变这条性质失效。脚本改为 revision 一致时跳过属主/权限/自举/precache，
需要重做时用新增的 `--repair` 显式要求。

## 遗留风险与未完成项

1. **闸门 3（改 `runner.envs` 并重启 act_runner）未获授权，保持 NOT RUN**。因此本次
   **没有**修改 `/opt/act-runner/config.yaml`、没有修改 systemd unit、没有重启任何服务——
   `MainPID=525` 与 `ExecMainStartTimestamp=2026-09-15 20:38:48 CST` 在安装前后一致即为证据。
   `PUB_CACHE` 与 `PATH` 由消费方 workflow 在 job 级 `env:` 声明，样例见 `01` §4.3。
   随闸门 3 一起不成立的 AC-8 因此不存在，不是未完成项。
2. **job step 内环境是否按预期生效未验证**，也无法在本 Issue 内验证：唯一消费方 workflow
   属于 NewEMaint #158。#158 首跑应显式验一次 `echo $PUB_CACHE` 与 `flutter --version`，
   不要把「#309 完成」直接当成「job 内已生效」。
3. **NewEMaint `apps/mobile` 当前 `dart analyze` 不干净**：105 条，其中
   `lib/shared/services/sync_service.dart:130` 有两条编译期错误（`categoryId`、`reasonId`
   两个必填具名参数缺实参）。#158 的 `mobile-verify` job 一接上就会红。这是 NewEMaint 自己的
   代码问题，属于 #158 范围，本 Issue 不修，也不改其判定。
4. **pub.dev 是新的外部依赖**，npm 侧 Verdaccio 在 pub 侧没有等价物。pub.dev 不可达时消费方
   job 会红；持久 `PUB_CACHE` 只减少重复下载（实测省 247 MiB / 8s），不提供离线能力。
   离线镜像不在本 Issue 范围。
5. **`/opt/node22` 没有 provenance marker**，安装者与来源读不到，`01` §4.2 如实记为 `unknown`。
   补齐它需要另一次变更，不在 #309 范围。
6. **`PUB_CACHE` 与 `HOME` 的重合是巧合**：Dart 默认 pub cache 是 `$HOME/.pub-cache`，
   而 act_runner 的 unit 把 `HOME` 设成 `/opt/act-runner`，恰好指向同一处。`HOME` 一变默认路径
   就漂走，所以合同要求消费方**显式**声明 `PUB_CACHE`，不要依赖默认值。
7. **临时产物已清理**：`/tmp/309-ac3-a`、`/tmp/309-ac3-b`、`/tmp/309-coldcache` 均已删除；
   安装日志 `/tmp/309-install-1.log`、`/tmp/309-install-2.log`、`/tmp/309-fail.log` 保留在
   VM 的 `/tmp` 下作现场证据，重启即失，关键内容已抄进本文件。
