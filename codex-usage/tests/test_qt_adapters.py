import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Event, Thread
from time import monotonic
from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication, QEventLoop, QProcess, QTimer, QUrl
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest

from usage_app.adapters import CodexAdapter, HttpQuotaAdapter
from usage_app.credentials import new_reference
from usage_app.models import Account, ErrorCode, Provider
from usage_app.refresh import RequestTicket


@pytest.fixture(scope="module")
def qt_app():
    return QCoreApplication.instance() or QCoreApplication([])


def until(predicate, timeout=2000):
    loop = QEventLoop()
    poll = QTimer()
    poll.timeout.connect(lambda: loop.quit() if predicate() else None)
    poll.start(5)
    deadline = QTimer(loop)
    deadline.setSingleShot(True)
    deadline.timeout.connect(loop.quit)
    deadline.start(timeout)
    if not predicate():
        loop.exec()
    poll.stop()
    deadline.stop()
    assert predicate(), "Qt operation did not complete"


class RoutingManager(QNetworkAccessManager):
    def __init__(self, endpoint):
        super().__init__()
        self.endpoint = endpoint
        self.status = 200
        self.body = b'{"is_available":true,"balance_infos":[{"currency":"CNY","total_balance":"12.00"}]}'
        self.retry = b""
        self.requests = []

    def createRequest(self, operation, request, outgoingData=None):
        self.requests.append((operation, request))
        local = QNetworkRequest(request)
        local.setUrl(QUrl(self.endpoint))
        return super().createRequest(operation, local, outgoingData)


@pytest.fixture
def transport(qt_app):
    # Real Qt replies and a loopback server. Synthetic headers only; production
    # still exposes only the two fixed HTTPS endpoints.
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            hold = getattr(manager, "hold", None)
            if hold is not None:
                hold.wait(15)
            self.send_response(manager.status)
            self.send_header("Content-Length", str(len(manager.body)))
            self.send_header("Retry-After", manager.retry.decode())
            self.end_headers()
            try:
                self.wfile.write(manager.body)
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                pass
        def log_message(self, format, *args):
            pass
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    manager = RoutingManager(f"http://127.0.0.1:{server.server_port}/quota")
    thread = Thread(target=lambda: server.serve_forever(poll_interval=.01), daemon=True)
    thread.start()
    yield manager
    manager.deleteLater()
    qt_app.processEvents()
    server.shutdown()
    server.server_close()
    thread.join(timeout=1)


class TestSecrets:
    def read(self, reference):
        return "synthetic-not-a-real-key"


def test_http_read_is_async_fixed_endpoint_and_cancel_drops_late_result(qt_app, transport):
    account = Account("00000000-0000-4000-8000-000000000011", Provider.DEEPSEEK, "DeepSeek")
    account = Account(account.id, account.provider, account.display_name, new_reference(account.provider, account.id))
    manager = transport
    adapter = HttpQuotaAdapter(Provider.DEEPSEEK, TestSecrets(), manager=manager)
    successes, failures = [], []
    adapter.succeeded.connect(lambda ticket, snapshot: successes.append(snapshot))
    adapter.failed.connect(lambda ticket, error: failures.append(error))
    adapter.read(account, RequestTicket(account.id, 1, 1))
    assert not successes
    until(lambda: bool(successes))
    assert successes[0].balances[0].total == 12
    operation, request = manager.requests[0]
    assert operation == QNetworkAccessManager.Operation.GetOperation
    assert request.url().toString() == "https://api.deepseek.com/user/balance"
    assert request.rawHeader("Authorization").data() == b"Bearer synthetic-not-a-real-key"
    assert request.attribute(QNetworkRequest.Attribute.RedirectPolicyAttribute) == QNetworkRequest.RedirectPolicy.ManualRedirectPolicy
    adapter.read(account, RequestTicket(account.id, 1, 2))
    adapter.cancel(account.id)
    qt_app.processEvents()
    assert len(successes) == 1 and failures == []


@pytest.mark.parametrize("status,body,code", [(401, b"sensitive body", ErrorCode.AUTH_REQUIRED),
    (403, b"sensitive body", ErrorCode.FORBIDDEN), (429, b"sensitive body", ErrorCode.RATE_LIMITED),
    (503, b"sensitive body", ErrorCode.SERVICE), (200, b"broken json", ErrorCode.INCOMPATIBLE),
    (200, b" " * (1024 * 1024 + 1), ErrorCode.INCOMPATIBLE)], ids=["auth", "forbidden", "rate-limit", "service", "malformed", "oversized"])
