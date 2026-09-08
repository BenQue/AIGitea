# 只读诊断包 · Issue #278

`company-platform-baseline-diagnostics/v1` 是独立说明性 evidence。`receipt.validation=PASS` 仅表示结构、checksum、pins 与判定一致；观察状态 PASS 不代表 baseline adopt、UFW 网段获批或公司部署完成。`mutation_authorized=false` 固定不变。

## 开发侧准备与审阅

在已审核的 exact platform commit checkout 中运行 builder。`--source-sha` 必须是完整 40 位 SHA，`origin` 必须绑定 AISoftPlatform canonical remote；collector 与 builder 本地字节须等于该 commit。源文件通过 Git blob identity 复核后 materialize，绝不复制 dirty collector/schema/docs。profile 来自项目已审核 canonical `baseline-profile.json`；其独立预期 SHA-256 必须匹配，平台不保存项目值。

```text
python3 -I -S -B company-delivery/baseline/prepare-diagnostics-bundle.py build \
  --repo /APPROVED-PLATFORM-CHECKOUT --source-sha PLATFORM_COMMIT_40_HEX \
  --profile /APPROVED-PROJECT/baseline-profile.json --profile-sha256 PROFILE_PIN_64_HEX \
  --output /NEW-LOCAL-REVIEW-DIRECTORY
```

将 `build` 换成 `verify` 并使用相同参数，独立回读 bundle。目录必须为新建 `0700`，六个文件均为 `0600`：collector、diagnostics schema、profile schema、本文、profile、manifest。manifest 固定前五个 payload 的 SHA-256、大小与 mode；manifest 自身摘要由 builder 回执单独给出，交接卡独立保存，避免自引用。拒绝已有目录、symlink、额外文件、mode、内容、profile、source object 漂移。失败遗留的本地候选保留供审阅，不自动覆盖或删除。

该 builder 只在开发侧运行；bundle 不包含 builder、凭据、现场 evidence 或安装/服务变更脚本。生成 review bundle 不授予拷贝或现场执行权限。source 回滚使用最终 PR revert；没有现场状态回滚。

## 另行授权后才可使用的现场接口

本 Issue 不拷贝到公司、不执行以下命令。未来交接必须固定可信主机、角色、环境、exact source SHA、collector/profile digest、原 baseline evidence v4 UUID 和一个不同的新 diagnostic v4 UUID。host pin 是绑定标识，不是身份认证证明；source SHA 由审核者从上述 bundle 独立确认，不能从不可信回执反推预期值。

```text
python3 -I -S -B /APPROVED-BUNDLE/aisoft_company_baseline_diagnostics_v1.py identity
python3 -I -S -B /APPROVED-BUNDLE/aisoft_company_baseline_diagnostics_v1.py collect \
  --environment company-scm-ci --host-role scm-ci \
  --host-sha256 HOST_PIN_64_HEX --source-sha PLATFORM_COMMIT_40_HEX \
  --collector-sha256 COLLECTOR_PIN_64_HEX --profile-sha256 PROFILE_PIN_64_HEX \
  --baseline-evidence-id ORIGINAL_BASELINE_V4_UUID --evidence-id FRESH_DIAGNOSTIC_V4_UUID
```

由现场操作员另行取得批准身份；collector 不调用 sudo、不尝试提权。固定 argv 只有 `systemctl show aisoft-gitea.service --property=LoadState,ActiveState,SubState,Result,MainPID,ExecMainStatus` 与 `/usr/sbin/ufw status verbose`；stdin/stderr 丢弃，环境固定，timeout 4 秒，stdout 上限 65536 bytes。`MainPID` 只输出 yes/no，退出状态限 0–255，未知字段/状态均 BLOCKED。

固定 `/etc/aisoft/gitea/app.ini` 必须为 non-symlink regular file、group/other 不可写且至多 65536 bytes。仅识别 `[server]` 的 `PROTOCOL`、`HTTP_ADDR`、`HTTP_PORT`，不插值，不采用默认值，不回显任何 key/value；输出四个 yes/no。缺失字段或不匹配是 GAP，文件/格式/权限不可用为 BLOCKED。

UFW 仅返回 active、default-deny-incoming 与规则数量。空 stdout、权限失败、缺失必需元数据、未知行或输出超限返回 BLOCKED 与 null；不可据此推断 inactive 或零规则。已知 inactive 是 GAP。规则数量不能证明允许网段正确，owner review 仍是独立事项。

输出只到 stdout，现场不使用重定向或 tee。collector 无 shell、HTTP、SQL、日志、目录扫描、environment 或 service mutation 入口。读取配置时只投影允许字段，不持久化或输出任何其他内容。系统对只读访问附带的 atime/审计不由程序控制。

## 开发侧验证回传 evidence

使用同一交接卡全部 pins，将 `collect` 换为 `verify`，在开发侧用 stdin 传入 envelope。verify 不运行主机探针、不打开现场配置，且无需相邻 profile；回执不包含 profile 原值。时间窗口为 24 小时，未来或过期、parent UUID、诊断 UUID、host/source/collector/profile 漂移、额外字段、checksum 或状态伪造均拒绝。退出码 20 表示 BLOCKED，零表示验证成功（可能仍有 GAP）。

诊断 envelope 不补写 baseline、不覆盖 #79 旧 evidence、不授权 repin、安装、重启、改防火墙、连接数据库或注册 Runner。公司 installed/live 固定 `NOT RUN`，后续采用由项目独立合同决定。
