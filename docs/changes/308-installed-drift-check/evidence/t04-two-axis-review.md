# T04 增量两轴只读审查

比较固定 fresh main `11c0410d3878d5449fa61796f174ba3d2dd5e59c` 与 rebased T03 `bf0d76ce2f185e743a3576b7a368e56e1941b0d5` 的 smoke 八行；T02 runtime 原复审结果保留。两名 code-review agents 均只读，不写文件、访问 remote 或真实安装面。

## Standards

增量复审无新增阻塞或发现，smell 0 项。新增两个入口的 bash -n/ShellCheck、source-only 与隔离 fixture 调用；既有门与顺序保留，符合批准 spec。原父目录竞态问题维持关闭。

## Spec

初审新增 1 项 P1：smoke 将 source-only 的整体退出码用作门，但 checker 同时要求受管源等于 origin/main；合法的受管代码/skills/manifest PR 在合并前必然不同，会被错误阻断。对应 spec AC-5 与 source-only 只校验定义自洽的合同。

修复 commit `48d410132dfa5f7332a0e37e96011535e71f170f`：source-only 的退出码仅由定义合法性决定；source 身份字段继续独立报告 GAP/managed_source_matches_cached_main=false/EXTERNAL_EVIDENCE_REQUIRED。installed 模式仍要求身份与目标字节通过，不忽略其 GAP。新增合法受管源 PR fixture，要求 source-only 整体 PASS、身份 GAP、八行 SOURCE，且 installed 模式仍退出 1。

复审确认：该项 P1 已关闭，未发现新增 Spec 问题；没有输出 INSTALLED PASS 或当前 main 全同步。agent 结论仅来自静态审查；主会话的 23 项测试结果另留证。

Standards：本轮 0 新发现、0 未关闭；Spec：本轮 1 个 P1 已关闭、0 未关闭。原 AC-2 真安装 GAP 不计实现缺陷，也不因审查通过视为验收通过。
