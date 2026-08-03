---
issue: 22
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/22
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - security
  - shared-core
  - ci-change
  - artifact
  - deployment
  - migration
  - rollback
  - platform-governance
depends_on:
  - 23
status: approved
branch: change/22
pr_url:
created: 2026-08-02
updated: 2026-08-02
---

# Implementation plan

## 任务分解

1. 读取 Issue #21/#23 的批准合同，冻结跨 Issue ownership 和 #23 profile/catalog/lock
   identity；实现期间允许并行，但 final review 前必须等待 #23 交付并整合最新 `main`。
2. 建立 `docker-release/` contract v1 schema、target profile schema、无 Secret templates 和
   架构说明，锁定 release bytes、环境配置与两种 transport 的边界。
3. 在 `codex/runtime/aisoft_release/` 实现 strict manifest/profile parser、path/checksum、
   architecture lock 和 host-role preflight，确保不调用 Docker 即可拒绝不安全输入。
4. 实现捕获并脱敏 subprocess 输出的 Docker adapter、`RegistryTransport` 和
   `OfflineBundleTransport`；offline 必须在 mutation 前完成 archive checksum/load/inspect。
5. 实现 Compose render/config 安全验证、deployment lock、原子 state、healthy no-op、
   migration、`up --wait`、exact-release health、失败回切、status 和 explicit rollback。
6. 提供稳定 wrapper 与幂等 install；安装只复制版本化 runtime/schema/template，不创建
   profile/Secret、Docker login、systemd unit，也不 enable/start/deploy。
7. 添加 contract/transport/runner/installer tests，使用 fake Docker 覆盖 tamper、role
   mismatch、catalog mismatch、重复部署、migration/health failure、rollback 与脱敏。
8. 更新 README、02/07/12 和 onboarding 文档；运行定向 tests、`bash -n`、ShellCheck、
   `git diff --check` 与 `bash codex/tests/smoke.sh`。
9. #23 人工合并且达到 `completed/deployed` 后，从最新 `origin/main` 整合一次并运行
   architecture-release integration suite；若 contract 漂移，更新 #22 实现而非 fork catalog。
10. 填写 `03-verification.md`，提交并推送 `change/22`，创建 `Closes #22` 的最终 PR，
    停在人工合并闸门。真实 AppServer/production 均保持 `NOT RUN`。
11. 平台 PR 合并后，在 NewEmaint 独立 Change 中消费 contract v1；该后续工作不在本 PR
    修改应用或环境。

## 涉及文件

- `docs/changes/22/{00-summary,01-spec,02-plan,03-verification}.md`
- `docker-release/README.md`
- `docker-release/schema/release-manifest-v1.schema.json`
- `docker-release/schema/target-profile-v1.schema.json`
- `docker-release/templates/target-profile.example.json`
- `docker-release/bin/aisoft-docker-release`
- `docker-release/install.sh`
- `codex/runtime/aisoft_release/*.py`
- `codex/runtime/tests/test_release_*.py`
- `codex/tests/test-docker-release-install.sh`
- `codex/tests/fixtures/docker-release/*`
- `codex/tests/smoke.sh`
- `README.md`
- `02-CI与自动部署流水线.md`
- `07-内网与生产平移路线.md`
- `12-Linux-GitHub-Gitea-双服务器自动部署方案.md`
- #23 合并后的 `architecture/` contract 只作为 dependency 输入，不在本分支复制。

## 数据库迁移

平台仓库无数据库迁移。Runtime 只约定并调用 manifest 中的版本化 migration service；真实
应用 migration、backup、expand/contract 和 PostgreSQL restore 由消费项目和环境 Gate
管理。Fake tests 不连接真实数据库。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | `rg -n 'Docker-first|PM2 legacy|offline' README.md 02-* 07-* 12-Linux-*` 与历史状态 review |
| AC-2 | `python3 -m unittest codex.runtime.tests.test_release_contract -v` |
| AC-3 | invalid/tamper/path/catalog fixtures 断言 Docker adapter 调用数为 0 |
| AC-4 | CLI parser/installer tests 与 Secret marker/argv/state scan |
| AC-5 | transport tests 断言 digest pull、checksum/load/inspect 和 mutation 顺序 |
| AC-6 | Compose fixture tests 覆盖 build/root/privileged/socket/port/security/resource/logging/network/label |
| AC-7 | host-role integration fixtures：`scm-ci` deploy denied、AppServer allowed |
| AC-8 | runner tests：lock/no-op/migration/up-wait/exact health/state/failure rollback |
| AC-9 | 定向 unittest、installer smoke、`bash -n`、ShellCheck、全量 smoke |
| AC-10 | templates/onboarding review；断言仓库无 NewEmaint 产品文件 |
| AC-11 | `03-verification.md` 的环境状态与 PASS/FAIL/BLOCKED/NOT RUN review |
| AC-12 | Gitea dependency readback；#23 合并后 architecture-release integration suite |

## 部署与回滚

本 PR 不执行应用部署。Install smoke 在临时目录连续运行两次并证明不会创建 profile/Secret
或调用 Docker。Deliberate failure 至少覆盖 bundle tamper、host-role mismatch 和 health
failure：前两者 mutation 前停止，后者回切 previous release。真实测试部署须等待 #23、
平台 PR 与应用消费 PR 人工合并并另获授权；production promotion 保持 `NOT RUN`。
