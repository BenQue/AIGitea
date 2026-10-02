---
issue: 316
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/316
change_type: security
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - security
  - authorization
  - platform-governance
  - shared-core
  - ci
depends_on:
  - 313
status: approved
branch: change/316-service-pat-rotation
created: 2026-10-02
updated: 2026-10-02
---

# #316 实施与验收计划（已批准）

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 只应用 03/06 的轮换、权限、恢复治理合同，形成可审核本地 commit，停止本 turn | - | done |
| T02 | fresh turn：固定版本 helper 对 exact PAT/UID 安全撤销，隔离 DB 验证，不安装现场 | T01 | done |
| T02A | 仅应用方案 A 的 Mac canonical store/内部管道治理修订，文档检查与本地 commit 后停止 | T02 | done |
| T03 | fresh run：operator command 完整轮换/失败恢复/no-op，与 typed grant 路径接通，测试零授权零 mutation | T02A | done |
| T04 | shell/Python/Go 全量验证、文档/判级复核，准备唯一 manual PR 候选 | T03 | in_progress（local 已验证，required CI/PR 待确认） |
| T05 | 人工合并后独立授权 helper 安装/operator grant/真实轮换和第二次 no-op，形成 AC-2 现场证据 | T04 | pending |

T01 与 T02、T02A 与 T03 均不得在同一 turn 实施。用户于 2026-10-02 以“按建议继续”批准方案 A；下一 fresh run 重读治理合同后，T03 可沿用这次批准继续，不重复询问启动确认。T05 不是已获批准的执行任务；缺 live/Secret 授权不能运行。PR 提交与 human merge 各遵守现有闸门，真实验收缺口不因 merge 自动消失。

## Expected touch points

- T01：03-Issue-Spec-Plan与单闸门开发流程.md、06-运维手册与踩坑集.md、docs/changes/316-service-pat-rotation/。不改 AGENTS/CLAUDE/runtime。
- T02：新增 codex/tools/gitea-pat-helper/（Go 源码、go.mod/go.sum、临时 DB 测试、固定构建定义）；helper 只使用固定 v1.26.4 的 identity/token model。no generic SQL or admin endpoint。
- T02A：只修订 T01 的六份 Markdown；不改 helper、runtime、shell、CI、AGENTS 或 CLAUDE。
- T03：新增 codex/tools/rotate-gitea-service-account.sh 与 codex/runtime/aisoft_host_access/credential_rotation.py；host-access broker contract.py/broker.py/runner.py/cli.py、codex/config/host-access-broker.json；codex/install-host-access-broker.sh；相应 operator grant/typed tests、shell black-box 套件。现有 bootstrap/rollback marker 协议保持。
- T03 custody/transport：Mac operator 交易只写 manifest 固定 canonical store，同一文件系统 journal/旧凭据隔离/候选/原子发布；固定 VM 的 CLI/helper 以现有 git service user 经内部 stdin/pipe 传 Secret，禁止进入 Agent/tool 返回、日志或 VM 普通临时目录。不新增通用 VM 代理，不自动同步或清理既有 VM 副本；markers 缺失拒绝。
- T04：codex/tests/smoke.sh、.gitea/workflows/ci.yml 的 fixed helper build/test；相关 Python suites 与四份映射文档。只加新路径必要验证，不削弱已有 contexts/硬门。
- T05：仅确定性版本化工具、精确 operator grant/Secret store 与回执。具体授权必须绑定 exact 新源码/制品、目标、Mac canonical store、VM exact helper、操作和窗口；先验证 ownership evidence，缺失拒绝而不补建。本计划不预授权 VM 副本同步/清理或其它消费端恢复。

## 数据库迁移

无 schema/业务数据迁移。helper 的 live 唯一 DB mutation 是在已证明的 exact non-admin 服务账号下删除 exact PAT；这是凭据撤销，不得延伸为任意表操作。

## 测试与验收映射

| AC | Ticket | Verification command or review |
|---|---|---|
| AC-1 | T03/T04 | bash codex/tests/test-rotate-gitea-service-account.sh；完整 smoke 纳入该套件；记录先红后绿 |
| AC-2 | T05 | 独立授权的 exact typed rotate 一次与第二次 no-op；Mac typed host.access.audit project=newemaint；旧 PAT 拒绝、新 scopes 精确相等，只保存脱敏回执；VM 消费端另记边界 |
| AC-3 | T01/T02A/T04 | PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli check-change-documents --repo <本票worktree>；bash codex/tools/apply-classification-labels.sh --repo <本票worktree> --verify 316；03/06 diff review |
| AC-4 | T02/T04 | 固定 toolchain 的 go test ./...（helper 目录、临时 DB）；只读验 version/model pin + zero wrong-target deletion + secret error redaction |
| AC-5 | T03/T04 | shell transaction/crash/lock/filesystem suite：每个失败边界前后 canonical、journal、mutation counts 与目标隔离读回；固定 Mac 同一文件系统、VM 副本无自动 mutation |
| AC-6 | T03/T04 | 对应 test_host_access/test_credential_rotation 的 typed parameter/grant/identity/store/helper 负向矩阵；env/path/URL override 拒绝；broker shell operation count 与 CLI schema 验证 |
| AC-7 | T04 | bash -n 修改的 shell；ShellCheck 若可用；bash codex/tests/smoke.sh；对应 Python suites；fixed helper build/check；唯一 PR 最终 head 的 required CI |

T02 helper 与临时 DB 测试已实现并运行，证据见 verification。T03 新 shell/Python 套件已实施并本地运行，证据见 verification；T04 的新 shell smoke 接入、CI/Linux 制品及进程级验证仍为计划/NOT RUN，不把表当执行回执。

## 安装、现场与回滚

现有 #313 两台 broker 重装已 PASS，不能复用为未来 #316 helper/operator transport installed PASS。#316 source 合并后如需现场安装，先独立明确安装和 live grant 授权，再验证全包 pinned 字节/权限/provenance。轮换使用同一请求验证两次，隔离失败/恢复在测试环境完成；实际 live 故意故障须另行授权，不擅自损坏 service PAT。

源码 revert + 版本化 installer 的 previous 文件恢复只能撤销代码安装，不能恢复 PAT。撤旧前可恢复经证实仍有效且符合当前 policy 的原凭据；撤旧后仅用受保护候选恢复。无可恢复候选或授权/归属不确定时保持 canonical 隔离并升级负责人。


## 合同决策已解除与 fresh run 边界

T02 本地实现/测试/审查已完成，exact head 为 0ffe6bda169d70bd89f48fa527635aa079a23bff。旧 no-Mac Secret 限制与现有 Mac credential resolver 的冲突已由用户明确批准方案 A 解除。T02A 独立治理步骤完成后停止，下一 fresh run 重读更新合同才实施 T03。仅固定 Mac canonical store 可接收候选；既有 VM 副本及其消费端仍需各自授权与证据。安装、grant 与 live 不获预授权。
