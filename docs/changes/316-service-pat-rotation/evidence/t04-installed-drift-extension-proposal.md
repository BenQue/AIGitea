# #316 T04 installed-drift 范围补充提案（待确认，未生效）

## 已读回事实

- 实现 head：`4643c3826ca6bcede5a5e81930debfcd8df0c9c8`；branch：`change/316-service-pat-rotation`。
- fresh main：`70baa3588c0504e5d81facd99c63b74741967967`；无冲突组合 tree：`675692cda5a6fb778a460d683d84f755b132dc49`。组合只在隔离 lab 测试，未改写本票 branch/history。
- 默认 `C.UTF-8` 环境的组合 smoke 退出 2：`installer-mapping-stale`。日志：`/private/tmp/issue-316-build/t04-fresh-main-default-smoke.log`。闸门来自 #308，#288 是另一个 Dockerfile digest 修复。
- broker installer 当前 SHA-256：`72df0ff5540ab1bc2a6c9a10924fdd87d8854f7fc99eb35fbaa2db62039502f2`；mapper 仍固定旧摘要 `685fc3eae15dbcbe1658c5bad9d926f39fd4985f67590a9b51fee38204b193a9`。
- 缺少新 rotate 脚本、生成的 source metadata、可选 helper 三项映射。仅更新 installer 指纹会掩盖遗漏，不是有效修复。

## 建议新增的精确授权

在本票 complex spec/plan 补充 T04A（仅治理文档、本地提交后停止）与 T04B（fresh run 实施）。保留原启动批准及 T01–T04 已执行证据，不把提案当已批准合同。

T04B 只允许修改：

1. `codex/tools/check-installed-drift.py`：仅补 #316 broker 安装面的映射、非 Secret generated metadata/制品比较规则和下述可选证据参数。
2. `codex/tests/fixtures/installed-drift/test-installed-drift.py`：对应真实 installer 的隔离 fixture、负向和零写入验证。
3. 本票 mapped summary/spec/plan/verification 及本票脱敏 evidence。

不需要修改 AGENTS、skills、Controller、其它 Issue 文档、installer、CI workflow、manifest、sudoers 或真实安装面。既有 smoke 已接入 drift suite，无需新增跳过或弱化门。回滚采用后续受控 PR revert 这两个源码文件及本票文档；checker 本身零写入，无安装回滚步骤。

## 建议比较政策

| 安装面 | 规则 |
|---|---|
| `/usr/local/libexec/aisoft/rotate-gitea-service-account` | 按对应 `.sh` 源码字节核对；缺失、旧字节、链接或异常类型报 GAP |
| `/usr/local/share/aisoft/credential-rotation-source.json` | 独立标准库 verifier；严格 schema/重复键拒绝；固定四个 files 键从源码映射推导，不跟随 JSON 提供的路径；依据 checker 的本地源码及缓存 origin/main 核对声明源码 SHA、merged-main 状态、源码与安装文件摘要；缓存 ancestry 不证明远端 freshness；不执行 installer，不 import 轮换 runtime |
| metadata 的 `helper: null` | 普通 broker 可以通过，明确 `LOCAL_HELPER_NOT_DECLARED`、`rotation=NOT_ASSESSED`；installer 未选择 helper 时可以保留旧 binary，该文件不得被报告为已验证 helper，checker 不读取其内容。Mac 本机可无 Linux helper 而使用 VM helper，不能据此判断整个轮换不可用 |
| metadata 的非 null helper | 必须有独立非 Secret build provenance，严格绑定固定 Gitea 1.26.4/Go1.26.3、Linux 架构、clean source commit、Go 源码/go.mod/go.sum/build-lock 输入及 binary 摘要；只比较固定 libexec binary，不执行 `--version`；证据缺失或不等报 GAP，不能信 installed receipt 自报 hash 就报告制品有效 |

建议新增可选 CLI 参数 `--pat-helper-provenance ABSOLUTE_PUBLIC_PROVENANCE`，仅接受明确指定的公开构建证据文件 `gitea-pat-helper.provenance.json`。不从 installed JSON/env 派生证据路径；参数的词法绝对路径在回执标明；source-only 不 stat、不 resolve 或解引用外部证据路径。这是 checker CLI/验收合同的新增，只用于只读比较，不授予安装或运行 helper。缺参数而已选择 helper 时返回 GAP；显式提供 helper 证据但安装 metadata 尚未选择 helper 也返回 GAP。仅输出校验结果与摘要，不输出 build_info/未知值，不跟随 provenance 的 Dir/路径。此比较仅证明与指定外部 build receipt 一致，不能证明签名可信 release；制品证据本身的签发/审批不由 drift checker证明。

保留恰好八个 installer、退出码 0/1/2、source/installed 分层与原有 source identity 硬门。`--source-only` 只检查映射定义与仓库 SOURCE 输入，即使给出新参数也不 stat/read/resolve 外部制品证据，绝不 stat/read target metadata 或 helper；不能输出 installed/helper PASS。source identity 必须纳入新增生成/制品验证输入，避免遗漏 helper Go/mod/sum/lock/build 定义。

## 验证与停止边界

- 真实 installer 在同一独立 fixture_source baseline 安装，避免 generated source SHA 来自另一个 HEAD。
- rotate 缺失/同长度旧字节；metadata 缺失/坏 JSON/重复键/额外字段/错 SHA/错固定键和摘要；helper 缺失/错摘要/错 provenance、model/toolchain/platform/dirty source；各项恢复后回到预期结果；provenance 路径本身及父目录的 symlink/FIFO/异常类型不得读取。
- `helper:null` 加遗留 binary 必须真实反映未选择政策；metadata 自选 path/Secret 字段拒绝，输出无 synthetic canary。
- metadata/helper symlink、FIFO、parent 替换均不读取 Secret。source-only 使用 read/stat spy 证明零 target 访问；installed 模式禁止 installer/helper/sudo/network/修复调用，文件树前后相等且无 temp/cache/pyc。
- 映射和 acceptance fixtures 同步通过后才更新 installer 指纹；重跑 source-only、drift fixture、默认 locale fresh-main 组合完整 smoke 及双轴复审。
- 不 rebase/merge/change branch。Controller 的 fresh-main 基线整合仍须走它的受控流程；本提案不授权绕过 `BASE_BRANCH_STALE`。required CI 在获得唯一 manual PR 提交确认后真实运行。
- helper 安装、operator grant provision、PAT 轮换、消费端副本清理和 live AC-2 仍为 NOT RUN，不继承 #313/#308 的安装批准。

## 确认要求的来源

#316 当前 spec 的 source touch points 未列上述共享 checker；`gitea-implement-change/SKILL.md` 第 5 条要求受保护文件只能在 complex spec 明确列出 exact 文件及变更/验证/回滚授权后修改，第 2 条要求新 material 决策不能猜测。两轴只读复审均建议先补精确治理合同；本提案尚未修改 mapper 或其 fixture，也不改变已批准的 Secret custody 方案 A。
