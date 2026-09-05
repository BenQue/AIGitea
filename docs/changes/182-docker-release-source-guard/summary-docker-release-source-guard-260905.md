---
issue: 182
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/182
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 收窄 Issue 65 的 CI 证据闸门并给 docker-release installer 接入 fail-closed staleness 判断，同时触及 CI 闸门与安装期行为
risk_flags:
  - ci-change
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
documents:
  summary: summary-docker-release-source-guard-260905.md
  spec: spec-docker-release-source-guard-260905.md
  plan: plan-docker-release-source-guard-260905.md
confidence: high
override_reason: ''
depends_on: []
status: pr-open
branch: change/182-docker-release-source-guard
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/245
created: 2026-09-05
updated: 2026-09-05
---

## 问题/需求总结

`#171` 把 source provenance 输出与 staleness fail-closed 闸门抽成共用库
`codex/lib/install-source-guard.sh`，并接到五个 installer 上。第六个
`docker-release/install.sh` 被一条独立的证据闸门挡住，因此切出为本 Issue。

该闸门位于 `codex/tests/integration/test-docker-release-v2-lifecycle-e2e.sh`：它把
`docker-release/` 相对 Issue 65 delivery base `7ef7fa2` 的 `git diff --name-only`
逐字钉死为两个文件。给 `install.sh` 接上 guard 会让它成为第三个，`smoke.sh` 因此变红。

平台已于 2026-09-05 以 Issue 评论裁定采用路径 3：把该 pin 从「整个目录」收窄到
「发布语义面」，显式排除 `install.sh`，而不是把它加进 `expected_docker_release_diff`。

## 影响范围

- `codex/tests/integration/test-docker-release-v2-lifecycle-e2e.sh`：两处 diff 断言（preflight 前置与 lifecycle 后置）改为先剔除豁免路径再比较。
- `docker-release/install.sh`：在第一次 `install -d` 之前 source 共用库并调用一次 guard。
- `codex/tests/test-installer-source-guard.sh`：`INSTALLERS` 数组恢复 `docker-release/install`，删掉说明本缺口的注释。
- `06-运维手册与踩坑集.md` 踩坑 20：`docker-release/install` 从「暂无闸门」改为已覆盖。

不触及 docker-release 的发布语义、schema、compatibility 矩阵、transport 或 CLI。

## 初步方案与建议

在 harness 里引入一份显式的 `docker_release_evidence_exempt` 路径清单与一个过滤函数，
两处断言共用它。闸门保持 name-only 语法判断，只是判断的集合从「`docker-release/` 下全部
路径」收窄为「`docker-release/` 下的发布语义路径」。豁免清单在文件里写明为什么每一条
不参与发布语义，使得后续想再豁免一条的人必须给出同级别理由。

## 风险

- 收窄闸门意味着 `docker-release/install.sh` 此后不再受 Issue 65 证据钉死。缓解：它不进 release manifest、不被 transport 或 capability gate 读取，且 `codex/tests/test-docker-release-install.sh` 与 `codex/tests/test-installer-source-guard.sh` 两条测试独立覆盖它。
- 豁免清单可能被后来者当作通用白名单扩张。缓解：清单在 harness 里逐条注明排除理由，而不是一个裸数组。
- guard 在 checkout 落后 upstream 时 fail-closed，会让 `test-docker-release-install.sh` 在陈旧 worktree 上变红。这是既有的、其余五个 installer 已经承担的同一行为，不是本次新增的失败模式。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 收窄 Issue 65 的 CI 证据闸门并给 docker-release installer 接入 fail-closed staleness 判断，同时触及 CI 闸门与安装期行为
risk_flags:
  - ci-change
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
confidence: high
override_reason: ''
```

### 判级证据

- `change_type: platform` 属 `FORCED_COMPLEX_TYPES`，`codex/runtime/aisoft_loop/classification.py` 因此强制 complex。
- `ci-change` 与 `platform-governance` 同属 `FORCED_COMPLEX_RISKS`：本次改动直接修改一条 required CI 里的证据闸门判据。
- `contract_effect: change`：`install.sh` 获得新的拒装路径，闸门覆盖面被显式收窄，两者都不是恢复既有合同。
- `required_docs` 不含 `verification`：全部 AC 的证据都由 `bash codex/tests/smoke.sh`（required CI 内）与 diff review 复现，没有只能在真实环境一次性观测到的证据，符合 `03` §3 的判据表第一行。

### 缺失的 acceptance criteria 或决策

- 无。三选一的治理决定已由平台在 2026-09-05 的 Issue 评论中裁定为路径 3，实施边界一并给出。
