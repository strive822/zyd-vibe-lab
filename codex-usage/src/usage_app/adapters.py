"""Async Qt transports for fixed read-only provider operations. No raw logging."""

from __future__ import annotations

import json
import math
import os
import shutil
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Callable

from PySide6.QtCore import QByteArray, QObject, QProcess, QTimer, QUrl, Signal
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from .credentials import CredentialError, SecretStore, validate_reference
from .models import Account, ErrorCode, Provider, ProviderError, UsageSnapshot
from .parsers import GLM_PERSONAL_MAPPING, GlmWindowMapping, object_map, parse_codex, parse_deepseek, parse_glm
from .refresh import RequestTicket
from .source_evidence import glm_schema_observation

MAX_RESPONSE_BYTES = 1024 * 1024


def retry_after(value: str, now: datetime) -> float | None:
    try:
        delay = float(value)
    except ValueError:
        try:
            until = parsedate_to_datetime(value)
            if until.tzinfo is None:
                return None
            delay = (until - now).total_seconds()
        except (ValueError, TypeError, OverflowError):
            return None
    return max(0, delay) if math.isfinite(delay) else None


def http_error(status: int, retry: str, now: datetime) -> ProviderError | None:
    if status in (401, 403):
        return ProviderError(ErrorCode.AUTH_REQUIRED if status == 401 else ErrorCode.FORBIDDEN)
    if status == 429:
        return ProviderError(ErrorCode.RATE_LIMITED, retry_after(retry, now))
    if status >= 500:
        return ProviderError(ErrorCode.SERVICE)
    if status != 200:
        return ProviderError(ErrorCode.INCOMPATIBLE)
    return None


def decode_response(raw: bytes) -> object:
    if len(raw) > MAX_RESPONSE_BYTES:
        raise ProviderError(ErrorCode.INCOMPATIBLE)
    try:
        return json.loads(raw)
    except (ValueError, UnicodeDecodeError):
        raise ProviderError(ErrorCode.INCOMPATIBLE) from None


class ProviderAdapter(QObject):
    succeeded = Signal(object, object)  # RequestTicket, UsageSnapshot
    failed = Signal(object, object)  # RequestTicket, classified ProviderError

    def read(self, account: Account, ticket: RequestTicket) -> None:
        raise NotImplementedError

    def cancel(self, account_id: str) -> None:
        raise NotImplementedError


