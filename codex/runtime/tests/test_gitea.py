import json
import unittest

from aisoft_loop.gitea import GiteaClient, GiteaError


class FakeTransport:
    def __init__(self, responses: list[tuple[int, dict[str, str], object]]) -> None:
        self.responses = list(responses)
        self.calls: list[tuple[str, str, dict[str, str], bytes | None]] = []

    def __call__(
        self, method: str, url: str, headers: dict[str, str], body: bytes | None
    ) -> tuple[int, dict[str, str], bytes]:
        self.calls.append((method, url, dict(headers), body))
        status, response_headers, payload = self.responses.pop(0)
        if isinstance(payload, bytes):
            encoded = payload
        elif isinstance(payload, str):
            encoded = payload.encode()
        else:
            encoded = json.dumps(payload).encode()
        return status, response_headers, encoded


def issue_payload(labels: list[tuple[int, str]] | None = None) -> dict:
    return {
        "number": 8,
        "state": "open",
        "title": "Pilot",
        "labels": [
            {"id": label_id, "name": name} for label_id, name in (labels or [])
        ],
    }


class GiteaClientTests(unittest.TestCase):
    def client(self, transport: FakeTransport, *, sleeps: list[float] | None = None) -> GiteaClient:
        recorded = sleeps if sleeps is not None else []
        return GiteaClient(
            "http://gitea.test:3000",
            "owner",
            "repo",
            "sentinel-token",
            transport=transport,
            sleep=recorded.append,
        )

    def test_token_only_appears_in_authorization_header(self) -> None:
        transport = FakeTransport([(200, {}, issue_payload())])
        issue = self.client(transport).get_issue(8)
        self.assertEqual(issue["number"], 8)
        _, url, headers, body = transport.calls[0]
        self.assertNotIn("sentinel-token", url)
        self.assertEqual(headers["Authorization"], "token sentinel-token")
        self.assertIsNone(body)

    def test_error_never_exposes_token_or_response_secret(self) -> None:
        transport = FakeTransport(
            [(401, {}, "Authorization: token sentinel-token\nGITEA_TOKEN=abc")]
        )
        with self.assertRaises(GiteaError) as caught:
            self.client(transport).get_issue(8)
        message = str(caught.exception)
        self.assertNotIn("sentinel-token", message)
        self.assertNotIn("abc", message)
        self.assertIn("[REDACTED]", message)

    def test_set_labels_preserves_unmanaged_and_enforces_three_dimensions(self) -> None:
        all_labels = [
            {"id": 1, "name": "type/bugfix"},
            {"id": 2, "name": "type/docs"},
            {"id": 3, "name": "complexity/small"},
            {"id": 4, "name": "complexity/complex"},
            {"id": 5, "name": "approved"},
            {"id": 6, "name": "awaiting-triage"},
            {"id": 90, "name": "customer-visible"},
        ]
        transport = FakeTransport(
            [
                (200, {}, issue_payload([(2, "type/docs"), (4, "complexity/complex"), (6, "awaiting-triage"), (90, "customer-visible")])),
                (200, {}, all_labels),
                (200, {}, {}),
            ]
        )
        self.client(transport).set_labels(
            8, {"type/bugfix", "complexity/small", "approved"}
        )
        method, _, _, body = transport.calls[-1]
        self.assertEqual(method, "PUT")
        self.assertEqual(set(json.loads(body)["labels"]), {1, 3, 5, 90})

    def test_unclear_route_has_no_complexity_label(self) -> None:
        all_labels = [
            {"id": 1, "name": "type/maintenance"},
            {"id": 2, "name": "complexity/small"},
            {"id": 3, "name": "awaiting-triage"},
        ]
        transport = FakeTransport(
            [
                (200, {}, issue_payload([(2, "complexity/small")])),
                (200, {}, all_labels),
                (200, {}, {}),
            ]
        )
        self.client(transport).set_labels(
            8, {"type/maintenance", "awaiting-triage"}
        )
        labels = set(json.loads(transport.calls[-1][3])["labels"])
        self.assertEqual(labels, {1, 3})

    def test_set_labels_accepts_completed_as_the_only_lifecycle(self) -> None:
        all_labels = [
            {"id": 1, "name": "type/platform"},
            {"id": 2, "name": "complexity/complex"},
            {"id": 3, "name": "pr-open"},
            {"id": 4, "name": "completed"},
            {"id": 90, "name": "priority/high"},
        ]
        transport = FakeTransport(
            [
                (
                    200,
                    {},
                    issue_payload(
                        [
                            (1, "type/platform"),
                            (2, "complexity/complex"),
                            (3, "pr-open"),
                            (90, "priority/high"),
                        ]
                    ),
                ),
                (200, {}, all_labels),
                (200, {}, {}),
            ]
        )
        self.client(transport).set_labels(
            8, {"type/platform", "complexity/complex", "completed"}
        )
        labels = set(json.loads(transport.calls[-1][3])["labels"])
        self.assertEqual(labels, {1, 2, 4, 90})

    def test_invalid_managed_label_combinations_are_rejected_before_http(self) -> None:
        transport = FakeTransport([])
        client = self.client(transport)
        cases = (
            {"approved"},
            {"type/docs", "type/test", "approved"},
            {"type/docs", "complexity/small", "complexity/complex", "approved"},
            {"type/docs", "complexity/small", "approved", "pr-open"},
            {"type/docs", "complexity/small", "completed", "deployed"},
            {"type/docs", "approved", "unknown-managed"},
        )
        for labels in cases:
            with self.subTest(labels=labels), self.assertRaises(GiteaError):
                client.set_labels(8, set(labels))
        self.assertEqual(transport.calls, [])

    def test_create_pr_requires_issue_closure_and_contract_link(self) -> None:
        transport = FakeTransport([(201, {}, {"number": 4, "state": "open"})])
        client = self.client(transport)
        for body in ("Closes #8", "docs/changes/8/00-summary.md"):
            with self.subTest(body=body), self.assertRaises(GiteaError):
                client.create_pr(8, "Pilot", "change/8", "main", body)
        result = client.create_pr(
            8,
            "Pilot",
            "change/8",
            "main",
            "Closes #8\n\nChange documents:\n- docs/changes/8/00-summary.md",
        )
        self.assertEqual(result["number"], 4)
        payload = json.loads(transport.calls[-1][3])
        self.assertEqual(payload["head"], "change/8")
        self.assertNotIn("merge", payload)

    def test_ci_status_mapping(self) -> None:
        transport = FakeTransport(
            [
                (200, {}, {"state": "pending"}),
                (200, {}, {"state": "success"}),
                (200, {}, {"state": "failure"}),
                (200, {}, {"state": "error"}),
            ]
        )
        client = self.client(transport)
        self.assertEqual(
            [client.get_commit_status("abc") for _ in range(4)],
            ["pending", "success", "failure", "failure"],
        )

    def test_429_and_5xx_retry_with_bounded_backoff(self) -> None:
        sleeps: list[float] = []
        transport = FakeTransport(
            [
                (500, {}, {"message": "temporary"}),
                (429, {"Retry-After": "1"}, {"message": "rate"}),
                (200, {}, issue_payload()),
            ]
        )
        result = self.client(transport, sleeps=sleeps).get_issue(8)
        self.assertEqual(result["number"], 8)
        self.assertEqual(len(transport.calls), 3)
        self.assertEqual(sleeps, [0.25, 1.0])

    def test_4xx_is_not_blindly_retried(self) -> None:
        transport = FakeTransport([(404, {}, {"message": "missing"})])
        with self.assertRaises(GiteaError):
            self.client(transport).get_issue(8)
        self.assertEqual(len(transport.calls), 1)

    def test_comment_and_get_pr_use_expected_endpoints(self) -> None:
        transport = FakeTransport(
            [(201, {}, {"id": 10}), (200, {}, {"number": 3, "state": "open"})]
        )
        client = self.client(transport)
        client.comment(8, "READY_FOR_REVIEW")
        client.get_pr(3)
        self.assertTrue(transport.calls[0][1].endswith("/issues/8/comments"))
        self.assertTrue(transport.calls[1][1].endswith("/pulls/3"))


if __name__ == "__main__":
    unittest.main()
