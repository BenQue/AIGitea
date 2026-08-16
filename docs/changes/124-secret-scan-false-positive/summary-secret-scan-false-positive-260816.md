---
issue: 124
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/124
change_type: security
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 修正 company-delivery 对真实确定性制品的 Secret 扫描语义并保持 fail-closed 与 no-echo 边界，直接触及共享安全、制品和部署合同，必须按 complex 处理
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
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
documents:
  summary: summary-secret-scan-false-positive-260816.md
  spec: spec-secret-scan-false-positive-260816.md
  plan: plan-secret-scan-false-positive-260816.md
  verification: verification-secret-scan-false-positive-260816.md
status: approved
branch: change/124-secret-scan-false-positive
pr_url:
created: 2026-08-16
updated: 2026-08-16
---

## 2026-08-16 人工简化决定（最新且优先）

用户明确批准将 `images.tar` 视为已通过 `docker-release/v2` 校验的 opaque immutable artifact，接受其内部
可能包含 credential-like 或实际凭据材料的风险；公司内网安装、授权和 Secret 配置均由人手工处理。本决定
覆盖下文早期“必须深度扫描全部 image layer”的约束：

- `images.tar` 通过现有 artifact-only identity/checksum/graph 校验后原字节搬运；
- builder 不解压、不读取或分类 image 内部文件，也不声称 image 内部无 Secret；
- operator source、handoff metadata、`compose.model.json`、`compose.yaml` 与其它可见文本仍做 no-secret 检查；
- 公司运行时 Secret、授权和部署动作仍只在公司内网由人处理，不进入本地 bundle、Issue、PR 或日志；
- 这是统一 artifact-type 规则，不使用 release SHA、image digest 或内部路径特判。

这是对根 [README.md](../../../README.md)“制品与环境配置分离”和
[07-内网与生产平移路线.md](../../../07-内网与生产平移路线.md)“环境 Secret 与 release bytes 分离”的
#124 范围内显式风险例外：平台仍保证环境 Secret 不进入交接包，但不再保证已经验证的应用镜像内部不含
release owner 打包进去的 credential-like 或实际凭据材料。该内容风险由 NewEmaint release owner 与公司
人工授权承担，不能被表述成平台已证明 image 无 Secret。

本 Change 继续完成本地 deterministic handoff、唯一 PR 和 required CI，停在人工合并闸门。正式可搬运包须在
PR 人工合并后从 protected `main` 的 exact source SHA 重新生成；pre-Stage 00 local exact-release regression
不生成 Stage evidence，公司 Stage 00–110 仍为 `NOT RUN`。

## 问题/需求总结

Issue #124 跟踪一个已在 exact NewEmaint docker-release/v2 release 上复现的 fail-closed 阻塞：artifact-only verification 保持零 Docker/零 target facts，但 company-delivery build-bundle 把合法 Compose 外部引用或镜像归档中的非 Secret 字节判为 SENSITIVE_CONTENT。当前只允许记录命中文件类别，不处理、回显或猜测任何命中值。

## 影响范围

影响 company-delivery bundle 的 Secret 扫描 seam、docker-release/v2 Compose 安全规则与 Docker/OCI archive 只读解析，以及对应的 fake/negative/real external-fixture tests 和 mapped change documents。公司 VM、NewEmaint repository/release bytes、Secret、数据库、服务与部署状态均不在本 Change 的 planning 或当前执行范围。

## 历史初步方案（已被人工简化决定覆盖）

保持统一 fixed-code/no-echo 失败接口，把原始全文件 Latin-1 正则替换为可审计的 payload 分类器：普通文本使用精确外部引用语法；compose.model.json 复用现有 normalized Compose validator；compose.yaml 只把与既有合同一致的完整参数引用视为占位符，任何 default/alternate 中的具体内容继续扫描或拒绝；images.tar 先复用 docker-release/v2 已验证的 Docker/OCI graph 与 digest allowlist，再有界解析 config 和 layer archive，对每个支持的内容类别执行同一 concrete-secret 判定，未知格式或解析失败 BLOCKED。真实 006d release 作为仓库外 integration fixture 重放，412MB bytes 永不提交。

