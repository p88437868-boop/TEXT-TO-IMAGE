# TextPic Studio

TextPic Studio turns a typed message into a Messenger-style PNG and puts it on the clipboard, ready to paste into any chat.

- **F6** renders the current message and copies the image.
- **F9** pastes the copied image into the focused chat window without stealing focus.
- **F8** opens History.
- **Ctrl+Alt+1** through **Ctrl+Alt+9** apply saved templates.
- Light/dark themes, message styles, font sizing, emoji, timestamps, and message grouping.
- Local history, templates, settings, and image files. No account or upload is required.

## Requirements

- Windows 10 version 1809 or later, or Windows 11, 64-bit.
- The installer is per-machine and requires administrator approval.
- The MSI bundles the Python runtime, Qt, and application assets; Python is not required on the target PC.

## Install

1. Run `TextPicStudio-1.0.3-x64.msi`.
2. Approve the UAC prompt.
3. Choose an install folder or keep `C:\Program Files\TextPic Studio`.
4. Leave **Launch TextPic Studio** checked to start the app when setup finishes.

Silent install:

```powershell
msiexec /i .\TextPicStudio-1.0.3-x64.msi /qn
```

Silent install with Windows startup enabled:

```powershell
msiexec /i .\TextPicStudio-1.0.3-x64.msi /qn AUTOSTART=1
```

Uninstall from **Settings > Apps > Installed apps**, or:

```powershell
msiexec /x .\TextPicStudio-1.0.3-x64.msi /qn
```

Uninstalling removes the application and shortcuts but deliberately preserves user data in `%APPDATA%\TextPicStudio`.

The MSI is currently unsigned. Windows SmartScreen may show an unknown-publisher warning. Sign the EXE and MSI with an Authenticode certificate before public distribution.

## Use

1. Open **Compose** and enter a message.
2. Pick a style and theme, then adjust scale or options if needed.
3. Press **F6** to render and copy the image.
4. Focus the chat input and press **Ctrl+V**, or press **F9** to paste directly.
5. Reuse previous messages from **History** or save common wording as a template.

The tray icon keeps the app running when the window is closed. Right-click it for quick actions or to quit.

## Data and privacy

All data is stored locally:

```text
%APPDATA%\TextPicStudio\
  settings.json
  textpic.db
  images\YYYY\MM\<uuid>.png
```

Set `TEXTPIC_DATA_DIR` to use a different data directory. The app does not create accounts, upload message content, or include telemetry.

The bundled Inter font is licensed under the SIL Open Font License; see `assets\fonts\OFL.txt`.

## Development

Python 3.12 is required. From the project root:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
$env:PYTHONPATH = 'src'
.\.venv\Scripts\python.exe main.pyw
```

Run the test suite:

```powershell
$env:PYTHONPATH = 'src'
.\.venv\Scripts\python.exe -m pytest
```

Run the application selftest and write its report to `%TEMP%\TextPicStudio-selftest.txt`:

```powershell
.\.venv\Scripts\python.exe main.pyw --selftest
```

## Build the installer

Install WiX once:

```powershell
dotnet tool install --tool-path .tools\wix wix --version 4.0.6
.\.tools\wix\wix.exe extension add -g WixToolset.UI.wixext/4.0.6
```

Then build the application and MSI:

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

The script runs the tests, builds the PyInstaller onedir app, regenerates `installer\AppFiles.wxs`, compiles the MSI, and writes a SHA-256 checksum.

Useful options:

```powershell
.\build.ps1 -SkipTests
.\build.ps1 -SkipAppBuild
```

Outputs:

```text
dist\TextPicStudio\TextPicStudio.exe
dist\TextPicStudio-1.0.3-x64.msi
dist\TextPicStudio-1.0.3-x64.msi.sha256
```

## Verify the MSI

The smoke test installs and uninstalls both autostart variants, checks shortcuts, App Paths, the installed executable selftest, and user-data preservation. It requires an elevated PowerShell session and temporarily modifies the local machine:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\msi-smoke.ps1
```

The report is written to `%TEMP%\textpic-msi-smoke.txt`.

## Project layout

```text
main.pyw                     Development launcher
src\textpic\app.py           Bootstrap, CLI, logging, selftest
src\textpic\services\        Rendering, clipboard, hotkeys, storage
src\textpic\ui\              Shell, pages, dialogs, widgets
src\textpic\theme\           Color tokens and generated QSS
assets\                      Icons, fonts, images, sounds
installer\                   WiX source, artwork, license, version info
tools\generate_wix.py        Generates deterministic WiX file components
tests\                       Pytest suite
TextPicStudio.spec           PyInstaller build definition
build.ps1                    Reproducible app and MSI build
```
