# 公司平台只读接管基线（Issue #271）

这是独立的 `company-platform-baseline/v1` 采集与审核入口，collector 版本 `1.0.0`。
它不安装组件、不创建 evidence 目录、不启动服务、不生成现场写入授权。
原 `aisoft-company-delivery inventory` 面向 greenfield，不能代替这个入口。

本次开发侧交付状态：公司 `BLOCKED_EXTERNAL`，现场检查全部 `NOT RUN`。
没有现场连接或已批准主机指纹时，到此停止；下列检查包供已授权操作员在批准的目标执行。
不得为执行它安装 Python、提权或复制凭据。脚本必须已位于可读取的版本化 checkout 或只读介质；
如果没有这种输入，采集保持 `NOT RUN`，介质准备/现场文件放置不在本 Issue 授权内。

## 固定目标与可信输入

角色为 `scm-ci`，环境为 `company-scm-ci`。开始前由交接卡固定 source commit、collector SHA-256、
批准的主机 hostname SHA-256 和本轮 UUID。主机指纹是绑定标识，不能证明主机真实性；
操作员必须从已有可信资产清单确认目标，不能把脚本自动读出的任意主机指纹自行提升为批准。
source SHA 与 collector digest 必须从审阅过的同一个提交取得；程序验证 digest，source SHA 由交接者核对。
collector 源文件为 `codex/runtime/aisoft_company_baseline.py`，只使用 Python 3.10+ 标准库。

`evidence_id` 是用户已有审核材料目录的逻辑 UUID，输出不包含目录路径。
公司侧只显示 stdout，由用户将脱敏 JSON 带回开发侧现有 evidence 目录；公司侧不使用重定向或 tee。
`python3 -B` 禁止 bytecode 写入。退出码 20 表示 BLOCKED（可能仍有完整有效 inventory），并非需要提权重试。

第一段：在已确认的公司主机读取两个指纹（2 行）。路径请替换成已有只读介质或 checkout 中的 exact 文件。

```bash
python3 -B /APPROVED-READONLY-SOURCE/codex/runtime/aisoft_company_baseline.py identity
```

第二段：将交接卡的固定值代入，运行一次采集（8 行）。`HOST_PIN` 等大写文本是必须替换的占位符，
原样运行会 fail closed；不要用环境变量、hostname 命令或上一段结果自动填充已批准值。

```bash
python3 -B /APPROVED-READONLY-SOURCE/codex/runtime/aisoft_company_baseline.py collect \
  --environment company-scm-ci \
  --host-role scm-ci \
  --host-sha256 HOST_PIN_64_HEX \
  --source-sha SOURCE_COMMIT_40_HEX \
  --collector-sha256 COLLECTOR_DIGEST_64_HEX \
  --evidence-id APPROVED_V4_UUID
```

