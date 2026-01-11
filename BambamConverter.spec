# -*- mode: python ; coding: utf-8 -*-
import os

if '__file__' in globals():
    project_dir = os.path.dirname(os.path.abspath(__file__))
else:
    project_dir = os.getcwd()

datas = [
    (os.path.join(project_dir, 'bambam_logo.png'), '.'),
    (os.path.join(project_dir, 'bambam_logo.ico'), '.'),
    (os.path.join(project_dir, 'image_presets.json'), '.'),
]

binaries = []
ffmpeg_path = os.path.join(project_dir, 'ffmpeg.exe')
if os.path.exists(ffmpeg_path):
    binaries.append((ffmpeg_path, '.'))

a = Analysis(
    ['bambam_converter_suite.py'],
    pathex=[project_dir],
    binaries=binaries,
    datas=datas,
    hiddenimports=['PIL', 'tkinterdnd2', 'PyPDF2'],
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
    name='BambamConverter',
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
    icon=['bambam_logo.ico'],
)
