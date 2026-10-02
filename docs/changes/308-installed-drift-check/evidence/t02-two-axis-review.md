# T02 两轴只读审查

固定点为已批准 plan 的 T01 提交 `df17985fa4911475fcca7e6d06baec3923a55211`；初审候选为 `dfa7fa1db43f1143cd5c1c72aa1def9ab8c0095d`。两个 code-review subagents 只读取本 worktree，不访问真实 installed 或 remote，不写文件。修订后分别复审未提交差异。测试由主会话执行并另行留证。

## Standards

初审发现 1 项 P2 硬边界问题：父目录 lstat 与完整路径 open 之间存在竞态，`O_NOFOLLOW` 只限制最终分量。引用 `06-运维手册与踩坑集.md` 的零写入/不读取 Secret 与链接边界。smell 发现 0 项。

修复：以 `parent_descriptor` 从边界目录 fd 开始逐级 `O_DIRECTORY | O_NOFOLLOW`；stat/read/list/readlink 通过 dir_fd 锚定。fixture 在检查后、打开前确定性替换父目录，验证读取被拒绝。

复审原文：原 P2 发现已关闭；实际读取不再依赖检查后的完整路径；新增 fixture 覆盖原触发场景。本次只读复审未发现新增规范问题或值得报告的 smell。结论基于代码审查，未运行测试或访问真实安装面。

## Spec

初审发现 3 项：P1 默认 agent boundary 自身的 symlink 可被跟随（spec 链接 GAP 边界）；P1 Git diff 可能执行 clean filter（AC-6 零写入）；P2 Matt manifest 未核对既有内容/控制段/LICENSE 完整性字段（源自洽与非法定义退出 2）。未发现范围扩张。T03/T04 尚未执行与 AC-2 GAP 属于已知阶段边界。

修复：检查 root 自身并拒绝未声明链接；Git 只读 ls-tree 元数据、由 Python 比较原始 Git blob 哈希，不调用 diff/clean filter，并隔离继承 GIT_* 变量；固定 versioned manifest 指纹并重新验证 LICENSE、skill 目录与控制段哈希。增加同条件负向 fixture，另覆盖整个受管 skill 删除和 GIT_DIR 重定向。

复审原文：原 3 项发现均已在实现层关闭。新增 fixture 对应上述触发条件，未发现新的阻塞性 Spec 缺陷或范围扩张。此次仅静态复审；测试执行结果由主会话留证，AC-2 真实安装 GAP 仍保留。

Standards：初始 1、未关闭 0、轴内最严重 P2 已关闭；Spec：初始 3、未关闭 0、轴内最严重 P1 已关闭。
