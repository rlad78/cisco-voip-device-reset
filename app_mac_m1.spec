# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files
from pathlib import Path

datas = [('pyproject.toml', '.')]
datas += collect_data_files('ciscoreset')
datas += collect_data_files('ciscoaxl')


block_cipher = None


a = Analysis(['ciscoreset/gui.py'],
             binaries=[],
             datas=datas,
             hiddenimports=[],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,  
          [],
          name='Cisco VoIP Device Reset',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False,
          target_arch='arm64',
          disable_windowed_traceback=False,
          codesign_identity=None,
          entitlements_file=None )
app = BUNDLE(exe,
             name='Cisco VoIP Device Reset.app',
             icon=None,
             bundle_identifier=None)