def test_http_error_channels_never_retain_body(qt_app, transport, status, body, code):
    account = Account("00000000-0000-4000-8000-000000000012", Provider.GLM, "GLM")
    account = Account(account.id, account.provider, account.display_name, new_reference(account.provider, account.id))
    manager = transport
    manager.status, manager.body, manager.retry = status, body, b"90"
    adapter = HttpQuotaAdapter(Provider.GLM, TestSecrets(), manager=manager)
    failures = []
    adapter.failed.connect(lambda ticket, error: failures.append(error))
    adapter.read(account, RequestTicket(account.id, 1, 1))
    until(lambda: bool(failures))
    assert len(failures) == 1 and failures[0].code == code
    assert "sensitive" not in str(failures[0])
    assert manager.requests[0][1].rawHeader("Authorization").data() == b"synthetic-not-a-real-key"
    if code == ErrorCode.RATE_LIMITED:
        assert failures[0].retry_after == 90


def test_stalled_http_times_out_without_blocking_qt_and_next_read_recovers(qt_app, transport):
    # Stall a real loopback connection; no credentials or provider traffic.
    account = Account("00000000-0000-4000-8000-000000000014", Provider.DEEPSEEK, "DeepSeek")
    account = Account(account.id, account.provider, account.display_name, new_reference(account.provider, account.id))
    hold = Event()
    transport.hold = hold
    adapter = HttpQuotaAdapter(Provider.DEEPSEEK, TestSecrets(), manager=transport)
    failures, successes, ticks = [], [], []
    adapter.failed.connect(lambda ticket, error: failures.append((ticket, error)))
    adapter.succeeded.connect(lambda ticket, snapshot: successes.append((ticket, snapshot)))
    heartbeat = QTimer()
    heartbeat.timeout.connect(lambda: ticks.append(True))
    heartbeat.start(50)
    expired = RequestTicket(account.id, 1, 1)
    started = monotonic()
    try:
        adapter.read(account, expired)
        assert transport.requests[0][1].transferTimeout() == 10_000
        until(lambda: bool(failures), timeout=13_000)
        assert monotonic() - started >= 8
        assert failures == [(expired, failures[0][1])] and failures[0][1].code == ErrorCode.TIMEOUT
        assert not successes and len(ticks) >= 10
        transport.hold = None
        hold.set()
        recovered = RequestTicket(account.id, 1, 2)
        adapter.read(account, recovered)
        until(lambda: bool(successes))
        assert len(successes) == 1 and successes[0][0] == recovered
        assert successes[0][1].balances[0].total == 12
        assert len(failures) == 1  # Late completion cannot emit success or another failure.
    finally:
        heartbeat.stop()
        hold.set()
        adapter.cancel(account.id)


class ScriptProcess(QProcess):
    def __init__(self, script):
        super().__init__()
        self.script = script

    def start(self, program, arguments):
        return super().start(sys.executable, [str(self.script)])


def test_codex_handshake_readonly_and_old_process_exit_isolated(qt_app, tmp_path: Path):
    script = tmp_path / "fake_app_server.py"
    log = tmp_path / "methods.jsonl"
    script.write_text('''import sys,json
from pathlib import Path
log=Path(%r)
for line in sys.stdin:
 message=json.loads(line)
 method=message.get("method")
 with log.open("a") as f:f.write(json.dumps(method)+"\\n")
 if method=="initialize":print(json.dumps({"id":1,"result":{"userAgent":"test"}}),flush=True)
 if method=="account/rateLimits/read":print(json.dumps({"id":2,"result":{"rateLimits":{"primary":{"usedPercent":75,"windowDurationMins":300}}}}),flush=True)
''' % str(log), encoding="utf-8")
    adapter = CodexAdapter(executable="synthetic", process_factory=lambda: ScriptProcess(script))
    account = Account("00000000-0000-4000-8000-000000000013", Provider.CODEX, "Codex")
    successes, failures = [], []
    adapter.failed.connect(lambda ticket, error: failures.append(error))
    def success(ticket, snapshot):
        successes.append(snapshot)
        if len(successes) == 1:
            # Next request starts before the previous killed process exits.
            adapter.read(account, RequestTicket(account.id, 2, 2))
    adapter.succeeded.connect(success)
    adapter.read(account, RequestTicket(account.id, 1, 1))
    until(lambda: len(successes) == 2)
    qt_app.processEvents()
    assert failures == []
    assert successes[0].window(300).remaining_percent == 25
    assert [json.loads(line) for line in log.read_text().splitlines()] == ["initialize", "initialized", "account/rateLimits/read"] * 2
