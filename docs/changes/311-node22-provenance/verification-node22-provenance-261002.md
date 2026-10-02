---
issue: 311
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/311
change_type: maintenance
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - shared-core
  - ci-integration
  - rollback
depends_on: []
status: verified
branch: change/311-node22-provenance
created: 2026-10-02
updated: 2026-10-02
---

## 基线、授权与范围

日期2026-10-02（Asia/Shanghai）；session=01a0fc7c-2504-7261-8e84-95a3ebcb8a0f。
初始fresh origin/main与worktree head=5c2cd726c9aeaee9d17541d8feb049e33881bbac。
唯一branch=change/311-node22-provenance；worktree=/private/tmp/issue-311-node22-provenance，已claim本session。
授权原文与scope见authorization-node22-provenance-261002.md。Gitea/remote均经对应manifest broker；host例外经本聊天用户明确批准，只读/写marker不推导应用部署授权。

## 四仓当前消费方盘点

所有workflow逐文件（包括无命中者）及nonSecret committed实现/配置扫描文件完整列表见fresh-consumer-inventory-261002.json。

| 仓库 | fresh main SHA | workflow文件数 | nonSecret实现/配置扫描文件数 |
|---|---|---|---|
| aisoft-platform | 5c2cd726c9aeaee9d17541d8feb049e33881bbac | 1 | 332 |
| LocalWMS | 182ea7e04499f0b77162a5c95bfa3670417b04ee | 1 | 236 |
| NewEMaint | 4c30573341c668826b3af515e870eb5bf9b362b0 | 6 | 576 |
| SFMDigitalBoard | 1be980d238c37495a808170ee8ce4a5bf04fbaf3 | 3 | 277 |

- SFMDigitalBoard .gitea/workflows/ci.yml:31 活动PATH前置/opt/node22/bin；sfm-board/tests/platform/run.sh:73 真实断言workflow保持该pin。
- SFMDigitalBoard ci.yml:60、deploy.yml:11/49、run.sh:50 是注释，不算额外消费者；deploy workflow已取消该pin。
- LocalWMS ci.yml:25 使用node24.18.0；NewEMaint ci.yml:24/366、deploy-appserver.yml:20、publish-docker-release.yml:15 使用node24.18.0；无node22活动引用。
- 平台node22命中为合成测试夹具和Flutter脚本注释，平台workflow无直接node22引用。
- fresh refs均与初查相同。SFMDigitalBoard共享checkout dirty，只有refs刷新，未checkout/rebase/修改其文件。
- 仓库扫描排除docs/archive/vendor/lock/Secret文本，保留完整扫描名单与边界；不是全主机无未知消费方证明。

## 静态主机盘点

- benque批准探针：host-inventory-261002.jsonl，600条JSONL；584个普通systemd文件（路径alias可能重复）无node22引用。初次因末尾目录PermissionError退出，598条不完整回执保留在host-inventory-incomplete-261002.jsonl；只修异常处理后重试，不提权。
- node22是实际755目录，uid=999/gid=986（runner）；Node22.22.0/npm10.9.4/pnpm10.28.0；原marker不存在。npm/pnpm/corepack版本命令未执行，仅读固定package.json版本字段。
- Node binary实测SHA-256=8eeefcacdf48f58541a651016e604055d14a992e39df98636b76495bc7244395。目录mtime不冒充安装日期，binaryhash不冒充上游归档hash。
- root批准补读：host-root-detail-261002.jsonl；effective unit、两个drop-in、runner config与runner用户profile均有逐文件字段回执。unit静态PATH无node22；config无envs块；.profile的两条标准HOME/bin、HOME/.local/bin前置目录均不存在，无node22引用；.bashrc无引用、.bash_profile不存在。
- 151个unique systemd link metadata（含/run）：130个alias的目标都有真实ordinary-file扫描回执（本地逐目标交叉校验PASS）、19个/dev/null mask、2个缺失chrony目标；不存在未读取的active target被伪报scanned。130个目标在initial普通扫描或effective-file补读中逐项证实，不单信探针布尔值。
- 初始profile.d的4个symlink补读：profile-alias-metadata-261002.json + profile-alias-261002.jsonl。目标均root-owned/644的正常配置；初次额外.sh后缀假设拒绝正常OrbStack profile，依据真实metadata改用4个exacttarget绑定后读回。无node22引用。profile-late仅继承PATH并前置/追加3个固定OrbStack路径，unknown_parts=0；不执行profile或导出process环境。
- 进程exe快照只枚举可读link，没有node22执行文件；不读argv/environ，不据零计数推导无人消费。
- 动态profile执行/process Secret环境按批准合同排除；known_consumers仅陈述已证实消费者。

## Marker真实动作与回执

固定payload见marker-node22-provenance-261002.txt；cat实际读回见marker-live-readback-261002.txt，bytes一致。
SHA-256=bd3c6ccaf6929449631684667043dc614607170722d5fb658025b6d281d5db8c。
安装日期、安装者、来源、上游校验均unknown；recorded_at=2026-10-02；known_consumers=admin/SFMDigitalBoard:.gitea/workflows/ci.yml。