输出为一个 JSON envelope：`inventory`、canonical JSON `inventory_sha256`、`receipt`。
原始命令/HTTP 内容不会落盘或透传。每个失败只给固定状态，不打印 stderr/异常输入。
collector 仅运行两个 fixed service 的 enabled/active、Runner unit、固定二进制 `--version`、
两个 fixed port 的 `ss -ltn`、UFW 摘要和两个数据目录 stat/statvfs。UFW 无读取权限则 BLOCKED，禁止 sudo 重试。
不读取 unit 文件/ExecStart、app.ini、环境变量、credential path、数据内容或日志；不查询 PostgreSQL 数据库。
两个 GET 仅为 `127.0.0.1:8888/api/healthz` 和 `/api/v1/version`，不跟随 redirect、不使用认证或代理；
`/api/healthz` 的 checks 必须非空且全部 pass，避免把未完成安装页的空 checks 判为健康。
端点语义参考 [Gitea 官方 health handler](https://github.com/go-gitea/gitea/blob/v1.26.4/routers/web/healthcheck/check.go)。

第三段：仅在开发侧，对带回的脱敏 JSON 做离线验证（8 行）。重新使用同一交接卡的 pins；
不要从不可信 envelope 自动读取期望值。校验通过只表示结构、checksum、绑定与判定一致。

```bash
python3 -B codex/runtime/aisoft_company_baseline.py verify \
  --environment company-scm-ci \
  --host-role scm-ci \
  --host-sha256 HOST_PIN_64_HEX \
  --source-sha SOURCE_COMMIT_40_HEX \
  --collector-sha256 COLLECTOR_DIGEST_64_HEX \
  --evidence-id APPROVED_V4_UUID < /LOCAL-EXISTING-EVIDENCE/envelope.json
```

## 当前证据与人工补充

全部 `current` 项必需。每项 `status=PASS/GAP/BLOCKED/NOT RUN`；`basis` 明确 host-probe、
operator-reviewed 或 none。历史放在 `historical` 对象中，必须带历史 evidence digest；
历史 PASS 从不填补当前缺口。历史日期与来源保留在 digest 指向的脱敏审核记录。
采集结果当前有效期 24 小时，未来/过期/非法日期拒绝；过期后重新只读采集，不能改时间续期。

以下记录必须由操作员通过已有登录会话或已审核的运维记录确认，不能为盘点建立账号、读 Secret、
查询数据库、访问原始日志或运行临时生产命令。没有可用记录就保留 `NOT RUN`：

| 项目 | 允许回流的值与核对要求 |
|---|---|
| network | reachable/unreachable：批准内网入口本轮是否可达，独立于认证 |
| authentication / acl | available/unavailable、read-allowed/denied；不回流账号或 cookie，匿名 404 不证明对象不存在 |
| repository | 已确认 identity 的 SHA-256、公司 head SHA 与 exists；目标不存在但缺可信 refs 时保持 NOT RUN，不填虚构 SHA |
| protection | direct/force push 禁止、仅人工 merge、required CI 数量；CI 成功不等于 protection 已配置 |
| runner_registration | registered/absent/unknown；与 unit enabled/active 分开，不读取注册文件 |
| sync | 固定 timer 已审核 enabled/active 与 source/destination SHA；不读取环境或 timer 内容、不启用 timer |
| backup / isolated_restore | available/off_host、verified/isolated、相同备份集 digest；备份存在不能证明恢复成功，本轮不做备份或恢复 |
| postgresql_server_version | 审核记录中的实际 server 版本；本地二进制 --version 不能代替运行版本 |
| ufw_review | approved-networks-only/remediation-required；规则数量不能证明放行范围正确 |
| storage_ownership / service_binding | expected-service-owners/mismatch、fixed-binaries-and-data/mismatch：人工核对批准的 uid/gid、服务与固定二进制/数据关联；不在本 Issue 读取完整 unit 或配置 |

`operator-record.example.json` 仅是 schema 形状，`facts` 故意留空，没有实际 PASS。
record 必须有相同 environment/role/host/source/collector/UUID，`observed_at` 不早于采集，
且距审核时间不超过 24 小时。`evidence_sha256` 指向人工审核过的脱敏事实记录（只含上表允许字段和来源日期），
不指向原始日志、Secret 或配置。程序只保留 digest，不读取任何证据路径。

开发侧准备一个严格对象 `{"envelope": <原采集结果>, "record": <人工记录>}`；
`supplement` 命令的参数与第三段相同，将 `verify` 换为 `supplement`，stdin 改为这个对象。
只能补充上表字段，禁止覆写 host-probe。新 envelope 保留最初采集时间并重新计算 checksum。
人工补充是一项可信审核输入：digest 和本工具不验证其真实性，不构成签名或现场来源证明。

## 接管决定与 B2/B3 前置卡

| 决定 | 确定性条件 | 后续 |
|---|---|---|
| BLOCKED | 任一 current 缺失/不可采集；或健康/版本/监听/存储/UFW/访问/恢复等关键项 GAP；或恢复集不匹配 | 收集缺失只读证据，列出阻塞项，不进入现场写入 |
| adopt-with-remediation | 当前证据全部已知，只有 repo/protection/Runner/sync 项存在明确差异 | B2/B3 独立合同列整改，不自动执行 |
| adopt | 全部当前项符合固定基线，备份和恢复对应同一集合 | 仅为采用候选；仍须 B2/B3 审核与新授权 |

决定仅表示本 schema 覆盖的接管前置项，不宣称完整生产准入。接管的容量/RPO/RTO/业务 SLA 等新决策归后续合同。
`receipt.validation=PASS` 表示输入有效；`receipt.status=BLOCKED_EXTERNAL` 可以与之同时存在。
源码测试通过、schema 校验通过、历史或人工陈述均不得描述成自动验证了公司现场。

当前 B2/B3 卡：

| 字段 | 当前值 |
|---|---|
| 来源 | #268 B1 → #271；#270 可并行，后续 mutation 依赖其已合并 exact platform pin |
| 环境/角色 | company-scm-ci / scm-ci；批准 host pin 尚未取得 |
| source / collector / evidence | 本地最终提交与 digest 见交接回执；本轮公司 UUID/目录由用户已有 evidence 机制固定 |
| current / 历史 | current 全部 NOT RUN；历史 1.26.4/18.4/8888/55432 仅为目标线索，不导入 current |
| 基线结论 | BLOCKED；没有可采纳的公司 current inventory |
| B2 输入 | 可信 host/版本/健康/权限/备份及隔离恢复记录、差异清单、审批人 |
| B3 输入 | B2 基线、公司 repo/protection/Runner/sync 当前记录、#270 已合并 pin 与所选组件清单 |
| mutation grant | false；reinstall/upgrade/部署/清理未选择、未执行 |
| PR 状态 | 本地验证后 AWAITING_PR_CONFIRMATION；manual；不 push/建 PR/merge |

## 复跑与验证

已有版本化 collector 的现场重复只读采集由用户按同一 pin 独立运行两次；每次使用不同 UUID，
比较状态事实时排除时间/UUID/剩余容量的自然变化。没有真实回流前两次现场执行均为 NOT RUN。
本地 mock 证明相同注入状态的两次结果一致与固定探针边界，不能证明现场文件 atime、系统审计或服务自身日志不变。
“零写入”指 collector 不执行文件/配置/服务 mutation；系统正常处理只读请求的附带审计不在 collector 控制内。

本地运行 `PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests -p 'test_company_baseline.py'`。
负向测试覆盖未知字段、重复键、敏感哨兵、错 pin、过期/历史证据、状态伪造、checksum 篡改、
超限输出、权限失败、redirect、未安装 health 与恢复集合不一致。schema 从同一实现的 `schema` 命令导出。
源码可普通 revert；现场没有本工具引入的状态需要回滚。
