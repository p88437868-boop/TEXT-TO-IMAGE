from __future__ import annotations

import ctypes
import time
from ctypes import wintypes
from dataclasses import dataclass

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
shell32 = ctypes.WinDLL("shell32", use_last_error=True)
advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000

WM_HOTKEY = 0x0312
WM_APP_STOP = 0x8001
WM_QUIT = 0x0012
WM_NCHITTEST = 0x0084
HTLEFT = 10
HTRIGHT = 11
HTTOP = 12
HTTOPLEFT = 13
HTTOPRIGHT = 14
HTBOTTOM = 15
HTBOTTOMLEFT = 16
HTBOTTOMRIGHT = 17

VK_CONTROL = 0x11
VK_SHIFT = 0x10
VK_MENU = 0x12
VK_LWIN = 0x5B
VK_RWIN = 0x5C
VK_V = 0x56
VK_A = 0x41
VK_C = 0x43

CF_TEXT = 1
CF_UNICODETEXT = 13

INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
TOKEN_QUERY = 0x0008
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
TOKEN_ELEVATION = 20

ULONG_PTR = ctypes.c_ulonglong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_ulong


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]


class _INPUTUNION(ctypes.Union):
    _fields_ = [
        ("mi", MOUSEINPUT),
        ("ki", KEYBDINPUT),
        ("hi", HARDWAREINPUT),
    ]


class INPUT(ctypes.Structure):
    _anonymous_ = ("union",)
    _fields_ = [("type", wintypes.DWORD), ("union", _INPUTUNION)]


class TOKEN_ELEVATION_STRUCT(ctypes.Structure):
    _fields_ = [("TokenIsElevated", wintypes.DWORD)]


user32.RegisterHotKey.argtypes = [
    wintypes.HWND,
    ctypes.c_int,
    wintypes.UINT,
    wintypes.UINT,
]
user32.RegisterHotKey.restype = wintypes.BOOL
user32.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]
user32.UnregisterHotKey.restype = wintypes.BOOL
user32.GetMessageW.argtypes = [
    ctypes.POINTER(wintypes.MSG),
    wintypes.HWND,
    wintypes.UINT,
    wintypes.UINT,
]
user32.GetMessageW.restype = ctypes.c_int
user32.TranslateMessage.argtypes = [ctypes.POINTER(wintypes.MSG)]
user32.DispatchMessageW.argtypes = [ctypes.POINTER(wintypes.MSG)]
user32.PostThreadMessageW.argtypes = [
    wintypes.DWORD,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
]
user32.PostThreadMessageW.restype = wintypes.BOOL
user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
user32.GetAsyncKeyState.restype = ctypes.c_short
user32.GetForegroundWindow.restype = wintypes.HWND
user32.GetWindowThreadProcessId.argtypes = [
    wintypes.HWND,
    ctypes.POINTER(wintypes.DWORD),
]
user32.GetWindowThreadProcessId.restype = wintypes.DWORD
user32.SendInput.argtypes = [
    wintypes.UINT,
    ctypes.POINTER(INPUT),
    ctypes.c_int,
]
user32.SendInput.restype = wintypes.UINT
user32.GetClipboardSequenceNumber.argtypes = []
user32.GetClipboardSequenceNumber.restype = wintypes.DWORD
user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetWindowTextW.restype = ctypes.c_int
user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
user32.GetWindowRect.restype = wintypes.BOOL
user32.IsZoomed.argtypes = [wintypes.HWND]
user32.IsZoomed.restype = wintypes.BOOL
user32.OpenClipboard.argtypes = [wintypes.HWND]
user32.OpenClipboard.restype = wintypes.BOOL
user32.CloseClipboard.argtypes = []
user32.CloseClipboard.restype = wintypes.BOOL
user32.GetClipboardData.argtypes = [wintypes.UINT]
user32.GetClipboardData.restype = wintypes.HANDLE
user32.EmptyClipboard.argtypes = []
user32.EmptyClipboard.restype = wintypes.BOOL
kernel32.GlobalLock.argtypes = [wintypes.HANDLE]
kernel32.GlobalLock.restype = ctypes.c_void_p
kernel32.GlobalUnlock.argtypes = [wintypes.HANDLE]
kernel32.GlobalUnlock.restype = wintypes.BOOL

