# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['pspai_server.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config.yaml', '.'),
        ('SOUL.md', '.'),
        ('MEMORY.md', '.'),
        ('skills', 'skills'),
        ('pspai_search.py', '.'),
    ],
    hiddenimports=['yaml', '__future__', 'run_agent', 'hermes_cli', 'hermes_cli.config', 'hermes_cli.models'],
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
    a.binaries,
    a.datas,
    [],
    name='xiaolongren-engine-linux-arm64',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
