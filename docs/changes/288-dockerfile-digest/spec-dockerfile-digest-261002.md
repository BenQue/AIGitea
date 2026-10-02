---
issue: 288
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/288
change_type: bugfix
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - shared-core
  - schema-change
  - platform-governance
depends_on: []
status: approved
branch: change/288-dockerfile-digest
created: 2026-10-02
updated: 2026-10-02
---

# Dockerfile 基镜像 digest 一致性合同

## 问题与目标

容器交付声明与 catalog 一致并不能证明源码中的 Dockerfile 一致。当前 CLI 的 validate、
validate --lock 与 lock 都只消费 JSON，Dockerfile 改 digest、移除 digest 或删除文件仍假绿。
本 Change 选择 Issue 候选 A：在共同的 architecture lock 构建入口加入离线文件核验，
让同一套检查覆盖 validate、lock、validate --lock 以及既有项目 checker。
不采用独立的 advisory checker 或 lock evidence 字段作为唯一防线。

## 用户故事

1. 作为应用维护者，我希望声明构建使用的 Dockerfile 路径，让平台检查真实源码输入。
2. 作为 reviewer，我希望任一外部 FROM 改 digest 时立即失败，避免声明与构建输入漂移。
3. 作为 CI 维护者，我希望可变 tag、缺失文件或无法静态核验的输入都返回可搜索诊断。
4. 作为多阶段构建维护者，我希望内部 stage 引用与 scratch 不被当成外部镜像。
5. 作为使用构建变量的维护者，我希望默认值和外部 override 的区别被明确处理，避免假绿。
6. 作为非容器项目维护者，我希望原生交付继续通过原有校验，不必声明不存在的 Dockerfile。
7. 作为离线 operator，我希望校验不运行 Docker、不 pull、不访问 Registry、不执行文件内容。
8. 作为下游 lock 使用者，我希望 lock schema 和 release reader 的精确字段合同保持兼容。
9. 作为平台维护者，我希望 fixture 迁移可重放，并明确 target-candidate 与真实应用的边界。
10. 作为 reviewer，我希望静态核验结果不被误称为已构建镜像或现场部署的来源证明。

## 声明、文件根与接口

- Project declaration 新增 `dockerfiles`：非空、去重的字符串数组，每项为仓库根相对 POSIX
  文件路径。一份声明覆盖一个 delivery contract 下被该构建使用的全部 Dockerfile。
- 容器交付集合沿用现有 `CONTAINER_DELIVERY_CONTRACTS`；每个容器声明必须提供该字段。
  不以 profile slot 决定是否检查。非容器交付禁止该字段且不打开 Dockerfile。
- CLI validate/lock 新增可选 `--repo-root`。未传入时仅对直接位于 `.aisoft/` 的 project 文件
  从其父目录确定仓库根；其它布局的容器声明必须显式提供。禁止从 cwd 猜测或 glob 搜索。
  既有 `aisoft-project-check.sh --repo` 使用 `.aisoft/architecture.json`，因此无需修改脚本。
- 共用 `build_lock` 增加 keyword-only 的 `repo_root` 输入；容器声明没有可用根目录时拒绝。
  纯 JSON 的容器调用方也必须提供根目录，不保留静默跳过的兼容分支。非容器调用保持原签名可用。
- 路径拒绝 absolute、空项、`.`/`..` segment、反斜线、控制字符；解析后的文件必须位于根内。
  拒绝文件路径或目录链上的 symlink、目录、不可读文件、非 UTF-8 和过大输入（1 MiB 上限）。
  不读取凭据文件，不回显内容；diagnostic path 使用 declaration 字段或逻辑行编号。
- 不改 catalog pin、profile slot、catalog/profile revision、lock schema、release runtime 或 installer。

## FROM 核验规则

1. 解析 Dockerfile 指令，而非简单逐行 grep。接受大小写不敏感指令、空白、整行注释、CRLF、
   默认反斜线续行与 Docker `escape` directive 的反引号续行；不得把注释当作 FROM。
   directives 仅在 Docker 规定的文件头位置生效；重复/非法 escape 与任意 custom syntax frontend
   返回 `DOCKERFILE_SYNTAX_UNSUPPORTED`。标准 `docker/dockerfile:1`/稳定 `1.x` frontend 可识别，
   不支持 labs 或会改变本合同指令语义的 frontend，不访问网络加载 parser。
2. 每份 Dockerfile 至少有一个 FROM。FROM 语法仅接受可选一个 `--platform=...`、一个 image
   token 和可选 `AS stage`。重复 stage、前向/自引用、畸形语法均失败。
3. 先前命名 stage 的 FROM 引用属于内部依赖，不要求新 digest；stage 名比较遵循 Docker
   大小写不敏感语义。数字 stage 引用若不能证明符合 FROM 语义则拒绝，不当作豁免。
4. `FROM scratch` 不引用外部镜像，可通过该行检查；允许最后一层为 scratch，但一份容器声明
   至少实际引用一个声明的 OCI digest，不能以全部 scratch 绕过已有 base-image requirement。
