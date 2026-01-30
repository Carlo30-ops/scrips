# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec para Generador de Reportes COTU (fusionado con ttkbootstrap)
# Genera un .exe único que incluye Python, tkinter, pandas, openpyxl y ttkbootstrap.

from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = collect_all('ttkbootstrap')

a = Analysis(
    ['generador_facturas_cotu.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=[
        'pandas',
        'openpyxl',
        'openpyxl.cell',
        'openpyxl.cell.cell',
        'openpyxl.styles',
        'openpyxl.utils',
        'openpyxl.worksheet',
        'openpyxl.workbook',
    ] + hiddenimports,
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
    name='GeneradorCOTU',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
