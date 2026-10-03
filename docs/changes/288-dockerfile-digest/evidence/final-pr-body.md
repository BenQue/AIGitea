现有 architecture 校验只读取 JSON：Dockerfile 的 FROM 改成错误 digest、可变 tag 或文件缺失，仍可能返回 valid=true。本变更在共用 build_lock 加入离线 Dockerfile 硬门，让 validate、lock、validate --lock 和现有只读项目 checker 发现实际声明源码漂移。

- 容器必须声明完整 dockerfiles 路径；显式 --repo-root 或直接 .aisoft 父目录推导，路径/symlink/读取/变量/未知语法 fail closed，不执行 Docker、不联网。
- 检查每个外部 FROM 的字面量 tag+sha256 与已校验 OCI 声明双向一致；支持内部 stage/scratch。失败 exit 2，lock 不创建或覆盖输出。
- 保留已合入 #287 的默认 V2 writer、严格 V1/V2 architecture reader 和 V1-only release reader。非容器四合同 × 两版本的八组 canonical bytes 与 pinned main 相同。
- 已批准 T04 root 输入迁移、T05 exact synthetic lock pin、防篡改单测及 T06 隔离 fixture 基线；真实 installed checker 与硬门不变。

本地验证（source head 69d5ad511dd9620f2f3865e6439773b2c1744d1f；pinned main 65268ee5f1e622c486fd9e354dd35e20a2900f91）：完整受控 host smoke PASS，含 fixture 23 tests / 47.297s 与 runtime 1008 tests / 109.408s。bash -n、ShellCheck、文档、approved/onboarding/protection、唯一 PR 与 exact #288 分类 projected 读回通过。Spec findings 0；Standards hard violations 0，保留批准 patch 的非阻塞复制代码建议 1。

历史失败及各治理停止 receipt 保留，最新完整日志/hash 与验收映射见 [verification](http://gitea-ci.orb.local:3000/admin/aisoft-platform/src/branch/change%2F288-dockerfile-digest/docs/changes/288-dockerfile-digest/verification-dockerfile-digest-261002.md)。合同文件：[summary](docs/changes/288-dockerfile-digest/summary-dockerfile-digest-261002.md)、[spec](http://gitea-ci.orb.local:3000/admin/aisoft-platform/src/branch/change%2F288-dockerfile-digest/docs/changes/288-dockerfile-digest/spec-dockerfile-digest-261002.md)、[plan](http://gitea-ci.orb.local:3000/admin/aisoft-platform/src/branch/change%2F288-dockerfile-digest/docs/changes/288-dockerfile-digest/plan-dockerfile-digest-261002.md)。

required CI 待此唯一 PR 实际运行。真实应用迁移、全局安装、制品构建/provenance、现场与部署均 NOT RUN；synthetic fixtures/临时安装回归不证明这些结果。现有容器调用方需补齐路径并重建 lock，本仓仅迁移参考输入。无数据库迁移。Policy manual，人工审核合并；回滚为人工 revert 本 PR 后运行相同回归，旧源码漂移盲点将恢复。

Closes #288
