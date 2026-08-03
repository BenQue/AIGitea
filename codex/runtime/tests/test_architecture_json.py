from pathlib import Path
import tempfile
import unittest

from aisoft_architecture.errors import ArchitectureError
from aisoft_architecture.jsonio import canonical_bytes, load_json, loads_strict, write_canonical


ROOT = Path(__file__).resolve().parents[3]


class ArchitectureJsonTests(unittest.TestCase):
    def test_duplicate_keys_fail_closed(self) -> None:
        with self.assertRaises(ArchitectureError) as caught:
            load_json(ROOT / "architecture/fixtures/invalid/duplicate-key.json")
        self.assertEqual(caught.exception.diagnostic.code, "JSON_DUPLICATE_KEY")

    def test_non_finite_and_float_numbers_are_rejected(self) -> None:
        for raw, code in (("{\"value\": NaN}", "JSON_NON_FINITE_NUMBER"), ("{\"value\": 1.5}", "JSON_FLOAT_NOT_CANONICAL")):
            with self.subTest(raw=raw), self.assertRaises(ArchitectureError) as caught:
                loads_strict(raw)
            self.assertEqual(caught.exception.diagnostic.code, code)

    def test_yaml_path_is_rejected_without_reading(self) -> None:
        with self.assertRaises(ArchitectureError) as caught:
            load_json(ROOT / "architecture/fixtures/invalid/architecture.yaml")
        self.assertEqual(caught.exception.diagnostic.code, "YAML_NOT_SUPPORTED")

    def test_secret_markers_fail_without_echoing_values(self) -> None:
        sentinel = "must-never-appear"
        with self.assertRaises(ArchitectureError) as caught:
            loads_strict('{"api_token":"' + sentinel + '"}')
        diagnostic = caught.exception.diagnostic
        self.assertEqual(diagnostic.code, "SECRET_FIELD_FORBIDDEN")
        self.assertNotIn(sentinel, diagnostic.message)
        self.assertNotIn(sentinel, diagnostic.remediation)

        for raw in (
            '{"note":"Authorization: token ' + sentinel + '"}',
            '{"note":"SERVICE_PASSWORD=' + sentinel + '"}',
            '{"note":"postgresql://user:' + sentinel + '@db/app"}',
        ):
            with self.subTest(raw=raw), self.assertRaises(ArchitectureError) as caught:
                loads_strict(raw)
            self.assertEqual(caught.exception.diagnostic.code, "SECRET_VALUE_FORBIDDEN")
            self.assertNotIn(sentinel, caught.exception.diagnostic.message)

    def test_canonical_output_is_sorted_and_byte_stable(self) -> None:
        value = {"z": [3, 2, 1], "a": "中文", "m": {"b": True, "a": None}}
        expected = canonical_bytes(value)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "value.json"
            write_canonical(path, value)
            first = path.read_bytes()
            write_canonical(path, load_json(path))
            second = path.read_bytes()
        self.assertEqual(first, expected)
        self.assertEqual(first, second)
        self.assertTrue(first.endswith(b"\n"))


if __name__ == "__main__":
    unittest.main()