class HttpQuotaAdapter(ProviderAdapter):
    schema_observed = Signal(object)
    ENDPOINTS = {Provider.GLM: "https://open.bigmodel.cn/api/monitor/usage/quota/limit",
                 Provider.DEEPSEEK: "https://api.deepseek.com/user/balance"}

    def __init__(self, provider: Provider, secrets: SecretStore, parent: QObject | None = None,
                 *, glm_mapping: tuple[GlmWindowMapping, ...] = GLM_PERSONAL_MAPPING,
                 manager: QNetworkAccessManager | None = None) -> None:
        super().__init__(parent)
        if provider not in self.ENDPOINTS:
            raise ValueError("Unsupported HTTP provider")
        self.provider = provider
        self._secrets = secrets
        self._mapping = glm_mapping
        self._manager = manager or QNetworkAccessManager(self)
        self._requests: dict[str, tuple[RequestTicket, QNetworkReply]] = {}

    def read(self, account: Account, ticket: RequestTicket) -> None:
        if account.provider != self.provider or account.id != ticket.account_id:
            raise ValueError("Adapter/account mismatch")
        if account.id in self._requests:
            raise ValueError("Request already in flight")
        try:
            if not account.credential_ref:
                raise ProviderError(ErrorCode.UNCONFIGURED)
            validate_reference(account.credential_ref)
            if account.credential_ref.split("/")[1:3] != [self.provider.value, account.id]:
                raise ProviderError(ErrorCode.UNCONFIGURED)
            secret = self._secrets.read(account.credential_ref)
            if not secret:
                raise ProviderError(ErrorCode.UNCONFIGURED)
            if any(char in secret for char in "\r\n\x00"):
                raise ProviderError(ErrorCode.AUTH_REQUIRED)
        except CredentialError:
            self.failed.emit(ticket, ProviderError(ErrorCode.AUTH_REQUIRED))
            return
        except ProviderError as error:
            self.failed.emit(ticket, error)
            return
        request = QNetworkRequest(QUrl(self.ENDPOINTS[self.provider]))
        request.setAttribute(QNetworkRequest.Attribute.RedirectPolicyAttribute,
                             QNetworkRequest.RedirectPolicy.ManualRedirectPolicy)
        request.setTransferTimeout(10_000)
        authorization = f"Bearer {secret}" if self.provider == Provider.DEEPSEEK else secret
        request.setRawHeader(QByteArray(b"Authorization"), QByteArray(authorization.encode("utf-8")))
        request.setRawHeader(QByteArray(b"Accept"), QByteArray(b"application/json"))
        request.setRawHeader(QByteArray(b"User-Agent"), QByteArray(b"usage/0.1"))
        reply = self._manager.get(request)
        reply.setReadBufferSize(MAX_RESPONSE_BYTES + 1)
        self._requests[account.id] = (ticket, reply)
        deadline = QTimer(reply)
        deadline.setSingleShot(True)
        def expire() -> None:
            reply.setProperty("deadlineExpired", True)
            reply.abort()
        deadline.timeout.connect(expire)
        deadline.start(10_000)
        reply.finished.connect(deadline.stop)
        reply.downloadProgress.connect(lambda received, total: self._limit(account.id, received))
        reply.finished.connect(lambda: self._finish(account, ticket, reply))

    def _limit(self, account_id: str, received: int) -> None:
        active = self._requests.get(account_id)
        if active and received > MAX_RESPONSE_BYTES:
            ticket, reply = self._requests.pop(account_id)
            reply.abort()
            reply.deleteLater()
            self.failed.emit(ticket, ProviderError(ErrorCode.INCOMPATIBLE))

    def _finish(self, account: Account, ticket: RequestTicket, reply: QNetworkReply) -> None:
        if self._requests.get(account.id) != (ticket, reply):
            return
        self._requests.pop(account.id)
        now = datetime.now(UTC)
        status = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        try:
            if reply.property("deadlineExpired"):
                raise ProviderError(ErrorCode.TIMEOUT)
            if status is not None:
                error = http_error(int(status), bytes(reply.rawHeader("Retry-After").data()).decode("ascii", errors="ignore"), now)
                if error:
                    raise error
            if reply.error() != QNetworkReply.NetworkError.NoError:
                code = ErrorCode.TIMEOUT if reply.error() in (
                    QNetworkReply.NetworkError.TimeoutError,
                    QNetworkReply.NetworkError.OperationCanceledError) else ErrorCode.NETWORK
                raise ProviderError(code)
            raw = decode_response(bytes(reply.readAll().data()))
            if self.provider == Provider.GLM:
                self.schema_observed.emit(glm_schema_observation(raw))
            snapshot = (parse_deepseek(raw, account, now) if self.provider == Provider.DEEPSEEK
                        else parse_glm(raw, account, now, self._mapping))
            self.succeeded.emit(ticket, snapshot)
        except ProviderError as error:
            self.failed.emit(ticket, error)
        finally:
            reply.deleteLater()

    def cancel(self, account_id: str) -> None:
        active = self._requests.pop(account_id, None)
        if active:
            active[1].abort()
            active[1].deleteLater()


def find_codex_executable() -> str | None:
    resolved = shutil.which("codex.exe" if os.name == "nt" else "codex")
    if resolved:
        return resolved
    base = os.environ.get("LOCALAPPDATA")
    if os.name == "nt" and base:
        # Discover installed binaries only. Never inspect credentials or process command lines.
        candidates = list((Path(base) / "OpenAI" / "Codex" / "bin").glob("*/codex.exe"))
        if candidates:
            return str(max(candidates, key=lambda path: path.stat().st_mtime))
    return None