| 动作 | 结果 | 回执 |
|---|---|---|
| apply创建 | PASS / created | marker-apply-261002.json |
| 首次check内容/runner属主644/版本 | PASS / verified | marker-check-first-261002.json |
| 重复apply | PASS / already-current-no-op | marker-noop-261002.json |
| exact rollback | PASS / removed-only-matching-marker | marker-rollback-261002.json |
| rollback后marker不存在、node22仍存在 | PASS | marker-rollback-readback-261002.json |
| reapply重建 | PASS / created | marker-reapply-261002.json |
| 最终check | PASS / verified | marker-check-final-261002.json |
| cat内容与固定payload字节比对 | PASS | marker-live-readback-261002.txt |
| 非marker metadata/Nodehash/configmetadata前后对比 | PASS / completely equal | runtime-metadata-before-261002.json / runtime-metadata-after-261002.json |

3783条非marker元数据hash=1c81035bde190fabf8e2368d18130e157ffb8b458820751147348e83da81e59c，前后完全一致。
配置metadata（unit/drop-in/config/profile/node24marker）前后完全一致；未导出完整配置或Secret内容，不声称全目录内容hash逐文件均已验证。
runner broker写前观测：active/running，PID533，child_count0。写后runner-status-after-261002.json仍PID533、active/running，未重启服务。

## 平台、source/local、CI证据

| 检查 | 结果 | 边界 |
|---|---|---|
| host.access.audit | PASS | agent Write/manager Admin；main不可push/force，human admin merge；requiredCI=CI / verify (pull_request)，routine disabled |
| gitea.issue.read/comments.read #311 | PASS | 初查open/needs-analysis，comments=[]，无先前合同批准 |
| gitea.pulls.read --state open | PASS | 初查[]；唯一PR尚未创建 |
| 初始sandbox issue read | BLOCKED_EXTERNAL（已修正） | TRANSPORT_ERROR，同typed受控host重试成功，不是对象缺失 |
| 初始三仓fetch cwd检查 | BLOCKED_EXTERNAL（已修正） | TARGET_MISMATCH，同typed在各自canonicalcheckout重试PASS |
| ownership scan | PASS | exact #311属于本session；没有其他writer代rebase/commit |
| classification canonical YAML/summary一致性 | PASS | maintenance/complex，shared-core/ci-integration/rollback强制complex |
| 初始live label写入 | BLOCKED（历史） | 自动审核拒绝无启动授权的标签修改；未绕过，待明确启动确认后执行 |
| approved后official projector --apply 311 | PASS | installed project=aisoft-platform broker result=updated |
| official projector --verify 311 | PASS / projected | type/maintenance + complexity/complex真实readback |
| lifecycle持久化 | PASS / approved | before needs-analysis；after approved/complexity/complex/type/maintenance |
| check-change-documents | PASS | changes145/pass2/gap0；四角色映射正确，pr_url空、尚无PR |
| Python AST与命令literal/payloadbytes一致性 | PASS | source/local静态检查；host命令已按同一payload实执行 |
| full smoke | FAIL（既有基线回归） | sandbox 初次受 loopback 禁止阻塞；同完整命令受控 host 重跑 exit1，registry-preflight 停 registry 后预期1实际0；三个源文件与 fresh main 字节相同，独立 baseline 同失败，见 local-validation 回执 |
| code-review | PASS（两轴均0） | Standards：0硬违例/0smell；Spec：0findings；fixed base/candidate 及独立审查记录见 review 附件 |
| PR required CI | NOT RUN | 尚未获最终提交确认、未创建PR |
| 应用部署/重启/删除目录/工具链升级 | NOT RUN | 不在本合同动作；没有静默实施 |

官方projector为官方脚本及两份library的byte-identical临时副本（无siblingbroker），使其固定使用/usr/local/libexec/aisoft/host-access-broker；不修改源工具或安装文件、不接触凭据。

## Acceptance criteria结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | PASS（批准的静态边界内） | 四仓fresh完整文件列表、unit/config/profile与alias字段回执；动态Secret环境明确排除 |
| AC-2 | PASS | exact marker读回、owner644、no-op、精确回滚重建、binary/metadata不变 |
| AC-3 | PASS（source/local/live classification） | 01§4.2已同步实际；semanticcheck PASS；--verify projected；PR CI仍NOT RUN |
| AC-4 | PASS | 明确授权记录；无Secret读取/输出、无服务配置修改、无node24/Flutter/app仓变更 |

## 未完成项与交付边界

host marker验收已经完成，不等于应用部署或上游provenance可信。来源仍unknown。
两轴review已经完成，Standards/Spec各0 findings。完整smoke已运行但FAIL，不能进入最终PR候选或READY_FOR_REVIEW。fresh origin/main仍5c2cd726c9aeaee9d17541d8feb049e33881bbac；同基线三文件的独立复现与候选同失败。该既有回归由#319处理，owner当前等待最终PR确认；本Issue不修改其脚本、不设置LC_ALL绕过。待真实合入main后，本owner更新自己的worktree并重跑完整smoke，再准备唯一manual PR确认。当前没有push/PR/merge/归档。
总调度集成优先级10，不构造新产品依赖，depends_on仍[]。
