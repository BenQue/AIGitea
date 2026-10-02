---
issue: 288
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/288
change_type: bugfix
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 容器源码文件新增强制核验入口改变共享架构校验合同并迁移声明输入
risk_flags:
  - shared-core
  - schema-change
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
documents:
  summary: summary-dockerfile-digest-261002.md
  spec: spec-dockerfile-digest-261002.md
  plan: plan-dockerfile-digest-261002.md
  verification: verification-dockerfile-digest-261002.md
depends_on: []
status: approved
branch: change/288-dockerfile-digest
pr_url:
created: 2026-10-02
updated: 2026-10-02
---

## 问题/需求总结

现有 architecture validate/lock 完全不读取 Dockerfile。基线探针修改 digest、退回 tag 或删除文件后仍 valid true 且 lock hash 相同。#288 选择 validator 共用入口核验源码 FROM。

## 影响范围

仅 AISoftPlatform architecture declaration schema、README、runtime、相关 tests 与 fixtures/reference；complex/manual，不修改应用、catalog/profile pin、release reader、Agent 或 CI/部署脚本。

## 初步方案与建议

映射 spec 固定 dockerfiles 路径数组、repo root、全部外部 FROM 的 digest 集合双向检查及保守变量/语法边界；独立 T01 治理合同 commit 后停止，fresh run 再做 T02/T03。

## 风险

- 已有容器声明缺 Dockerfile 输入将 fail closed，需要应用自身 Change 迁移，不能用旧兼容跳过。
- 静态核验仅证明声明源码输入；不能证明实际 builder 参数或制品 provenance。
- 与 #287 文件邻近，独立 worktree/PR；只由本 owner 自行整合 fresh main。

## AI 判级

```yaml
change_type: bugfix
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 容器源码文件新增强制核验入口改变共享架构校验合同并迁移声明输入
risk_flags:
  - shared-core
  - schema-change
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- 2026-10-02 broker read #288 open、needs-analysis、无 approved 合同，唯一评论为旧调度延后说明；本轮明确派单重新准备。
- broker onboarding PASS；main 禁 direct/force push，required CI / verify (pull_request)，routine disabled。
- fresh origin/main 5c2cd726c9aeaee9d17541d8feb049e33881bbac；本 worktree 已 claim 到 session 01a0fc7b-f327-7a93-a48c-a254937cb08d。
- 共用 build_lock 与 CLI _build 不消费 Dockerfile；4 场景基线假绿已记入 verification。
- 现有 architecture 57 tests PASS，未覆盖真实 FROM 核验；未发现冗余实现。
- .out-of-scope 与 CONTEXT.md 未发现本 Change 相关既有拒绝或词汇合同；ADR-0001/0004/0006 已读取。

### 缺失的 acceptance criteria 或决策

- 无；如后续发现缺失则回到 awaiting-triage。

## 合同与实施边界

- Policy: manual；用户于 2026-10-02 明确回复“确认”，批准本映射 spec/plan 启动。PR 提交尚未授权。
- 完整合同见 [spec](spec-dockerfile-digest-261002.md)，ticket graph 见 [plan](plan-dockerfile-digest-261002.md)，基线结果见 [verification](verification-dockerfile-digest-261002.md)。
- Matt triage 已验证 bug，推荐 ready-for-agent；当前 broker 没有 triage 双维度 projector，live 投影为 GAP，不绕行直接 API，不在 #288 修改 broker。
- T02 runtime 已实现并完成本地回归，T03 smoke 固定证据边界待处理；PR CI、installed/live/现场验收为 NOT RUN。无硬依赖；#287 仅关联与提交顺序协调。

## 启动授权与治理步骤

授权记录见 [receipt](evidence/contract-start-authorization.json)，冻结批准时 spec/plan SHA256。
T01 只应用 schema 与 README 合同；运行时文件核验仍为 NOT RUN。治理独立 commit 后停止，fresh run 重读本合同继续 T02/T03，无需重复启动确认。

## 最小范围补充授权

用户于 2026-10-02 再次回复“确认”，仅批准两处 shell 测试的显式 root 参数与 synthetic 模板迁移；receipt 与完整 patch 在 evidence。T04 独立应用后停止，原合同批准持续有效，runtime/最终 PR/安装部署仍未执行。

## 当前实现进度

T02 已完成：容器所有声明文件的 FROM digest 双向检查，root/路径/语法 fail closed，
三 CLI 入口、库调用与现有 checker 共用硬门。非容器四合同 canonical bytes 与 baseline 完全一致。
平台 smoke 真实 FAIL：release evidence checker 仍冻结旧 reference lock bytes。
未修改该治理文件；T03/最终 PR 待补充授权与 #287 fresh main 组合验证。
