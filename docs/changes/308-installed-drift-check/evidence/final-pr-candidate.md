# #308 唯一最终 PR 候选（尚未提交）

Branch：`change/308-installed-drift-check`；base：`main`；policy：`manual`。

拟定标题：`platform: add read-only drift checks for eight installer surfaces (#308)`。

## 拟定正文

新增拒绝条件或模块已合并、安装副本仍陈旧时，原来的安装日志不会主动显示差异。本变更新增 `bash codex/tools/check-installed-drift.sh`：逐个核对八个 installer 的受管文件字节、存在/类型、声明链接和既有可读量，即使计数相同也能定位缺模块或旧实现；检查过程无凭据、网络、安装或写入。

smoke 只执行 source-only 自洽性门和真实 installer 的隔离 fixture。source-only 允许合法待合并的受管源码变化，同时独立输出 cached main 差异和 freshness 限定；installed 模式仍严格检查来源与目标。

验证：23 项 fixture 用例通过；bash -n/ShellCheck/文档与归属检查通过；完整 smoke 的最终结果见映射 verification 与 `t04-local-validation.json`。默认 host 环境的 registry-preflight fixture FAIL 已保留，未修改其它 Issue。两轴审查均无未关闭发现。

两台真实只读检查已运行：source 与此次 broker fresh main `11c0410d3878d5449fa61796f174ba3d2dd5e59c` 的受管字节一致；installed 仍 GAP，broker 两台均 PASS。Mac/VM runtime 缺模块、skills 字节漂移、architecture/release/sync 默认面缺失；Mac `/etc` 父链接依原严格合同也报 GAP。完整 roots/差异在 `t04-mac-installed.json` 与 `t04-gitea-ci-installed.json`。

原 AC-2「Mac 全 PASS」仍未通过。提交 PR 只用于审阅，不是全部验收完成；该缺口未解决或未获明确验收合同修订前不应合并关闭本 Issue，不标 completed，不归档。实际安装、适用性/链接例外、凭据、合并和部署均未由本合同授权。

Closes #308

## 提交边界

该文件仅是 reviewable 草稿；没有 push/PR/CI。必须取得绑定 exact #308、上述 branch 与 manual policy 的提交确认后，才通过 installed broker 提交唯一 PR。确认可继续范围内 CI 修复；required CI 全绿后停在人工 review/merge，AC-2 缺口仍不得省略。runtime 已测 HEAD 和最终 docs-only 候选 HEAD 分别保存，不把阶段前测试冒充 CI。
