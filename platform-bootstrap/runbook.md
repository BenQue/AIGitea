# 公司平台 bootstrap 操作合同 v1

本版所有动作仍须遵守开发权威/公司部署权威分离。命令应在选定的已合并且已验证 source pin 上运行。
这里是平台工具协议；公司 exact 资产、路径、身份、窗口和现场执行步骤由 B1/B2 部署 Change 保存。
本版不负责实际 Gitea/Runner 安装；现场执行绑定不完整时必须 BLOCKED，不能以临时 shell 补齐。

## 00 构建与携带身份（开发侧）

人工从批准记录填写完整 40 位 source SHA、组件、rollback identity 和 approval reference。
首次安装的 uninstalled identity 是 canonical JSON（ASCII、排序、紧凑、末尾 LF）的
`{"state":"uninstalled","target_identity_sha256":"<approved asset digest>"}` SHA-256。
snapshot identity 是已验证恢复基线清单摘要；有数据库的采用必须有独立隔离 restore 证据。

下面路径由操作员替换为批准的绝对路径。模板不得原样用于公司 evidence。

```bash
umask 077
mkdir -m 700 /approved/output-a /approved/output-b
/approved/platform/platform-bootstrap/bin/aisoft-platform-bootstrap build-bundle \
  --repository-root /approved/platform \
  --approval /approved/source-approval.json --output-directory /approved/output-a
/approved/platform/platform-bootstrap/bin/aisoft-platform-bootstrap build-bundle \
  --repository-root /approved/platform \
  --approval /approved/source-approval.json --output-directory /approved/output-b
cmp /approved/output-a/platform-bootstrap.tar.gz /approved/output-b/platform-bootstrap.tar.gz
cmp /approved/output-a/handoff.json /approved/output-b/handoff.json
```

任一 failure 停止 handoff；禁止放宽 clean HEAD、组件或摘要检查。相同输入两次 byte-identical 只证明本地可重复构建。
真实现场前须选定 merged source/CI pin，把 handoff digest 通过独立审批通道送达公司，不以旁边 checksum 文件自证批准。

## 10 verify-handoff（执行包内代码之前）

先使用公司已信任的 hash 工具把收到的 handoff/归档摘要与独立批准记录逐字比对。
再使用已信任的 verifier 运行下面完整验证；它有 tar 大小限制、closed path/member/mode gate，且不解包。

```bash
TRUSTED_CLI=/approved/trusted/platform-bootstrap/bin/aisoft-platform-bootstrap
HANDOFF_SHA256=<independently-approved-64-char-handoff-sha256>
"$TRUSTED_CLI" verify-handoff \
  --handoff /approved/incoming/handoff.json \
  --archive /approved/incoming/platform-bootstrap.tar.gz \
  --expected-handoff-sha256 "$HANDOFF_SHA256"
```

收到的新 CLI 本身不作首次信任根。确认 archive 完整校验后，才可在新的空目录用审查过的解包流程展开固定成员；
不覆盖已安装文件。package 不是安装记录。故意修改 archive 一个字节必须 `CHECKSUM_MISMATCH`，未批准的 handoff
identity 即使 archive 自洽也必须被外部 pin 拒绝。所有错误只输出稳定 code，不回显 input、token 或原始日志。

## 20 盘点、采用与停止

由 B1 只读盘点采集并脱敏，填写 inventory；工具只验证声明，不自动连接服务器。target 记录确切资产和仓库
identity、独立现场审批引用、允许的 Gitea 版本与非空 required CI。未知字段/身份、不完整数据须退回盘点。
本版兼容候选固定为仓库既有 `1.26.4`；目标改变须新合同。target 必须填写全部 `action_inputs`：
具体字段见 target schema/模板；不要用 URL、用户名、credential 或任意 shell 代替 digest/批准引用。
repo-bootstrap 与 one-shot-inbound 的 refs/transport 摘要和 staging 必须相同，staging 格式是
`refs/heads/sync/platform-<本次40位source SHA>`；required-ci/canary 与 target 的 contexts 必须完全一致。

| 条件 | 决策 | 后续 |
|---|---|---|
| 明确不存在 Gitea/仓库、无活动 Runner/inbound，回退为绑定该资产的 uninstalled | first-install | B1/B2 批准独立候选 namespace 和 package-set pin 后才可安装 |
| 已有健康实例、版本匹配、仓库/source/保护/CI/scoped Runner/inbound 全部匹配、已验证恢复 | adopt | 读回/no-op，canary 仍需新证据 |
| 已有健康兼容实例，身份无冲突，所需配置有差异且已有恢复基线 | adopt-with-remediation | 审阅 exact 差异，每个变更获现场授权；不运行空白安装器 |
| 版本或已采用 source 与候选不同 | controlled-upgrade / BLOCKED | 单独升级合同；本版无升级执行 |
| 未知状态、AI、自动 inbound timer、越界 Runner、身份冲突、无 restore 证据 | BLOCKED | 返回固定原因，不自动修复或降级身份 |

```bash
"$TRUSTED_CLI" verify-inventory --input /approved/inventory.json
"$TRUSTED_CLI" adoption-plan \
  --handoff /approved/incoming/handoff.json \
  --archive /approved/incoming/platform-bootstrap.tar.gz \
  --expected-handoff-sha256 "$HANDOFF_SHA256" \
  --inventory /approved/inventory.json --target /approved/target.json \
  --output /approved/adoption-plan.json
```

plan 绑定 handoff、inventory、target 的 canonical 摘要。批准计划后任何输入变化都必须重审；apply/rollback
重新计算计划并检查 `--expected-plan-sha256`，不能编辑 plan 来绕过门禁。BLOCKED plan 无动作列表。

## 30 固定动作合同与 apply dry-run

