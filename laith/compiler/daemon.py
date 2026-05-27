from __future__ import annotations
import json
import os
import socket
import struct
import threading
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

DAEMON_SOCKET = "/tmp/laith-compilerd.sock"


@dataclass
class DaemonRequest:
    id: int
    method: str
    params: dict = field(default_factory=dict)


@dataclass
class DaemonResponse:
    id: int
    ok: bool
    result: Optional[str] = None
    error: Optional[str] = None
    timing: dict = field(default_factory=dict)


class CompilerDaemonClient:
    def __init__(self, socket_path: str = DAEMON_SOCKET):
        self._socket_path = socket_path
        self._conn: Optional[socket.socket] = None
        self._request_id = 0
        self._lock = threading.Lock()

    def _connect(self):
        if self._conn is not None:
            return
        self._conn = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._conn.settimeout(30.0)
        self._conn.connect(self._socket_path)

    def send_request(self, method: str, params: dict = None) -> dict:
        with self._lock:
            self._connect()
            self._request_id += 1
            req = DaemonRequest(
                id=self._request_id,
                method=method,
                params=params or {},
            )
            data = json.dumps(asdict(req)).encode()
            header = struct.pack("!I", len(data))
            self._conn.sendall(header + data)
            resp_header = self._conn.recv(4)
            if not resp_header:
                raise ConnectionError("Daemon closed connection")
            resp_size = struct.unpack("!I", resp_header)[0]
            resp_data = b""
            while len(resp_data) < resp_size:
                chunk = self._conn.recv(resp_size - len(resp_data))
                if not chunk:
                    raise ConnectionError("Daemon closed connection mid-response")
                resp_data += chunk
            return json.loads(resp_data.decode())

    def compile(self, source: str, phase: str = "emit_kotlin") -> str:
        resp = self.send_request("compile", {"source": source, "phase": phase})
        if not resp["ok"]:
            raise RuntimeError(resp.get("error", "Unknown error"))
        return resp["result"]

    def ping(self) -> bool:
        try:
            resp = self.send_request("ping")
            return resp.get("ok", False)
        except (ConnectionError, OSError):
            return False

    def shutdown(self):
        try:
            self.send_request("shutdown")
        except Exception:
            pass
        finally:
            if self._conn:
                self._conn.close()
                self._conn = None

    def __enter__(self):
        self._connect()
        return self

    def __exit__(self, *args):
        self.shutdown()
