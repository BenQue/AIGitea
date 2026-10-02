# AISoftPlatform architecture catalog V1

本目录是技术架构版本、profile、例外和项目 lock 有效性的唯一平台事实源。它只验证候选，
不会升级依赖、修改应用、部署、访问服务器或宣称 migration 完成。

## Canonical contract

- 所有输入仅接受 strict JSON；V1 明确拒绝 `.yaml`/`.yml`，没有 YAML parser。
- `catalog.json` 固定 component 的精确版本、状态、lifecycle、官方来源和 provenance 要求。
- Next.js、React 与 Prisma preferred entries 固定 component-scoped npm stable-release snapshot、
  精确 Registry URL 和 integrity；validator 拒绝未被 snapshot 覆盖的版本、Canary/Experimental、
  `latest`、范围、package 集合漂移和同组件 package 版本不一致，且不会在 lock 生成时访问网络。
- `profiles/*.json` 的每个 slot 保留唯一 `preferred` component，并可由 profile owner 维护同
  category 的 closed `transitions` allowlist；delivery 能力仍由 #22/应用 Change 提供。
- 一个 profile 的 `delivery_contracts` 可以列出多个取值，但一份 declaration 只取其中一个。
  同一个仓库的多个环境如果交付归属不同，各写一份 declaration 与一份 lock，不合并成一份；
  取值之间的互斥性因此保持不变（ADR-0006）。
- 声明容器交付取值的 declaration 必须同时声明一个按 digest 固定的 `oci-image` component，
  否则 `DELIVERY_BASE_IMAGE_REQUIRED` fail closed。这条按 delivery contract 触发，
  不是 profile slot——`required_components` 无条件，加 slot 会逼原生交付声明不存在的镜像。
- 项目人工维护 `.aisoft/architecture.json`，提交生成的 `architecture.lock.json`。
- lock 不含生成时间或主机信息；相同输入会生成 byte-identical canonical JSON。
- Project 每个 slot 只能选择 preferred 或一个 allowlisted `supported`/`sunset` transition；
  transition 不是第四种永久 profile，也不表示 major migration 已完成。
- Component 版本默认与 catalog pin 精确相等。项目实际运行的构建不同时，可以显式声明
  `as_built: true` 如实记录，条件是有且只有一个有效 exception、与 pin 同 major 且不相等；
  `0.x` major 下 minor 也必须相等，按 digest 固定的 component 一律拒绝 as-built。
  lock 记录声明的真实构建而不回显 catalog pin，偏差由同一条目的 `exception_id` 与
  `exception_expires_at` 承载，lock 不新增标记字段（ADR-0006）。
- Transition 必须引用绝对 http 或 https migration Issue，并与唯一、未过期 exception 一一绑定；
  多个 component 可共享一个逐项列明范围的 umbrella Issue，但每个 component 仍保留自己的
  exception。lock 固化 Issue、exception ID/expiry 与 catalog/profile/declaration checksums。
- `prohibited`、EOL、过期/超过 180 天或晚于 `migrate_by` 的 exception、mutable-only OCI 和
  lock drift 均 fail closed；没有 bypass flag。

## CLI

```bash
architecture/bin/aisoft-architecture validate \
  --catalog architecture/catalog.json \
  --profiles-dir architecture/profiles \
  --schema-dir architecture/schemas \
  --project architecture/templates/project-architecture.example.json

architecture/bin/aisoft-architecture lock \
  --catalog architecture/catalog.json \
  --profiles-dir architecture/profiles \
  --schema-dir architecture/schemas \
  --project .aisoft/architecture.json \
  --output architecture.lock.json

architecture/bin/aisoft-architecture explain \
  --catalog architecture/catalog.json \
  --component runtime.node.24
```

`--today YYYY-MM-DD` 只用于可复现的 lifecycle/边界测试。生产 CI 不应覆盖当天 UTC date。
CLI diagnostics 只返回 code、path、remediation，不回显输入值。

CLI 与 `codex/tools/aisoft-project-check.sh` 都从**脚本所在平台 checkout 的工作树**解析
`catalog.json` 与 `profiles/`。本地 `main` 没有 fast-forward 到最新时，新增的 profile
解析不到，表现为 `PROFILE_UNKNOWN` 或 slot 对不上——那是 checkout 陈旧，不是声明写错。
先 `git fetch` 并 ff 本地 `main`，再重跑。

## Dockerfile 基镜像源码一致性合同（#288）

