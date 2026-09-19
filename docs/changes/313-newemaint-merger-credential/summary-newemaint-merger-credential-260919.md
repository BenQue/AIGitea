---
issue: 313
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/313
change_type: security
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: routine merge agent 的 token scope 合同与 broker 身份闸门互相排斥，修复要动 governance manifest、governance runtime 校验、bootstrap 签发闸门与共享测试，属于安全与凭据边界的治理变更，按强制规则判为 complex。
risk_flags:
  - security
  - authorization
  - platform-governance
  - shared-core
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-newemaint-merger-credential-260919.md
  spec: spec-newemaint-merger-credential-260919.md
  plan: plan-newemaint-merger-credential-260919.md
  verification: verification-newemaint-merger-credential-260919.md
confidence: high
override_reason: ''
depends_on:
  - 312
status: analyzed
branch: change/313-newemaint-merger-credential
pr_url:
created: 2026-09-19
updated: 2026-09-19
---

## 问题/需求总结

`312`（PR `314`，merge `3ff6972`）合并并两台重装之后，broker
`host.access.audit --project newemaint` 不再报 `PROTECTION_MISMATCH`，而是稳定返回
`BLOCKED_EXTERNAL / HTTP_403`。audit 是 routine merge 硬门的前置，所以 NewEMaint 的 routine
自动合并路径当前不可用（manifest 里 `routine_auto_merge_enabled` 为 true）。manual PR 与用
`newemaint-agent` 凭据的 typed 写操作不受影响。

Issue 正文假设根因是凭据过期、被撤销或账号被禁，处置是由负责人重新签发 token。**本次取证否定了
这个假设**：根因是平台自己的合同缺陷，重新签发同一份 token 会一字不差地复现同一个 403。

## 影响范围

- `codex/config/gitea-governance.json` 的 `routine_merge_agent_policy.token_scopes`
- `codex/runtime/aisoft_gitea_governance/contract.py` 对该 scope 集合的逐字校验
- `codex/tools/bootstrap-gitea-service-account.sh` 对 routine PAT 的 scope 读回闸门
- `codex/runtime/tests/test_host_access.py` 里 `/api/v1/user` 的假 transport（缺陷对测试不可见的原因）
- `06-运维手册与踩坑集.md`：merger 403 的诊断路径与「前一个闸门遮蔽后一个缺陷」这一形态
- 运行面：只有 NewEMaint 一个仓库 `routine_auto_merge_enabled` 为 true，因此只有它触发这条代码路径

## 初步方案与建议

见 spec。核心是：scope 合同补 `read:user`，三处逐字钉子同步，测试改成真的模拟 Gitea 的 scope 闸门，
然后由负责人重新签发 token 并两台重装，会话只做只读复验。

## 风险

- 这是安全边界变更：给 routine merger 增加一个只读 scope。必须论证它不放大合并能力。
- 三处钉子只改一处会让整份合同拒绝加载，或让 audit 从 403 变成 `TOKEN_SCOPE_MISMATCH`。
- 凭据签发与写入是负责人动作，会话不生成、不粘贴、不入库任何 token 值。
- source 合并不等于 installed 生效，AC-1 只能在两台重装且 token 重发之后复验。

## AI 判级

```yaml
change_type: security
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: routine merge agent 的 token scope 合同与 broker 身份闸门互相排斥，修复要动 governance manifest、governance runtime 校验、bootstrap 签发闸门与共享测试，属于安全与凭据边界的治理变更，按强制规则判为 complex。
risk_flags:
  - security
  - authorization
  - platform-governance
  - shared-core
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- `change_type` 为 `security`，本身就在 `FORCED_COMPLEX_TYPES` 里。
- `risk_flags` 命中 `security`、`authorization`、`platform-governance`、`shared-core` 四条强制风险。
- 目标文件包含 governance manifest 与共享 governance runtime，属于治理文件，须由 complex 的 spec 明确授权。
- `aisoft-platform` 仓库没有声明 `change_control`，按默认 production 路径，四份语义文档全部必需。

### 缺失的 acceptance criteria 或决策

Issue 的 AC-1 至 AC-3 可测且完整，但 Issue 的「范围」第 2 条把处置写成「重新签发 token」，
与取证结论不符。需要人在确认点 1 裁决是否把范围扩到修合同（见 spec 的两个选项）。
