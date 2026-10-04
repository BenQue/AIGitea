---
issue: 337
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/337
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - agent-governance
  - security
  - shared-core
depends_on: []
status: approved
branch: change/337-restore-hsdb-governance
created: 2026-10-04
updated: 2026-10-04
---

# Plan 恢复 HSDB 治理注册

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 独立治理合同、manifest 原子注册、最小权限回归、源码回滚与 final manual candidate | - | in-progress |
| T02 | 已人工合并 source 与受保护安装后的 HSDB registration fresh readback | T01 | blocked-external |

T01 是一个完整可验证的配置切片：两份 manifest 与 seal 互相约束，不拆成无效中间树。
T02 的 prerequisite 为用户 final PR 确认、人工合并及独立安装批准；不是待授权的应用部署。
不创建子 Issue，不启动 HSDB 下游业务修复/UAT。

## Expected touch points

T01：spec 的授权清单；先完成四件套并记录启动授权，再独立应用治理 patch。
只改配置和支撑测试/在册文档，生产 runtime 与本次 AGENTS 不修改。

T02：源码不再扩展；外部 owner 依据 verification 的 exact pin/窗口/readback/rollback 卡执行。
任何账号或 Secret GAP 保持独立 scope，不能扩大安装窗口。

## 数据库迁移

无。

## 测试与验收映射

| AC | 验证 |
|---|---|
| AC-1/3 | 两份 JSON 与基线语义 diff；同树 seal 现算；其它仓保护不变量比较 |
| AC-2/4 | aisoft_host_access.cli validate、runtime contract tests、保护文件零 diff |
| AC-5 | targeted unittest、test-host-access-broker.sh、smoke.sh、bash -n、ShellCheck、check-change-documents、git diff --check |
| AC-6 | scratch checkout 真实 git revert --no-commit + validate；git revert --abort 后 validate 与 byte equality |
| AC-7 | owner marker、exact branch、干净 worktree、classification --verify 337、candidate receipt |
| AC-8 | broker pull/status/actions read + fresh git.fetch.main + exact merge ancestry |
| AC-9 | 独立已批准安装后两端受管 manifest 字节/权限/source pin；installed hsdb typed read/access/onboarding；缺口保留 |

## 部署与回滚

应用部署无。本阶段不安装、不做 Secret/account/service 变更。
source/local 和 installed/live rollback 分离；详细窗口和恢复卡见 mapped verification。
