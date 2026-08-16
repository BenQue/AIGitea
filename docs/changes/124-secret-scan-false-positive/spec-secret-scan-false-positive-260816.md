---
issue: 124
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/124
change_type: security
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - security
  - shared-core
  - cross-module
  - external-contract
  - artifact
  - deployment
  - deployment-boundary
  - compatibility
  - rollback
depends_on: []
status: approved
branch: change/124-secret-scan-false-positive
pr_url:
created: 2026-08-16
updated: 2026-08-16
---

# Spec：真实 release 的格式化 Secret 扫描

## 目标与原因

修正 `company-delivery build-bundle` 对真实 NewEmaint `docker-release/v2` 制品的 Secret 扫描误报，
使 exact release `006d0c43cafebff058889e3338d1e8bdcc8b661c` 能在不放宽 Secret 边界的前提下生成
确定性 handoff bundle。

当前已知事实分层如下：

- `docker-release/v2` artifact-only verification 为 `PASS`，`docker_calls=0`、
  `target_facts=NOT_READ`；DockerLab 原位六文件与本机临时副本 SHA256 逐项一致。
- `build-bundle` 在 artifact verification 后返回固定 `SENSITIVE_CONTENT` 并清理输出。当前唯一可记录的
  命中文件类别为 `compose.model.json`、`compose.yaml`、`images.tar`；不读取、回显、记录或猜测命中值。
- 因未生成可交接的 exact bundle，Stage 00 local preparation 为 `BLOCKED`；公司 Stage 10–110 全部
  `NOT RUN`。

本 Change 只改变 scanner 如何证明“具体 Secret”或“无法安全完成扫描”，不削弱 #120 的
fail-closed、no-echo、exact-bytes、artifact-only、两台公司 VM 和人工逐阶段批准合同。

## 安全扫描合同

### 1. 固定结果与 no-echo

scanner 必须先完成现有 `docker-release/v2` identity/checksum/graph 验证，再按 payload 类型执行只读扫描：

| 条件 | 固定结果 | 对外信息边界 |
|---|---|---|
| 发现符合合同定义的具体 Secret | `SENSITIVE_CONTENT` | 只允许固定 code/message；不得包含值、片段、offset、内层 archive path 或原始异常 |
| archive/media/compression/content 无法在有界规则内安全解析 | `SENSITIVE_SCAN_BLOCKED` | 只允许固定 code/message；不得退化为 raw-byte PASS |
| release identity、checksum 或 graph 非法 | 现有 `ARTIFACT_INVALID` | 沿用现有 artifact-only 包装，不暴露底层输入 |
| 全部分类器完成且无命中 | `PASS` | 只声明 scanner contract/version 与顶层类别完成，不输出被扫描内容 |

异常对象、CLI stdout/stderr、测试断言和 verification 都不得保存命中值。实现不得调用 `strings`、
shell、Docker 或 target profile，也不得把 rejected input 串接进 exception chain。任一失败仍须删除
bundle root、archive 与 sidecar；不得留下部分 handoff。

#### 有限 JSON-context 脱敏诊断

人工已批准为 `classifier=JSON_CONTEXT` 增加一个仅供显式诊断消费的固定 reason code。允许集合恰为：

```text
JSON_RESOURCE_LIMIT
JSON_PARSE_UNSAFE
JSON_SOURCE_ASSIGNMENT_AMBIGUOUS
JSON_RUNTIME_ENV_INVALID
JSON_SOURCE_SENSITIVE_AMBIGUOUS
JSON_GENERIC_SENSITIVE_AMBIGUOUS
JSON_REASON_UNAVAILABLE
```

reason code 必须是无参数常量；不得拼接或伴随 OCI 内部 path、JSON key/path、值、片段、长度、offset、hash、
计数或原始异常。正常 `build-bundle` CLI 仍只输出既有 fixed code/message，不输出 reason。显式诊断最多输出
`top_level=images.tar classifier=JSON_CONTEXT reason=<one-fixed-code>`；非集合值一律折叠为
`JSON_REASON_UNAVAILABLE` 并保持 `SENSITIVE_SCAN_BLOCKED`。

该诊断只解释为什么 scanner 无法安全分类，不提供放行能力。若结果对应真实 credential material，继续返回
`SENSITIVE_CONTENT`；若 reason 为 ambiguity、parse/resource failure 或 unavailable，继续返回
`SENSITIVE_SCAN_BLOCKED`。它不得形成 release/image/path/digest 特判，也不得改变 runtime concrete、known
token/JWT、有效 PEM、真实 userinfo URL 或完整 Authorization credential 的拒绝语义。

