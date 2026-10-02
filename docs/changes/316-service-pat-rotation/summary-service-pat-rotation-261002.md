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
status: approved
branch: change/316-service-pat-rotation
pr_url:
created: 2026-10-02
updated: 2026-10-02
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

- 方案 A 已批准，T03 凭据消费位置冲突已解除，无新增产品依赖。T02A 与 T03 已分 turn；T03 fresh run 已实现交易、typed grant 与受控 transport，完成本地隔离验证和审查修复。T04 已接入 smoke/CI 并完成 local Linux/arm64 制品、model/race、实际 helper 进程级 synthetic DB/canary 与双轴验证；required CI 尚未运行，最终 PR 提交确认与 T05 独立现场授权/验收仍待，不能写成整票完成。
