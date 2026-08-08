---
issue: 37
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/37
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - schema-change
  - security
  - external-contract
  - shared-core
  - ci-change
  - artifact
  - deployment
  - compatibility
  - rollback
  - platform-governance
depends_on: []
status: pr-open
branch: change/37
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/40
created: 2026-08-08
updated: 2026-08-08
---

# Implementation plan

## 任务分解

1. 冻结 `origin/main@69251fd4d07665385eb6d9142038848c2b9392d7`、Issue #37、#27
   合同和 NewEmaint 两份真实 Docker 29 artifact 失败；只记录非敏感 identity、archive structure、
   checksum 和 diagnostic，不复制 artifact 或 Secret 到仓库。
2. 从真实 containerd/classic archive 提取最小、脱敏、确定性 fixtures，先写 positive/negative tests
   固化 Config digest、OCI descriptor graph、full-name/tag-only annotation 和 exact allowlist 语义。
3. 重构 archive validator：将 Docker manifest Config validation、OCI graph validation 与 reference
   normalization 分离；要求每个 service 唯一映射，并保持 traversal/link/unknown/duplicate/unreferenced
   member全部 fail closed。
4. 评审 current schema/model 是否足够。优先不新增 manifest 字段；若测试证明无法无歧义表达，再以
   versioned migration扩展 schema，并同步 inventory/install/runtime/fixtures/docs。
5. 扩展 fixed fake Docker tests，证明所有 pre-load negative case Docker mutation count=0，且
   post-load/pre-start failure 不运行 migration/up；保持 bounded/redacted diagnostic。
6. 更新 real Engine harness，使 producer archive validation 与 consumer deployment capability 分开
   记录，并支持 containerd/classic exact expected store。Harness 默认 `NOT RUN`，不创建/restart
   VM/service、不切 store、不 prune。
7. 在不需要 daemon mutation的前提下，对 retained NewEmaint containerd/classic artifact 运行新
   read-only preflight/parser；记录 exact artifact SHA 与结果，不把它写成 consumer E2E。
8. 只有获得后续精确授权，才运行 disposable containerd/classic consumer E2E；否则
   `03-verification.md` 对 load/Compose/health/cleanup 保持 `NOT RUN / BLOCKED`，compatibility
   matrix 不升级 classic。
9. 更新 Docker release README、compatibility说明和 Issue #37 verification，明确平台 parser PASS
   与 NewEmaint build、DockerLab deploy、database migration、health、browser acceptance、rollback
   的独立状态。
10. 运行 focused Python tests、installer repeatability、`bash -n`、ShellCheck、
    `bash codex/tests/smoke.sh` 和 `git diff --check`。按失败证据修复，不放宽 contract 绕过测试。
11. 提交并推送 `change/37`，创建只含本 Change 的 PR 并以 `Closes #37` 关联；CI 若未配置则写
    `NOT CONFIGURED / NOT RUN`，停止在人工合并闸门，不自动 merge 或 deploy。

## 涉及文件

- `docs/changes/37/{00-summary,01-spec,02-plan,03-verification}.md`
- `docker-release/README.md`
- `docker-release/compatibility/image-stores-v1.json`（只有 evidence/state 语义需要时修改）
- `codex/runtime/aisoft_release/contract.py`
- `codex/runtime/tests/test_release_contract.py`
- `codex/runtime/tests/test_release_transport.py`
- `codex/runtime/tests/release_test_support.py`
- `codex/tests/fixtures/docker-release/**`
- `codex/tests/integration/test-docker-image-store-e2e.sh`
- `codex/tests/test-docker-release-install.sh`
- `codex/tests/smoke.sh`

实际修改以最小 diff 为准；不因清单存在就机械修改 schema、matrix 或 installer。

## 数据库迁移

无平台或应用数据库 migration。不得连接、读取或修改真实 PostgreSQL；backup、restore、seed 和
schema/data mutation 全部 `NOT RUN`。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | Contract/model documentation review + real archive shape fixtures |
| AC-2 | Focused archive graph positive/negative unit tests for containerd/classic |
| AC-3 | Full-name/tag-only annotation normalization and extra-name/tag rejection tests |
| AC-4 | traversal/link/member/blob/config/content/checksum tamper tests with zero Docker mutation |
| AC-5 | schema/model diff review; legacy Registry positive and legacy offline reject tests |
| AC-6 | `python3 -m unittest` focused runtime suites + stable diagnostic assertions |
| AC-7 | Separately authorized real harness run; otherwise `NOT RUN / BLOCKED` |
| AC-8 | Compatibility matrix/evidence review; no classic promotion without exact E2E |
| AC-9 | installer twice, `bash -n`, ShellCheck, full smoke, `git diff --check`, verification status review |
| AC-10 | Cross-repository handoff review after platform merge; NewEmaint adoption remains later Gate |

## 部署与回滚

本 Change 不部署平台或应用。代码回滚使用 revert PR；artifact 不原地编辑。任何真实 Docker E2E
mutation 需后续单独批准，并仅限指定 disposable daemon 上 fixture 自有 container/image/network；
不得 restart VM/service、切换 store、prune 或触碰 DockerLab。NewEmaint target profile、Secret、
database、health、browser acceptance 和 rollback 均不在本 PR 内。
