---
issue: 340
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/340
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - external-contract
  - security
  - shared-core
  - platform-governance
depends_on: []
status: approved
branch: change/340-appserver-preflight-read
created: 2026-10-06
updated: 2026-10-06
---

# #340 实施与验证计划

实际本人已确认四份合同。本轮完成 T01 治理应用、文档验证与本地提交后 STOP；
T02–T05 保持 pending，first frontier=T02，必须后续 fresh run 重新读取后继续。
T01 的独立治理 STOP 是 AGENTS 强制边界；其后的 fresh run 不需要重复同范围启动确认。

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 仅 06 与本 Issue 合同落地、docs 验证、本地治理 commit 后 STOP | - | completed |
| T02 | fresh run：strict target/CLI/typed broker/runner 与 no-autostart transport gate 正反切片 | T01 | pending |
| T03 | 固定 identity/OS/resources/runtime/metadata/sockets/units collector 与安全路径、限额 fixture | T02 | pending |
| T04 | AppServer-only Docker 投影、PG 无授权显式 BLOCKED、Secret/零写/竞态/overflow 回归 | T03 | pending |
| T05 | 完整本地验证、source helper fingerprint/未来安装清单、证据分层与最终唯一 manual PR 确认卡 | T04 | pending |

每个 Ticket commit subject 包含 #340 与 Txx；唯一 owner/branch。
不因未来 operator、PG 或 Docker 权限不足建立 helper 层或机械子 Issue。
T02 若找不到能证明零自启的固定 execution primitive，允许以明确 BLOCKED 测试安全拒绝，
但不能把 target execution 端到端可用或 AC2 running 完整验收写成 PASS；
完整 source readiness/最终 PR 卡必须呈现该限制，必要替代设计另作具体裁决。

## Expected touch points

- T01：只 06-运维手册与踩坑集.md、本 Issue 映射文档；本地 commit 后 STOP。
  对照 approved spec/确认原文检查 scope；本轮已记录实际本人确认，local approved 与 live projection 分开。
- T02：仅 spec allowlist 中 manifest、contract.py/cli.py/broker.py/runner.py、
  新 application_preflight.py、test_application_preflight.py/test_host_access.py 与
  test-host-access-broker.sh 新合同断言。strict kwargs 保持旧操作兼容。
  输入拒绝必须在 helper/target/credential access 前；验证 stopped/race/unknown 三类。
- T03：新 application-target-preflight.py 与上述专用测试；每一个 probe 都先有 fixture、
  safe metadata 和 bounded output。未知数据源逐项 BLOCKED/GAP，不扩大路径 allowlist。
- T04：只 collector/module 与专用测试；默认无 PG连接、无权限授予、无 Docker CLI 配置，
  fixed readonly投影、假 Secret sentinel 和 forbidden-command/file-access spy。
- T05：只本 Issue 文档和 evidence；记录 candidate exact SHA、ownership/diff/验证，
  check-change-documents 与分类 projected 读回；若 live classification 未获合同范围授权
  或 operation 不可读，保留 blocker，不能编造 projected。
  不改 CI workflow/installer/skills/controller，不做现场运行。

## 数据库迁移

无。本操作不创建角色/库、不连接未经批准的数据库，不运行迁移或写 SQL。

## 测试与验收映射

下列为各层预定命令；T01 已运行项见 verification，其余不表示已经运行或通过。
全部从本人 worktree 执行。

| Acceptance criterion | Verification command or review |
|---|---|
| AC1 | PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests -p test_application_preflight.py -v；目标/参数增删/跨项目/root/shell/path/URL/credentialpath/port-range与调用次数断言 |
| AC1/AC3 旧行为 | PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests -p test_host_access.py -v；bash codex/tests/test-host-access-broker.sh |
| AC2 | 专用 fixture：stopped/missing VM、running→stopped竞态、no-autostart primitive 未证明、helper不存在/版本错误；zero lifecycle、zero target execution on reject；running固定probe正向 |
| AC3 | 专用fixture：symlink/owner/mode/路径替换、npm无config/cache、Secret/Env/argv sentinel、socket/container枚举max/max+1、bytes上限、单项/全局timeout；全路径/调用spy；旧gitea-ci与项目ACL回归 |
| AC4 source准备 | bash codex/tests/test-install-host-access-broker.sh，限临时 fake install root；验证现有installer复制新增module/manifest，不代表正式安装。生成helper SHA256/精确文件安装清单 |
| AC4 现场 | 单独安装卡后：绑定 exact merged SHA、Mac/gitea-ci broker必要文件、AppServer one-shot helper、mode/owner/bytes/version、真实snapshot restore与重复no-op；当前 NOT RUN |
| AC5 | 获批 installed/live后 fresh localwms task：installed broker --project localwms --operation application.target.preflight.read --target localwms-local-test；实际target/operator/helper/limits/每项值读回。当前 NOT RUN |
| AC6 | source sanitized fixture回执与live evidence分开；#333消费路径/回执，完整保留对象before/after若无法取得为NOT RUN；不发消息或修改消费者worktree |
| 全量local | LC_ALL=C bash codex/tests/smoke.sh；其既有 unittest discovery 包含专用新测试；不得删断言/降级required context |
| shell改动 | bash -n codex/tests/test-host-access-broker.sh；ShellCheck 若可用：shellcheck codex/tests/test-host-access-broker.sh；不可用写 NOT RUN |
| docs/范围 | PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli resolve-required-documents 340 --repo /private/tmp/issue-340-appserver-preflight-read；同CLI check-change-documents；git diff --check；exactbranch/claim/diff allowlist |
| CI | 唯一最终 PR 提交确认后读 final exact head/base + CI / verify (pull_request)；当前 NOT RUN |

本轮只执行合同文档解析/静态一致性与归属检查，不提前跑/报 feature 测试或 full smoke。
执行后将真实命令、时间、结果、受测 SHA 与未执行层写回 verification，
普通范围内失败自主修复；合同冲突、安全新决定、同因三次或外部现场缺条件 STOP。

## 部署与回滚

本轮没有部署或真实安装。T05 只准备源制品与后续具体卡，不执行卡。
scope内源码回滚通过本owner追加revert commit，保留错误和claim；不动他人对象。

正式安装/最小operator与权限/live分别由同一Issue后续具体卡确认，
无需为暂未授权而新建机械Issue。应用、DB、服务/代理和VM/OS部署是消费者独立合同。
source/local/CI、正式installed-byte/readback与fresh live独立验收；
合入source不能把AC4–AC6抹除为PASS或当作LocalWMS #333已解除阻塞。