按序执行的现场责任合同见 [actions.json](actions.json)。每项必须由 B1/B2 将 exact 参数绑定到受审版本化脚本，
保持 no-op 和最小权限；所有后继动作必须先有前驱现场 PASS。这个前驱门由现场执行器负责，不能从本工具的
DRY_RUN 推导。B1/B2 绑定至少包含：执行器 source/hash、merged/CI 证据、目标 identity、该动作参数摘要、
独立授权、禁用默认 timer、两轮隔离重跑及失败恢复。禁止任意 URL/shell/credential path 参数接口。

| 顺序/动作 | exact 输入和 no-op | 故意失败、负向权限与恢复 |
|---|---|---|
| gitea-adoption | 目标 identity、version、package-set digest；同实例版本只读采用 | 错误 checksum/namespace 停止，原实例不动；first-install 回 uninstalled |
| repo-bootstrap | 精确仓库、source/ref digest、bootstrap trust approval；相同 SHA no-op | 外仓/错误 source 拒绝，main 不动；保留 refs，不删采用仓库 |
| protected-main | main、空 direct/force allowlists、人类 merge 身份引用；相等 no-op | 逐一测试 agent/manager/provider/shared bot 不能越权；回退不得放宽保护 |
| required-ci | exact repo、非空 canonical context 集合；相等 no-op | 失败/缺失 check 阻断 merge，修复后 exact head 重验 |
| runner | scm-ci identity、binary/config digest、platform-only scope；相同不重启 | 失败 job 后恢复；无生产 Secret/跨项目权；仅撤回本次启用 |
| one-shot-inbound | allowlisted ref、source SHA、非 main staging；相同 no-op | 错误 SHA 在写前停止，direct/force main/自动 merge 拒绝；timer 保持关闭 |
| canary | 真实本地平台 Change、source、公司审批 PR/human merge SHA、required CI | CI 故意失败→修复→人合并→provenance；普通 protected PR revert |

```bash
PLAN_SHA256=<approved-canonical-plan-sha256>
"$TRUSTED_CLI" apply --dry-run --action repo-bootstrap \
  --handoff /approved/incoming/handoff.json \
  --archive /approved/incoming/platform-bootstrap.tar.gz \
  --expected-handoff-sha256 "$HANDOFF_SHA256" \
  --inventory /approved/inventory.json --target /approved/target.json \
  --expected-plan-sha256 "$PLAN_SHA256" \
  --output /approved/repo-bootstrap-request.json
```

每个新 output 必须不存在，工具不覆盖历史 evidence。运行结果只能是 DRY_RUN/NOT RUN。
不带 `--dry-run` 固定返回 `SITE_EXECUTOR_NOT_BOUND`；本版没有 live mutation 隐式 fallback。

## 40 readback 与平台 canary

现场执行器产生独立脱敏 observation，绑定原 request digest、target/repo/source、证据对象 digest 和实际层次。
所有 PASS 要有 identity/no-op/deliberate-failure/recovery；相关动作另需 negative-permission、required-ci，
canary 另需 human-merge/provenance 和 company_merge_sha。source_sha 与公司 merge SHA 分栏。
FAIL/BLOCKED/NOT RUN 保留原状态，不补虚假 PASS。单纯传入布尔值或 checks 不是事实采集：工具只验证结构与关联。

```bash
REQUEST_SHA256=<approved-request-sha256>
"$TRUSTED_CLI" readback \
  --request /approved/repo-bootstrap-request.json \
  --expected-request-sha256 "$REQUEST_SHA256" \
  --observation /approved/repo-bootstrap-observation.json
```

真实闭环：开发侧 Issue/受控 Change → exact source 结果入站 → 公司审批 PR → required CI/验证 → 人合并 →
原 source 与公司 merge SHA/包摘要的 provenance/readback。公司不复制开发 Issue、账号或 PAT；不依赖应用部署作 canary。

## 50 rollback dry-run 与停止恢复

没有上一 application release 的 first-install 使用精确 uninstalled 基线，不能填虚构 previous release。
adopt 使用已验证 snapshot；数据 restore、仓库删除或权限放宽仍需单独风险决定。
故意失败后停止后继步骤，保留原始失败与恢复证据；不能跳过恢复用重跑成功覆盖错误。

```bash
"$TRUSTED_CLI" rollback --dry-run --action repo-bootstrap \
  --handoff /approved/incoming/handoff.json \
  --archive /approved/incoming/platform-bootstrap.tar.gz \
  --expected-handoff-sha256 "$HANDOFF_SHA256" \
  --inventory /approved/inventory.json --target /approved/target.json \
  --expected-plan-sha256 "$PLAN_SHA256" \
  --output /approved/repo-bootstrap-rollback-request.json
```

本命令准备请求，execution 始终 NOT RUN；实际恢复由后续批准的 exact 脚本执行并提供 observation。
no-op 步骤回退也是 no-op；不能删已有仓库、改 main 或覆盖未经绑定的 snapshot。

## 60 分层交付

| 层 | 可证明的内容 |
|---|---|
| source | schema、CLI、封闭入口和静态脚本合同通过 review/test |
| local | 指明 source SHA 的两次 bundle、负向测试、dry-run、隔离 fixture |
| installed | 需后续安装清单/实际 bytes/role/profile readback；本 Issue NOT RUN |
| company live | 需现场原始事实经脱敏后的完整操作/恢复/观察证据；本 Issue NOT RUN |

以上 Stage 编号属于平台 bootstrap，和 company-delivery application Stage 00–110 独立，不能互相替代 PASS。
本 Issue 完成只提供 A1 source；Gate A/B 整体完成仍需依赖 Issue 合并、稳定 pin、现场绑定和实际验收。
