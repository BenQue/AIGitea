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

# Implementation plan · 309 flutter-runner-preinstall

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 幂等安装脚本 `codex/tools/install-runner-flutter.sh`（含只读 `--check` 与 `--repair`）与其单元测试，登记进 smoke 静态闸门 | - | done |
| T02 | 在 gitea-ci 主机真实执行安装：`unzip` + `/opt/flutter/3.32.8` + 自举 + `precache`，取得 AC-1/AC-2/AC-6 与 `df` 证据 | T01 | done |
| T03 | 创建 `/opt/act-runner/.pub-cache`，以 `gitea-runner` 身份对 NewEMaint `apps/mobile` 干净 checkout 实测 `pub get` + `dart analyze` 耗时，另一份 checkout 复测 `pub get` 缓存命中（AC-3、AC-7） | T02 | done |
| T04 | `01-基础设施-VM-Gitea-Runner.md`：新增 Flutter 小节 + 三处 as-built 更正（`config.yaml`、`ExecStart -c`、`/opt/node24.18.0`）+ runner 作业环境小节（AC-4） | - | done |
| T05 | **仅当闸门 3 获批**：`config.yaml` 新增 `runner.envs`，重启 act_runner，配置与 daemon 环境双读回（补回的 AC-8） | T02, T03 | not-planned（建议拒绝闸门 3） |
| T06 | verification 文档定稿、`check-change-documents`、全量 smoke、判级投影 `--verify`（AC-5） | T02, T03, T04 | done |

**主机写入的 ticket 与授权闸门逐条对应**（闸门表见 spec「风险与回滚约束」）：

| Ticket | 闸门 | 未授权时 |
|---|---|---|
| T02 | 闸门 1 | NOT RUN；T03、T05 连带 NOT RUN；AC-1/AC-2/AC-3/AC-6/AC-7/AC-8 全部达不成 |
| T03 | 闸门 2 | NOT RUN；AC-3、AC-7 达不成；AC-1/AC-2/AC-6 仍可达成 |
| T05 | 闸门 3 | 默认就不执行（spec 建议拒绝）；拒绝时无 AC 受影响，因为 AC-8 随闸门 3 一起不成立 |

T01、T04、T06 不需要任何主机写入，三条闸门全不授权时它们仍然交付，T06 的 AC-5 相应记为部分 NOT RUN。
闸门 3 是三条里唯一影响三个仓库既有 CI 的，可以单独拒绝而不影响闸门 1、2。

T04 的三处 as-built 更正全部基于已经取得的只读证据，因此**不 blocked by T02**：授权与否都能交付。
范围 3 由调度会话在 2026-09-18 扩为三处（Issue 正文 `updated_at: 2026-09-18T21:20:41+08:00`）。

## Expected touch points

- **T01**：`codex/tools/install-runner-flutter.sh`（新增）、`codex/tests/test-install-runner-flutter.sh`（新增）、
  `codex/tests/smoke.sh`（把两个新文件加入 `bash -n` 与 `shellcheck` 清单）。
- **T02/T03/T05**：无仓库文件改动，只产出 verification 里的命令与输出。
  T05 改的是主机上的 `/opt/act-runner/config.yaml`，不是仓库里的任何文件。
- **T04**：`01-基础设施-VM-Gitea-Runner.md`（§4.1 as-built 重写 + 新增 Flutter 小节 + 新增 `/opt/node24.18.0` as-built 小节）。
- **T05**：`docs/changes/309-flutter-runner-preinstall/verification-flutter-runner-preinstall-260918.md`（新增）、
  `summary-flutter-runner-preinstall-260918.md`（`status` 推进与 PR 回填）。

范围提示，不授权扩大 spec。特别地：不改 `codex/install-*.sh` 任何 installer，不新增第 9 个 installer。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | `sudo -u gitea-runner /opt/flutter/3.32.8/bin/flutter --version`；`sudo -u gitea-runner /opt/flutter/3.32.8/bin/dart --version`；`command -v unzip` |
| AC-2 | 连续两次 `sudo bash <script>`，第二次输出含「already installed」且无 `Cloning`；两次输出全文入 verification |
| AC-3 | 在 VM 上 `git clone /mnt/mac/Users/benque/Projects/NewEmaint` 得干净 checkout，`chown` 给 `gitea-runner` 后以该身份 `time flutter pub get` 与 `time dart analyze --format=machine .` |
| AC-4 | `git diff` review `01-基础设施-VM-Gitea-Runner.md`，三处逐条比对：(a) `stat`/`cat /opt/act-runner/config.yaml`；(b) `systemctl show act_runner -p ExecStart`；(c) `cat /opt/node24.18.0/.aisoft-runtime-source` 与 `stat` mtime。全部取自 T02 之前的只读输出 |
| AC-5 | `df -h /opt`（安装前后各一次）；`PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli check-change-documents --repo <checkout>`；`bash codex/tests/smoke.sh`；`codex/tools/apply-classification-labels.sh --verify 309` |
| AC-6 | `sudo -u gitea-runner /opt/flutter/3.32.8/bin/flutter --version` 连跑两次，比对第二次输出无 Dart SDK 下载/自举行 |
| AC-7 | `stat -c '%U:%G %a' /opt/act-runner/.pub-cache`；首次 `pub get` 后 `du -sh` |
| AC-8（仅闸门 3 获批时存在） | `cat /opt/act-runner/config.yaml`（读回 `runner.envs`）；重启后 `sudo tr '\0' '\n' < /proc/$(systemctl show act_runner -p MainPID --value)/environ` |

## 部署与回滚

本次**不是应用部署**：不产出制品、不晋级环境、不触及任何应用运行时。它是 CI 主机的一次
持久能力安装，因此按主机侧变更处理：

- **两次重复执行**：AC-2 即为幂等证据（第二次 no-op）。
- **一次故意失败回滚**：在安装前先用一个错误 revision 跑一次脚本，断言它在 revision 校验处失败退出、
  不留下半装状态（失败后 `/opt/flutter/3.32.8` 不存在或被脚本清理干净），输出入 verification。
- **回滚命令**：`sudo rm -rf /opt/flutter/3.32.8`。目录本次之前不存在，删除即回到安装前状态。
  `unzip` 保留，不在回滚范围。
- **推荐形状下不重启任何服务**：闸门 1、2 只新增路径，act_runner 全程不受影响。
- **仅当闸门 3 获批**才涉及一次 `systemctl restart act_runner`：重启前用
  `orbstack.runner.status` 确认 `execution.child_count == 0`，非零就等；读回不符立刻回滚——
  删除新增的 `runner.envs` 段并再次重启，回到 `capacity`/`timeout` 两键的原状态。
- **不涉及**：systemd unit 与既有 `10-config.conf` drop-in 的修改、act_runner 升级、生产主机。
