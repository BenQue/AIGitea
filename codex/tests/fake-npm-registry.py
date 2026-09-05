#!/usr/bin/env python3
"""Stand-in npm registry for codex/tests/test-registry-preflight.sh (Issue #201).

The preflight assertion must be provable without touching the real Verdaccio on
gitea-ci: stopping that service is outside what a session may do, and the
negative verification must not be faked by clearing an npm cache. So the test
drives this process instead -- starting it, killing it and starting it again
reproduces the exact failure signature of the outage (connection refused on a
port with no listener) at the level the assertion actually reads.

Modes select which layer misbehaves, one per failure stage the script names.
"""

from __future__ import annotations

import json
import socket
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

MODE = sys.argv[1]
PORT = int(sys.argv[2])
PACKAGE = "fflate"
VERSION = "0.8.3"

PACKUMENT = json.dumps(
    {
        "name": PACKAGE,
        "dist-tags": {"latest": VERSION},
        "versions": {
            VERSION: {
                "name": PACKAGE,
                "version": VERSION,
                "dist": {
                    "tarball": f"http://127.0.0.1:{PORT}/{PACKAGE}/-/{PACKAGE}-{VERSION}.tgz"
                },
            }
        },
    }
).encode()

# Not a tarball, only bytes: the assertion checks that the package body is
# served at all, which is what npm ci needs and what the outage denied.
TARBALL = b"\x1f\x8b\x08\x00stand-in-tarball-bytes"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):  # keep the test output readable
        pass

    def _send(self, status, body, content_type="application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        is_tarball = self.path.endswith(".tgz")
        if MODE == "http500" and not is_tarball:
            self._send(500, b"upstream exploded", "text/plain")
        elif MODE == "notpackument" and not is_tarball:
            # A proxy, login page or error page standing in for the registry:
            # HTTP 200 with a body that is not package metadata.
            self._send(200, b"<html><body>Sign in to continue</body></html>", "text/html")
        elif MODE == "tarball404" and is_tarball:
            self._send(404, b"not found", "text/plain")
        elif is_tarball:
            self._send(200, TARBALL, "application/octet-stream")
        else:
            self._send(200, PACKUMENT)


class Server(HTTPServer):
    allow_reuse_address = True
    address_family = socket.AF_INET


Server(("127.0.0.1", PORT), Handler).serve_forever()
