"""Isolated shell black-box fixture; never imported or installed by runtime."""
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'codex/runtime'))
from aisoft_host_access.broker import BrokerError
from aisoft_host_access.contract import load_access_contract
from aisoft_host_access.credential_rotation import operator_main, OperatorGrant
from tests.test_credential_rotation import FakeGitea, SOURCE, CAPABILITY

store = Path(os.environ['ROTATION_FIXTURE_STORE']).resolve()
database = store / 'fake-gitea.json'


class Backend(FakeGitea):
    def __init__(self, *args):
        super().__init__()
        if database.exists():
            self.__dict__.update(json.loads(database.read_text()))

    def save(self):
        database.write_text(json.dumps(self.__dict__))
        database.chmod(0o600)

    def generate(self, name):
        token = super().generate(name)
        if os.environ.get('ROTATION_FIXTURE_FAILURE') == 'scope':
            self.tokens[token]['scopes'] = ['write:repository']
        self.save()
        return token

    def revoke(self, token, metadata):
        if os.environ.get('ROTATION_FIXTURE_FAILURE') == 'revoke':
            raise BrokerError('REVOKE_FAILED', 'candidate-secret-canary upstream stderr')
        super().revoke(token, metadata)
        self.save()


contract = load_access_contract(ROOT / 'codex/config/host-access-broker.json',
                               ROOT / 'codex/config/gitea-governance.json')
contract.raw['mac_host']['credential_root'] = str(store)


def grant(contract, target, issue, source, **kwargs):
    if issue != 316 or source != SOURCE or target.project_id != 'newemaint' or target.token_kind != 'routine-merge-agent':
        raise BrokerError('ROTATION_GRANT_INVALID', 'fixture refuses wrong target')
    return OperatorGrant(dict(issue=issue, source_sha=source, project_id=target.project_id,
                token_kind=target.token_kind, creation_issue=213), capability=CAPABILITY)


rename = os.rename
def fault_rename(src, dst, **kwargs):
    if os.environ.get('ROTATION_FIXTURE_FAILURE') == 'write' and src == 'candidate.token':
        raise OSError('old-secret-canary synthetic write error')
    return rename(src, dst, **kwargs)


with patch('os.geteuid', return_value=0), patch('sys.platform', 'darwin'), \
     patch('aisoft_host_access.contract.load_access_contract', return_value=contract), \
     patch('aisoft_host_access.credential_rotation.authorization', side_effect=grant), \
     patch('aisoft_host_access.credential_rotation.SystemBackend', Backend), \
     patch('os.rename', side_effect=fault_rename):
    raise SystemExit(operator_main(sys.argv[1:]))
