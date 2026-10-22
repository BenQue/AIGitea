---
issue: 413
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/413
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 改写使用发布包内 architecture 校验器对 FROM 基础镜像 pin 的接受规则并发新版本，同时改平台漂移检查的主机语义，属于共享核心、供应链安全语义、发布制品与平台治理工具变更
risk_flags:
  - security
  - shared-core
  - artifact
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-dockerfile-arg-drift-host-261021.md
  spec: spec-dockerfile-arg-drift-host-261021.md
  plan: plan-dockerfile-arg-drift-host-261021.md
  verification: verification-dockerfile-arg-drift-host-261021.md
route:
  process: complex-production
  tier: frontier
  effort: max
  skills: to-spec, to-tickets, executing-plans, verification-before-completion
  method: spec-plan
  verify: full+reverse-proof
  review: cross-provider+security
  confirm: 2
confidence: high
override_reason: ''
depends_on: []
status: pr-open
branch: change/413-dockerfile-arg-drift-host
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/415
created: 2026-10-21
updated: 2026-10-21
---

## 问题/需求总结

第二轮终审 §5 第 4 项的两处修复。T01：architecture 校验器对 `FROM ${NAME}` 一律报
`DOCKERFILE_FROM_VARIABLE_UNSUPPORTED`，NewEMaint 的 `ARG NODE_BASE_IMAGE=<tag@digest>` 加逐 stage
`RUN test` 守卫的写法读不出来。T02：`check-installed-drift.py --host vm` 在 macOS 上读本机根，产出假 GAP。

## 影响范围

- `codex/runtime/aisoft_architecture/dockerfile.py` 与其测试、`architecture/README.md` 的 Dockerfile 合同段；
  该模块是使用发布包 `tool-provenance` 成员，同 PR 发 1.11.0。
- `codex/tools/check-installed-drift.py` 与其夹具测试、`06` 漂移核对节一句话。

## 初步方案与建议

T01 采用「默认值展开加守卫」：只接受第一个 FROM 之前声明、带字面量默认值的全局 ARG，FROM 镜像 token
必须恰好是 `${NAME}` 或 `$NAME`，且该 stage 里有 `RUN` 指令含 `test "${NAME}" = "<默认值>"`，使构建期
`--build-arg` 覆盖时构建失败。展开后照原规则核验 tag、digest 与声明集合。T02 在 macOS、真实根、installed
模式下拒绝 `--host vm`，退出码 2，`error.reason` 为 `host-mismatch` 并给出 OrbStack 转发命令。

## 风险

`architecture/README.md` 现行合同明文写着「即使全局 ARG 有默认值也拒绝，build-time override 能改变默认值」。
不带守卫地展开默认值会重新打开这条已关闭的洞（NewEMaint CI 确实以 `--node-base-image` 覆盖）。守卫方案保留
fail-closed：覆盖成别的镜像时构建在该 stage 失败，不产出制品。回滚为 revert 本 PR 并发下一版本。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 改写使用发布包内 architecture 校验器对 FROM 基础镜像 pin 的接受规则并发新版本，同时改平台漂移检查的主机语义，属于共享核心、供应链安全语义、发布制品与平台治理工具变更
risk_flags:
  - security
  - shared-core
  - artifact
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

- `architecture/README.md`「镜像 token 中有 `$` 一律拒绝，即使全局 ARG 有默认值」是现行合同，T01 改它，contract_effect 为 change。
- `usage/bundle.json` 把 `codex/runtime/aisoft_architecture/dockerfile.py` 列为 `tool-provenance` 成员，须发版。
- 先例：#406 改漂移检查语义判 complex（platform-governance），#409 改 architecture CLI 判 complex。
- 反向证据（修复前红）只能在改动前观测，不能由 required CI 重放，故声明 `verification`。

### 缺失的 acceptance criteria 或决策

- 无。负责人 2026-10-21 确认合同并选定「默认值展开加守卫」。
