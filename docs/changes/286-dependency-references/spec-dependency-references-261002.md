---
issue: 286
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/286
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - shared-core
  - external-contract
  - authorization
  - platform-governance
depends_on: []
status: approved
branch: change/286-dependency-references
created: 2026-10-02
updated: 2026-10-03
---

# #286 · 仓库限定依赖合同

## 目标与原因

跨仓依赖必须带仓库身份，并按 manifest 中批准的 exact 目标读取；本仓同号终态不能满足外仓
依赖。用户已批准推荐 A。本合同的 A1–A7 使用 AC-1–AC-7 作为平台验收映射编号。

## Acceptance criteria

- [x] AC-1（A1）：旧正整数、缺省、空列表的现有合同与测试不回退，旧数字明确只查本仓。

- [x] AC-2（A2）：本仓 #284 closed+completed、目标仓 #284 open 的 collision fixture 必须阻塞；
  读取请求指向目标仓，不能以源仓同号代替。目标仓 closed+completed/deployed 后才满足。

- [x] AC-3（A3）：allowed source→target 成功；未知 target、未授权边、URL、host、路径、bool、
  零/负数、错误格式、自依赖与 canonical 重复 fail closed，越界 request 次数为零。

- [x] AC-4（A4）：外仓返回 PR、错误仓库/编号、404、403、transport/invalid JSON 等失败均阻塞，
  不出现 READY_FOR_REVIEW/AUTO_MERGED；routine merge POST 次数为零。

- [x] AC-5（A5）：Controller 与 routine broker 对同一组依赖 fixture 给出一致终态；拒绝 project-agent、
  routine merger、admin/mutation credential 外仓 fallback。两个 host adapter 覆盖相同输入。

- [x] AC-6（A6）：跨仓阻塞及解锁过程中 provider/PR 各只创建一次；state、comment、PR body 显示正确
  canonical reference，重启/轮询不丢依赖。

- [x] AC-7（A7）：03/04、模板、Codex/Claude skill 源与 relevant broker 合同示例一致；全量 runtime、
  `bash codex/tests/smoke.sh` 通过。涉及 shell 时 bash -n 与可用 ShellCheck 通过。

## 接口、数据与兼容性影响


### 目标、接口与兼容

1. depends_on 可混合旧正整数和严格 `owner/repo#N` scalar。仅支持同一个 manifest-fixed
   Gitea host 的 Issue，不支持 URL、跨 host、任意 object、路径跳转或动态 owner/repo。
   schema 保持现有受限 front matter parser；无需导入通用 YAML object 解析器。
2. 旧整数及当前已支持的数字 scalar 继续只表示源仓 Issue。不得从标题、正文、评论或
   数字碰撞推断目标仓。模板和两个 provider 的 skill 必须把这个边界写在示例旁。
3. 限定形式的 owner/repo 必须精确匹配 canonical manifest，N 为正十进制整数；错误形式、
   未治理仓库、未允许 source→target 边均拒绝。大小写/别名不隐式 fallback。
4. canonical identity 是 (manifest repository identity, Issue number)。本仓整数与本仓限定
   引用若重复则报重复；本仓自依赖拒绝，外仓同号不是自依赖。保留声明顺序。
5. runtime 使用来自 trusted project binding 的源仓身份，不能把 summary.gitea_url 当作
   routing 或凭据选择依据。离线文档检查只做语法/可离线验证部分，不能冒充 live ACL 验证。

### 只读权限与 resolver 合同

6. 新 typed dependency read 仅接受 reference scalar，源 project 由既有 --project 绑定；
   reference 必须先通过 manifest 中显式 dependency_read_targets 的 exact 映射，才能构造
   request。不给既有 issue.read 增加任意 owner/repo 或 URL 参数。
7. 所有项目缺省只允许本仓。唯一新增跨仓边为 sfm-digital-board → aisoft-platform，
   对应 admin/SFMDigitalBoard → admin/aisoft-platform。LocalWMS、NewEMaint 等不顺带启用。
   approval 只允许 source 合同与实现，不 provision credential、不扩 collaborator ACL、
   不安装、不 live apply。以后增加其它边须独立治理变更。