> 实施边界：#288 的 T02 已实现以下离线源码核验与 `--repo-root` 参数。
> architecture/CLI 与 release reader 集成回归已通过；固定 release evidence 的 exact pin
> 已在 T05 受控同步。T06 已受控应用 installed-drift fixture 基线隔离，专项测试通过；
> fresh run 的完整 smoke/runtime 本地验收均通过（详见 #288 verification）；
> 最终 PR/required CI/安装与部署未执行。

容器交付 declaration 在既有 `oci-image` component 之外，必须增加非空、去重的 `dockerfiles`
数组，列出该构建使用的全部 Dockerfile。路径以应用仓库根为基准，使用相对 POSIX 形式，例如：

```json
"dockerfiles": ["docs/deploy/Dockerfile", "worker/Dockerfile"]
```

这是 declaration 的字段示例，不是完整 JSON 文件。非容器交付（`pm2-legacy`、
`embedded-sqlite/v1`、`systemd-native/v1`、`windows-iis/v1`）禁止该字段，也不读取 Dockerfile。
该规则按 delivery contract 触发，不由 profile slot 决定。

validate、lock 与 validate --lock 共用同一文件核验入口。CLI 未传 `--repo-root` 时，
仅对 project 文件直接位于 `.aisoft/` 的布局，从其父目录确定仓库根；其它容器布局必须传
显式 `--repo-root`。不从 cwd 猜测，也不 glob 搜索 Dockerfile。既有项目 checker 使用
`.aisoft/architecture.json`，沿该入口检查。容器库调用方同样必须提供 `repo_root`，没有
纯 JSON 跳过文件核验的通道。

路径不得是 absolute、空项，不得含 `.`/`..` segment、反斜线、控制字符、空路径 segment；
文件及目录链禁止 symlink。必须是根内可读普通 UTF-8 文件，最大 1 MiB。不运行 Docker、
shell、Registry 查询或文件内容；诊断仅含稳定 code、声明字段/逻辑行位置和修复建议。

### FROM 支持范围

- 所有外部 `FROM` 必须保留字面量 `image:tag@sha256:<64 lowercase hex>`，digest 必须在
  已通过 catalog 校验的声明 OCI 集合中。反向也要求每个声明 OCI digest 至少被引用一次。
  允许多文件、多外部 stage 使用不同的已声明 digest，不只检查最后一个 stage。
- 命名 stage 可以引用先前 stage；禁止重复、前向或自引用。`FROM scratch` 无外部镜像，
  但不能以全部 scratch 绕过声明基镜像的实际引用要求。数字 FROM stage 引用不作为豁免。
- 接受大小写不敏感指令、空白、整行注释、CRLF，以及默认反斜线或有效 `escape` directive
  指定的反引号续行。directives 仅在 Docker 规定的文件头位置生效；重复/非法 escape 拒绝。
- 镜像 token 中有 `$` 一律拒绝，即使全局 ARG 有默认值；build-time override 能改变默认值，
  静态展开默认值不能作为证据。其它指令内普通 ARG/ENV 不受该规则限制。
  `--platform=$BUILDPLATFORM` 等平台变量允许，但不新增 CPU/OS 与 child/index 兼容性证明。
- 只接受一个可选 `--platform=...`、一个 image token、可选 `AS stage` 的 FROM 形式。
  标准 `docker/dockerfile:1`/稳定 `1.x` frontend 可识别；custom frontend、labs、heredoc
  与无法证明语义的结构 fail closed，不通过忽略行取得 PASS。

### 稳定诊断与迁移

| 诊断码 | 原因 |
|---|---|
| `DOCKERFILE_DECLARATION_REQUIRED` / `DOCKERFILE_DECLARATION_FORBIDDEN` | delivery contract 与路径声明不匹配 |
| `DOCKERFILE_ROOT_REQUIRED` | 容器文件核验没有明确仓库根 |
| `DOCKERFILE_PATH_INVALID` / `DOCKERFILE_READ_FAILED` | 路径不安全或文件无法安全读取 |
| `DOCKERFILE_FROM_REQUIRED` / `DOCKERFILE_FROM_INVALID` | 缺少 FROM 或 FROM 语法无效 |
| `DOCKERFILE_SYNTAX_UNSUPPORTED` / `DOCKERFILE_FROM_VARIABLE_UNSUPPORTED` | 无法静态证明支持的语法或镜像变量 |
| `DOCKERFILE_DIGEST_REQUIRED` / `DOCKERFILE_DIGEST_MISMATCH` | 外部镜像缺有效 digest 或不在声明/catalog 集合 |
| `DOCKERFILE_BASE_IMAGE_UNUSED` | 声明了没有实际 FROM 引用的 OCI digest |

