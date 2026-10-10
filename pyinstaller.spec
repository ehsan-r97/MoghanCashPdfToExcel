# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

numpy_datas,      numpy_bins,      numpy_hidden      = collect_all('numpy')
pandas_datas,     pandas_bins,     pandas_hidden     = collect_all('pandas')
openpyxl_datas,   openpyxl_bins,   openpyxl_hidden   = collect_all('openpyxl')
pdfplumber_datas, pdfplumber_bins, pdfplumber_hidden = collect_all('pdfplumber')
pdfminer_datas,   pdfminer_bins,   pdfminer_hidden   = collect_all('pdfminer')
pillow_datas,     pillow_bins,     pillow_hidden     = collect_all('PIL')

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=(
        numpy_bins + pandas_bins + openpyxl_bins +
        pdfplumber_bins + pdfminer_bins + pillow_bins
    ),
    datas=(
        numpy_datas + pandas_datas + openpyxl_datas +
        pdfplumber_datas + pdfminer_datas + pillow_datas
    ),
    hiddenimports=(
        numpy_hidden + pandas_hidden + openpyxl_hidden +
        pdfplumber_hidden + pdfminer_hidden + pillow_hidden + [
            'tkinter',
            'tkinter.filedialog',
            'tkinter.messagebox',
            'arabic_reshaper',
            'bidi',
            'openpyxl.cell._writer',
        ]
    ),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='BankPDFImporter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='version_info.txt',
)