### 2. Compose 外部引用与具体值

`compose.model.json` 继续以 `aisoft_release.security` 和 `validate_compose_model` 为唯一语义合同。
平台只把以下两个**完整值**视为允许的外部引用：

```text
${NAME}
${NAME:?required}
```

其中 `NAME` 必须匹配 `[A-Za-z_][A-Za-z0-9_]*`；`:?required` 是固定的缺值失败语义，不是 Secret 值。
这是平台有意采用的 Compose/POSIX 参数展开严格子集，不等于允许所有语法。以下内容不得被整体 mask：

- `${NAME:-literal}`、`${NAME-literal}`、`${NAME:+literal}`、`${NAME+literal}`；
- 任意非固定 error word、前后拼接、嵌套展开、command substitution 或不配对的 `${...}`；
- quoted/unquoted concrete literal、credential URL、authorization header、token/private-key signature。

对敏感 environment key，只有位于 `services.<service>.environment` 且完整值匹配上述严格子集才可通过；
default/alternate 的 word 必须继续进入 concrete-value 判断，不能因表达式语法合法就整段忽略。其它位置的
sensitive field 继续 fail closed。

`compose.yaml` 不通过正则替换任意 `${...}`。scanner 使用有界 token lexer 识别 YAML scalar 内的完整
外部引用，并与已验证的 normalized model 规则保持同界；敏感赋值的 RHS 只有完整外部引用才豁免。
无法确定边界或出现上述非允许展开时返回 `SENSITIVE_CONTENT` 或 `SENSITIVE_SCAN_BLOCKED`，不得通过
宽泛 placeholder allowlist。

### 3. 普通 operator/release 文本

- operator source 继续只允许现有精确 placeholder（如 `$IDENT`、`${IDENT}`、格式占位符及固定的
  protected-file 读取形态）；不得重新允许 `${IDENT:-literal}` 或任意 `$()`。
- JSON payload 先按 strict parser/字段路径和 document context 检查，再对 scalar 执行高置信 material 扫描；
  重复 key、超限、非 UTF-8 或上下文歧义 fail closed。Docker config、environment 与显式 runtime-config
  surface 中，敏感 key 的任意非空 concrete scalar 必须拒绝；schema、i18n、source/doc JSON 中的字段名和
  示例文本由结构化 source 规则处理，不能仅因出现敏感单词而判为凭据。
- 敏感 key 的 RHS 只有完整外部引用、标识符/member/function/regex reference 等明确的非凭据表达式可避免
  “具体值”判定。OCI `config.Env` 与被结构确认的 runtime-config 中，敏感键的任何非空 concrete value 必须
  拒绝；source/doc/schema/test-fixture 中的字段名、示例、regex 或不完整 signature 不是实际凭据。无法可靠
  区分 runtime config 与 source/example 的 payload 必须 `SENSITIVE_SCAN_BLOCKED`。
- 任意 byte stream 都至少经过跨 chunk 的高置信 signature 扫描；不能按扩展名或是否含 NUL 直接跳过。

高置信 byte signature 的对象是完整 credential material，不是孤立语法文本：

- private key 仅在存在匹配的 `BEGIN`/`END`、有界且可验证的 base64 body 时判为 material；源码、schema、
  文档或 binary 中孤立的 PEM header 字符串仍会被扫描，但不能单独触发 `SENSITIVE_CONTENT`；
- 任意位置的 known token/JWT 格式与完整有效 PEM private-key material 必须拒绝；
- generic byte stream 中的 credential URL 仅在存在非 placeholder 的完整 userinfo 时拒绝；`Authorization`
  仅在形成完整 scheme + concrete credential block 时拒绝。源码/文档中的 placeholder、示例、regex 或不完整
  header 继续扫描但不等同 material；
- typed runtime-config/environment context 不依赖熵：敏感 key 中任何非空 concrete value 仍拒绝；
- 以上规则按内容和结构判定，不得引入 filename、inner path、image digest、release SHA 或命中值 allowlist。

### 4. `images.tar` 格式化扫描

不得再对 outer tar 的 header/padding/compressed bytes 运行通用 Latin-1 key/value 正则。实现必须复用或
提取现有 `aisoft_release.transport` 的 read-only verified graph seam，并满足：

