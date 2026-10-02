# #320 场景验证（合成桌面推演）

依据批准 spec AC-1/2/3 对六份指导逐条审查并推演。下列程序仅解释文字规则；不调用 broker，不验证实际 runtime，不执行真实 push/backfill/CI repair。

A/B/C/X 分别为 a/b/c/d 重复40次的固定 lowercase 合成 SHA。当前规则全部17例符合预期；把所有 push 的比较锚恢复为首次候选 A 时，合法回填 B 与 CI 修复 C 被错误停止，复现文字歧义。

| 场景 | 预期 | 推演结果 |
|---|---|---|
| first-verified-candidate | CONTINUE | CONTINUE / PASS |
| summary-backfill-new-head | CONTINUE | CONTINUE / PASS |
| in-contract-CI-new-head | CONTINUE | CONTINUE / PASS |
| other-session-rewrites-before-push | STOP | STOP / PASS |
| backfill-reuses-old-anchor | STOP | STOP / PASS |
| CI-reuses-previous-anchor | STOP | STOP / PASS |
| missing-push-readback | STOP | STOP / PASS |
| push-return-mismatch | STOP | STOP / PASS |
| scope-expanded | STOP | STOP / PASS |
| session-ownership-mismatch | STOP | STOP / PASS |
| exact-branch-mismatch | STOP | STOP / PASS |
| first-candidate-changed-after-confirmation | STOP | STOP / PASS |
| backfill-mixed-files | STOP | STOP / PASS |
| backfill-wrong-PR-URL | STOP | STOP / PASS |
| CI-validation-failed | STOP | STOP / PASS |
| dirty-tree | STOP | STOP / PASS |
| no-exact-tuple-submission-authorization | STOP | STOP / PASS |

## 推演规则（非 runtime 实现）

```python
from pathlib import Path
import json,copy,re,hashlib
r=Path('/private/tmp/issue-320-push-head-anchor'); e=r/'docs/changes/320-push-head-anchor/evidence'
A='a'*40;B='b'*40;C='c'*40;X='d'*40
normal=dict(phase='first',candidate=A,verified=A,local=A,pushed=A,authorized=True,owner=True,branch=True,in_scope=True,validation=True,clean=True,unexpected_rewrite=False,summary_only=True,actual_pr=True,readback=True)
def case(name,expected,**updates):return dict(name=name,expected=expected,inputs=dict(normal,**updates))
cases=[case('first-verified-candidate','CONTINUE'),case('summary-backfill-new-head','CONTINUE',phase='backfill',local=B,verified=B,pushed=B),case('in-contract-CI-new-head','CONTINUE',phase='ci',local=C,verified=C,pushed=C),case('other-session-rewrites-before-push','STOP',phase='ci',local=X,verified=C,pushed=X,unexpected_rewrite=True),case('backfill-reuses-old-anchor','STOP',phase='backfill',local=B,verified=A,pushed=B),case('CI-reuses-previous-anchor','STOP',phase='ci',local=C,verified=B,pushed=C),case('missing-push-readback','STOP',readback=False),case('push-return-mismatch','STOP',phase='ci',local=C,verified=C,pushed=X),case('scope-expanded','STOP',phase='ci',local=C,verified=C,pushed=C,in_scope=False),case('session-ownership-mismatch','STOP',owner=False),case('exact-branch-mismatch','STOP',branch=False),case('first-candidate-changed-after-confirmation','STOP',local=B,verified=B,pushed=B),case('backfill-mixed-files','STOP',phase='backfill',local=B,verified=B,pushed=B,summary_only=False),case('backfill-wrong-PR-URL','STOP',phase='backfill',local=B,verified=B,pushed=B,actual_pr=False),case('CI-validation-failed','STOP',phase='ci',local=C,verified=C,pushed=C,validation=False),case('dirty-tree','STOP',clean=False),case('no-exact-tuple-submission-authorization','STOP',authorized=False)]
def evaluate(s,legacy=False):
 checks=(s['authorized'],s['owner'],s['branch'],s['in_scope'],s['validation'],s['clean'],not s['unexpected_rewrite'],s['readback'])
 if not all(checks):return 'STOP'
 if s['phase']=='backfill' and not(s['summary_only'] and s['actual_pr']):return 'STOP'
 if not all(re.fullmatch('[a-f0-9]{40}',s[k]) for k in ('candidate','verified','local','pushed')):return 'STOP'
 if s['phase']=='first' and s['verified']!=s['candidate']:return 'STOP'
 anchor=s['candidate'] if legacy or s['phase']=='first' else s['verified']
 return 'CONTINUE' if s['local']==s['verified']==s['pushed']==anchor else 'STOP'
```

六文件 clause_evidence 的真实行号与每例固定输入/输出见 `t02-scenarios.json`。同源指令的 runtime/模型/live 生效不在本验证范围；这三个层次不能由此推演得出 PASS。
