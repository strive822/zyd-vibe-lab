"""Only this adapter accesses Windows Credential Manager; never a file fallback."""

from __future__ import annotations

import ctypes
import os
from ctypes import wintypes
from typing import Protocol
from uuid import UUID, uuid4

from .models import Provider


class CredentialError(Exception):
    pass


class SecretStore(Protocol):
    def read(self, reference: str) -> str | None: ...
    def write(self, reference: str, secret: str) -> None: ...
    def delete(self, reference: str) -> None: ...


def new_reference(provider: Provider, account_id: str) -> str:
    UUID(account_id)
    return f"Duizhaoye/{provider.value}/{account_id}/{uuid4()}"


def validate_reference(reference: str) -> None:
    parts = reference.split("/")
    try:
        if len(parts) != 4 or parts[0] != "Duizhaoye":
            raise ValueError
        Provider(parts[1])
        UUID(parts[2])
        UUID(parts[3])
    except ValueError:
        raise CredentialError("Invalid application credential reference") from None


class _Credential(ctypes.Structure):
    _fields_ = [
        ("Flags", wintypes.DWORD), ("Type", wintypes.DWORD),
        ("TargetName", wintypes.LPWSTR), ("Comment", wintypes.LPWSTR),
        ("LastWritten", wintypes.FILETIME), ("CredentialBlobSize", wintypes.DWORD),
        ("CredentialBlob", ctypes.POINTER(wintypes.BYTE)),
        ("Persist", wintypes.DWORD), ("AttributeCount", wintypes.DWORD),
        ("Attributes", ctypes.c_void_p), ("TargetAlias", wintypes.LPWSTR), ("UserName", wintypes.LPWSTR),
    ]


class WindowsCredentialStore:
    def __init__(self) -> None:
        if os.name != "nt":
            raise CredentialError("Windows Credential Manager is required")
        self._api = ctypes.WinDLL("Advapi32.dll", use_last_error=True)
        self._api.CredReadW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                                      ctypes.POINTER(ctypes.POINTER(_Credential))]
        self._api.CredReadW.restype = wintypes.BOOL
        self._api.CredWriteW.argtypes = [ctypes.POINTER(_Credential), wintypes.DWORD]
        self._api.CredWriteW.restype = wintypes.BOOL
        self._api.CredDeleteW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]
        self._api.CredDeleteW.restype = wintypes.BOOL
        self._api.CredFree.argtypes = [ctypes.c_void_p]
        self._api.CredFree.restype = None

    def read(self, reference: str) -> str | None:
        validate_reference(reference)
        pointer = ctypes.POINTER(_Credential)()
        if not self._api.CredReadW(reference, 1, 0, ctypes.byref(pointer)):
            if ctypes.get_last_error() == 1168:  # ERROR_NOT_FOUND
                return None
            raise CredentialError("Secure credential read failed")
        try:
            value = pointer.contents
            if value.CredentialBlobSize > 2560:
                raise CredentialError("Invalid credential size")
            try:
                return ctypes.string_at(value.CredentialBlob, value.CredentialBlobSize).decode("utf-8")
            except UnicodeDecodeError:
                raise CredentialError("Invalid stored credential") from None
        finally:
            self._api.CredFree(pointer)

    def write(self, reference: str, secret: str) -> None:
        validate_reference(reference)
        raw = secret.encode("utf-8")
        if not raw or len(raw) > 2560 or any(char in secret for char in "\r\n\x00"):
            raise CredentialError("Invalid credential value")
        buffer = (wintypes.BYTE * len(raw)).from_buffer_copy(raw)
        value = _Credential()
        value.Type = 1  # CRED_TYPE_GENERIC
        value.TargetName = reference
        value.CredentialBlobSize = len(raw)
        value.CredentialBlob = ctypes.cast(buffer, ctypes.POINTER(wintypes.BYTE))
        value.Persist = 2  # Same user, this computer, subsequent logon sessions.
        try:
            if not self._api.CredWriteW(ctypes.byref(value), 0):
                raise CredentialError("Secure credential save failed")
        finally:
            ctypes.memset(buffer, 0, len(raw))

    def delete(self, reference: str) -> None:
        validate_reference(reference)
        if not self._api.CredDeleteW(reference, 1, 0) and ctypes.get_last_error() != 1168:
            raise CredentialError("Secure credential removal failed")
