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

# Verification

## 实时治理与 source baseline

- AISoftPlatform remote protected `main`：
  `69251fd4d07665385eb6d9142038848c2b9392d7`。
- `change/37` 从该 exact SHA 创建于独立 worktree；canonical checkout 保持
  `change/33`，用户的 untracked `.DS_Store` 未修改。
- `e59359f2e2811d78a252ec95cbb6e573b5501863..69251fd4...` 在
  `docker-release/**` 与 `codex/runtime/aisoft_release/**` 无 byte drift；变化仅位于其它
  governance tests。因此 NewEmaint 当前 pinned contract 与实现 baseline 可直接比较。
- Gitea Issue #37 为 open，当前 labels 为 `pr-open`、`complexity/complex`、`type/platform`；
  创建前没有相关 open Issue/PR。
- `main` direct push=false、merge whitelist=true、required approvals=0、
  `enable_status_check=false`；exact main commit statuses total=0，Actions runs=0。Remote CI
  结论为 **NOT CONFIGURED / NOT RUN**。
- OrbStack sandbox/host paired probe 的既有实时结论为 `SANDBOX_PATH_BLOCKED`；本 Change 的
  Gitea 与 retained-artifact 查询均走 host path。未重启 OrbStack、VM 或 service。
- DockerLab host-path read-back：Ubuntu 24.04.4 LTS、amd64、Docker 29.7.1、Compose 5.1.4、
  containerd 2.2.6；0 containers、0 images、0 volumes、0 build cache，3000/3030 无 listener，
  `127.0.0.1:3000` connection refused。

PR #40 已创建：`change/37 -> main`。初始 implementation head
`b17654a93066964633fb0562ee02dba527062eb9` 实时为 open、mergeable=true、merged=false，
commit statuses total=0，matching Actions runs=0。本文档 handoff 回填会产生新的 PR head；remote CI
仍只能按最终 exact head 读回，不能把本地 tests 写成 remote CI PASS。Issue lifecycle 已从
`approved` 收敛为 `pr-open`，type/complexity labels 保持不变。

## 失败事实与实现结果

NewEmaint protected `main@ee4f6a1205a5df1603568e455e158c460b675a89` 的两份 retained
Docker 29.7.1 artifact 在旧 validator 上分别稳定失败：

| Producer store | Artifact SHA256 | 旧 diagnostic |
|---|---|---|
| containerd | `7022ac2e012b446bc6fc8e92fa4b90e6162514cbb2b2ae3592ee9a2afb65764c` | Docker Config digest 不等于声明的 top-level OCI index `image_id` |
| classic | `334833830d29e8798cee37ca555d37d6b05cde786f28cc307fc7647c78cf346b` | tag-only `org.opencontainers.image.ref.name` 被当作完整 name 拒绝 |

新 validator 不放宽为任意 digest/tag/member：

- containerd：验证 exact top index digest、唯一 `linux/amd64` runnable manifest、Config/layers、
  attestation type/reference 和所有 content-addressed blobs。
- classic：验证 config digest identity、full-name/tag-only annotation pairing、`LayerSources`、
  OCI manifest graph，以及 legacy layer metadata 的 content digest、parent graph、leaf/config
  数量和 image layer chain lengths。
- 两条路径仍拒绝额外 repository/tag/descriptor、unknown member、悬空/重复 blob、错误
  Config/layer、content/size/schemaVersion、attestation target 和 legacy metadata graph。

在 disposable builder 上以 change/37 runtime 临时副本重新执行 read-only archive preflight：

| Artifact | Result | Docker mutation |
|---|---|---|
| retained containerd artifact `7022ac...` | **PASS** | 0；未调用 Docker daemon |
| retained classic artifact `334833...` | **PASS** | 0；未调用 Docker daemon |

Artifact 未复制、改写或重新打包；checksum 与失败前一致。

## 测试结果

| Verification | Result |
|---|---|
| `PYTHONPATH=codex/runtime python3 -m unittest codex.runtime.tests.test_release_transport` | **PASS**；17 tests，含 Docker 29 containerd/classic positive 与多类 pre-load tamper |
| `PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests -p 'test_*.py'` | **PASS**；216 tests |
| `bash codex/tests/test-docker-release-install.sh` | **PASS**；两次安装 bytes/idempotence |
| `bash codex/tests/smoke.sh` | **PASS**；216 Python tests 与全部 shell regression |
| `bash -n ...` + `shellcheck ...`（Docker release CLI/install/E2E/smoke） | **PASS** |
| `python3 -m py_compile ...` | **PASS** |
| `git diff --check` | **PASS** |

上述是 platform-local unit/fake/installer/smoke 与 retained-artifact **read-only parser**
evidence，不是 Docker consumer `load`、Compose、target deploy 或应用验收。

## Acceptance criteria 映射

| AC | Status | Evidence |
|---|---|---|
| AC-1 | **PASS** | README/runtime 明确 daemon inspect identity、OCI descriptor 和 config digest |
| AC-2 | **PASS** | containerd index + classic manifest graph positive/negative fixtures；两份真实 archive read-only PASS |
| AC-3 | **PASS** | full-name/tag-only pair positive；其它 tag/name/reference negative |
| AC-4 | **PASS** | member/link/path/blob/config/layer/content/size graph fail-closed；mutation=0 |
| AC-5 | **PASS** | 不需新增 schema field/version；legacy Registry/offline 既有 tests 保持通过 |
| AC-6 | **PASS** | synthetic real-shape fixtures、stable generic diagnostics、216 tests |
| AC-7 | **BLOCKED / NOT RUN** | 未获 restart/service/store-switch 或 consumer mutation 的单独授权 |
| AC-8 | **PASS** | classic compatibility row 未提升；parser compatibility 与 deploy support 分离 |
| AC-9 | **PASS** | focused/full/install/smoke/bash-n/ShellCheck/compile/diff checks |
| AC-10 | **NOT RUN** | 等平台 PR 人工合并后才由 NewEmaint 独立采用 exact contract SHA |

## 分层验收状态

| Layer | Status | 说明 |
|---|---|---|
| Host readiness | **PASS** | DockerLab exact versions 与 0-object/0-listener baseline 已 host-path 只读复核 |
| Build | **PASS（retained producer evidence）** | exact NewEmaint main 已生成两份 artifact；explicit cache prep/SBOM 修复仍待业务变更 |
| Archive contract/preflight | **PASS** | 两份原 checksum artifact 以 change/37 read-only validator 通过 |
| Docker consumer load/Compose | **BLOCKED / NOT RUN** | 未获本 Change 的 daemon/service mutation 授权 |
| DockerLab deploy | **NOT RUN** | 无 target profile/Secret，NewEmaint 未部署 |
| Database migration/backup/restore | **NOT RUN** | 无授权，未连接或修改 PostgreSQL |
| Application health | **NOT RUN** | 无容器部署 |
| Browser acceptance | **NOT RUN** | `DockerLab.orb.local:3000` 尚无应用服务 |
| Rollback | **NOT RUN** | 无部署状态可回滚 |
| PR CI | **NOT CONFIGURED / NOT RUN** | branch protection 无 required status context，Actions runs=0 |
| PR merge | **NOT RUN** | 必须人工执行 |

## 回滚

平台代码回滚只通过 revert PR。既有 artifact 不原地编辑；平台合同发布后由受控 producer 重新生成
NewEmaint exact-main artifact。Runtime/container/database rollback 未运行，也不由本 Change 授权。
