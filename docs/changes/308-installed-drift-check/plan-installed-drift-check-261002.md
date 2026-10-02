---
issue: 308
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/308
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - platform-governance
  - cross-module
  - ci-change
depends_on: []
status: approved
branch: change/308-installed-drift-check
created: 2026-10-02
updated: 2026-10-02
---

# Plan：只读 installed drift 检查

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 独立应用 README/06 的检查范围、可读量、零写入与真实验收治理说明；停止该步骤 | - | completed |
| T02 | fresh run 重读后交付八面 CLI + fixture PASS/GAP/恢复与零写入验证 | T01 | pending |
| T03 | 独立仅修改 smoke 的静态/fixture 接入；保留全部既有门；停止该步骤 | T02 | pending |
| T04 | fresh run 跑完整门与两台只读回读、更新验收缺口和唯一最终 PR 候选 | T03 | pending |

每个 ticket 只在 exact branch 本地原子提交，subject 含 #308/Txx。T01、T03 受控步骤应用后停止；后续 fresh run 重读 source/合同继续，无需重复用户启动确认。AC-2 缺口不由这些 ticket 重装解决；T04 必须保留阻塞，未满足合同不能报已完成或归档。

## Expected touch points

- T01：README 安装核对段、06 踩坑 20/30；本 Issue spec/plan/evidence。
- T02：新增 `codex/tools/check-installed-drift.sh`、`check-installed-drift.py`、`codex/tests/test-installed-drift.sh` 与必要 fixture。
- T03：`codex/tests/smoke.sh`。
- T04：仅映射 verification/summary 与证据；范围内测试反馈修复在对应原 ticket 授权内追加 commit，治理改动仍独立步骤。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | `bash codex/tests/test-installed-drift.sh`：恰好八行、可读量、exact target 与退出码 |
| AC-3 | 同一 fixture CLI 测试：八面 PASS→GAP→PASS |
| AC-4 | 同一 fixture CLI 测试：缺模块/同计数字节差/错误链接 |
| AC-6 | 同一 fixture CLI 测试：写入 spy 与树指纹、不读取用户文件 |
| AC-2 | Mac 在 fresh authoritative main 下运行 checker；目前 GAP，外部独立安装处置后重跑 |
| AC-5 | `bash codex/tools/check-installed-drift.sh --source-only`；`bash codex/tests/smoke.sh` |
| AC-7 | Mac 与 gitea-ci 分别本机运行 checker；保存 source SHA、root、命令、stdout、退出码；不调用 installer |
| AC-8 | 无网络 fixture source identity 用例及 source-origin 差异拒绝，真实 fresh main 只通过 broker 获取并单独记录 |
| 语法/静态 | `bash -n` 新增/修改 shell；ShellCheck 可用时执行；`git diff --check` |
| 文档/归属 | `resolve-documents 308`、`check-change-documents`、claim marker 核对 |
| PR gate | `apply-classification-labels.sh --verify 308` 真实 projected；请求绑定 #308/exact branch/manual 的提交确认后才能 push/create；required CI 全绿后 human review/merge |

完整 smoke 遇当前已知 locale/fixture 问题时先留原环境失败证据，再按已有平台可重复环境验证；两者分别报告，不隐去 FAIL，不顺手实现其它 Issue。

## 部署与回滚

无安装/部署。本命令运行不写 installed；fixture 只在临时目录中创建、故意漂移与恢复。源码回滚经独立 PR revert #308 原子提交。
