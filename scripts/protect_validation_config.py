"""Temporary Windows DPAPI transport for authorized collector QA/secret setup.

Plaintext exists only in memory. No secret in argv, stdout or source. The
encrypted blob is scoped to the current Windows user and removed after setup.
"""
import ctypes
from ctypes import wintypes
import getpass
import json
import os
from pathlib import Path

CONFIG = Path('.tmp/validation-qa.dpapi')


def crypt(data, protect):
    if os.name != 'nt':
        raise RuntimeError('Windows DPAPI required')
    class Blob(ctypes.Structure):
        _fields_ = [('size', wintypes.DWORD), ('data', ctypes.POINTER(ctypes.c_ubyte))]
    source = ctypes.create_string_buffer(data)
    incoming = Blob(len(data), ctypes.cast(source, ctypes.POINTER(ctypes.c_ubyte)))
    outgoing = Blob()
    api = ctypes.WinDLL('crypt32', use_last_error=True)
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    if protect:
        ok = api.CryptProtectData(ctypes.byref(incoming), None, None, None, None, 1, ctypes.byref(outgoing))
    else:
        ok = api.CryptUnprotectData(ctypes.byref(incoming), None, None, None, None, 1, ctypes.byref(outgoing))
    if not ok:
        raise RuntimeError('Native DPAPI operation failed')
    try:
        return ctypes.string_at(outgoing.data, outgoing.size)
    finally:
        kernel.LocalFree(ctypes.cast(outgoing.data, ctypes.c_void_p))


def load_config():
    blob = CONFIG.read_bytes()
    if len(blob) > 16384:
        raise RuntimeError('Protected QA configuration exceeded its bound')
    return json.loads(crypt(blob, False))


if __name__ == '__main__':
    print('DPAPI_READY_FOR_CONFIG', flush=True)
    raw = getpass.getpass('').encode('utf-8')
    value = json.loads(raw)
    expected = {'endpoint', 'contactKey', 'readKey', 'qaKey'}
    if set(value) != expected or any(not isinstance(v, str) for v in value.values()) or len(raw) > 4096:
        raise SystemExit('Unexpected QA configuration')
    target = CONFIG.resolve()
    if Path.cwd().resolve() not in target.parents:
        raise SystemExit('Protected file must remain in workspace')
    CONFIG.write_bytes(crypt(raw, True))
    print(json.dumps({'dpapi_protected': True, 'plaintext_written': False}), flush=True)