class CodexAdapter(ProviderAdapter):
    """Owns one short-lived official app-server for each readonly snapshot."""

    def __init__(self, parent: QObject | None = None, *, executable: str | None = None,
                 process_factory: Callable[[], QProcess] | None = None) -> None:
        super().__init__(parent)
        self._auto_executable = executable is None
        self.executable = executable or find_codex_executable()
        self._factory = process_factory or (lambda: QProcess(self))
        self._process: QProcess | None = None
        self._active: tuple[Account, RequestTicket] | None = None
        self._buffer = bytearray()
        self._phase = ""
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(lambda: self._fail(ProviderError(ErrorCode.TIMEOUT)))

    def read(self, account: Account, ticket: RequestTicket) -> None:
        if account.provider != Provider.CODEX or account.id != ticket.account_id:
            raise ValueError("Adapter/account mismatch")
        if self._active:
            raise ValueError("Request already in flight")
        if self._auto_executable and (not self.executable or not Path(self.executable).is_file()):
            # Desktop updates replace versioned binaries while usage stays open.
            # Re-discover only when the cached program disappears; an explicit
            # override remains authoritative and is never silently substituted.
            self.executable = find_codex_executable()
        if not self.executable:
            self.failed.emit(ticket, ProviderError(ErrorCode.UNCONFIGURED))
            return
        self._active = (account, ticket)
        self._buffer.clear()
        self._phase = "initialize"
        process = self._factory()
        self._process = process
        process.setProcessChannelMode(QProcess.ProcessChannelMode.SeparateChannels)
        process.started.connect(lambda: self._initialize() if self._process is process else None)
        process.readyReadStandardOutput.connect(lambda: self._consume() if self._process is process else None)
        process.readyReadStandardError.connect(lambda: process.readAllStandardError())
        process.errorOccurred.connect(lambda error: self._process_error(error)
                                     if self._process is process else None)
        process.finished.connect(lambda code, status: self._fail(ProviderError(ErrorCode.SERVICE))
                                 if self._process is process else None)
        self._timer.start(10_000)
        process.start(self.executable, ["app-server", "--listen", "stdio://"])

    def _process_error(self, error: QProcess.ProcessError) -> None:
        code = (ErrorCode.UNCONFIGURED if error == QProcess.ProcessError.FailedToStart else
                ErrorCode.TIMEOUT if error == QProcess.ProcessError.Timedout else ErrorCode.SERVICE)
        self._fail(ProviderError(code))

    def _send(self, value: dict[str, object]) -> None:
        # Deliberately no generic RPC entrypoint on the public adapter.
        if value.get("method") not in ("initialize", "initialized", "account/rateLimits/read", None):
            raise ValueError("This adapter only reads quotas")
        if self._process:
            self._process.write((json.dumps(value) + "\n").encode("utf-8"))

    def _initialize(self) -> None:
        self._send({"id": 1, "method": "initialize", "params": {
            "clientInfo": {"name": "usage", "title": "usage", "version": "0.1.0"}}})

    def _consume(self) -> None:
        process = self._process
        if not process or not self._active:
            return
        self._buffer.extend(process.readAllStandardOutput().data())
        if len(self._buffer) > MAX_RESPONSE_BYTES:
            self._fail(ProviderError(ErrorCode.INCOMPATIBLE))
            return
        while b"\n" in self._buffer and self._active:
            line, _, rest = self._buffer.partition(b"\n")
            self._buffer = bytearray(rest)
            if not line.strip():
                continue
            try:
                message = object_map(decode_response(bytes(line)))
                self._message(message)
            except ProviderError as error:
                self._fail(error)

    def _message(self, message: dict[str, object]) -> None:
        if "method" in message:
            if "id" in message:
                self._send({"id": message["id"], "error": {"code": -32601, "message": "Unsupported request"}})
            return  # Quota reads never approve tools, sessions or login requests.
        expected_id = 1 if self._phase == "initialize" else 2
        if message.get("id") != expected_id:
            return
        if message.get("error") is not None:
            error = object_map(message["error"])
            code = error.get("code")
            # Inspect a message only to classify it. It is never retained/logged.
            text = str(error.get("message", "")).lower()
            auth = code in (401, 403) or any(word in text for word in ("not logged", "unauthorized", "authentication", "sign in"))
            self._fail(ProviderError(ErrorCode.AUTH_REQUIRED if auth else ErrorCode.SERVICE))
            return
        if "result" not in message:
            raise ProviderError(ErrorCode.INCOMPATIBLE)
        if self._phase == "initialize":
            self._phase = "quota"
            self._send({"method": "initialized", "params": {}})
            self._send({"id": 2, "method": "account/rateLimits/read", "params": {}})
        elif self._active:
            account, ticket = self._active
            snapshot: UsageSnapshot = parse_codex(message["result"], account, datetime.now(UTC))
            self._stop()
            self.succeeded.emit(ticket, snapshot)

    def _fail(self, error: ProviderError) -> None:
        if self._active:
            ticket = self._active[1]
            self._stop()
            self.failed.emit(ticket, error)

    def _stop(self) -> None:
        self._active = None
        self._timer.stop()
        process, self._process = self._process, None
        self._buffer.clear()
        if process:
            # Terminate only the process this adapter created; never the desktop app.
            process.kill()
            process.finished.connect(process.deleteLater)
            if process.state() == QProcess.ProcessState.NotRunning:
                process.deleteLater()

    def cancel(self, account_id: str) -> None:
        if self._active and self._active[0].id == account_id:
            self._stop()
