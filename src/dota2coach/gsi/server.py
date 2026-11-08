"""本地 GSI HTTP 服务：接收 Dota 2 的 POST 报文。

Dota 2 的 GSI 配置里写的是 http://127.0.0.1:31982/，它会在每个 tick 把
JSON POST 过来。这里只做三件事：校验、回调、回 200。
"""

from __future__ import annotations

import json
import sys
import threading
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable

from .models import Snapshot

OnSnapshot = Callable[[Snapshot], None]


class _CoachHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address, handler, on_snapshot: OnSnapshot | None):
        self.on_snapshot = on_snapshot
        self.errors = 0
        super().__init__(address, handler)

    def handle_error(self, request, client_address) -> None:
        """客户端主动断开（游戏退出、回放结束）不是错误，不要刷 traceback。"""
        exc = sys.exc_info()[1]
        if isinstance(exc, (ConnectionResetError, ConnectionAbortedError, BrokenPipeError)):
            return
        super().handle_error(request, client_address)


class _GsiHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "dota2coach-gsi/0.1"

    def do_POST(self) -> None:  # noqa: N802 (BaseHTTPRequestHandler 约定)
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        body = self.rfile.read(length) if length > 0 else b""
        if not body:
            self._reply(400, b'{"status":"empty"}')
            return
        try:
            payload = json.loads(body.decode("utf-8", "replace"))
        except json.JSONDecodeError:
            self._count_error()
            self._reply(400, b'{"status":"bad-json"}')
            return
        if not isinstance(payload, dict):
            self._count_error()
            self._reply(400, b'{"status":"bad-payload"}')
            return

        server = self.server
        callback = getattr(server, "on_snapshot", None)
        if callback is not None:
            try:
                callback(Snapshot(payload))
            except Exception:  # 单条报文处理失败不能拖垮服务
                self._count_error()
                traceback.print_exc()
        self._reply(200, b'{"status":"ok"}')

    def do_GET(self) -> None:  # noqa: N802
        # 方便用浏览器/curl 检查端口是否在听
        self._reply(200, b'{"status":"ok","service":"dota2coach-gsi"}')

    def _count_error(self) -> None:
        try:
            self.server.errors += 1  # type: ignore[attr-defined]
        except Exception:
            pass

    def _reply(self, code: int, body: bytes) -> None:
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        # 一问一答后立刻关连接：避免 keep-alive 半开连接在游戏退出时刷异常
        self.send_header("Connection", "close")
        self.end_headers()
        self.close_connection = True
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def log_message(self, fmt: str, *args) -> None:  # 别把每个请求都刷到控制台
        return


class GsiServer:
    """在后台线程里跑一个只监听本机的 HTTP 服务。"""

    def __init__(self, host: str = "127.0.0.1", port: int = 31982,
                 on_snapshot: OnSnapshot | None = None) -> None:
        self.host = host
        self.port = int(port)
        self.on_snapshot = on_snapshot
        self.payloads = 0
        self._httpd: _CoachHTTPServer | None = None
        self._thread: threading.Thread | None = None

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}/"

    @property
    def is_running(self) -> bool:
        return self._httpd is not None

    def start(self) -> None:
        if self._httpd is not None:
            return
        httpd = _CoachHTTPServer((self.host, self.port), _GsiHandler, self._on_snapshot_wrapper)
        self._httpd = httpd
        self.port = int(httpd.server_address[1])
        self._thread = threading.Thread(target=httpd.serve_forever, name="gsi-http", daemon=True)
        self._thread.start()

    def _on_snapshot_wrapper(self, snapshot: Snapshot) -> None:
        self.payloads += 1
        if self.on_snapshot is not None:
            self.on_snapshot(snapshot)

    def stop(self) -> None:
        httpd = self._httpd
        if httpd is None:
            return
        httpd.shutdown()
        httpd.server_close()
        if self._thread is not None:
            self._thread.join(timeout=5)
        self._httpd = None
        self._thread = None

    def __enter__(self) -> "GsiServer":
        self.start()
        return self

    def __exit__(self, *exc_info) -> None:
        self.stop()
