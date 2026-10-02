"""Issue #317 baseline evidence; uses only repository FakeDocker fixtures."""
import json
from pathlib import Path
import tempfile

from aisoft_release.errors import ReleaseError
from aisoft_release.runner import ReleaseRuntime
from tests.release_test_support import FakeDocker, SHA_A, SHA_B, create_release


def reproduce(action, version="docker-release/v2"):
    with tempfile.TemporaryDirectory(prefix="issue-317-fixture-") as directory:
        root = Path(directory)
        docker = FakeDocker()
        for release in (SHA_A, SHA_B):
            profile, model, manifest = create_release(root, release, contract_version=version)
            docker.register(release, model, manifest)
        runtime = ReleaseRuntime(docker, hostname="test-host")
        runtime.deploy(profile, SHA_A)
        if action == "activate":
            runtime.stage(profile, SHA_B)
            runtime.migrate(profile, SHA_B)
        elif action == "rollback":
            runtime.deploy(profile, SHA_B)
        docker.events.clear()
        if action != "rollback":
            docker.unhealthy_for.add(SHA_B)
        error = None
        try:
            getattr(runtime, action)(profile, SHA_A if action == "rollback" else SHA_B)
        except ReleaseError as exc:
            error = {"code": exc.code, "message": exc.safe_message}
        state = json.loads((root / "state" / "state.json").read_text())
        starts = [event[1] for event in docker.events if event[0] == "up"]
        return {
            "action": action, "version": version,
            "distinct_migrations_completed": len([r for r in state["migrations"].values() if r["status"] == "completed"]),
            "up_releases": starts, "old_release_start_count": starts.count(SHA_A),
            "compatibility_evidence": "ABSENT", "error": error,
            "real_docker_calls": 0, "database_restore_calls": 0,
            "conclusion": "BUG_CONFIRMED" if SHA_A in starts else "NOT_REPRODUCED",
        }


print(json.dumps([reproduce("activate"), reproduce("deploy", "docker-release/v1"),
                  reproduce("rollback")], indent=2, sort_keys=True))
