"""Explicit Windows current-user DPAPI state; no implicit initialization.

Only KeyStore.manage mutates state. Every access checks ancestors and the
protected single-user DACL. Fail closed on unsupported platforms or ACLs.
"""
import ctypes
import hashlib
import hmac
import os
import secrets
import stat
from pathlib import Path
from ctypes import wintypes as W

from .discovery import checked_stat, bounded_read


class Blob(ctypes.Structure):
    _fields_ = [("size", W.DWORD), ("data", ctypes.POINTER(ctypes.c_ubyte))]


class SecurityAttributes(ctypes.Structure):
    _fields_ = [("length", W.DWORD), ("descriptor", W.LPVOID), ("inherit", W.BOOL)]


class WindowsProtection:
    def __init__(self):
        if os.name != "nt":
            raise OSError("windows_required")
        self.kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        self.advapi = ctypes.WinDLL("advapi32", use_last_error=True)
        self.crypt = ctypes.WinDLL("crypt32", use_last_error=True)
        # Declare pointer-sized arguments explicitly on 64-bit Windows.
        signatures = [
            (self.kernel, "GetCurrentProcess", [], W.HANDLE),
            (self.kernel, "CloseHandle", [W.HANDLE], W.BOOL),
            (self.kernel, "LocalFree", [W.LPVOID], W.LPVOID),
            (self.kernel, "CreateDirectoryW", [W.LPCWSTR, ctypes.POINTER(SecurityAttributes)], W.BOOL),
            (self.kernel, "CreateFileW", [W.LPCWSTR, W.DWORD, W.DWORD, ctypes.POINTER(SecurityAttributes), W.DWORD, W.DWORD, W.HANDLE], W.HANDLE),
            (self.advapi, "OpenProcessToken", [W.HANDLE, W.DWORD, ctypes.POINTER(W.HANDLE)], W.BOOL),
            (self.advapi, "GetTokenInformation", [W.HANDLE, ctypes.c_int, W.LPVOID, W.DWORD, ctypes.POINTER(W.DWORD)], W.BOOL),
            (self.advapi, "ConvertSidToStringSidW", [W.LPVOID, ctypes.POINTER(W.LPWSTR)], W.BOOL),
            (self.advapi, "ConvertStringSecurityDescriptorToSecurityDescriptorW", [W.LPCWSTR, W.DWORD, ctypes.POINTER(W.LPVOID), ctypes.POINTER(W.DWORD)], W.BOOL),
            (self.advapi, "GetNamedSecurityInfoW", [W.LPCWSTR, ctypes.c_int, W.DWORD, ctypes.POINTER(W.LPVOID), W.LPVOID, ctypes.POINTER(W.LPVOID), W.LPVOID, ctypes.POINTER(W.LPVOID)], W.DWORD),
            (self.advapi, "GetSecurityDescriptorControl", [W.LPVOID, ctypes.POINTER(W.WORD), ctypes.POINTER(W.DWORD)], W.BOOL),
            (self.advapi, "EqualSid", [W.LPVOID, W.LPVOID], W.BOOL),
            (self.advapi, "GetAce", [W.LPVOID, W.DWORD, ctypes.POINTER(W.LPVOID)], W.BOOL),
            (self.crypt, "CryptProtectData", [ctypes.POINTER(Blob), W.LPCWSTR, W.LPVOID, W.LPVOID, W.LPVOID, W.DWORD, ctypes.POINTER(Blob)], W.BOOL),
            (self.crypt, "CryptUnprotectData", [ctypes.POINTER(Blob), W.LPVOID, W.LPVOID, W.LPVOID, W.LPVOID, W.DWORD, ctypes.POINTER(Blob)], W.BOOL),
        ]
        for library, name, args, result in signatures:
            fn = getattr(library, name)
            fn.argtypes, fn.restype = args, result
        handle, size = W.HANDLE(), W.DWORD()
        if not self.advapi.OpenProcessToken(self.kernel.GetCurrentProcess(), 8, ctypes.byref(handle)):
            raise OSError("token_unavailable")
        try:
            self.advapi.GetTokenInformation(handle, 1, None, 0, ctypes.byref(size))
            self.token = ctypes.create_string_buffer(size.value)
            if not self.advapi.GetTokenInformation(handle, 1, self.token, size, ctypes.byref(size)):
                raise OSError("token_unavailable")
            self.sid = ctypes.cast(self.token, ctypes.POINTER(W.LPVOID))[0]
            sid_text = W.LPWSTR()
            if not self.advapi.ConvertSidToStringSidW(self.sid, ctypes.byref(sid_text)):
                raise OSError("sid_unavailable")
            try:
                self.sddl = "O:" + sid_text.value + "D:P(A;;FA;;;" + sid_text.value + ")"
            finally:
                self.kernel.LocalFree(ctypes.cast(sid_text, W.LPVOID))
        finally:
            self.kernel.CloseHandle(handle)

    def descriptor(self):
        descriptor = W.LPVOID()
        if not self.advapi.ConvertStringSecurityDescriptorToSecurityDescriptorW(self.sddl, 1, ctypes.byref(descriptor), None):
            raise OSError("descriptor_failed")
        return descriptor

    def verify(self, path):
        checked_stat(path)
        owner, dacl, descriptor = W.LPVOID(), W.LPVOID(), W.LPVOID()
        if self.advapi.GetNamedSecurityInfoW(str(path), 1, 5, ctypes.byref(owner), None, ctypes.byref(dacl), None, ctypes.byref(descriptor)):
            raise OSError("acl_unavailable")
        try:
            control, revision = W.WORD(), W.DWORD()
            if not self.advapi.GetSecurityDescriptorControl(descriptor, ctypes.byref(control), ctypes.byref(revision)):
                raise OSError("acl_unavailable")
            # ACL header: BYTE revision, BYTE padding, WORD size, WORD count.
            if not dacl or not control.value & 0x1000 or not self.advapi.EqualSid(owner, self.sid):
                raise OSError("unsafe_acl")
            if ctypes.cast(dacl, ctypes.POINTER(W.WORD))[2] != 1:
                raise OSError("unsafe_acl")
            ace = W.LPVOID()
            if not self.advapi.GetAce(dacl, 0, ctypes.byref(ace)):
                raise OSError("unsafe_acl")
            # Exactly one non-inherited ACCESS_ALLOWED_ACE, FILE_ALL_ACCESS,
            # current user SID. No Everyone, groups, SYSTEM or extra grants.
            head = ctypes.string_at(ace, 8)
            if head[:2] != b"\x00\x00" or int.from_bytes(head[4:8], "little") != 0x1F01FF or not self.advapi.EqualSid(ace.value + 8, self.sid):
                raise OSError("unsafe_acl")
        finally:
            self.kernel.LocalFree(descriptor)

    def create(self, path, data=None):
        checked_stat(path.parent)
        descriptor = self.descriptor()
        attrs = SecurityAttributes(ctypes.sizeof(SecurityAttributes), descriptor, False)
        try:
            if data is None:
                if not self.kernel.CreateDirectoryW(str(path), ctypes.byref(attrs)):
                    raise OSError("secure_directory_failed")
            else:
                import msvcrt
                handle = self.kernel.CreateFileW(str(path), 0x40000000, 0, ctypes.byref(attrs), 1, 0x00200080, None)
                if handle == W.HANDLE(-1).value:
                    raise OSError("secure_file_failed")
                try:
                    fd = msvcrt.open_osfhandle(handle, os.O_WRONLY | os.O_BINARY)
                except BaseException:
                    self.kernel.CloseHandle(handle)
                    raise
                with os.fdopen(fd, "wb") as stream:
                    stream.write(data)
                    stream.flush()
                    os.fsync(stream.fileno())
            self.verify(path)
        finally:
            self.kernel.LocalFree(descriptor)

    def transform(self, data, encrypt):
        memory = (ctypes.c_ubyte * len(data)).from_buffer_copy(data)
        source, result = Blob(len(data), memory), Blob()
        if encrypt:
            ok = self.crypt.CryptProtectData(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(result))
        else:
            ok = self.crypt.CryptUnprotectData(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(result))
        if not ok:
            raise OSError("protection_failed")
        try:
            return ctypes.string_at(result.data, result.size)
        finally:
            self.kernel.LocalFree(result.data)


