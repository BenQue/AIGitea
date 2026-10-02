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
| T03 | operator command 完整轮换/失败恢复/no-op，与 typed grant 路径接通，测试零授权零 mutation | T02 | awaiting-contract-decision |
| T04 | shell/Python/Go 全量验证、文档/判级复核，准备唯一 manual PR 候选 | T03 | pending |
| T05 | 人工合并后独立授权 helper 安装/operator grant/真实轮换和第二次 no-op，形成 AC-2 现场证据 | T04 | pending |

T01 与 T02 不得在同一 turn 实施。T05 不是已获批准的执行任务；缺 live/Secret 授权不能运行。PR 提交与 human merge 各遵守现有闸门，真实验收缺口不因 merge 自动消失。

## Expected touch points

- T01：03-Issue-Spec-Plan与单闸门开发流程.md、06-运维手册与踩坑集.md、docs/changes/316-service-pat-rotation/。不改 AGENTS/CLAUDE/runtime。
- T02：新增 codex/tools/gitea-pat-helper/（Go 源码、go.mod/go.sum、临时 DB 测试、固定构建定义）；helper 只使用固定 v1.26.4 的 identity/token model。no generic SQL or admin endpoint。
- T03：新增 codex/tools/rotate-gitea-service-account.sh 与 codex/runtime/aisoft_host_access/credential_rotation.py；host-access broker contract.py/broker.py/runner.py/cli.py、codex/config/host-access-broker.json；codex/install-host-access-broker.sh；相应 operator grant/typed tests、shell black-box 套件。现有 bootstrap/rollback marker 协议保持。
- T04：codex/tests/smoke.sh、.gitea/workflows/ci.yml 的 fixed helper build/test；相关 Python suites 与四份映射文档。只加新路径必要验证，不削弱已有 contexts/硬门。
- T05：仅确定性版本化工具、精确 operator grant/Secret store 与回执。具体授权必须绑定 exact 新源码/制品、目标、操作和窗口；本计划不预授权。

## 数据库迁移

无 schema/业务数据迁移。helper 的 live 唯一 DB mutation 是在已证明的 exact non-admin 服务账号下删除 exact PAT；这是凭据撤销，不得延伸为任意表操作。

## 测试与验收映射

| AC | Ticket | Verification command or review |
|---|---|---|
| AC-1 | T03/T04 | bash codex/tests/test-rotate-gitea-service-account.sh；完整 smoke 纳入该套件；记录先红后绿 |
| AC-2 | T05 | 独立授权的 exact typed rotate 一次与第二次 no-op；typed host.access.audit project=newemaint；旧 PAT 拒绝、新 scopes 精确相等，只保存脱敏回执 |
| AC-3 | T01/T04 | PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli check-change-documents --repo <本票worktree>；bash codex/tools/apply-classification-labels.sh --repo <本票worktree> --verify 316；03/06 diff review |
| AC-4 | T02/T04 | 固定 toolchain 的 go test ./...（helper 目录、临时 DB）；只读验 version/model pin + zero wrong-target deletion + secret error redaction |
| AC-5 | T03/T04 | shell transaction/crash/lock/filesystem suite：每个失败边界前后 canonical、journal、mutation counts 与目标隔离读回 |
| AC-6 | T03/T04 | 对应 test_host_access/test_credential_rotation 的 typed parameter/grant/identity 负向矩阵；broker shell operation count 与 CLI schema 验证 |
| AC-7 | T04 | bash -n 修改的 shell；ShellCheck 若可用；bash codex/tests/smoke.sh；对应 Python suites；fixed helper build/check；唯一 PR 最终 head 的 required CI |

T02 helper 与临时 DB 测试已实现并运行，证据见 verification。T03 新 shell/Python 套件和 T04 CI 接入仍为计划/NOT RUN，须落实再执行，不把表当执行回执。

## 安装、现场与回滚

现有 #313 两台 broker 重装已 PASS，不能复用为未来 #316 helper/operator transport installed PASS。#316 source 合并后如需现场安装，先独立明确安装和 live grant 授权，再验证全包 pinned 字节/权限/provenance。轮换使用同一请求验证两次，隔离失败/恢复在测试环境完成；实际 live 故意故障须另行授权，不擅自损坏 service PAT。

源码 revert + 版本化 installer 的 previous 文件恢复只能撤销代码安装，不能恢复 PAT。撤旧前可恢复经证实仍有效且符合当前 policy 的原凭据；撤旧后仅用受保护候选恢复。无可恢复候选或授权/归属不确定时保持 canonical 隔离并升级负责人。


## T03 Frontier 暂停原因

T02 当前本地实现/测试/审查已完成。新源码读回发现 spec:57 的 no-Mac Secret 边界与现有 Mac-only credential resolver 消费路径冲突，无法直接保证 AC-2。用户正在选择 A（仅允许 fixed Mac canonical store）或 B（扩展 VM-only custody/代理执行）；不以建议选项或经过时间作为批准。原 spec 安全边界保持，T03 等待合同决策；安装、grant 与 live 不获预授权。
