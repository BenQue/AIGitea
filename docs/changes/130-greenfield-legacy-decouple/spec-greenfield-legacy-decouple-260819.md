---
issue: 130
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/130
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - external-contract
  - shared-core
  - deployment
  - compatibility
  - reliability
  - platform-governance
depends_on: []
status: approved
branch: change/130-greenfield-legacy-decouple
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/131
created: 2026-08-19
updated: 2026-08-19
---

# Spec：greenfield Gitea 与 legacy health 完全解耦

## 目标与原则

公司 Pilot 的新 Gitea 是独立的 binary + systemd greenfield installation；既有 Docker Gitea 既不是安装输入，
也不是健康、升级、迁移或切流对象。新版 portable operator 必须把二者的关系收敛为单向的
non-interference：新实例使用固定且独立的端口、路径、用户、unit 和自动化 namespace，所有公司侧
greenfield 阶段都不得调用 legacy Docker、HTTP/API、config、log、repository 或 credential。

本 Change 只交付 AISoftPlatform source、strict contracts、portable operator bytes 的构建能力和本地
deterministic tests。公司 Stage20、安装、appserver-prod inventory、Stage30–110 与新候选包生成均不在本次授权内。

## 合同版本与兼容策略

greenfield 语义是外部合同变更，采用新的严格版本，避免 1.1.1 receipt 被静默重解释：

| 对象 | 新合同 | 规则 |
|---|---|---|
| operator | `1.2.0` | 1.1.x Stage00/10 evidence 不满足新版前置 |
| inventory | `company-delivery-inventory/v3` | `scm.legacy` 字段删除；greenfield collector 不接受 legacy port |
| probe profile | `greenfield-isolated-install-v1` | 只含 candidate 与 automation |
| transition | `company-delivery-gitea-transition/v2` | greenfield decision 不含 legacy baseline/backup/equality prerequisite |
| target | Gitea `127.0.0.1:8888`；PostgreSQL `127.0.0.1:55432` | 调用方不可覆写 |

v1/v2 历史 schema 与 receipt 只作历史证据，不能通过 1.2.0 active greenfield verifier。若未来恢复
controlled-upgrade，必须使用独立命令/contract/approval，不得重新把 legacy 字段塞回 greenfield v3/v2。

## Stage10 inventory v3

`collect-inventory --role scm-ci --mode preflight|post-install --output <new-json>` 不再接受
`--legacy-gitea-http-port`。SCM inventory 的 `scm` 对象固定只有：

- `probe_profile: greenfield-isolated-install-v1`
- `candidate.ports`：8888 与 55432
- `candidate.resources`：Gitea binary/config/data/log 与 PostgreSQL data
- `candidate.services`：`aisoft-gitea.service` 与 `postgresql@18-aisoft-gitea.service`
- `candidate.health`：preflight 固定 `NOT RUN`；post-install 只读取固定 candidate `127.0.0.1:8888`
- `automation`：runner、sync timer、production gate、DNS/TLS、reverse proxy、repository import 等固定状态

collector 的 runner call graph 不得出现 `docker ps` 或其它 Docker container discovery；HTTP getter 不得用于
legacy；inventory 不包含 legacy presence、container ID、publish port、health、version、reason 或 baseline。

preflight PASS 继续要求 candidate ports free、resources absent/expected-empty、Gitea unit missing、PostgreSQL
unit 为 fixed safe pair、automation 全部 disabled/NOT RUN。post-install PASS 继续要求 candidate ports occupied、
resources occupied、两个 candidate units enabled/active，并要求新 Gitea 的固定本机 health/version readback；该 readback
只针对 `127.0.0.1:8888`，不得复用 legacy HTTP helper。

## Transition v2 与 non-interference

greenfield transition v2 只允许 decision `greenfield-isolated-install` 或 `BLOCKED`。PASS receipt 绑定：

- exact operator/source/release/handoff/package manifest；
- SCM inventory v3 与 appserver inventory v3 checksum；
- fixed candidate target 与 public-name fingerprint；
- candidate backup/rollback/install provenance prerequisites；
- Stage00/10/20 状态与 Stage30–110 `NOT RUN`；
- automation 全部 disabled。

transition v2 删除 `legacy_baseline_sha256`、`legacy_backup_required` 与
`legacy-pre-post-equality`。non-interference 的证明来源只能是：固定独立 namespace；所有 legacy probes/commands
为 zero-call；变更脚本没有 legacy Docker/container/path/port 输入；candidate collision 与 unsafe state fail closed。

Stage50 的 greenfield prerequisite 改为 `candidate-post-install-health`，验证新 Gitea/PostgreSQL identity、unit、port、
storage 与 health，不验证 legacy pre/post equality。历史 `verify-legacy-health` 不属于 v2 flow。

## Acceptance criteria

- [ ] **AC-1 Zero legacy probes**：greenfield preflight/post-install 不接受 legacy port，不调用 Docker container
  discovery 或 legacy HTTP/API，并且 inventory v3 不含任何 legacy 字段。
- [ ] **AC-2 Candidate isolation**：8888/55432、固定 paths、candidate units 与 automation 的 preflight/post-install
  strict PASS/BLOCKED 规则保持 fail closed。
- [ ] **AC-3 Strict version boundary**：operator 1.2.0 只接受 inventory v3 与 transition v2 active flow；1.1.1
  inventory v2/transition v1/evidence 不能充当新版前置。
- [ ] **AC-4 Transition decoupling**：greenfield transition v2 删除 legacy health/version/baseline/backup/equality，
  Stage50 prerequisite 为 candidate-only post-install health。
- [ ] **AC-5 Controlled-upgrade isolation**：controlled-upgrade 不在 active greenfield decision enum；未来若实现必须
  使用独立 contract/approval，不能改变 v3 inventory。
- [ ] **AC-6 No-echo and security**：collector/validator 继续拒绝 unknown、unsafe 与 sensitive output，不保存 raw
  hostname、IP、config、log、HTTP body/header、credential path 或 Secret。
- [ ] **AC-7 Portable consistency**：VERSION、runtime constants、schemas、templates、compatibility、README/runbook、
  handoff 与 deterministic bundle tests 全部绑定 1.2.0/v3/v2。
- [ ] **AC-8 Regression evidence**：focused spy/call-count、strict validator、schema、full company-delivery、smoke、
  shell syntax、diff/review 与 deterministic dual-build tests 通过。
- [ ] **AC-9 Governed delivery**：唯一 readable tuple 与最终 PR；PR body 恰有一行 `Closes #130`，CI 通过后停在
  人工合并闸门。
- [ ] **AC-10 Company boundary**：公司 Stage20、安装、appserver-prod inventory、new Stage00 package 与所有
  legacy mutation 均 `NOT RUN`。

## 非目标

- 不判断或记录既有 Docker Gitea 是否健康、可访问或包含哪些仓库。
- 不升级、重启、备份、迁移、phase out 或切换既有 Gitea。
- 不执行公司内网命令，不生成或传输 portable archive。
- 不安装 Gitea、PostgreSQL、Runner、proxy、DNS/TLS 或 automation。
- 不自动合并 protected `main`。

## 回滚与停止条件

source 回滚为最终 PR 的单一 revert。任何测试发现 greenfield 仍调用 legacy、candidate fail-closed 被放宽、旧
receipt 可被误接收、raw/sensitive output 落盘，或实现需要公司事实/Secret 时立即停止并升级给人；不得以兼容
1.1.1 为理由恢复 legacy 硬门槛。
