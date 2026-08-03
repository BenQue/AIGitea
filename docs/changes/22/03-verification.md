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
status: verified-local
branch: change/22
pr_url:
created: 2026-08-02
updated: 2026-08-03
---

# Verification

## 环境与版本

- Source baseline：`origin/main@b806317cc87a58049719fff103af2c9d7c14ed56`
- Integrated dependency baseline：`origin/main@7021224118a9d6b0bbb9e9cdd6ea5d4cbbb791bc`，
  即 PR #24 的人工 merge commit
- Planning baseline：`change/22@95a7a5672fce94d74a4a739a886718cadbd6534d`
- Pre-integration candidate head：
  `change/22@8cc8a0c103756dae5b343675ba95f236ad263a92`；runtime `1a4ba61`，tests
  `4631d16`，docs/verification `0407018`、`158d244`、`8cc8a0c`
- Dependency：2026-08-03 实时回读 PR #24 已由 head
  `dec1df1f5ad4ec425630a0cc84bb3084ce608fa7` 人工合并，Issue #23 为
  `closed + completed`；hard dependency terminal gate 已满足
- Runtime：Python `3.14.4`；ShellCheck `/opt/homebrew/bin/shellcheck`
- Docker/Compose：只使用 fake adapter；未安装或启动 Docker daemon，真实 Registry、offline
  media、AppServer 与 production 全部 `NOT RUN`

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| planning contract parse + AC map | PASS | `load_contract` 通过；12 条 AC 全部映射；dependency 为 #23 |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=codex/runtime python3 -B -m unittest discover -s codex/runtime/tests -p 'test_release_*.py' -v` | PASS | 35 项 release contract/architecture integration/Compose/transport/runner/CLI/safety tests 通过 |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=codex/runtime python3 -B -m unittest discover -s codex/runtime/tests -p 'test_architecture_*.py' -v` | PASS | 26 项 canonical catalog/schema/lock/CLI/governance tests 通过 |
| `bash -n`（architecture/docker-release CLI、installer、installer tests、smoke） | PASS | 七个 shell 入口语法通过 |
| `shellcheck`（architecture/docker-release CLI、installer、installer tests、smoke） | PASS | ShellCheck 可用且零 finding |
| architecture/docker-release installer repeatability | PASS | 两个临时 install root 均连续安装两次且 manifest 一致；未调用 Docker，未创建 target/Secret/systemd/state |
| JSON/schema/static doc checks | PASS | schemas/templates/fixtures 全部 `jq -e`；README、02/07/12/onboarding 统一 Docker-first + PM2 legacy 边界 |
| `git diff --check` | PASS | 当前实现与文档无 whitespace error |
| `PYTHONDONTWRITEBYTECODE=1 bash codex/tests/smoke.sh` | PASS | 166 项 Python tests、全部 shell mocks、双 installer 与 static smoke 通过 |
| #23 dependency + architecture-release integration | PASS | `origin/main@7021224` 已整合；由 canonical catalog/profile/project 重新生成 NewEmaint reference lock，byte-identical 后通过 #22 strict parser；未复制 catalog |
| Gitea PR CI | NOT RUN | PR 尚未创建 |
| Registry test AppServer | NOT RUN | 不在当前授权范围 |
| offline-bundle test AppServer | NOT RUN | 不在当前授权范围 |
| production promotion | NOT RUN | 不在当前授权范围 |

## Acceptance criteria 结果

