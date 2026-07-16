import json
import os
from pathlib import Path
import tempfile
import unittest

from aisoft_loop.state import (
    GlobalLock,
    LockUnavailable,
    LoopBudget,
    StateError,
    StateStore,
    TerminalState,
)


class StateStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.store = StateStore(self.root / "state")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_save_is_atomic_private_and_round_trips(self) -> None:
        state = {"issue": 8, "round": 2, "terminal": "CONTINUE"}
        self.store.save(8, state)
        target = self.root / "state" / "issues" / "8.json"
        self.assertEqual(self.store.load(8), state)
        self.assertEqual(os.stat(target).st_mode & 0o777, 0o600)
        self.assertEqual(list(target.parent.glob("*.tmp")), [])

    def test_corrupt_or_non_object_state_is_rejected(self) -> None:
        target = self.root / "state" / "issues" / "8.json"
        target.parent.mkdir(parents=True)
        for content in ("{", "[]"):
            with self.subTest(content=content):
                target.write_text(content)
                with self.assertRaises(StateError):
                    self.store.load(8)

    def test_missing_state_returns_empty_object(self) -> None:
        self.assertEqual(self.store.load(404), {})

    def test_sensitive_keys_are_rejected_recursively(self) -> None:
        cases = (
            {"token": "secret"},
            {"nested": {"Authorization": "secret"}},
            {"items": [{"db_password": "secret"}]},
            {"credential_path": "/tmp/file"},
        )
        for state in cases:
            with self.subTest(state=state), self.assertRaisesRegex(StateError, "sensitive"):
                self.store.save(8, state)

    def test_issue_number_must_be_positive(self) -> None:
        for number in (0, -1):
            with self.subTest(number=number), self.assertRaises(StateError):
                self.store.load(number)

    def test_global_lock_rejects_second_holder(self) -> None:
        path = self.root / "state" / "loop.lock"
        first = GlobalLock(path)
        second = GlobalLock(path)
        first.acquire()
        try:
            with self.assertRaises(LockUnavailable):
                second.acquire()
        finally:
            first.release()
        second.acquire()
        second.release()

    def test_state_file_is_valid_json_after_repeated_replacement(self) -> None:
        for round_number in range(20):
            self.store.save(8, {"issue": 8, "round": round_number})
            raw = (self.root / "state" / "issues" / "8.json").read_text()
            self.assertEqual(json.loads(raw)["round"], round_number)


class LoopBudgetTests(unittest.TestCase):
    def test_eight_round_limit_is_checked_before_ninth_round(self) -> None:
        budget = LoopBudget(max_rounds=8, max_same_root=3)
        for expected in range(1, 9):
            self.assertIsNone(budget.start_round())
            self.assertEqual(budget.rounds, expected)
        self.assertEqual(budget.start_round(), TerminalState.FAILED_LIMIT)
        self.assertEqual(budget.rounds, 8)

    def test_third_same_root_failure_reaches_limit(self) -> None:
        budget = LoopBudget(max_rounds=8, max_same_root=3)
        self.assertIsNone(budget.record_failure("unit-test"))
        self.assertIsNone(budget.record_failure("unit-test"))
        self.assertEqual(
            budget.record_failure("unit-test"), TerminalState.FAILED_LIMIT
        )

    def test_changed_root_resets_consecutive_count(self) -> None:
        budget = LoopBudget(max_rounds=8, max_same_root=3)
        budget.record_failure("lint")
        budget.record_failure("lint")
        self.assertIsNone(budget.record_failure("test"))
        self.assertEqual(budget.consecutive_same_root, 1)
        self.assertEqual(budget.last_root_cause, "test")

    def test_empty_root_cause_is_rejected(self) -> None:
        with self.assertRaises(StateError):
            LoopBudget().record_failure("  ")

    def test_budget_serialization_round_trip(self) -> None:
        budget = LoopBudget(max_rounds=5, max_same_root=2)
        budget.start_round()
        budget.record_failure("build")
        restored = LoopBudget.from_dict(budget.to_dict())
        self.assertEqual(restored.to_dict(), budget.to_dict())


if __name__ == "__main__":
    unittest.main()
