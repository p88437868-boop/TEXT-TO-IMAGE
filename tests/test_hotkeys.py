from __future__ import annotations

import pytest

from textpic.services.hotkeys import normalize_hotkey, parse_hotkey


@pytest.mark.parametrize(
    ("sequence", "expected"),
    [
        ("F6", "F6"),
        ("f9", "F9"),
        ("Ctrl+Alt+1", "Ctrl+Alt+1"),
        ("shift + control + f12", "Ctrl+Shift+F12"),
        ("Win+Space", "Win+SPACE"),
    ],
)
def test_normalize_hotkey(sequence: str, expected: str) -> None:
    assert normalize_hotkey(sequence) == expected


@pytest.mark.parametrize(
    "sequence",
    ["", "Ctrl", "Ctrl+Alt", "A+B", "F25", "Hyper+A", "Ctrl+Shift+Plus"],
)
def test_invalid_hotkeys(sequence: str) -> None:
    with pytest.raises(ValueError):
        parse_hotkey(sequence)


def test_parse_hotkey_modifier_masks() -> None:
    modifiers, key = parse_hotkey("Ctrl+Alt+F8")
    assert modifiers & 0x0002
    assert modifiers & 0x0001
    assert key == 0x77
