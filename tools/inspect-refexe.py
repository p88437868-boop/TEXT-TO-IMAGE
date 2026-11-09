#!/usr/bin/env python
"""Dump the code structure of the already-extracted reference PyInstaller app.

The reference executable was built with Python 3.10, but this project's venv
runs 3.12, so the built-in marshal module cannot read its .pyc files
("bad marshal data (unknown type code)"). This version unmarshals through
the xdis library, which supports cross-version bytecode, and falls back to
plain marshal when the versions happen to match.

Outputs:
  .tools/ref-summary.txt  compact report: per module, per function, the
                          constants and identifiers it uses. This is the
                          useful file - it reveals fonts, sizes, padding,
                          Pillow/Tk calls without needing a decompiler.
  .tools/ref-dis.txt      full disassembly of the functions that look like
                          drawing/sizing code (font, image, draw, size...).

Extraction is reused from .tools/ref-extract (already done); pass --reextract
to redo it.

Run with:
    .venv\\Scripts\\python.exe tools\\inspect-refexe.py
"""

from __future__ import annotations

import marshal
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
TOOLS = PROJECT / ".tools"
WORK = TOOLS / "ref-extract"
LIB = TOOLS / "reveng-lib"
SUMMARY = TOOLS / "ref-summary.txt"
DIS_FILE = TOOLS / "ref-dis.txt"
EXTRACTED = WORK / "ref_app.exe_extracted"

STDLIB_MARKERS = ("\\lib\\", "/lib/", "site-packages", "\\lib64\\", "/lib64/")
INTEREST = ("font", "image", "draw", "text", "size", "scale", "render", "thumb",
            "width", "height", "bbox", "wrap", "png", "save", "clip")
MAX_CONST = 120

sys.path.insert(0, str(LIB))

# ---------------------------------------------------------------- unmarshal


def load_code(path: Path):
    """Return (code_object, how) for a .pyc, or (None, reason)."""
    data = path.read_bytes()

    if data[:4] == __import__("importlib.util").util.MAGIC_NUMBER:
        try:
            obj = marshal.loads(data[16:])
            if hasattr(obj, "co_code"):
                return obj, "marshal"
        except Exception:  # noqa: BLE001
            pass

    try:
        from xdis.load import load_module
    except Exception as exc:  # noqa: BLE001
        return None, f"xdis import failed: {exc}"

    try:
        result = load_module(str(path))
    except Exception as exc:  # noqa: BLE001
        return None, f"xdis failed: {exc}"

    version = result[0] if result else "?"
    for item in result:
        if hasattr(item, "co_code"):
            return item, f"xdis {version}"
    return None, f"no code object (xdis {version})"


# ---------------------------------------------------------------- reporting


def short(value: object) -> str:
    if hasattr(value, "co_code"):
        return f"<code {value.co_name}>"
    try:
        text = repr(value)
    except Exception:  # noqa: BLE001
        return "<unrepr>"
    if len(text) > MAX_CONST:
        text = text[:MAX_CONST] + "..."
    return text


def walk(code):
    """Yield every code object, outermost first."""
    yield code
    for const in getattr(code, "co_consts", ()):
        if hasattr(const, "co_code"):
            yield from walk(const)


def is_interesting(code) -> bool:
    blob = " ".join(
        [code.co_name]
        + list(getattr(code, "co_names", ()))
        + [short(c) for c in getattr(code, "co_consts", ()) if not hasattr(c, "co_code")]
    ).lower()
    return any(needle in blob for needle in INTEREST)


def disassemble(code) -> str:
    try:
        from xdis.bytecode import Bytecode
        from xdis.opcodes import opcode_310 as opc

        table = opc.opcode_310
        out = []
        for ins in Bytecode(code, table).get_instructions(code):
            arg = getattr(ins, "argval", None)
            if isinstance(arg, str) and len(arg) > 60:
                arg = arg[:60] + "..."
            out.append(f"{ins.offset:6d} {ins.opname:<28} {arg!r}")
        return "\n".join(out)
    except Exception as exc:  # noqa: BLE001
        return f"<disassembly unavailable: {exc}>"