1. **先证明 graph**：沿用 outer archive 的 normalized path、duplicate/type allowlist、Docker
   `manifest.json`、OCI index/manifest、descriptor size/digest、config/layer reachability 与 exact transport
   tag 校验。只扫描该 graph 中全部 reachable blobs；存在额外或悬空 member 仍由现有 contract 拒绝。
2. **不落盘解包**：通过 `tarfile` file object 流式读取 outer archive 与 layer archive；不 extract，不跟随
   symlink/hardlink，不执行镜像内容。inner path traversal、duplicate path、device/FIFO 或无法识别的 member
   type 触发 `SENSITIVE_SCAN_BLOCKED`。
3. **config/metadata**：有界解析 Docker/OCI config JSON。对 `config.Env` 先拆分 name/value；敏感 name 的
   非空 concrete value 必须 `SENSITIVE_CONTENT`，完整外部引用可通过。labels/history/commands 和 attestation
   等 reachable JSON 仍做高置信 signature 扫描，但不能把普通字段名或源码文本当成凭据。
4. **layer 内容**：支持 graph 声明且 stdlib 可安全读取的 uncompressed/gzip layer tar。每个 regular file
   依据内容而非扩展名分为 structured JSON、UTF-8 text 或 binary；structured/runtime-config surface 使用
   key/value concrete-literal 规则，所有三类都执行 byte-signature scan。symlink target 等 metadata 也扫描，
   但不读取链接目标。
5. **binary 不豁免**：ELF、图片、压缩片段或其它 binary 不运行容易误报的普通 key/value 语法，却仍扫描
   完整 PEM private-key material、known token/JWT、含真实 userinfo 的 credential URL、完整具体
   Authorization credential block 等 byte signature。孤立 header、source placeholder、regex 或示例文本
   不等于 material，但仍进入同一有界 parser，不能通过 whole-binary skip。
   未知 outer/layer compression 或不能完成既定 byte scan 时 `SENSITIVE_SCAN_BLOCKED`，不能记录为 PASS。
6. **资源上限**：JSON 继续使用现有 8 MiB bound；inner archive 总 member 数不超过 200,000、单 member
   声明大小不超过 2 GiB、所有 layer 的累计展开字节不超过 8 GiB，且全程 1 MiB 级流式读取。超限只返回
   固定 blocked code。

这里没有“允许某个 image/file 绕过扫描”的机制。允许的是版本化格式与精确语法；新增 broad filename、
image digest 或 release-specific allowlist 均违反本 Spec。

## Acceptance criteria

- [ ] **AC-1 Exact real release**：对 repo-external exact release
  `006d0c43cafebff058889e3338d1e8bdcc8b661c` 先复核 artifact-only
  `ok=true`、`docker_calls=0`、`target_facts=NOT_READ`，再从 clean candidate HEAD 以同一 UTC input 构建两次；
  两次 archive SHA256 相同且 `verify-handoff` PASS。真实约 412MB bytes、临时 bundle 与命中内容均不提交。
- [ ] **AC-2 Compose strict subset**：`compose.model.json` 与 `compose.yaml` 中 `${NAME}`、
  `${NAME:?required}` 的完整引用通过；default/alternate、拼接、command substitution、malformed expansion 和
  concrete literal 不能被整体 mask，并由正负 fixture 固定。
- [ ] **AC-3 Concrete Secret/no-echo**：Compose 或普通 payload 中注入 sentinel concrete Secret 时稳定返回
  `SENSITIVE_CONTENT`、退出非零、完整清理输出；exception、stdout/stderr、test failure 和 evidence 均不含
  sentinel、片段、offset 或内层路径。
- [ ] **AC-4 Format-aware image scan**：`images.tar` 必须先通过现有 Docker/OCI verified graph，再扫描全部
  reachable config/layer/attestation 内容；不扫描 outer tar header/padding，不按 binary/扩展名跳过，不启动
  Docker、不读取 target facts。
- [ ] **AC-5 Image negative matrix**：fake archive 至少覆盖 config Env concrete Secret、layer runtime-config
  concrete Secret、binary 高置信 signature 跨 chunk、unsafe/duplicate inner path、unsupported compression、
  JSON/member/decompressed-size bound；每项分别得到 `SENSITIVE_CONTENT` 或 `SENSITIVE_SCAN_BLOCKED`，且 no-echo。
- [ ] **AC-6 False-positive fixtures**：包含敏感字段名的 schema/source/doc 文本、完整 external references、
  ordinary binary 和合法 Docker/OCI metadata 在无具体 Secret 时通过；不得靠 release SHA、image digest、文件名
  或 whole-binary allowlist 实现。
