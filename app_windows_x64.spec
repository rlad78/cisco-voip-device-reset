# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files

datas = [('pyproject.toml', '.')]
datas += collect_data_files('ciscoreset')
datas += collect_data_files('ciscoaxl')


block_cipher = None


a = Analysis(['ciscoreset\\gui.py'],
             pathex=['C:\\Users\\gooby\\OneDrive\\Documents\\GitHub\\cisco-voip-device-reset'],
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
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None )
