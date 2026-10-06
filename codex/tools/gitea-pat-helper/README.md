# #316 固定版本 PAT model helper

本目录提供 #316 已合并的固定版本 helper 源码、构建入口与隔离验证。源码随 [PR #332](http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/332) 于 2026-10-03 进入稳定 main；安装与真实 PAT 轮换由独立 [#333](http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/333) 现场合同验收，源码合并不证明现场动作已执行。

依赖固定 `code.gitea.io/gitea v1.26.4`、Go `1.26.3`；`build-lock.json` 保存官方工具链归档 SHA-256、module sum 与 token model 文件摘要。`go.mod/go.sum` 固定实际依赖图，上游 compatibility replacements 显式保留。构建工具先核对官方归档摘要，再逐文件核对实际 GOROOT（拒绝额外文件与 symlink），将归档和 tree 摘要写入 provenance；随后核对 exact pin、module bytes 和 `go mod verify`，运行真实 SQLite model 测试后生成 binary SHA-256、source hashes 与 Go build info 回执。Mac 构建只证明该平台的源码/隔离 DB 行为；Linux 制品与 CI 的 T04 验证见 [#316 verification](../../../docs/changes/316-service-pat-rotation/verification-service-pat-rotation-261002.md)，不能由 Mac 结果推导。

本地构建使用负责人已有或独立临时目录中的官方摘要验证工具链；不安装全局 Go：

```text
python3 build.py --go <固定 Go 1.26.3 的绝对路径> --toolchain-archive <同版本官方归档路径> --output <本地制品路径>
```

运行入口仅接受有界 stdin JSON，包含 `action=inspect|revoke`、`project_id`、`token_kind`、PAT 与可选的 exact token ID/UID/name。PAT 不进入 argv；revoke 必须带三个 exact binding。未知、重复或多文档输入拒绝。账号由 root-owned canonical governance/access manifests 解析，不能传 username、URL、SQL 或配置路径。`--version` 只输出公开构建元数据。

实际运行只接受 Linux 的现有 `git` service user、固定 `/usr/local/bin/gitea` 版本和固定 `/etc/gitea/app.ini`。它只初始化 engine、不执行 migrations/Sync，不签发 PAT，不修改账号/权限/协作者/分支保护。授权 grant、ownership markers、protected stdin transport、HTTP 401 复验与完整交易恢复由 T03 的独立 operator 路径完成；helper 不是 Agent 通用数据库入口。

核心流程在上游 `db.WithTx` 中按 raw PAT 查找 exact salted hash，验证 UID 对应账号精确、active、non-admin、非 organization，拒绝多个 salt/hash match，核验 token name 与 ID/UID，调用 `DeleteAccessTokenByID(ID,UID)`，在 transaction 内和 commit 后分别读回 ID 不存在。返回受控元数据或固定错误码，禁止输出上游 Error()/panic、hash、salt 或 PAT。旧 scope 可与新 policy 不同，`inspect` 只返回 model 规范化后的集合；候选必须符合当前 manifest，由 operator 复验。

隔离测试创建本地临时 SQLite DB 与 synthetic PAT，覆盖精确删除、其它 PAT/账号保留、inspect 零删除、错用户/管理员/组织/停用/版本/ID/UID/name/project/kind/未知/歧义 token 拒绝、严格 stdin schema、manifest 目标绑定、构建替换拒绝、真实 driver error 与 Secret canary 脱敏。临时 DB 不包含现场 Secret。

源码 revert 只能撤销 helper 源码，不能恢复已撤销 PAT。installed/live 状态由 #333 的实际回执确认，本次文档同步未重新核对；只在对应独立授权下安装和使用。

版本事实源：[Gitea v1.26.4 token model](https://github.com/go-gitea/gitea/blob/v1.26.4/models/auth/access_token.go)、[上游 go.mod](https://github.com/go-gitea/gitea/blob/v1.26.4/go.mod)、[Go 官方归档](https://go.dev/dl/)。
