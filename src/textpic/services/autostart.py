from __future__ import annotations

import sys
import winreg
from pathlib import Path

from textpic.paths import project_root


RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
VALUE_NAME = "TextPicStudio"


def startup_command() -> str:
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}" --startup'
    pythonw = Path(sys.executable).with_name("pythonw.exe")
    launcher = project_root() / "main.pyw"
    return f'"{pythonw}" "{launcher}" --startup'


class AutostartService:
    def is_enabled(self) -> bool:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
                value, _ = winreg.QueryValueEx(key, VALUE_NAME)
                return bool(value)
        except OSError:
            return False

    def set_enabled(self, enabled: bool) -> None:
        if enabled:
            with winreg.CreateKeyEx(
                winreg.HKEY_CURRENT_USER,
                RUN_KEY,
                0,
                winreg.KEY_SET_VALUE,
            ) as key:
                winreg.SetValueEx(
                    key,
                    VALUE_NAME,
                    0,
                    winreg.REG_SZ,
                    startup_command(),
                )
        else:
            try:
                with winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    RUN_KEY,
                    0,
                    winreg.KEY_SET_VALUE,
                ) as key:
                    winreg.DeleteValue(key, VALUE_NAME)
            except FileNotFoundError:
                pass
            except OSError:
                pass