读取/核验失败返回 exit 2 与 `valid: false`，lock 不创建或覆盖输出。已有容器声明必须补充路径并
重新生成 declaration checksum/lock，不保留 bypass；非容器声明及 lock 的 byte identity 保持不变。
lock schema、release reader 的精确字段集合不变，不在 lock 中新增 Dockerfile evidence 字段。
仓内容器 reference 使用 synthetic/target Dockerfile，不构成真实下游应用迁移证据。

通过核验只证明**声明的源码输入**中全部外部 FROM 与声明/catalog 一致。应用 CI 必须把实际
构建选用的 Dockerfile 与同一 declaration 绑定；其它 `-f`、stdin、生成文件、额外 build context
与外部 `COPY --from`/RUN 下载不在本保证内。正式制品来源需 builder provenance/attestation，
`valid: true` 不表示已经构建、pull、部署或现场验收。应用迁移走应用自己的 Issue/PR。

## 更新与例外

### Profile checksum 与重 lock（#287 源码已实现，安装与消费者验收另行执行）

本节与 [ADR-0007](decisions/0007-profile-machine-checksum.md) 定义已实现的哈希合同。当前源码
CLI 默认生成 V2，并严格校验 V1/V2。源码本地验证不证明工具已安装或实际消费者已验收 V2。

现有 V1 的 `source_checksums.profile_sha256` 对整个解析后的 profile canonical JSON
求 SHA-256。空白与 object key 顺序本来就不会改变该值；字符串和数组内容变化会改变它。
因此，仅润色 `compatibility_rules` 也会让 V1 lock 报 `LOCK_DRIFT`。

新格式采用带域标识的 `profile-machine-v1`：从通过 strict schema 校验的 profile 顶层
只排除 `description` 和 `compatibility_rules`，将其余完整对象放入固定 envelope：

```json
{"hash_contract":"profile-machine-v1","profile":{"...":"除两项说明字段外的完整 profile"}}
```

以上只是哈希输入形状说明，省略号不是可提交输入。envelope 使用既有 canonical JSON 规则
求 SHA-256；object keys 排序，数组保持原序，不排序、去重或另作归一化。

| Profile 字段 | V2 是否覆盖 | 影响 |
|---|---|---|
| `description`、`compatibility_rules` | 否 | 说明润色不使 V2 lock 漂移 |
| `$schema`、`schema_version`、`profile_id`、`version`、`catalog_revision`、`status` | 是 | 身份、状态、版本与绑定变化仍检测 |
| 完整 `required_components`，包括 `allowed_states` 和 `transitions` | 是 | slot、component 和允许状态变化仍检测 |
| 完整 `delivery_contracts` | 是 | 交付取值与顺序变化仍检测 |
| 完整 `constraints` | 是 | 部署、存储、并发、备份/恢复约束仍受保护 |
| 未来获 strict schema 批准的其它机器字段 | 是 | 不会因旧字段 allowlist 遗漏 |

`constraints` 虽然是自然语言字符串，却承载真实运维约束，因此其措辞变化仍保守触发漂移。
本合同不承诺所有散文编辑都稳定。规范变化必须同步到对应机器字段或约束；不得只编辑
被排除的说明字段来改变实际实施要求。未知字段仍由 schema 拒绝。

V2 lock 使用独立 `architecture-lock-v2.schema.json`、`schema_version: 2.0` 和必填顶层
`profile_checksum_contract: profile-machine-v1`。`source_checksums.profile_sha256` 采用
上述投影哈希；catalog 和 declaration 仍使用原完整 canonical 哈希。`lock_sha256`
覆盖完整 lock，包括格式与算法标识。profile 的既有 `version` 与 declaration 的匹配
检查保留；版本相等不能忽略 hash，漏 bump 的合法机器变化仍须 `LOCK_DRIFT`。

当前源码 CLI 的新 lock writer 默认生成 V2；`validate --lock` 按 lock 自身的已知版本选择
schema/expected lock：V1 保持完整 profile 哈希，V2 使用明确投影。未知 version/marker、
marker 混用/缺失、额外字段和 checksum 篡改均 fail closed；没有 ignore、自动降级、
自动迁移或 CLI legacy writer 开关。输入非法时可先失败于 schema/semantic 诊断；
合法机器输入发生变化时才精确断言 `LOCK_DRIFT`。