kernel32.GetCurrentThreadId.restype = wintypes.DWORD
kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
kernel32.OpenProcess.restype = wintypes.HANDLE
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.GetCurrentProcess.restype = wintypes.HANDLE
advapi32.OpenProcessToken.argtypes = [
    wintypes.HANDLE,
    wintypes.DWORD,
    ctypes.POINTER(wintypes.HANDLE),
]
advapi32.OpenProcessToken.restype = wintypes.BOOL
advapi32.GetTokenInformation.argtypes = [
    wintypes.HANDLE,
    ctypes.c_int,
    ctypes.c_void_p,
    wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD),
]
advapi32.GetTokenInformation.restype = wintypes.BOOL


def register_hotkey(hotkey_id: int, modifiers: int, virtual_key: int) -> bool:
    return bool(user32.RegisterHotKey(None, hotkey_id, modifiers, virtual_key))


def unregister_hotkey(hotkey_id: int) -> None:
    user32.UnregisterHotKey(None, hotkey_id)


def last_error() -> int:
    return ctypes.get_last_error()


def get_current_thread_id() -> int:
    return int(kernel32.GetCurrentThreadId())


def post_thread_message(thread_id: int, message: int) -> bool:
    return bool(user32.PostThreadMessageW(thread_id, message, 0, 0))


def get_message(message: wintypes.MSG) -> int:
    return int(user32.GetMessageW(ctypes.byref(message), None, 0, 0))


def translate_message(message: wintypes.MSG) -> None:
    user32.TranslateMessage(ctypes.byref(message))


def dispatch_message(message: wintypes.MSG) -> None:
    user32.DispatchMessageW(ctypes.byref(message))


def modifier_keys_down() -> bool:
    keys = (VK_CONTROL, VK_SHIFT, VK_MENU, VK_LWIN, VK_RWIN)
    return any(user32.GetAsyncKeyState(key) & 0x8000 for key in keys)


def send_key_combination(virtual_key: int) -> bool:
    """Sends Ctrl+key with a short gap so the target app sees the modifier."""
    control_down = bool(user32.GetAsyncKeyState(VK_CONTROL) & 0x8000)
    if control_down:
        # The user is still holding Ctrl: keep it down, but make sure the
        # target saw a Ctrl-down before the key.
        definitions = (
            (VK_CONTROL, 0),
            (virtual_key, 0),
            (virtual_key, KEYEVENTF_KEYUP),
        )
    else:
        definitions = (
            (VK_CONTROL, 0),
            (virtual_key, 0),
            (virtual_key, KEYEVENTF_KEYUP),
            (VK_CONTROL, KEYEVENTF_KEYUP),
        )

    def send(key: int, flags: int) -> bool:
        event = INPUT()
        event.type = INPUT_KEYBOARD
        event.ki = KEYBDINPUT(
            wVk=key,
            wScan=0,
            dwFlags=flags,
            time=0,
            dwExtraInfo=0,
        )
        return user32.SendInput(1, ctypes.byref(event), ctypes.sizeof(INPUT)) == 1

    for key, flags in definitions:
        if not send(key, flags):
            send(virtual_key, KEYEVENTF_KEYUP)
            if not control_down:
                send(VK_CONTROL, KEYEVENTF_KEYUP)
            return False
        time.sleep(0.012)
    return True


def clear_clipboard() -> bool:
    """Empties the system clipboard without going through Qt."""
    for _ in range(8):
        if user32.OpenClipboard(None):
            try:
                return bool(user32.EmptyClipboard())
            finally:
                user32.CloseClipboard()
        time.sleep(0.02)
    return False


