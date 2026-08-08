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

# Spec

## 目标与原因

让 `docker-release/v1` 对 Docker Engine 29 containerd/classic 两种实际 `docker image save`
archive 表达进行严格、可移植、fail-closed 的 identity 验证，同时不削弱 #27 建立的 exact
release/tag/image/Compose/architecture/mutation ordering。

NewEmaint 的两份真实 artifact 已证明当前逻辑把三个层次混为一谈：OCI top-level index/manifest
digest、image config digest、daemon inspect identity。Classic archive 还证明 OCI annotation 可能用
full name 与 tag-only 两种互补字段表达同一个 exact reference。合同必须解析 archive graph 和
reference semantics，而不是放宽为任意 digest 或 basename 匹配。

## Acceptance criteria

- [ ] **AC-1** 文档与 runtime model 明确定义 `reference` Registry digest identity、`image_id`
  daemon inspect identity、Docker archive Config digest、OCI descriptor digest 四者关系；不得要求
  containerd `image_id` 必然等于 Config digest，也不得允许 manifest 无法绑定到 exact config。
- [ ] **AC-2** Archive validator 对每个 manifest image 唯一解析 Docker `manifest.json` entry、
  Config blob、layers和可选 OCI descriptor graph。Classic 只在 `image_id == Config digest` 时接受；
  containerd 只在 `image_id` 等于 exact allowlisted top-level OCI descriptor digest，且该 graph
  最终指向 Docker entry 的 exact Config digest/layers 时接受。未知、重复、悬空或多义 graph拒绝。
- [ ] **AC-3** OCI annotations 只接受 exact transport reference 的规范化表达：
  `io.containerd.image.name` 可为完整 name，`org.opencontainers.image.ref.name` 可为同一完整 name
  或其 exact tag。两者同时存在时必须互相一致；digest name、其它 repository、其它 tag、空 tag、
  大小写/路径漂移、额外 descriptor 均在 load 前拒绝。
- [ ] **AC-4** 既有 Docker archive、纯 OCI layout 和 mixed layout 的允许成员集合由已验证 descriptor
  graph 派生；path traversal、symlink、hardlink、unknown member、duplicate member、unreferenced blob、
  Config/content digest mismatch 和 checksum mismatch 继续在任何 Docker mutation 前 fail closed。
- [ ] **AC-5** V2 manifest/inventory schema 保持 strict。若无需新增字段则必须证明 current fields 足以
  表达两种 store；若新增字段，必须有 contract version/compatibility migration、legacy Registry
  positive 与 legacy offline pre-load reject，禁止 silent default 或原地修改既有 bundle。
- [ ] **AC-6** Unit/fake fixtures 覆盖来自真实 Docker 29 containerd 与 classic archive 的最小脱敏
  shape，并覆盖 Config/index/annotation/tag/graph tamper。Pre-load negative cases 的 Docker mutation
  count 为 0；错误信息稳定且不输出 Secret、daemon raw details 或 archive payload。
- [ ] **AC-7** 获得精确环境授权后，以同一 fixed release fixture 在独立 producer/consumer daemon
  完成 containerd 与 classic E2E：save/checksum/transfer/preflight/load/exact inspect/Compose
  `--pull never --no-build`/health/container identity/offline pull rejection/exact cleanup；每行记录
  Engine、Compose、store、daemon IDs、release SHA、archive SHA 和结果。缺少授权保持 `NOT RUN / BLOCKED`。
- [ ] **AC-8** Compatibility matrix 将 producer archive compatibility 与 consumer deployment
  support 分开解释。修复 parser 不自动把 classic target 提升为 `supported`；只有 AC-7 同级真实
  consumer E2E PASS 才能改变 row，且 evidence 必须 versioned、不可变、可追溯。
- [ ] **AC-9** Installer repeatability、focused runtime tests、`bash -n`、ShellCheck、platform full
  smoke 和 `git diff --check` PASS。`03-verification.md` 分开记录 host readiness、artifact parser、
  real Docker build/transport、deploy、database migration、health、browser acceptance、rollback；
  未运行项不得写成 PASS。
- [ ] **AC-10** NewEmaint 只在平台 PR 人工合并并发布 exact contract SHA 后，通过独立业务变更采用。
  业务侧另行修复 explicit dependency-cache preparation、producer identity/SBOM，并重新生成 protected
  main exact artifact；本平台 PR 不复制 target-candidate lock、不部署或修改数据库。

## 接口、数据与兼容性影响

Top-level 与 offline sub-contract 继续优先保持 `docker-release/v1` 和
`docker-release-offline-bundle/v2`。`image_id` 的语义是 exact runtime reference 在目标 daemon
上的 inspect identity；archive Config digest 是独立的 archive graph 事实，可由
`manifest.json[].Config` 和 content-addressed blob 验证，不要求新增信任输入。

允许的 OCI reference normalization 只接受：

```text
full transport reference: aisoft.local/<owner>/<repo>/<service>:<40-char-sha>
exact tag:                <40-char-sha>
```

Tag-only annotation 只有在同一 descriptor 同时存在、且 full-name annotation正好等于 manifest 的
`transport_reference` 时才有意义；不能从 tag-only annotation 猜 repository。若 archive 没有 OCI
layout，则使用 Docker manifest `RepoTags` + Config identity 路径。

## 风险与回滚约束

- Validator 必须保持 pre-load 完成，任何 identity/reference/graph 不确定性都 fail closed。
- 不在现有 daemon 上切换 image store、修改 daemon config、restart Docker/VM 或 prune。真实 E2E
  只在用户逐项批准的 disposable target 执行，并只清理 fixture 自有对象。
- 平台变更回滚使用 revert PR；已发布 bundle 不原地编辑，只能由受控 producer 重新发布。
- Runtime rollback 不自动执行 PostgreSQL restore；database migration/backup/restore 始终是独立批准。

## 非目标

- 不修改 NewEmaint 应用代码、Dockerfile、Compose、architecture current lock 或 database schema。
- 不创建 DockerLab target profile/Secret/Docker login，不部署、不迁移数据库、不做浏览器验收。
- 不修改 Gitea 权限，不自动 merge PR，不启用/dispatch/rerun CI workflow。
- 不支持 multi-arch、Kubernetes/Swarm 或任意未 allowlist 的 OCI annotation/reference 形式。

## 未决问题

无会改变实现方向的未决问题。真实 daemon mutation 是否运行由后续精确授权决定；在此之前对应
AC 保持 `NOT RUN / BLOCKED`。
