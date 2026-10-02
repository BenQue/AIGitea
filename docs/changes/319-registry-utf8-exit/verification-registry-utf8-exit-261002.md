---
issue: 319
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/319
change_type: bugfix
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - ci-change
depends_on: []
status: contract-drafting
branch: change/319-registry-utf8-exit
created: 2026-10-02
updated: 2026-10-02
---

# #319 验证记录

## 基线与范围

- authoritative origin/main：`5c2cd726c9aeaee9d17541d8feb049e33881bbac`，broker fresh fetch PASS。
- macOS /bin/bash 3.2.57 arm64-apple-darwin26，默认 LC_ALL=C.UTF-8。
- Linux gitea-ci /bin/bash 5.3.9 aarch64；C.utf8、python3/curl/rg 可用。
- 所有 HTTP 请求仅测试 fixture 的 127.0.0.1 临时端口；未访问真实 registry/credential。

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| 默认 C.UTF-8 /bin/bash codex/tests/test-registry-preflight.sh（改前） | FAIL（已复现） | 停掉 registry 后期望 1，实际 0 |
| en_US.UTF-8 / zh_CN.UTF-8 同完整 fixture（改前） | FAIL（已复现） | baseline-macos-utf8.json full-test-clean-env |
| 三组 UTF-8：healthy 与停止后直接 probe（改前） | 健康 0；停止 0（错误） | [baseline-macos-utf8.json](evidence/baseline-macos-utf8.json)，stderr unbound variable |
| Linux C.UTF-8 同 fixture（改前） | PASS | [baseline-linux-utf8.txt](evidence/baseline-linux-utf8.txt) |
| main protection / Issue comments / open PR 只读 | PASS | main 禁 push/force，required CI 为 CI / verify (pull_request)，#319 open/无评论/无开放 PR |
| 判级投影计划（无 --apply） | BLOCKED_APPROVAL_REVIEW | 历史记录：自动审批认为可能写 live 标签，原命令未执行；用户本 turn 明确确认后已解决 |
| 用户合同批准、classification --apply 319 / --verify 319 | PASS | mapped summary 与 live labels 一致，result=projected，bugfix/complex |
| broker approved 生命周期读回 | PASS | after=[approved,complexity/complex,type/bugfix] |
| 改后 matrix / bash -n / ShellCheck / 完整 smoke | NOT RUN | 尚未批准实施 |
| PR CI / installed / live / 下游 / 部署 / 人 merge | NOT RUN | fixture/source 不推断这些层次 |

第一次证据包装器继承 REGISTRY_PREFLIGHT_REGISTRY，覆盖了完整测试的内部 fixture 端口。该记录保留并标 INVALID_HARNESS_ENV，不作为产品基线；纠正外部配置后三组完整测试均在停止 fixture 处真实复现。

Bash 3.2 最小 nounset 实验中，原 EXIT trap 与保存 $? 再 exit 的 trap 都返回 0；此观察只界定方案，正式验收以真实 HTTP 行为为准。

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | 改后 NOT RUN | 基线仍有 4 处错误边界 |
| AC-2 | 改前 FAIL | 三组 UTF-8 停止 fixture 错误退出 0 |
| AC-3 | 改前比较已执行；改后 NOT RUN | macOS 失败，Linux 通过，非修复验收 |
| AC-4 | NOT RUN | 实施未批准 |

## 遗留风险与未完成项

用户已确认合同及 broker 判级/流程投影；独立合同批准步骤本 turn 完成并停止，fresh run 才实施，无需重复启动确认。Matt live triage 投影 typed operation 缺口为 GAP，不扩大 #319 到 broker 治理或绕过访问合同。无阻塞 Issue 依赖。

## 合同批准步骤证据

本会话用户于 2026-10-02 回复“确认”，接受已展示的 exact #319 / change/319-registry-utf8-exit / manual 合同及 broker 判级/流程投影。本次只更新合同/批准证据，CI/runtime、AC、权限、安装、服务、remote branch 和 PR 未改变。

判级工具及两个依赖以逐字节相同的临时扁平副本运行，既有 fallback 选择 /usr/local/libexec/aisoft/host-access-broker；未修改平台工具。真实投影与独立读回见 [contract-approval.json](evidence/contract-approval.json)。live Matt triage typed operation 缺口仍为 GAP。