| AC | Result | Evidence / boundary |
|---|---|---|
| AC-1 | PASS（local candidate） | README、02、07、12 与 onboarding 统一新 Linux Docker-first、独立 builder/AppServer、共享 Nginx/PostgreSQL 和 PM2 legacy；历史 as-built 保留 |
| AC-2 | PASS（local candidate） | strict release schemas/parser 固定 merge SHA、`linux/amd64`、Compose/architecture checksums、service digest/image ID、runtime services 与 migration identity；消费 #23 `schema_version: 1.0` canonical lock |
| AC-3 | PASS（local candidate） | invalid/mutable/duplicate/unknown/path/checksum/lock self-hash/delivery/profile/catalog/source-URL credential/destructive fixtures fail closed；undeclared `.env`/file 被拒绝；mutation count 为 0 |
| AC-4 | PASS（local candidate） | CLI 只有 `verify/deploy/status/rollback --profile --release-id`；profile mode/owner/hostname/role/paths 受验证；subprocess 无 shell 且失败输出不回显 |
| AC-5 | PASS（fake adapter） | Registry 只 pull `name@sha256`；offline 在 load 前验证 inventory/archive checksums 与 tar traversal，load 后 inspect RepoDigest/image ID/platform |
| AC-6 | PASS（fake normalized Compose） | build/mutable/root/privileged/host namespace/socket/bind/public port/literal env 等反例拒绝；health/read-only/cap/resource/log/network/labels 正例通过 |
| AC-7 | PASS（fake host-role） | `scm-ci` verify PASS；deploy 与 hostname mismatch 在任何 Docker 调用前拒绝；AppServer role deploy PASS |
| AC-8 | PASS（fake state machine） | process lock、same-SHA no-op、migration started/completed/failed、`up --wait` adapter、exact container identity、atomic state、health failure 回切、explicit rollback 均覆盖；DB restore 未调用 |
| AC-9 | PASS（local candidate） | 35 项 release tests + 26 项 architecture tests + 双 installer + bash -n + ShellCheck + 166 项 full smoke；fake Secret marker 未进入 state/output/events |
| AC-10 | PASS（template/docs） | 无 Secret target profile 与 NewEmaint onboarding 示例已提供；明确应用仓须独立 Change，未修改 NewEmaint/其它应用仓 |
| AC-11 | PASS（记录结构） | 本文件分离 local candidate、PR CI、Registry/offline AppServer、重复部署、故意失败和 production，未执行项保持 `NOT RUN` |
| AC-12 | PASS | #23 已 `closed + completed`；`origin/main@7021224` 已整合，canonical lock generation/validation 与 release parser integration suite 全绿且没有第二份 catalog |

## 重复部署/执行

- architecture 与 docker-release installer 第一次/第二次：PASS，安装文件 checksum manifest 完全一致；没有 Docker/Secret/profile/systemd/state 副作用
- fake Registry deploy 第一次/同 SHA 第二次：PASS；第二次 exact healthy no-op，不重复 pull、migration 或 `compose up`
- fake offline deploy：PASS；每次部署只 load archive 一次，不执行 registry pull
- 真实 test deploy：NOT RUN

## 故意失败与回滚

- Compose/manifest/architecture self-hash/delivery/profile/catalog/unknown field/source-URL credential、inventory/archive tamper、tar traversal、undeclared `.env`：PASS；均在 container mutation 前失败，其中 bundle tamper/path traversal 为零 Docker 调用。
- `scm-ci` target role 与 hostname mismatch：PASS；deploy 在零 Docker 调用时 denied。
- migration failure：PASS；state 记为 `failed`，后续自动重跑在 pull/load 前拒绝。
- health failure：PASS；fake previous container release 自动回切，current state 保持旧 SHA；已完成 migration identity 不被伪装成 DB rollback。
- explicit rollback：PASS；只接受 recorded `previous_release`，不运行 migration 或 PostgreSQL restore。
- PostgreSQL restore：NOT RUN；runtime 明确返回 `NOT_RUN_MANUAL_ONLY`，真实 restore 不在授权范围。

## 遗留风险与未完成项

- #23 profile/catalog/lock 已通过 PR #24 合并进 `origin/main@7021224`，Issue 已
  `closed + completed`。#22 tests 直接消费 canonical NewEmaint reference lock，并从 #23
  catalog/profile/project 重新生成后验证 byte identity；旧的临时 architecture lock fixture 已删除，
  没有复制第二份 catalog。未来 schema/revision 变更仍需新 Change 与 integration rerun。
- Fake Docker 证据不等于真实 Docker Engine/Compose 版本、Gitea Registry、TLS、offline media、
  AppServer、共享 PostgreSQL/Nginx、backup/restore 或 production。
- 未验证真实 `docker image load` 后 RepoDigest 保留、Registry authentication、offline media
  custody、Compose engine compatibility 和目标 hostname/profile ownership；这些属于后续环境 Gate。
- NewEmaint 消费与全部环境部署属于独立 Change/Gate。