def get_clipboard_text() -> str:
    """Reads CF_UNICODETEXT directly, bypassing Qt's clipboard cache."""
    opened = False
    for _ in range(8):
        if user32.OpenClipboard(None):
            opened = True
            break
        time.sleep(0.02)
    if not opened:
        return ""
    try:
        handle = user32.GetClipboardData(CF_UNICODETEXT)
        if handle:
            pointer = kernel32.GlobalLock(handle)
            if pointer:
                try:
                    return ctypes.wstring_at(int(pointer))
                finally:
                    kernel32.GlobalUnlock(handle)
        handle = user32.GetClipboardData(CF_TEXT)
        if handle:
            pointer = kernel32.GlobalLock(handle)
            if pointer:
                try:
                    raw = ctypes.string_at(int(pointer))
                    return raw.decode("mbcs", errors="replace")
                finally:
                    kernel32.GlobalUnlock(handle)
        return ""
    finally:
        user32.CloseClipboard()


def _process_token_elevated(process_handle: int) -> bool:
    token = wintypes.HANDLE()
    if not advapi32.OpenProcessToken(process_handle, TOKEN_QUERY, ctypes.byref(token)):
        return False
    try:
        elevation = TOKEN_ELEVATION_STRUCT()
        returned = wintypes.DWORD()
        ok = advapi32.GetTokenInformation(
            token,
            TOKEN_ELEVATION,
            ctypes.byref(elevation),
            ctypes.sizeof(elevation),
            ctypes.byref(returned),
        )
        return bool(ok and elevation.TokenIsElevated)
    finally:
        kernel32.CloseHandle(token)


def is_process_elevated(process_id: int) -> bool:
    if process_id <= 0:
        return False
    handle = kernel32.OpenProcess(
        PROCESS_QUERY_LIMITED_INFORMATION, False, process_id
    )
    if not handle:
        return False
    try:
        return _process_token_elevated(handle)
    finally:
        kernel32.CloseHandle(handle)


def is_current_process_elevated() -> bool:
    return _process_token_elevated(kernel32.GetCurrentProcess())


@dataclass(frozen=True)
class ForegroundInfo:
    hwnd: int
    process_id: int
    title: str
    elevated: bool


def foreground_info() -> ForegroundInfo | None:
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return None
    process_id = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
    title_buffer = ctypes.create_unicode_buffer(512)
    user32.GetWindowTextW(hwnd, title_buffer, len(title_buffer))
    return ForegroundInfo(
        hwnd=int(hwnd),
        process_id=int(process_id.value),
        title=title_buffer.value,
        elevated=is_process_elevated(int(process_id.value)),
    )


def clipboard_sequence() -> int:
    return int(user32.GetClipboardSequenceNumber())


def target_blocks_input() -> bool:
    target = foreground_info()
    if target is None:
        return True
    return target.elevated and not is_current_process_elevated()


def resize_hit_test(hwnd: int, screen_x: int, screen_y: int, border: int = 7) -> int:
    if not hwnd or user32.IsZoomed(hwnd):
        return 0
    rect = wintypes.RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        return 0
    left = abs(screen_x - rect.left) <= border
    right = abs(screen_x - rect.right) <= border
    top = abs(screen_y - rect.top) <= border
    bottom = abs(screen_y - rect.bottom) <= border
    if top and left:
        return HTTOPLEFT
    if top and right:
        return HTTOPRIGHT
    if bottom and left:
        return HTBOTTOMLEFT
    if bottom and right:
        return HTBOTTOMRIGHT
    if left:
        return HTLEFT
    if right:
        return HTRIGHT
    if top:
        return HTTOP
    if bottom:
        return HTBOTTOM
    return 0


def set_app_user_model_id(app_id: str) -> None:
    try:
        shell32.SetCurrentProcessExplicitAppUserModelID(ctypes.c_wchar_p(app_id))
    except Exception:
        pass
