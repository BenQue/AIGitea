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
status: pending
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
- **主机写入状态**：授权闸门 1、2 截至本次记录**尚未获得负责人授权**，因此 T02、T03 为 NOT RUN，
  AC-1、AC-2、AC-3、AC-6、AC-7 相应为 NOT RUN。闸门 3 由 spec 建议拒绝、默认不执行。
  本记录中所有主机侧条目均为**只读观测**，未安装、未修改、未重启任何东西。

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

### 仓库侧（T01、T04）

| Command / check | Result | Evidence |
|---|---|---|
| `bash -n codex/tools/install-runner-flutter.sh` | PASS | 无输出 |
| `shellcheck codex/tools/install-runner-flutter.sh` | PASS | 无 finding |
| `bash codex/tests/test-install-runner-flutter.sh` | PASS | `PASS: install-runner-flutter`（8 个用例：未知参数、`--check` 只读、首次安装、二次 no-op、已装态 `--check`、revision 不符 fail closed 且无残留、磁盘闸门、`--no-pub-cache`） |
| `/bin/bash codex/tests/test-install-runner-flutter.sh`（bash 3.2） | PASS | `PASS: install-runner-flutter`，确认不依赖 bash 4+ 语法 |
| `bash codex/tests/smoke.sh` | 见下 | 见「全量 smoke」 |
| `aisoft-loop check-change-documents --repo <checkout>` | PASS | `PASS: change-documents` / `PASS: change-pr-url` / `changes=141 pass=2 gap=0` |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 SDK 与解压工具就位 | **NOT RUN** | 闸门 1 未授权；安装前基线已确认 `/opt/flutter` 不存在、`unzip` 缺失 |
| AC-2 安装幂等 | **NOT RUN**（逻辑已单测覆盖） | 真实主机两次执行未做；`test-install-runner-flutter.sh` 用例 4 在 mock 环境证明第二次不 clone 且安装根下 mtime 集合不变 |
| AC-3 job 形态实测耗时 | **NOT RUN** | 依赖 AC-1；`gitea-runner` 对 NewEMaint checkout 的读权限已确认 |
| AC-4 文档与主机一致 | **PASS** | §4.1 重写（`config.yaml` 存在/20m、`ExecStart -c` 已生效、drop-in 而非 `edit --full`）、新增 §4.2 预装工具链 as-built（含 `/opt/node24.18.0`）、新增 §4.3 Flutter 合同；每处都标注了更正日期 2026-09-18 与依据命令 |
| AC-5 证据与闸门 | **部分 PASS** | `df -h /opt` 安装前已记，安装后 NOT RUN；`check-change-documents` PASS；smoke 见下；判级 `--verify` 在提交 PR 前执行 |
| AC-6 runner 身份不重复自举 | **NOT RUN** | 依赖 AC-1 |
| AC-7 持久 pub 缓存就位 | **NOT RUN** | 闸门 2 未授权；已确认该目录当前不存在 |

## 遗留风险与未完成项

1. **授权闸门 1、2 未获授权**，主机上零写入。T02、T03 未执行，AC-1/2/3/6/7 全部 NOT RUN。
   交付物是安装脚本、runbook（§4.3）与上面的只读证据——这正是 Issue 正文「未授权即保持
   NOT RUN，只交付 runbook 与只读证据」要求的形态。
2. **授权闸门 3（改 `runner.envs` 并重启 act_runner）由 spec 建议拒绝**，默认不执行。
   采纳建议形状后，`PUB_CACHE` 与 `PATH` 由消费方 workflow 在 job 级 `env:` 声明，
   平台侧不碰三仓共用的 daemon。若负责人改为批准闸门 3，需补回 spec 中列出的 AC-8。
3. **AC-2 的真实主机证据缺口**：单测在 mock 环境覆盖了幂等逻辑，但「同一条命令在真实
   `/opt` 上跑两次」这条只能在授权后补。mock 不能替代它。
4. **pub.dev 是新的外部依赖**，npm 侧 Verdaccio 在 pub 侧没有等价物。pub.dev 不可达时
   消费方 job 会红；持久 `PUB_CACHE` 只减少重复下载，不提供离线能力。离线镜像不在本 Issue 范围。
5. **`/opt/node22` 没有 provenance marker**，安装者与来源读不到，§4.2 如实记为 `unknown`。
   补齐它需要另一次变更，不在 #309 范围。
6. **job step 内环境是否生效未验证**：本 Issue 不改 runner 环境，消费方 workflow 的
   `env:` 声明是否按预期工作，由 NewEMaint #158 的首次真实 run 证明。
