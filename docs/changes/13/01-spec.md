---
issue: 13
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/13
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - platform-governance
  - external-contract
  - authentication-authorization
  - cross-service
  - ci-deployment
depends_on: []
status: contract-ready
branch: change/13
pr_url:
created: 2026-07-24
updated: 2026-07-24
---

# Spec

## 目标与原因

在本地 `gitea-ci` POC 建立一个版本化、可迁移、失败关闭的 GitHub → Gitea 入站同步组件。GitHub 只提供 allowlisted `main` 候选；Gitea 重新创建不可变 sync 分支和内网 PR，重新运行 CI、重新审批。同步身份永远不能写或合并 `main`，timer 在 synthetic 与真实 POC 验收前保持 disabled。

## Acceptance criteria

- [ ] AC-1：`reconcile <profile>` 只接受安全 profile 名，要求 profile 和 token files mode 400/600，并把 state、lock、Git cache 和 worktree 按 profile 隔离。
- [ ] AC-2：GitHub credential 从 repo-scoped read-only token file 经 Git credential helper 提供；fetch 只请求 `refs/heads/main`，token 不进入 argv、stdout、stderr或持久 Git config。
- [ ] AC-3：脚本验证 40 位 GitHub SHA、last successful SHA ancestry 和 Gitea `main` 共同历史；history rewrite、无共同历史和不合法 SHA 都在任何 push/API mutation 前失败。
- [ ] AC-4：一个 GitHub SHA 对应唯一 `sync/github/<full-sha>`；同名分支异 SHA失败，禁止 force push、mirror、`main` push 和 merge API。
- [ ] AC-5：相同 SHA 重跑最多保留一个分支和一个 open PR；已有其它活跃 sync PR 时不更新它，只原子记录 `pending-sha`。
- [ ] AC-6：Gitea PR 正文记录 GitHub URL、source ref、完整 SHA、compare range/基线和“GitHub review 仅为 provenance”声明；PR base 固定 `main`。
- [ ] AC-7：Gitea token 从 600 文件经 curl stdin config 使用；日志和失败输出不包含任何 sentinel secret。
- [ ] AC-8：安装脚本可重复执行，安装 root-owned runtime/profile/systemd 模板但不创建 credential、不 enable/start timer；unit 包含 `NoNewPrivileges`、`ProtectSystem`、`ProtectHome`、读写路径收敛。
- [ ] AC-9：synthetic tests 覆盖 same SHA、new SHA、history rewrite、conflicting branch、active PR pending、API failure、main-push 静态禁令和 secret redaction。
- [ ] AC-10：真实 `newrsdesign` POC 读回 GitHub/Gitea 基线、sync identity 权限、timer disabled；在具备凭据后执行同 SHA幂等和新 SHA建 PR，任何未运行项在 verification 中保持 `NOT RUN`。

## 接口、数据与兼容性影响

Profile 示例：

```text
GITHUB_URL=https://github.com/BenQue/RSDesignNew.git
GITHUB_REF=refs/heads/main
GITHUB_TOKEN_FILE=/etc/aisoft-sync/keys/newrsdesign-github-token
GITEA_URL=http://gitea-ci.orb.local:3000
GITEA_OWNER=admin
GITEA_REPO=rsdesign-new
GITEA_GIT_URL=http://gitea-ci.orb.local:3000/admin/rsdesign-new.git
GITEA_USERNAME=aisoft-sync
GITEA_TOKEN_FILE=/etc/aisoft-sync/keys/newrsdesign-gitea-token
```

状态目录：

```text
/var/lib/aisoft-sync/<profile>/
├── lock
├── repository.git/
├── last-successful-sha
└── pending-sha
```

`last-successful-sha` 仅在幂等已合入、已存在同 SHA PR 或成功创建 PR 后原子更新；任何失败不前移。`pending-sha` 是可观察状态，不代表成功。

## 风险与回滚约束

- 首次真实 POC 前 timer 必须 inactive/disabled；只允许手工 one-shot。
- 关闭 timer、停止 service并保留 `/var/lib/aisoft-sync/<profile>` 即可停止自动化；删除 unit 或 credential 不是首选回滚。
- 已创建 sync 分支/PR作为审计证据保留，不自动删除或 force-update。
- GitHub history rewrite、Gitea branch conflict、API/网络失败一律 fail closed 并等待人处理。
- Gitea 分支保护和 bot 权限必须真实读回；脚本里的禁止字符串检查不能替代服务端拒绝测试。

## 非目标

- 不镜像 GitHub PR、审批、评论或 CI 状态。
- 不写、合并或部署 Gitea `main`。
- 不实现测试/生产应用部署、Promotion PR 或生产 credential。
- 不启用 timer，不创建长期 secret，不修改 rsdesign 应用代码。
- 不把 `newrsdesign` 硬编码为其它项目默认值。
- 普通 implementation worker 永远不得编辑本运行 governing `AGENTS.md`。

## 未决问题

无。
