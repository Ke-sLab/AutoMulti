# Third-party notices

AutoMulti itself is distributed as a binary-only Windows x64 package under a
proprietary End User License Agreement (EULA). The public AutoMulti binary
package contains the PyInstaller onedir application (`AutoMulti.exe` and its
`_internal` runtime directory) plus license, third-party notice, relinking, and
target-machine diagnostics documents. Checksum and short usage-note files are
provided alongside the zip in the public reviewer repository. AutoMulti source
code, tests, build scripts, and the development repository are not included in
the public binary package.

Third-party components remain governed by their own licenses.

This package does not redistribute Multiwfn, xTB, Gaussian, or ORCA. Users must
obtain and install those programs separately under their respective licenses.

## PySide6, Shiboken6, and Qt

The AutoMulti Windows application uses PySide6 6.10.2, Shiboken6 6.10.2, and
Qt 6.10.2 runtime libraries as dynamically loaded shared libraries.

AutoMulti does not modify the upstream PySide6, Shiboken6, or Qt library source
code. Generated AutoMulti UI/resource Python files are application artifacts,
not modified library source.

The intended public release package is the PyInstaller onedir layout. It should
ship only the reviewed LGPL-compatible Qt runtime DLL allowlist:

- `Qt6Core.dll`
- `Qt6Gui.dll`
- `Qt6Network.dll`
- `Qt6OpenGL.dll`
- `Qt6OpenGLWidgets.dll`
- `Qt6Svg.dll`
- `Qt6Test.dll`
- `Qt6Widgets.dll`
- matching `pyside6.cp*.dll`, `shiboken6.cp*.dll`, PySide6 extension modules, and
  PySide6 plugins needed by those modules

Do not distribute GPL-only Qt modules with the AutoMulti release unless a
commercial Qt license is used or the whole release is made GPL-compatible. The
release audit blocks known GPL-only modules such as `Qt6QmlCompiler.dll`,
Qt Graphs, Qt GRPC, Qt HTTP Server, Qt Lottie Animation, Qt MQTT, Qt Network
Authorization, Qt Virtual Keyboard, Qt Quick 3D, Qt Wayland Compositor, Qt CoAP,
Qt Quick Timeline, and Qt Canvas runtime libraries.

## License text and corresponding source

LGPLv3 text: https://www.gnu.org/licenses/lgpl-3.0.txt

Qt 6.10.2 corresponding source:
https://download.qt.io/official_releases/qt/6.10/6.10.2/single/qt-everywhere-src-6.10.2.tar.xz

PySide6/Shiboken6 corresponding source:
https://code.qt.io/cgit/pyside/pyside-setup.git/

Use the source tag or release matching PySide6/Shiboken6 6.10.2. If AutoMulti
ever distributes modified PySide6, Shiboken6, or Qt libraries, publish the full
corresponding modified library source or provide a written source offer with the
release.

## PaDELPy and PaDEL-Descriptor

AutoMulti includes PaDELPy as an optional descriptor/fingerprint backend.
PaDELPy is a Python wrapper for PaDEL-Descriptor and is distributed by its
upstream project under its own upstream license terms.

PaDEL-Descriptor is bundled by PaDELPy and may appear under
`_internal/padelpy/PaDEL-Descriptor` in the frozen AutoMulti runtime. It is a
third-party component used for descriptor/fingerprint calculations when Java is
available. PaDEL-Descriptor and its bundled subcomponents, including CDK,
AMBIT2, Apache Commons CLI, and other Java libraries, remain governed by their
own upstream license notices and license text files included with that bundled
component. Those third-party notices do not change the proprietary EULA that
governs the AutoMulti binary package itself.

If the PaDEL backend is not needed, AutoMulti remains usable with other
descriptor backends such as RDKit and Mordred, subject to their own licenses.

## Other Python/runtime dependencies

The AutoMulti binary and ML testing package rely on Python packages and model
runtime libraries listed in the README and requirements files. Descriptor
support may use RDKit, Mordred, PaDEL/CDK-related wrappers, and Java when
available in the user runtime. Each third-party component remains governed by
its own license.