8. 外仓读取由 broker 内部 manager-audit 只读路由完成，不能把 source project-agent 或
   routine merger credential 用到外仓；凭据不出 broker，无 admin/mutation-token fallback。
   返回仅含 canonical repository identity、number、state、labels 和可诊断 reference，
   无 Issue 正文、credential、header。必须核回 repository/number 并拒绝 PR 响应。
9. Controller 和 routine merger 共用 dependency identity/终态规则与受控读取边界。
   本仓保留现有读取与兼容行为；外仓统一经上述 resolver，禁止新建任意跨仓 GiteaClient。
   Mac 与 VM adapter 都要有确定性可验证接入；若 VM 无受控依赖读取 surface，启动时
   BLOCKED_EXTERNAL，不能 direct API/fallback。安装与服务启用不属于本票 source 交付。
10. open、closed 但没有 completed/deployed 的依赖未满足；全部 closed 且有终态才满足。
    网络/认证/ACL/404/JSON/identity 错误均不视作满足；未授权或格式错误返回
    NEEDS_HUMAN_DECISION，已授权读取不可达返回 BLOCKED_EXTERNAL。routine 一律零 merge POST。
11. PR 就绪与 merge receipt 中保留仓库限定引用。awaiting_dependencies 轮询不再次调用
    provider、不新建 PR；权限或 schema 漂移不能抹掉旧依赖后继续。


### 错误与状态边界

Schema/未治理目标/未授权边失败 → NEEDS_HUMAN_DECISION，零越界 GET；已授权但不可读
→ BLOCKED_EXTERNAL，不把 404/ACL/transport failure 当满足。依赖非终态 → awaiting_dependencies。
全部可验证依赖终态且 CI 通过 → manual READY_FOR_REVIEW，routine 仍须其它 final-head 硬门。

## 治理步骤与明确修改授权

T01（G01）仅授权 README、03、04、skill-for-codex/references/private-gitea-access.md、
Codex/Claude issue-session-flow skill 源、summary 模板、其必须同步的 codex/config/change-template-sync.json digest 与本票四份映射文档。该独立步骤完成后
停止；后续 fresh run 重读这些文档、现行 AGENTS.md 及已批准合同再实施 runtime。

T02–T04 明确授权 aisoft_loop 的 contract/依赖 resolver、controller、gitea 与 CLI/状态展示
适配，aisoft_host_access 的 contract/broker/CLI 及 exact host-access manifest，相关 runtime
和 smoke 测试、必要依赖读取 adapter 与合同内模板/skill 同步。新模块限于该依赖功能。
不在 T01 写新增 executable manifest 字段，避免在 parser 仍为旧版本时造成未知 schema。

## 风险与回滚约束

未来 dependency_read_targets 是 source 项目上的 explicit target project id 列表；缺省只允许
本仓。源与目标都必须来自 canonical manifest，唯一新增边为 sfm-digital-board→aisoft-platform。
manager-audit 仅在 broker 内只读使用；零 admin/mutation-token/project-agent/routine fallback。
Mac/VM adapter 可达性需测试，installed/live 仍要独立安装授权与验收。

人工 revert 本票 source PR 可恢复旧本仓依赖实现。新增 qualified 文档在旧 runtime 应报错，
不能降成数字或清空依赖求绿。未来安装后回滚另行验收；本轮 source 文档不改变 installed/live。

## 非目标

不得修改 AGENTS.md；不得改变 #289 required_docs 或 documents 存在性算法；不得处理其它
Issue、开启跨 host、扩大其它 source→target 边、扩 collaborator ACL、provision credentials、
安装 global skills、live apply、merge 或部署。本票不追溯重写 SFM #142 的历史依赖声明。

## 未决问题

无。2026-10-02 用户确认推荐 A、A1–A7 及启动边界；旧部署调度前置由本次授权覆盖，
未取得部署成功证据的事实保留。runtime 具体代码组织是合同内实现选择，不准改变只读身份边界。
