"""#286: exercise dependency routing at contract/broker/controller seams."""
import unittest
from pathlib import Path
from unittest.mock import patch

from aisoft_host_access.broker import BrokerError, HostAccessBroker, ResolvedCredential
from aisoft_host_access.contract import load_access_contract, AccessContractError
from aisoft_host_access.dependencies import (
    DependencyError, parse_dependencies, project_issue, resolve_target, is_terminal,
)

ROOT = Path(__file__).resolve().parents[3]


def access():
    return load_access_contract(ROOT / 'codex/config/host-access-broker.json',
                                ROOT / 'codex/config/gitea-governance.json')


def issue(state='open', label='completed'):
    return {'number': 284, 'repository': {'full_name': 'admin/aisoft-platform'},
            'state': state, 'labels': [{'name': label}], 'body': 'discard this body'}


class DependencyTests(unittest.TestCase):
    def test_parser_compatibility_and_explicit_identity(self):
        self.assertEqual(parse_dependencies(['3', 7, 'admin/aisoft-platform#284'], 142),
                         (3, 7, 'admin/aisoft-platform#284'))
        for values in (None, '', []):
            self.assertEqual(parse_dependencies(values, 142), ())

    def test_invalid_duplicate_and_self_rejected(self):
        for values in ([True], [0], [-1], [{}], ['http://host/repo#3'],
                       ['admin/../repo#3'], ['admin/repo#0'], [142], [3, '3'],
                       [3, 'admin/repo#3'], ['admin/repo#142']):
            with self.subTest(values=values), self.assertRaises(DependencyError):
                parse_dependencies(values, 142, ('admin', 'repo'))
        self.assertEqual(parse_dependencies(['admin/other#142'],142,('admin','repo')),
                         ('admin/other#142',))

    def test_only_canonical_manifest_edge_allowed(self):
        c=access(); s=c.project('sfm-digital-board')
        self.assertEqual(resolve_target(c,s,'admin/aisoft-platform#284')[0].project_id,
                         'aisoft-platform')
        for source,ref in [('localwms','admin/aisoft-platform#284'),
                           ('sfm-digital-board','other/aisoft-platform#284'),
                           ('sfm-digital-board','admin/AISoftPlatform#284')]:
            with self.subTest(source=source,ref=ref), self.assertRaises(DependencyError):
                resolve_target(c,c.project(source),ref)

    def test_response_identity_pr_and_schema_fail_closed(self):
        self.assertFalse(is_terminal(project_issue(issue(),('admin','aisoft-platform',284))))
        for label in ('completed','deployed'):
            self.assertTrue(is_terminal(project_issue(issue('closed',label),('admin','aisoft-platform',284))))
        self.assertFalse(is_terminal(issue('closed','approved')))
        for changes in ({'number':True},{'number':285},{'repository':{}},
                        {'pull_request':{}},{'state':'unknown'},{'labels':[{}]}):
            with self.subTest(changes=changes),self.assertRaises(DependencyError):
                project_issue({**issue(),**changes},('admin','aisoft-platform',284))

    def test_broker_denies_edge_before_any_credentials_or_get(self):
        c=access(); b=HostAccessBroker(c)
        with patch.object(b.credentials,'resolve') as cred, patch.object(b,'_request_json') as get:
            with self.assertRaises(BrokerError) as err:
                b.execute('localwms','gitea.dependency.read',reference='admin/aisoft-platform#284')
            self.assertEqual(err.exception.code,'DEPENDENCY_TARGET_DENIED')
            cred.assert_not_called(); get.assert_not_called()

    def test_broker_reads_exact_target_with_audit_identity_and_projection(self):
        c=access(); b=HostAccessBroker(c)
        with patch.object(b.credentials,'resolve',return_value=ResolvedCredential('audit','fixture-audit')) as cred, \
                patch.object(b,'_request_json',return_value=issue()) as get, \
                patch.object(b,'_verify_identity'):
            result=b.execute('sfm-digital-board','gitea.dependency.read',reference='admin/aisoft-platform#284')
            self.assertEqual(cred.call_args.args[1].identity_route,'manager-audit')
            self.assertEqual(get.call_args.args[0],c.governance.base_url+'/api/v1/repos/admin/aisoft-platform/issues/284')
            self.assertEqual(get.call_args.args[1],'fixture-audit')
            self.assertEqual(result['reference'],'admin/aisoft-platform#284')
            self.assertNotIn('body',result)

    def test_routine_dependency_path_uses_same_target_and_terminal_rule(self):
        c=access(); source=c.project('sfm-digital-board'); b=HostAccessBroker(c)
        with patch.object(b.credentials,'resolve',return_value=ResolvedCredential('audit','fixture-audit')), \
                patch.object(b,'_request_json',return_value=issue()) as get, \
                patch.object(b,'_verify_identity'):
            dep=b._read_dependency(source,'admin/aisoft-platform#284',local_token='fixture-routine')
            self.assertFalse(is_terminal(dep))
            self.assertEqual(get.call_args.args[1],'fixture-audit')
            get.return_value=issue('closed')
            self.assertTrue(is_terminal(b._read_dependency(source,'admin/aisoft-platform#284',local_token='fixture-routine')))


if __name__=='__main__': unittest.main()