5. 全部外部 FROM 必须为保留可读 tag 的 `image:tag@sha256:<64 lowercase hex>`。无 digest 或
   非法 digest 返回 `DOCKERFILE_DIGEST_REQUIRED`；格式正确但不在声明的 OCI digest 集合中返回
   `DOCKERFILE_DIGEST_MISMATCH`。匹配集合来自已通过 catalog pin/exception 等原有检查的声明。
6. 不要求多个 stage 使用相同 digest；每个外部 stage 都须属于已声明的 digest 集合。
   反向也检查：每个声明的 `oci-image` digest 至少被这些文件中的某个外部 FROM 引用，
   否则 `DOCKERFILE_BASE_IMAGE_UNUSED`。这样不能拿无关 OCI entry 假装满足基镜像要求。
7. 镜像 token 中出现 `$` 一律 `DOCKERFILE_FROM_VARIABLE_UNSUPPORTED`，包括全局 ARG 默认值。
   不读取环境、不展开变量、不执行 shell、不接受声明默认值代替实际 build override。
   修复方式为在外部 FROM 使用字面量 tag+digest。其它指令内的普通 ARG/ENV 不受此规则限制。
8. `--platform=$BUILDPLATFORM` 等平台变量允许，不参与 digest 展开；此结果只证明 digest identity，
   不新增 CPU/OS child-index 兼容性保证。
9. 明确支持的语法之外 fail closed，返回 `DOCKERFILE_SYNTAX_UNSUPPORTED` 或
   `DOCKERFILE_FROM_INVALID`。V1 对 heredoc 不尝试忽略内容，发现 heredoc 结构即拒绝，
   防止 payload 内的 FROM 被误识别。不能以“跳过不认识的行”吞掉无法证明的 FROM。
10. stable codes 另含 `DOCKERFILE_DECLARATION_REQUIRED`、`DOCKERFILE_DECLARATION_FORBIDDEN`、
    `DOCKERFILE_ROOT_REQUIRED`、`DOCKERFILE_PATH_INVALID`、`DOCKERFILE_READ_FAILED`、
    `DOCKERFILE_FROM_REQUIRED`。CLI exit 2、`valid: false`；lock 失败不得覆盖原输出。

## 兼容性与证据边界

- 已有容器声明必须增加路径并重新生成 declaration checksum/lock；迁移为有意 fail closed，
  不提供 bypass。仓内 valid fixtures、容器 target-candidate reference 与对应 lock 在本 Change
  同步，reference Dockerfile 明确标注 synthetic/target，不声称读取了下游真实应用源码。
- 非容器声明及 lock 的 byte identity 不变；保留 strict JSON、unknown-field、pin、exception、
  EOL 和 lock drift 硬门。lock 仍不写主机、生成时间、Dockerfile evidence 字段。
- 通过 static source check 只表示声明的这些 Dockerfile 的全部外部 FROM 与声明/catalog 一致。
  若实际 builder 选择其它 `-f`、stdin、生成文件、额外 build context 或另一份 declaration，
  必须在应用 Change/CI 中把同一构建输入绑定起来；本 Issue 不修改应用仓、不验证全部 CI 语法。
  正式制品来源仍需独立 builder provenance/attestation；不能从 `valid: true` 推导镜像已构建、
  已 pull、已部署或已现场验收。`COPY --from` 外部镜像与 RUN 下载也不属于 FROM digest 保证。

## Acceptance criteria

- [ ] AC-1：SFM #145 报告的真实 catalog Node 22 child digest fixture 通过；任一外部 FROM
  的 digest 改一个字符、换未声明 digest 或去掉 digest，都在 validate、lock、validate --lock 红。
- [ ] AC-2：多文件、多阶段外部镜像、stage 复用和 scratch 通过；遗漏任何 stage/file 的错误不能假绿。
- [ ] AC-3：镜像变量即使有 ARG 默认值也红；平台变量可通过；无默认、重复/前向 stage、
  malformed FROM、heredoc、无 FROM 均有确定诊断。
- [ ] AC-4：容器缺路径、缺 root、缺文件、越界/symlink/非法编码/超限输入均失败且不泄漏内容。
  root 不受调用 cwd 影响；读取失败无原始 exception/input 内容输出。
- [ ] AC-5：`pm2-legacy`、`embedded-sqlite/v1`、`systemd-native/v1`、`windows-iis/v1` 无误伤，
  不要求或打开 Dockerfile；非容器 lock 既有 hash/bytes 相同。
- [ ] AC-6：CLI lock 连续两次 byte-identical；失配不写/不覆盖 output；`--lock` 使用最新 Dockerfile
  核验，正确 checksum 的旧 lock 不能让错误 FROM 通过。lock schema/release reader 兼容。
- [ ] AC-7：architecture README 说明路径/root、支持语法、fail-closed 迁移与证明边界；
  所有现有 fixtures、architecture/release integration 测试和 smoke 不回退。
- [ ] AC-8：只读项目 checker 能沿现有 `.aisoft` 输入发现漂移；任何修改不改变现有 required CI context。

## 测试决策

