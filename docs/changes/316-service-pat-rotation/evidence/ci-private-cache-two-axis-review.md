# #316 T04 CI 私有缓存清理双轴复审（2026-10-03）

基线 head=8cb6b03904e50a81a06454a0ac4efd37a80a2835；只审工作树 test-gitea-pat-helper-linux.sh 与 test_build.py 两份 delta。按既有 Matt code-review 技能并行复用 Standards/Spec 只读 agent。

Standards：0 findings、0 hard blocker、0 smell judgement。只 chmod/rm 本次 mktemp 私有树，不扩到 caller GOPATH/GOCACHE；保留原失败退出码，成功但清理失败转 FAIL。真实 shell setup/EXIT trap 回归覆盖 0/37、私有目录删除及外部 sentinel 字节/0444。

Spec：0 findings。映射 spec 固定构建、AC-7/测试授权与 plan T04 覆盖此 CI 修复；pin、model/provenance、build/race/process 硬门未变。仅本地测试清理，不是安装或 live 操作。

审查 agent 未自行运行测试或访问 remote。父会话已实际运行 Mac 与 disposable Linux UID65534 12 unit、bash-n/ShellCheck PASS；完整 smoke 结果另在最终修复回执记录。run1757 整体仍 FAIL，DB fixture NOT RUN；新 head required CI 必须真实重跑，不能从旧 head 的单项 PASS 推导整个 job PASS。
