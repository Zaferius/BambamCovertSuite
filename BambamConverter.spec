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
    (os.path.join(project_dir, 'localization.py'), '.'),
    (os.path.join(project_dir, 'update_checker.py'), '.'),
    (os.path.join(project_dir, 'landing_tab.py'), '.'),
    (os.path.join(project_dir, 'image_tab.py'), '.'),
    (os.path.join(project_dir, 'sound_tab.py'), '.'),
    (os.path.join(project_dir, 'video_tab.py'), '.'),
    (os.path.join(project_dir, 'document_tab.py'), '.'),
    (os.path.join(project_dir, 'batch_rename_tab.py'), '.'),
    (os.path.join(project_dir, 'settings_tab.py'), '.'),
    (os.path.join(project_dir, 'constants.py'), '.'),
]

binaries = []
ffmpeg_path = os.path.join(project_dir, 'ffmpeg.exe')
if os.path.exists(ffmpeg_path):
    binaries.append((ffmpeg_path, '.'))

ffprobe_path = os.path.join(project_dir, 'ffprobe.exe')
if os.path.exists(ffprobe_path):
    binaries.append((ffprobe_path, '.'))

a = Analysis(
    ['bambam_converter_suite.py'],
    pathex=[project_dir],
    binaries=binaries,
    datas=datas,
    hiddenimports=[
        'PIL', 
        'PIL.Image', 
        'PIL.ImageTk',
        'tkinterdnd2', 
        'PyPDF2',
        'urllib.request',
        'json',
        'threading',
        'webbrowser',
        'packaging',
        'packaging.version',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'scipy',
        'pandas',
        'pytest',
        'unittest',
        'pydoc',
        'doctest',
        'IPython',
        'notebook',
    ],
    noarchive=False,
    optimize=2,
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
    strip=True,
    upx=True,
    upx_exclude=['vcruntime140.dll', 'python313.dll'],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['bambam_logo.ico'],
)
