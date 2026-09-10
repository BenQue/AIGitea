# Diagnostics v2 只读证据

仅准备 source/local 离线包。公司拷贝、管理员执行和整改需各自授权；
包、源码、CI 或 schema PASS 都不代表现场策略 PASS。

## 版本与失败原因

入口为 aisoft_company_baseline_diagnostics_v2.py，contract 为
company-platform-baseline-diagnostics/v2，collector 2.0.0。v1 入口、schema、builder 和 guide
保持原字节；按交接卡显式选择版本，不转换旧 envelope，不改写旧 checksum。

协议只比较固定配置文件中的显式字段：protocol_state 为 missing/http/other。
注释或缺失为 missing；其它显式值为 other；仅 http 字面值为 http。missing/other 是 GAP，
不采用默认值，不证明进程生效配置或实际网络协议。地址/端口只输出匹配 yes/no。

失败 reason：command-unavailable、command-failed、timeout、output-limit、decode-failed、
parse-failed、config-unavailable。失败均为 BLOCKED/null；observed 携带规范化事实并判 PASS/GAP。
command-failed 不等于权限不足；parse-failed 不等于防火墙故障。stderr 与异常正文从不输出。
UFW 未知行保持 BLOCKED，不跳过或推定默认策略；规则数量不证明批准网段正确。

## 开发侧生成与验证

使用已审阅 exact platform commit 及其相同字节 builder/collector，profile 由采用项目提供，
builder 从 Git object materialize；不得使用漂移工作树、HEAD 或 tag 代替固定 source SHA。

```text
python3 -I -S -B company-delivery/baseline/prepare-diagnostics-v2-bundle.py build \
  --repo /EXACT-PLATFORM-CHECKOUT --source-sha EXACT_COMMIT_40_HEX \
  --profile /APPROVED/baseline-profile.json --profile-sha256 PROFILE_PIN_64_HEX \
  --output /NEW-ABSOLUTE-REVIEW-DIRECTORY
```

将 build 换为 verify，用相同参数回读。六文件：v2 collector、diagnostics-v2.schema.json、
profile-v1.schema.json、DIAGNOSTICS-V2.md、baseline-profile.json、manifest.json。
目录 0700、文件 0600；拒绝已有目录、额外文件、symlink、mode/hash/source 漂移。
manifest 的独立 SHA-256 从 builder receipt 记录，不能自引用。
本地未合并 candidate 仅用于 review/test，不能作为现场发布制品。

## 现场接口（本票不执行）

现场管理员先核验完整包的 independent pins、owner、父目录与可写边界；不得盲目用 sudo
运行其它用户可修改的脚本或 profile。管理员身份和文件所有权变更需要项目独立授权。
collector 自身不调用 sudo，不修改权限。选择已审核 staging 后，仅批准的操作员运行：

```text
python3 -I -S -B /APPROVED-BUNDLE/aisoft_company_baseline_diagnostics_v2.py identity
python3 -I -S -B /APPROVED-BUNDLE/aisoft_company_baseline_diagnostics_v2.py collect \
  --environment company-scm-ci --host-role scm-ci \
  --host-sha256 HOST_PIN_64_HEX --source-sha SOURCE_PIN_40_HEX \
  --collector-sha256 COLLECTOR_PIN_64_HEX --profile-sha256 PROFILE_PIN_64_HEX \
  --baseline-evidence-id BASELINE_V4_UUID --evidence-id DIFFERENT_FRESH_V4_UUID
```

仅允许固定 systemctl show 属性与 ufw status verbose，固定 C locale、4 秒总期限、
65536 bytes stdout 上限；stdin/stderr 丢弃。配置只读固定 /etc/aisoft/gitea/app.ini，
拒绝 symlink、非普通文件、group/other writable 与超限。无 shell、HTTP、SQL、日志或环境读取。
不使用 redirect/tee，不回传配置、日志、UFW 原始规则或凭据。所有回执 mutation_authorized=false。

## 离线 verify

开发侧以同一交接卡独立 pins，将 collect 换成 verify，经 stdin 输入 envelope。
verify 不运行探针、不读取现场配置或相邻 profile；校验 24 小时时窗、UUID、全部 pins、
schema、reason/value/status 与 checksum。拒绝 v1 与未知版本。
退出 20 可表示有效 BLOCKED evidence；0 仍可能含 GAP，均不授权整改或采用 baseline。