def describe(fh, code, depth: int = 0) -> None:
    pad = "    " * depth
    args = list(getattr(code, "co_varnames", ())[: getattr(code, "co_argcount", 0)])
    fh.write(f"{pad}def {code.co_name}({', '.join(args)})\n")
    consts = [c for c in getattr(code, "co_consts", ()) if not hasattr(c, "co_code")]
    if consts:
        fh.write(f"{pad}  consts: {', '.join(short(c) for c in consts)}\n")
    names = list(getattr(code, "co_names", ()))
    if names:
        fh.write(f"{pad}  names:  {', '.join(names)}\n")
    locals_ = list(getattr(code, "co_varnames", ())[getattr(code, "co_argcount", 0):])
    if locals_:
        fh.write(f"{pad}  locals: {', '.join(locals_)}\n")
    for const in getattr(code, "co_consts", ()):
        if hasattr(const, "co_code"):
            describe(fh, const, depth + 1)


# ---------------------------------------------------------------- main


def main() -> int:
    if not EXTRACTED.exists():
        raise SystemExit(
            f"Extracted folder not found: {EXTRACTED}\n"
            "Run the extract step first (it was already run once), or delete\n"
            f"{WORK} and re-run this script."
        )

    pycs = sorted(EXTRACTED.rglob("*.pyc"))
    print(f"Found {len(pycs)} .pyc files in {EXTRACTED}", flush=True)

    modules = []
    broken = []
    for pyc in pycs:
        code, how = load_code(pyc)
        if code is None:
            broken.append(f"{pyc.relative_to(EXTRACTED).as_posix()}  ->  {how}")
            continue
        filename = (getattr(code, "co_filename", "") or "")
        if any(marker in filename.lower() for marker in STDLIB_MARKERS):
            continue
        modules.append((pyc.relative_to(EXTRACTED).as_posix(), pyc, code, how))

    print(f"{len(modules)} app modules, {len(broken)} unreadable", flush=True)

    with SUMMARY.open("w", encoding="utf-8", errors="replace") as fh:
        fh.write(f"reference exe: {PROJECT / 'Sufyan Text to Image.exe'}\n")
        fh.write(f"extracted:     {EXTRACTED}\n")
        fh.write(f"host python:   {sys.version.split()[0]}\n\n")

        if broken:
            fh.write(f"== unreadable ({len(broken)}) ==\n")
            for line in broken[:40]:
                fh.write("  " + line + "\n")
            if len(broken) > 40:
                fh.write(f"  ... and {len(broken) - 40} more\n")
            fh.write("\n")

        for rel, _pyc, code, how in modules:
            fh.write("=" * 78 + "\n")
            fh.write(f"MODULE {rel}   [{how}]\n")
            fh.write(f"SOURCE {getattr(code, 'co_filename', '?')}\n")
            fh.write("=" * 78 + "\n")
            describe(fh, code)
            fh.write("\n")

    with DIS_FILE.open("w", encoding="utf-8", errors="replace") as fh:
        fh.write("Disassembly of functions that reference drawing/sizing terms.\n\n")
        for rel, _pyc, code, _how in modules:
            header_written = False
            for sub in walk(code):
                if not is_interesting(sub):
                    continue
                if not header_written:
                    fh.write("=" * 78 + f"\nMODULE {rel}\n" + "=" * 78 + "\n")
                    header_written = True
                fh.write(f"\n### {rel} :: {sub.co_name}\n")
                fh.write(disassemble(sub) + "\n")

    print(f"\nWrote {SUMMARY} ({SUMMARY.stat().st_size:,} bytes)")
    print(f"Wrote {DIS_FILE} ({DIS_FILE.stat().st_size:,} bytes)")
    print("\nApp modules:")
    for rel, _pyc, _code, how in modules:
        print(f"  {rel}  [{how}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
