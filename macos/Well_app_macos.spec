# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
import platform
import sys

if sys.platform != 'darwin':
    raise SystemExit('Este arquivo gera um .app e deve ser compilado em macOS.')

project_dir = Path(SPECPATH)
a = Analysis(
    [str(project_dir / 'well_app.py')],
    pathex=[str(project_dir)],
    binaries=[],
    datas=[(str(project_dir / 'assets'), 'assets')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Well_app',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=platform.machine(),
    codesign_identity=None,
    entitlements_file=None,
)
collection = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name='Well_app',
)
app = BUNDLE(
    collection,
    name='Well_app.app',
    icon=str(project_dir / 'assets' / 'well.icns'),
    bundle_identifier='com.wellstudio.desktop',
    version='5.0.0',
    info_plist={
        'CFBundleName': 'Well Studio',
        'CFBundleDisplayName': 'Well Studio V5',
        'CFBundleShortVersionString': '5.0.0',
        'CFBundleVersion': '5.0.0',
        'NSPrincipalClass': 'NSApplication',
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,
        'CFBundleDevelopmentRegion': 'pt_BR',
        'CFBundleLocalizations': ['pt_BR'],
        'NSHumanReadableCopyright': 'Desenvolvido por Victor Leandro | USBABC Conteúdo Criativo',
    },
)