## 历史风险分析（已被人工简化决定覆盖）

- 过宽的占位符识别可能掩盖具体 Secret，必须只接受现有 release 合同的精确语法并对 default/alternate 负测。
- 只跳过 images.tar 或二进制内容会制造扫描盲区，必须解析已验证 graph、递归处理 layer 内容并对未知格式 fail closed。
- 扫描失败若携带路径内层细节、偏移或命中片段可能泄漏信息，外部错误和测试输出只能保留固定 code 与顶层类别。
- 真实 412MB fixture 若被复制进仓库会破坏制品治理，integration gate 只能消费显式的 repo-external exact release root。

## AI 判级

```yaml
change_type: security
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 修正 company-delivery 对真实确定性制品的 Secret 扫描语义并保持 fail-closed 与 no-echo 边界，直接触及共享安全、制品和部署合同，必须按 complex 处理
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
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- broker 回读 #124 为 open、0 comments；一次性 LabelProjector 投影后由 typed broker 精确读回
  `approved`、`complexity/complex`、`triage/enhancement`、`triage/ready-for-agent`、`type/security`；未修改
  其他 Issue 或标签定义。
- fresh origin/main 固定为 7950d119ab5c949d914de172dac8606369483cd4，即 #120 / PR #123 merge source。
- 用户提供的 exact release 006d0c43cafebff058889e3338d1e8bdcc8b661c 已通过 docker-release/v2 artifact-only verification，docker_calls=0 且 target_facts=NOT_READ。
- 初始基线的 bundle._scan_bundle_payloads 对所有 payload（包括 images.tar）按 Latin-1 原始字节套用 contains_sensitive_text；_mask_source_placeholders 仅覆盖简单变量引用。
- docker-release 已有 strict normalized Compose external-reference validator，以及 Docker/OCI manifest、descriptor digest、member/path/type 的 artifact-only graph 验证 seam，可作为格式化扫描的信任输入。
- 初始真实 build-bundle 返回固定 SENSITIVE_CONTENT 并清理输出；该历史阻塞现已被 opaque artifact 决定
  覆盖。当前只有 pre-Stage 00 local exact-release regression PASS；不生成 Stage evidence，公司 Stage 00–110
  全部 NOT RUN。

### 历史实施记录（已被最新人工简化决定覆盖）

- T01–T03 已完成；T04 从 clean candidate HEAD 对 exact release 执行时，artifact-only gate 为 PASS，
  `compose.model.json` 与 `compose.yaml` scanner 为 PASS，但 `images.tar` 仍固定返回 `SENSITIVE_CONTENT`，
  两份临时输出均已清理。人工已批准把 embedded source/example syntax 与完整 credential material 结构化
  区分，并保持 runtime-config concrete value 严格拒绝、JSON ambiguity fail closed、fixed-code/no-echo 与
  无 path/digest/release allowlist。人工现进一步批准结构感知分类：任意位置仅对 known token/JWT、完整有效
  PEM、含真实 userinfo 的 credential URL、完整具体 Authorization credential block 阻断；source/doc/schema/
  test-fixture 中的示例、regex 与不完整 header 不作为实际凭据，无法可靠分类仍 `SENSITIVE_SCAN_BLOCKED`。
  第二版 structure-aware 实现、fixed reason/source-role tests 与通用 package metadata 规则已完成。唯一二级
  diagnostic 为 `JSON_SOURCE_SENSITIVE_AMBIGUOUS / PACKAGE_METADATA`；通用正反 fixture 全绿，但首次完整
  real build 返回固定 `SENSITIVE_CONTENT`。按批准合同这是实际 credential signal，当前为
  `BLOCKED / NEEDS_HUMAN_DECISION`；不得再次扫描或探查内容。push、PR、CI、merge 与部署均未执行。
