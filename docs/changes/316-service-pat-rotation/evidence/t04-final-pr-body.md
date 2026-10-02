现有服务账号 bootstrap 只有创建/no-op；scope 合同变更后，缺少可测试、可恢复的显式 PAT 轮换路径。新增独立 operator-only typed 路径，先验证 manifest 固定 Mac canonical store 中的受保护候选，再以固定 Gitea 1.26.4 token-model helper 撤销 exact 旧 PAT，最后原子发布新凭据；同请求重试通过 journal 恢复或返回经验证的 no-op。

固定 Go 1.26.3 工具链和模块/model 摘要，保持现有 required CI context，增加隔离数据库、race、Linux helper 进程和交易负向测试。installed-drift 同步核对新增安装目标、generated metadata 与明确指定的独立 public provenance；source-only 不访问安装面或外部制品证据。

本地验证及受控整合证据见 mapped verification。required CI 待此 PR 上真实运行。helper/operator 安装、grant provision、真实 PAT 轮换及各消费端验收均 NOT RUN；AC-2 保持后续独立现场验收，不能从 source/CI 成功推断完成。

回滚：源码可通过受控 revert 撤销；真实 PAT 撤销不可逆，撤旧后的恢复必须使用保留的受保护候选并另行授权。

Closes #316

Final merge requires a human.
