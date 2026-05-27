from __future__ import annotations
import pytest
import json
from laith.compiler.daemon import CompilerDaemonClient, DaemonRequest, DaemonResponse


class TestDaemonProtocol:
    def test_request_serialization(self):
        req = DaemonRequest(id=1, method="compile", params={"source": "code"})
        d = {"id": 1, "method": "compile", "params": {"source": "code"}}
        assert json.loads(json.dumps(d)) == d

    def test_response_serialization(self):
        resp = DaemonResponse(id=1, ok=True, result="compiled code")
        d = {"id": 1, "ok": True, "result": "compiled code", "error": None, "timing": {}}
        assert json.loads(json.dumps(d)) == d

    def test_error_response(self):
        resp = DaemonResponse(id=1, ok=False, error="Something went wrong")
        assert resp.ok is False
        assert resp.error == "Something went wrong"

    def test_response_with_timing(self):
        resp = DaemonResponse(id=1, ok=True, result="ok", timing={"parse": 0.001})
        assert resp.timing["parse"] == 0.001

    def test_daemon_client_connection_failure(self):
        client = CompilerDaemonClient(socket_path="/tmp/nonexistent.sock")
        assert client.ping() is False