最高 seam 使用离线 CLI subprocess 与真实临时仓库文件；相同声明只更改 Dockerfile 即核对 exit、
diagnostics 与 output 是否保留。共用 build_lock 单测证明容器库调用方不能跳过文件证据。
沿用现有 unittest、CLI 测试与 lock determinism 测试，不引入第三方 parser/daemon。
新增测试专门覆盖四种基线假绿及 parser/path 边界，不以实现内部结构作为验收。

## 治理文件明确授权与 fresh-run 顺序

本 complex spec 的启动批准只授权以下治理合同步骤：修改 project declaration schema 与
architecture README 的 Dockerfile 约束，保留 AGENTS、skills、Controller、CI/部署脚本不动。
该步骤与 runtime 独立 commit 后停止。后续 fresh run 重读 AGENTS 和本合同再实施 runtime。
用户于 2026-10-02 明确回复“确认”，该启动授权已持久化到 evidence/contract-start-authorization.json。T01 仅应用上述治理合同，commit 后停止；不在当前步骤实施 runtime。

## 已批准补充：构建输入测试入口迁移

2026-10-02 用户对完整 `root-migration-proposal.patch` 明确回复“确认”；原合同继续有效。
授权 receipt 与批准 patch 保存于 evidence。只补充以下四路径：

- `codex/tests/smoke.sh`：既有 reference validate 命令加 `--repo-root "$ROOT/architecture"`。
- `codex/tests/test-architecture-install.sh`：既有模板 validate 命令加安装 share root 参数。
- `architecture/templates/project-architecture.example.json`：新增 `dockerfiles` 路径。
- `architecture/templates/Dockerfile.example`：synthetic target Node 24 catalog digest 示例。

不修改 installer、CI workflow/context、test selection、root 规则、catalog/profile 或 lock schema。
本补充独立受控应用并提交后停止，fresh turn 再继续 runtime。shell 静态检查本步运行；
修改 shell 后真实运行 smoke，旧 runtime 尚不支持 root 参数造成的阶段性失败如实记录，
不增加临时绕过，最终 T02/T03 必须修复并重跑全部硬门。

## 风险、回滚与非目标

已有容器消费方会 fail closed，应用迁移须各自 Issue/PR，不能代改 SFM/NewEmaint。
源码回滚通过人工批准的 revert PR 恢复本 Change，并明确将重新暴露原来的源码漂移缺口；
不通过放宽诊断、伪造 fixture、重写合同或 bypass 取得 PASS。
无数据库迁移、安装、发布、部署、Secret/ACL 变更。#287 的 profile checksum 合同保持独立，
本 worktree 不改 profile，不替其它 owner rebase/清理；提交前由本 owner 对 fresh main 自行整合。

## 未决问题

无实现方向未决项；用户已批准本合同的语法范围、容器迁移和 parser 限制。
工作流 GAP：当前 broker 未提供 Matt triage 双维度 typed projector，本次不绕行直接 API，
不在 #288 顺手新增 broker 操作；平台分类与 lifecycle 使用现有 typed surface。

## 官方语义依据

已用 Context7 `/docker/docs` 核对多阶段 FROM、全局 ARG 与 build-time override 语义。
参考 [Dockerfile reference](https://docs.docker.com/reference/dockerfile/)、
[Multi-stage builds](https://docs.docker.com/build/building/multi-stage/)。
V1 对变量与 heredoc 的拒绝是本平台的保守子集决策，不是 Docker 不支持它们。

## 已批准补充：固定 release evidence 的 architecture lock pin

用户对已展示的两文件 diff 明确回复“确认”；授权 receipt 在
`evidence/boundary-amendment-authorization.json`。批准 patch SHA256 为
`a2538e14a46d6568470271edb86d0ffac0c241ff221d133efdb01815ba86aa55`，
完整 diff 保存在 `evidence/boundary-amendment-proposal.json`；本补充不替换原合同。

仅授权以下两文件的独立 T05 治理步骤：

- `codex/tests/check-release-evidence-boundary.py`：为已批准迁移的唯一 synthetic
  `architecture/reference/newemaint/target-candidate/architecture.lock.json` 增加 exact
  SHA256 pin，并纳入该 checker 当前 pin 允许范围。保持 disk/index SHA256 双核验、
  历史 baseline/evidence 与原有 runtime pins，不加入 CONTENT_EXEMPT，不接受宽松路径豁免。
  明确该 architecture pin 仅绑定 synthetic declaration/lock 输入与静态 reader 回归，
  不刷新历史 E2E、real E2E、installed 或 company-live 证据。
- `codex/runtime/tests/test_release_evidence_boundary.py`：把该 lock 加入 synthetic fixture
  与 current amendment 测试，继续逐一拒绝 disk/index 单字节篡改及历史 evidence 替换。

T05 按完整批准 patch 原样应用，检查 hash、静态真实 source identity、防篡改单测与文档，
独立本地 commit 后停止。下一轮 fresh run 重读本 spec/plan 后恢复 T03 的完整 runtime、
smoke 与后续 fresh-main/lock/release 组合验收；本步不新增 runtime 功能或修改其它治理文件。
最终 PR 提交仍未授权。回滚通过本治理 commit 的人工 revert 并重跑同一硬门，
不得删除历史 evidence 或改成覆盖性豁免。
