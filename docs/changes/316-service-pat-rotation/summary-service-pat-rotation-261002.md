---
issue: 316
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/316
change_type: security
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 新增服务账号显式 PAT 轮换、受控撤销后台和 operator-only typed 路径，涉及安全、共享核心与 CI 制品治理
risk_flags:
  - security
  - authorization
  - platform-governance
  - shared-core
  - ci
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
documents:
  summary: summary-service-pat-rotation-261002.md
  spec: spec-service-pat-rotation-261002.md
  plan: plan-service-pat-rotation-261002.md
  verification: verification-service-pat-rotation-261002.md
depends_on:
  - 313
status: pr-open
branch: change/316-service-pat-rotation
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/332
created: 2026-10-02
updated: 2026-10-03
---

## 问题/需求总结

现有 bootstrap 仅创建 PAT；已有凭据返回 no-op，凭据缺失而 marker 存在仅要求 rotate explicitly。#316 要求显式、可恢复、可测试且不泄露 Secret 的轮换路径。#313 合并与两台安装前置已真实解除；真实轮换尚未授权。

## 影响范围

轮换操作、Gitea 1.26.4 本地 exact-token 撤销 helper、operator-only broker transport、installer、CI 与 shell/数据库隔离测试。生产配置、Gitea 账号/权限和分支保护不在源码实现范围。治理合同与 runtime 必须分开 turn。

## 初步方案与建议

采用先隔离旧 canonical 凭据、生成并验证受保护候选、精确撤销旧 PAT、提交 provenance、最后原子发布新凭据的状态机。新 helper 使用固定 Gitea v1.26.4 上游 token model，拒绝任意 SQL 和任意账号；通过独立 operator grant 的 typed broker 路径执行。完整合同与 ticket graph 见映射 spec/plan。T01 治理应用与 T02 helper 本地实现/审查均已完成。用户于 2026-10-02 以“按建议继续”批准方案 A：仅允许更新 manifest 固定 Mac canonical store，VM CLI/helper 只通过内部受控管道传 Secret。T02A 只修订六份 Markdown、检查与本地提交后停止；下一 fresh run 重读合同即可沿用本次批准进入 T03，无需再次启动确认。PR/后续安装/grant/live Secret 授权仍独立。

## 风险

- 旧 PAT 撤销不可恢复；撤销后写入失败必须保留受保护候选供恢复，不能假称回滚到旧 PAT。
- Gitea v1.26.4 upstream 未声明 DELETE /api/v1/token，现有 rollback mock 不能证明真实支持。新增本地撤销 helper 的安全/制品决策已随本合同获用户确认；真实安装与 live 授权仍独立。
- Go helper 必须固定上游版本、依赖与制品摘要并用隔离数据库验收；source/local/CI/installed/live 分开记录。
- 轮换期间 canonical 凭据隔离，目标身份暂时不可用；仅对应精确目标，不能扩大为全平台停用。
- 这是单 Mac store 发布；既有 VM 副本不自动同步/清理，旧 PAT 撤销后不能继续使用。消费这些副本的 runtime 须各自授权处理；Mac audit PASS 不能证明所有消费端通过。

## AI 判级

```yaml
change_type: security
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 新增服务账号显式 PAT 轮换、受控撤销后台和 operator-only typed 路径，涉及安全、共享核心与 CI 制品治理
risk_flags:
  - security
  - authorization
  - platform-governance
  - shared-core
  - ci
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- codex/tools/bootstrap-gitea-service-account.sh:344-363 只有创建与 no-op；307-309 缺失 credential 时要求显式轮换。
- codex/tools/rollback-gitea-routine-pilot.sh:285-309 假定 self-revoke /api/v1/token；该路径未被本会话现场验证。
- 已安装 gitea --version 为 1.26.4；admin user --help 没有 PAT revoke 命令。
- PR #315 exact merge 480d1d262c3e915f546049ede3f34ad7d3362f50 在 fresh origin/main 5c2cd726c9aeaee9d17541d8feb049e33881bbac。
- 2026-10-02 两台重装后，22 个安装文件各自对 pinned source SHA 字节/权限/root 归属一致；两台 scope 集合均含 read:user 与 write:repository。

### 当前决策与未完成验收

- 方案 A 已批准，T03 凭据消费位置冲突已解除，无新增产品依赖。T02A 与 T03 已分 turn；T03 fresh run 已实现交易、typed grant 与受控 transport，完成本地隔离验证和审查修复。T04 已接入 smoke/CI 并完成 local Linux/arm64 制品、model/race、实际 helper 进程级 synthetic DB/canary 与双轴验证；fresh-main 默认 locale 组合 smoke 的 #308 installer-mapping-stale 阻塞已在 T04B 修复，34 drift fixture、1056 runtime 与平台 static 检查 PASS；共享 mapper/fixture 的精确范围补充于 2026-10-03 获用户“确认继续”批准，见 [批准记录](evidence/t04-installed-drift-extension-proposal.md)。T04A 已独立应用治理并停止，T04B fresh run 已同步映射、generated metadata、独立 public provenance 与负向测试；仅 SOURCE/local 证据；2026-10-03 本会话已完成受控整合，详见下方最新状态。required CI 尚未运行，最终 PR 提交确认与 T05 独立现场授权/验收仍待，不能写成整票完成。

T04B source/local commit：875fd3043c2e6959e1c509fe276a9e60870692cf。当时 actual branch merge-tree 确认两份新增源码 add/add 冲突；该历史阻塞现已由下方 Controller 整合解除，旧提交保存在恢复 bundle 中。


### PR 前受控整合候选（2026-10-03，已获提交确认）

用户“继续下一步”后，本票所属会话按 03 的受控整合流程，将未推送历史保全到 Git bundle 并变基到 fresh main d647963bcfd6508c8c07baea8d3ef0e4e6a0e35d。两个 add/add 用经核对的 main 原文件加已批准最小 delta 解决；41 份本票文件字节不变，03/06/smoke 保留上游更新，没有改动其它 Issue。实际整合 source head=094c21fda5ff7625973181a2f2c512a1e1a25b83，main ancestry、无冲突 preview 与完整 C.UTF-8 smoke PASS（34 drift、197 release、1091 runtime、static）；详见 [整合回执](evidence/t04-controller-integration-validation.json)。

当时 handoff 为 AWAITING_PR_CONFIRMATION，Issue #316 / branch change/316-service-pat-rotation / policy manual；[PR 正文候选](evidence/t04-final-pr-body.md) 只有一条 Closes #316。本轮用户继续仅授权受控本地整合，没有最终 PR 提交确认，未 push/创建 PR/改标签/安装/操作 grant 或 PAT。required CI、human merge 与 T05 AC-2 仍待，整票未完成。


### 最新状态：唯一 PR #332 已创建，等待 required CI

用户于 2026-10-03 以“确认提交”批准 Issue #316 / change/316-service-pat-rotation / manual。首次推送 4658baa168838027559284bf211422e7fe5bcd21 与核验候选一致，唯一 [PR #332](http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/332) 创建后 summary-only 回填提交 b6a01697024c729f7c47fcc4525fcd14dc3c083d 已推送并核对 pushed_head/PR head；[发布回执](evidence/pr-publication-receipt.json) 保存两次 exact 推送。源码未变化；required CI 当前 pending，不能写成 PASS。PR open/未合并；人工合并、安装/grant/live AC-2 保持独立。
