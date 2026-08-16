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
status: needs-human-decision
branch: change/124-secret-scan-false-positive
pr_url:
created: 2026-08-16
updated: 2026-08-16
---

## 问题/需求总结

Issue #124 跟踪一个已在 exact NewEmaint docker-release/v2 release 上复现的 fail-closed 阻塞：artifact-only verification 保持零 Docker/零 target facts，但 company-delivery build-bundle 把合法 Compose 外部引用或镜像归档中的非 Secret 字节判为 SENSITIVE_CONTENT。当前只允许记录命中文件类别，不处理、回显或猜测任何命中值。

## 影响范围

影响 company-delivery bundle 的 Secret 扫描 seam、docker-release/v2 Compose 安全规则与 Docker/OCI archive 只读解析，以及对应的 fake/negative/real external-fixture tests 和 mapped change documents。公司 VM、NewEmaint repository/release bytes、Secret、数据库、服务与部署状态均不在本 Change 的 planning 或当前执行范围。

## 初步方案与建议

保持统一 fixed-code/no-echo 失败接口，把原始全文件 Latin-1 正则替换为可审计的 payload 分类器：普通文本使用精确外部引用语法；compose.model.json 复用现有 normalized Compose validator；compose.yaml 只把与既有合同一致的完整参数引用视为占位符，任何 default/alternate 中的具体内容继续扫描或拒绝；images.tar 先复用 docker-release/v2 已验证的 Docker/OCI graph 与 digest allowlist，再有界解析 config 和 layer archive，对每个支持的内容类别执行同一 concrete-secret 判定，未知格式或解析失败 BLOCKED。真实 006d release 作为仓库外 integration fixture 重放，412MB bytes 永不提交。

## 风险

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
- 现有 bundle._scan_bundle_payloads 对所有 payload（包括 images.tar）按 Latin-1 原始字节套用 contains_sensitive_text；_mask_source_placeholders 仅覆盖简单变量引用。
- docker-release 已有 strict normalized Compose external-reference validator，以及 Docker/OCI manifest、descriptor digest、member/path/type 的 artifact-only graph 验证 seam，可作为格式化扫描的信任输入。
- 真实 build-bundle 返回固定 SENSITIVE_CONTENT 并清理输出；Stage 00 local preparation 为 BLOCKED，公司 Stage 10+ 全部 NOT RUN。

### 缺失的 acceptance criteria 或决策

- T01–T03 已完成；T04 从 clean candidate HEAD 对 exact release 执行时，artifact-only gate 为 PASS，
  `compose.model.json` 与 `compose.yaml` scanner 为 PASS，但 `images.tar` 仍固定返回 `SENSITIVE_CONTENT`，
  两份临时输出均已清理。现有 Spec 同时要求所有 byte stream 的 high-confidence signature 与 layer JSON
  quoted sensitive scalar 一律拒绝；不得为使真实 bytes 变绿而自行放宽。是否将“embedded source/example
  signature”与“实际 credential material”改为结构化判定，需要新的人工安全决策；批准不包含 merge 或部署。
