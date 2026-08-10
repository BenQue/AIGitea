import unittest

from aisoft_change_name import ChangeName, ChangeNameError, select_change_name


class ChangeNameTests(unittest.TestCase):
    def test_readable_name_projects_one_canonical_tuple(self) -> None:
        name = ChangeName.new(75, "readable-change-names")
        self.assertEqual(name.branch, "change/75-readable-change-names")
        self.assertEqual(name.directory_name, "75-readable-change-names")
        self.assertEqual(name.worktree_name, "issue-75-readable-change-names")
        self.assertFalse(name.is_legacy)

    def test_internal_parser_preserves_legacy_read_compatibility(self) -> None:
        legacy = ChangeName.parse_branch("change/70")
        self.assertEqual(legacy.issue_number, 70)
        self.assertTrue(legacy.is_legacy)
        with self.assertRaisesRegex(ChangeNameError, "legacy"):
            ChangeName.parse_branch("change/70", allow_legacy=False)

    def test_slug_contract_is_fail_closed(self) -> None:
        invalid = (
            "one",
            "TOO-LONG",
            "one_two",
            "one-two-three-four-five",
            "1-2",
            "main",
            "legacy-fix",
            "temp-change",
            "x" * 30 + "-ok",
        )
        for slug in invalid:
            with self.subTest(slug=slug), self.assertRaises(ChangeNameError):
                ChangeName.new(75, slug)

    def test_directory_and_worktree_must_match_the_same_tuple(self) -> None:
        name = ChangeName.parse_directory("75-readable-change-names")
        self.assertEqual(
            ChangeName.parse_worktree("issue-75-readable-change-names"), name
        )
        with self.assertRaises(ChangeNameError):
            ChangeName.parse_directory("76-readable-change-names", issue_number=75)

    def test_same_issue_legacy_or_multiple_slugs_is_a_conflict(self) -> None:
        readable = ChangeName.new(75, "readable-change-names")
        self.assertEqual(select_change_name(75, [readable, readable]), readable)
        for candidates in (
            [ChangeName(75), readable],
            [readable, ChangeName.new(75, "other-change-name")],
        ):
            with self.subTest(candidates=candidates), self.assertRaisesRegex(
                ChangeNameError, "CHANGE_NAME_CONFLICT"
            ):
                select_change_name(75, candidates)


if __name__ == "__main__":
    unittest.main()
