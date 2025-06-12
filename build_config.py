#!/usr/bin/env python3
"""
Build Configuration for InstaReaper Windows Application
"""

import os
import sys
from pathlib import Path

# Application metadata
APP_NAME = "InstaReaper"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Automated Reddit to Instagram Content Pipeline"
APP_AUTHOR = "InstaReaper Team"
APP_COPYRIGHT = "© 2024 InstaReaper"

# Build paths
BUILD_DIR = "build"
DIST_DIR = "dist"
SPEC_FILE = f"{APP_NAME.lower()}.spec"

# Icon and resources
ICON_FILE = "assets/icon.ico"  # We'll create this
SPLASH_IMAGE = "assets/splash.png"  # Optional splash screen

# Data files to include
DATA_FILES = [
    ('config', 'config'),
    ('assets', 'assets'),
    ('README.md', '.'),
    ('requirements.txt', '.'),
]

# Hidden imports (modules that PyInstaller might miss)
HIDDEN_IMPORTS = [
    'instagrapi',
    'selenium',
    'webdriver_manager',
    'cv2',
    'PyQt5',
    'PyQt5.QtCore',
    'PyQt5.QtGui',
    'PyQt5.QtWidgets',
    'requests',
    'json',
    'sqlite3',
    'logging',
    'threading',
    'queue',
    'datetime',
    'pathlib',
    'os',
    'sys',
    'time',
    'random',
    'urllib',
    'html',
    're',
    'base64',
    'hashlib',
    'uuid',
    'tempfile',
    'shutil',
    'zipfile',
    'configparser',
]

# Excluded modules (to reduce size)
EXCLUDES = [
    'tkinter',
    'matplotlib',
    'numpy',
    'pandas',
    'scipy',
    'IPython',
    'jupyter',
    'notebook',
    'pytest',
    'unittest',
    'doctest',
]

def get_version_info():
    """Get version info for Windows executable"""
    return {
        'version': APP_VERSION,
        'description': APP_DESCRIPTION,
        'copyright': APP_COPYRIGHT,
        'product_name': APP_NAME,
        'file_description': APP_DESCRIPTION,
        'internal_name': APP_NAME.lower(),
        'original_filename': f'{APP_NAME}.exe',
    }

def create_pyinstaller_spec():
    """Create PyInstaller spec file"""
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['gui/main_window.py'],
    pathex=[],
    binaries=[],
    datas={DATA_FILES},
    hiddenimports={HIDDEN_IMPORTS},
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes={EXCLUDES},
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{APP_NAME}',
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
    icon='{ICON_FILE}' if os.path.exists('{ICON_FILE}') else None,
)
'''
    
    with open(SPEC_FILE, 'w') as f:
        f.write(spec_content)
    
    print(f"✅ Created PyInstaller spec file: {SPEC_FILE}")

def create_version_file():
    """Create Windows version info file"""
    version_info = f'''# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'{APP_AUTHOR}'),
        StringStruct(u'FileDescription', u'{APP_DESCRIPTION}'),
        StringStruct(u'FileVersion', u'{APP_VERSION}'),
        StringStruct(u'InternalName', u'{APP_NAME.lower()}'),
        StringStruct(u'LegalCopyright', u'(c) 2024 {APP_AUTHOR}'),
        StringStruct(u'OriginalFilename', u'{APP_NAME}.exe'),
        StringStruct(u'ProductName', u'{APP_NAME}'),
        StringStruct(u'ProductVersion', u'{APP_VERSION}')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
'''
    
    with open('version_info.txt', 'w', encoding='utf-8') as f:
        f.write(version_info)
    
    print("✅ Created version info file: version_info.txt")

if __name__ == "__main__":
    print(f"🔧 Building {APP_NAME} v{APP_VERSION}")
    print("=" * 50)
    
    create_pyinstaller_spec()
    create_version_file()
    
    print("\n📋 Next steps:")
    print("1. Run: python create_assets.py")
    print("2. Run: python build_executable.py")
    print("3. Run: python create_installer.py") 