# Qt/PySide6 LGPL relinking information

AutoMulti uses PySide6 6.10.2 and Qt 6.10.2 through dynamically loaded shared
libraries in the PyInstaller onedir package.

The public Windows package layout is:

```text
AutoMulti/
  AutoMulti.exe
  _internal/
    Qt6*.dll
    pyside6.cp*.dll
    shiboken6.cp*.dll
    PySide6/
      *.pyd
      plugins/
```

Users may replace the LGPL PySide6, Shiboken6, and Qt library files with
ABI-compatible builds. Keep the relative folder layout intact so the Python
extension modules and Qt plugin loader can find their dependencies.

## Replacement steps

1. Unzip the AutoMulti package.
2. Back up the original `AutoMulti/_internal` directory.
3. Replace the relevant LGPL runtime libraries with ABI-compatible builds for
   the same platform, architecture, Python ABI, and Qt/PySide6 version family.
4. Preserve the `PySide6/plugins` directory structure when replacing plugins.
5. Run the diagnostics:

```powershell
.\AutoMulti.exe --dll-probe
.\AutoMulti.exe --backend-probe --strict-vispy --strict-padel-module
```

If diagnostics fail, restore the original files or use replacement libraries
with compatible build options.

## Public distribution policy

The PyInstaller onedir package is the public distribution format for LGPL Qt
builds. Nuitka onefile builds are internal testing artifacts unless a release
also provides relinkable application code/object files and installation
information sufficient for users to replace the LGPL libraries.

## Source information

AutoMulti does not modify upstream PySide6, Shiboken6, or Qt libraries.

LGPLv3 text: https://www.gnu.org/licenses/lgpl-3.0.txt

Qt 6.10.2 corresponding source:
https://download.qt.io/official_releases/qt/6.10/6.10.2/single/qt-everywhere-src-6.10.2.tar.xz

PySide6/Shiboken6 corresponding source:
https://code.qt.io/cgit/pyside/pyside-setup.git/