- [ ] **AC-7 Stable handoff contract**：`company-delivery-handoff/v1`、六文件 exact bytes、逐文件 checksum、
  deterministic archive、`verify-handoff` 和 CLI 参数保持兼容；operator `VERSION` 从 `1.0.0` patch-bump 到
  `1.0.1`，不原地改写既有 bundle。
- [ ] **AC-8 Validation/evidence boundary**：focused/full unit tests、fake repeat build、tamper/security negatives、
  integration harness preflight、JSON parse、shell syntax/ShellCheck、full runtime suite、smoke、diff/no-secret checks
  通过；公司 VM/Gitea/Runner/Registry/AppServer/DB/Nginx/production、service/timer 和部署全部 `NOT RUN`。
- [ ] **AC-9 Fixed diagnostic privacy**：上述七个 reason code 均有 synthetic fixture；exception、普通 CLI 和
  显式 diagnostic output 只能出现 fixed code/message/top-level/classifier/reason，不能包含输入 sentinel 或任何
  path/key/value/snippet/length/offset/hash/count；真实诊断只运行一次。

## 接口、数据与兼容性影响

- `company-delivery build-bundle` 参数与成功结果结构保持不变；新增固定失败 code
  `SENSITIVE_SCAN_BLOCKED`，`SENSITIVE_CONTENT` 的 no-echo 语义保持不变。
- 新增 stdlib-only scanner 模块，并把 `aisoft_release.transport` 的已验证 Docker/OCI graph 暴露为只读、
  immutable internal result，供 artifact validator 与 company-delivery scanner 共用；不得形成第二套 graph 规则。
- `docker-release/v2`、`docker-release-offline-bundle/v2`、handoff/evidence/inventory schema version 均不变；
  normalized Compose 的外部引用规则不扩张。
- `company-delivery/VERSION` 升到 `1.0.1`，使新 scanner bytes 可被 handoff manifest 明确区分；旧 `1.0.0`
  bundle 不修改、不补签，也不能冒充已经通过新 scanner。
- 无数据库 migration、release rebuild、image rewrite、Compose rewrite 或 live configuration 变更。

## 风险与回滚约束

| 风险 | fail-closed 缓解 / 回滚 |
|---|---|
| 参数展开 parser 过宽，吞掉 literal Secret | 只接受现有两种完整引用；默认/替代/拼接/command substitution 负测；revert source PR |
| image scanner 仅绕开 binary，形成盲区 | verified graph + inner tar + config/text/binary 分层；每个 byte stream 至少 high-confidence scan；未知格式 BLOCKED |
| archive bomb 或恶意路径消耗资源/写盘 | 不 extract、固定 member/type/path/digest gate、entry/size/expanded-byte bounds；超限固定 blocked |
| 错误信息泄漏命中值 | fixed code/message、禁止 inner path/snippet/offset、sentinel 捕获 stdout/stderr/exception tests |
| 为真实 release 写 digest-specific 豁免 | 明确禁止 release/image/path broad allowlist；真实 fixture 只作为最后 integration 证明 |
| 修复后被误写成公司部署成功 | verification 分层；只可把 local Stage 00 preparation 写为 PASS，公司 Stage 10+ 继续 NOT RUN |

若实现或 real fixture 仍失败，停止在 `BLOCKED`，删除临时输出并保留 exact release 不变；不得修改或重建
NewEmaint bytes。source 回滚为单 PR revert；本 Change 无 live mutation，因此无数据库或环境回滚。

## 非目标

- 不读取、打印、记录或猜测任何真实命中值；不把 412MB release bytes 或临时 bundle 提交到仓库。
- 不修改 NewEmaint repository、release/Compose/image bytes，也不执行真实 release build。
- 不连接公司内网，不请求 SSH，不创建/读取/轮换 Secret、PAT 或 key。
- 不安装/升级 Gitea/Runner，不启用或重启 service/timer，不改 firewall/DNS/TLS。
- 不执行数据库 migration/restore、测试部署、生产部署或任何公司/live mutation。
- 不增加 binary/file/image/release broad allowlist，不用不同 bytes 替代 exact release。
- 不修改本次运行遵循的治理文件，不自动 merge。

## 未决问题

无。扫描语法、错误分类、资源边界、真实 fixture 入口与禁止项均已在本 Spec 固定；是否批准进入
`$implement #124 Txx` 是下一道人工流程门，不是实现方向未决。