V1 只有旧哈希，未保存机器投影或旧 profile 快照，无法证明新旧差异仅为说明。故新 reader
不会重新解释或放宽旧 V1 lock：V1 的说明漂移仍失败。采用 V2 后，新格式的既有 lock
才获得说明润色稳定性。旧工具，包括当前仅接受 V1 的 release reader，也会拒绝 V2；
消费者必须先核对实际读取链是否支持新格式，不能把 architecture validate 通过当作
release、安装或部署已兼容。

#### 下游显式迁移与人工通知

1. 平台变更维护者提供该 Change 的 Issue/PR、profile ID、旧/新 version 与 checksum
   contract、机器/约束变化和受影响环境的证据。只列真实读回的消费者，未盘点写 `NOT RUN`；
   不继承历史“只有一家”的 inventory 判断。
2. 项目维护者在自己的 Issue/Change 中确认每个环境的 declaration/lock 路径，以及实际
   CLI、schema 和 release reader 的版本兼容性。#287 不代为更新工具或写其它仓。
3. 采用已合并且符合读取链要求的工具后，复核当前 catalog/profile/declaration/exception。
   显式运行 lock，输出到临时候选路径；此动作仅生成候选，不证明当前合同已被应用接受。
4. 审阅 candidate diff，运行 `validate --lock` 和该项目的 required CI，再提交环境对应的
   lock。陈旧 V1 报 drift 时仍须审阅当前合同，不能用重生成消除真实机器变化。target lock
   不得复制或重命名为 current。
5. 消费者记录接受的格式、输入与校验结果，并按自己的 PR/部署边界完成后续流程。平台
   reference locks 原样保留，不批量重写。

V2 的纯说明编辑无需下游重 lock。机器/constraints/catalog/declaration 变化仍要求逐项目
审阅并按上述步骤处理。自动消费者发现、跨仓开 Issue 和 `needs-relock` 投递均为
**NOT IMPLEMENTED**；本合同没有跨仓写、live 配置、安装或部署授权。

回滚时，若已有消费者接受 V2，应保留支持双格式的 reader，或在应用独立 Change 中审阅
V1 兼容候选。旧 CLI 无法读 V2，不能只 revert 平台实现就宣称消费者已恢复。

Catalog 更新必须建立 Issue、complex spec/plan、兼容证据、PR/CI 和人工合并。Security 更新可走
快速通道但不能绕过这些门；patch 每月复审，minor 每季度复审，major 必须进入应用仓的 complex
Change。多个相互依赖 major 可以由一个 umbrella Change 统一治理，但必须逐 component 记录
compatibility、test、exception/expiry 与 rollback，不能把“部分完成”报告成整套迁移完成。
例外必须有 owner、reason、risk、controls、创建/到期日和 migration Issue；transition Issue
必须是应用仓中真实可读的绝对 http 或 https URL，不得带凭据、query 或 fragment，expiry 不得
超过创建日起 180 天或 component `migrate_by`，且到期当日即无效。as-built 版本例外使用同一套
字段与同一组上限。Preferred 路径不需要例外，也没有 `--ignore-all`。

离线导入顺序：从官方 source 获取 versioned artifact 和 metadata，校验签名/checksum，获取
SBOM/provenance/OCI attestations，导入批准 mirror，再由人工 PR 更新 catalog/lock。任何 timer 或
自动 updater 均不得直接改 production lock。

## 状态边界

`architecture/reference/` 是 read-only dry-run evidence。NewEmaint reference 明确分为：

- `target-candidate/`：project ID `newemaint-target-candidate`，描述 preferred 目标；
- current lock：本 Change 不生成；NewEmaint 实际采用 supported/preferred bytes 后，才可用
  project ID `newemaint` 在应用 Change 中生成；
- `gap-report.md`：记录 current facts、target 差异、umbrella tracking 与未执行边界。

Target lock 不能复制或重命名为 current，也不是项目已迁移、已部署或已验收的证据。
Transition 不能规避 `prohibited`/EOL/digest/expiry/checksum。Issue #26 明确采用 target-only
验收；NewEmaint [#52](http://gitea-ci.orb.local:3000/admin/NewEMaint/issues/52) 是唯一 umbrella
migration tracking Issue，但它不授权实施，也不能让 unsupported Next.js 14 进入 current lock。
