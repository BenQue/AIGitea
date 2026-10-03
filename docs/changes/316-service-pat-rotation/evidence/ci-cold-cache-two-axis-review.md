# #316 T04 CI 冷缓存修复双轴复审（2026-10-03）

审查基线 head=5f3f424fd6c04bcbafb1954fa73e620bdcb417c2，两份工作树源码 delta。按既有 Matt code-review 技能由 Standards 与 Spec 两名只读 agent 并行审查，未修改源码或执行远程操作。

Standards：0 findings、0 hard blocker、0 smell judgement。先验证 readonly graph，再下载 exact module@version，独立核对 Path/Version/Sum/Error、绝对 Dir、model SHA 和 module inputs 字节不变，保留原硬门。

Spec：0 findings。映射 spec 接口/AC-7/授权与 plan T02/T04 覆盖构建修复；无范围扩张、pin 或权限弱化。原工具链字节、mod verify、readonly test/build 闸门保留。

父会话实际验证：固定 Go1.26.3 冷缓存复现 missing Dir 后转绿，10 项 unit 与完整 C.UTF-8 smoke PASS。两名审查 agent 未独立运行测试或 CI；新 head required CI 仍须真实读回。安装/grant/live NOT RUN，不能宣称整票完成。
