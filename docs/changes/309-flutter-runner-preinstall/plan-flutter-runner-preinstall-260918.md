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
| T01 | 幂等安装脚本 `codex/tools/install-runner-flutter.sh`（含只读 `--check`）与其单元测试，登记进 smoke 静态闸门 | - | pending |
| T02 | 在 gitea-ci 主机真实执行安装：`unzip` + `/opt/flutter/3.32.8` + 自举 + `precache`，取得 AC-1/AC-2/AC-6 与 `df` 证据 | T01 | pending |
| T03 | 以 `gitea-runner` 身份对 NewEMaint `apps/mobile` 干净 checkout 实测 `pub get` + `dart analyze` 耗时，取得 AC-3 证据 | T02 | pending |
| T04 | `01-基础设施-VM-Gitea-Runner.md`：新增 Flutter 小节 + 三处 as-built 更正（`config.yaml`、`ExecStart -c`、`/opt/node24.18.0`）（AC-4） | - | pending |
| T05 | verification 文档定稿、`check-change-documents`、全量 smoke、判级投影 `--verify`（AC-5） | T02, T03, T04 | pending |

T02 是唯一需要主机写入的 ticket，受 Issue 正文的唯一授权闸门管辖；未授权时它停在 NOT RUN，
T03 随之 NOT RUN，T01/T04/T05 仍然交付（T05 的 AC-5 相应记为部分 NOT RUN）。

T04 的三处 as-built 更正全部基于已经取得的只读证据，因此**不 blocked by T02**：授权与否都能交付。
范围 3 由调度会话在 2026-09-18 扩为三处（Issue 正文 `updated_at: 2026-09-18T21:20:41+08:00`）。

## Expected touch points

- **T01**：`codex/tools/install-runner-flutter.sh`（新增）、`codex/tests/test-install-runner-flutter.sh`（新增）、
  `codex/tests/smoke.sh`（把两个新文件加入 `bash -n` 与 `shellcheck` 清单）。
- **T02/T03**：无仓库文件改动，只产出 verification 里的命令与输出。
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

## 部署与回滚

本次**不是应用部署**：不产出制品、不晋级环境、不触及任何应用运行时。它是 CI 主机的一次
持久能力安装，因此按主机侧变更处理：

- **两次重复执行**：AC-2 即为幂等证据（第二次 no-op）。
- **一次故意失败回滚**：在安装前先用一个错误 revision 跑一次脚本，断言它在 revision 校验处失败退出、
  不留下半装状态（失败后 `/opt/flutter/3.32.8` 不存在或被脚本清理干净），输出入 verification。
- **回滚命令**：`sudo rm -rf /opt/flutter/3.32.8`。目录本次之前不存在，删除即回到安装前状态。
  `unzip` 保留，不在回滚范围。
- **不涉及**：服务重启、systemd unit 修改、act_runner 配置、生产主机。