def derive(key, purpose, value):
    return hmac.new(key, b"WindowsAIDoctor/v1/" + purpose.encode("ascii") + b"\x00" + value, hashlib.sha256).hexdigest()


class KeyStore:
    def __init__(self):
        root = os.environ.get("LOCALAPPDATA", "")
        if not root or not Path(root).is_absolute():
            raise OSError("state_root_unavailable")
        self.directory = Path(root) / "WindowsAIDoctor" / "comparison"
        self.path = self.directory / "key.dat"

    def load(self):
        protection = WindowsProtection()
        protection.verify(self.directory)
        protection.verify(self.path)
        encrypted = bounded_read(self.path, 16384)
        key = protection.transform(encrypted, False)
        if len(key) != 32:
            raise ValueError("invalid_key")
        return key

    def status(self):
        try:
            key = self.load()
            return {"status": "available", "scope_code": "scope_" + derive(key, "scope", b"current")}
        except FileNotFoundError:
            return {"status": "missing", "scope_code": None}
        except (OSError, ValueError):
            return {"status": "unavailable", "scope_code": None}

    def manage(self, action):
        if action == "status":
            return self.status()
        protection = WindowsProtection()
        if action == "init":
            # Inspect root-to-leaf; never mkdir through an unchecked parent.
            for folder in (self.directory.parent, self.directory):
                try:
                    checked_stat(folder)
                except FileNotFoundError:
                    checked_stat(folder.parent)
                    protection.create(folder)
            protection.verify(self.directory)
            try:
                checked_stat(self.path)
            except FileNotFoundError:
                pass
            else:
                raise FileExistsError("key_exists")
            # Both protection and ACL setup finish before a byte is written.
            protection.create(self.path, protection.transform(secrets.token_bytes(32), True))
        elif action == "rotate":
            self.load()  # reject invalid/unavailable old state; preserve it
            temporary = self.directory / ("key-" + secrets.token_hex(16) + ".tmp")
            try:
                protection.create(temporary, protection.transform(secrets.token_bytes(32), True))
                protection.verify(self.path)
                os.replace(temporary, self.path)
            finally:
                try:
                    temporary.unlink()
                except FileNotFoundError:
                    pass
        elif action == "delete":
            self.load()
            self.path.unlink()
        else:
            raise ValueError("invalid_key_action")
        return self.status()
