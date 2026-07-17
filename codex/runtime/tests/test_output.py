"""Adapters must normalize their CLI output before the strict validators see it."""

import json
import unittest

from aisoft_loop.output import OutputError, extract_last_json_object


RESULT = {
    "status": "COMPLETE",
    "summary": "done",
    "changed_files": ["src/change.txt"],
    "root_cause": "",
    "escalation": "",
}
NESTED = {"classification": "change_type: platform", "detail": {"inner": {"deep": 1}}}


class ExtractLastJsonObjectTests(unittest.TestCase):
    def assert_extracts(self, text: str, expected: dict) -> None:
        self.assertEqual(json.loads(extract_last_json_object(text)), expected)

    def test_pure_json_is_returned_unchanged(self) -> None:
        self.assert_extracts(json.dumps(RESULT), RESULT)

    def test_prose_preamble_before_json_is_dropped(self) -> None:
        # This is the real Claude shape: it explains itself, then emits the object.
        self.assert_extracts(
            "I have verified every claim in the Issue.\n\n- **No CI exists**\n\n"
            + json.dumps(RESULT),
            RESULT,
        )

    def test_trailing_prose_after_json_is_dropped(self) -> None:
        self.assert_extracts(json.dumps(RESULT) + "\n\nLet me know if you want more.", RESULT)

    def test_markdown_fenced_json_is_unwrapped(self) -> None:
        self.assert_extracts("Here you go:\n\n```json\n" + json.dumps(RESULT) + "\n```\n", RESULT)

    def test_nested_objects_do_not_truncate_the_result(self) -> None:
        # Scanning backwards for '{' would wrongly return the innermost object.
        self.assert_extracts("Analysis:\n" + json.dumps(NESTED), NESTED)

    def test_braces_in_prose_do_not_win_over_the_real_object(self) -> None:
        self.assert_extracts(
            'The verifier reads {"version": 1} from disk.\n\n' + json.dumps(RESULT), RESULT
        )

    def test_last_object_wins_when_several_are_present(self) -> None:
        self.assert_extracts(json.dumps(NESTED) + "\n\nCorrected:\n" + json.dumps(RESULT), RESULT)

    def test_output_without_any_json_object_is_rejected(self) -> None:
        for text in ("", "   \n", "I could not complete the analysis.", "[1, 2, 3]"):
            with self.subTest(text=text), self.assertRaises(OutputError):
                extract_last_json_object(text)

    def test_unterminated_object_is_rejected(self) -> None:
        with self.assertRaises(OutputError):
            extract_last_json_object('{"status": "COMPLETE"')


if __name__ == "__main__":
    unittest.main()
