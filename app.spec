# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(['app.py'],
             pathex=['D:\\Python\\LogCollector'],
             binaries=[],
             datas=[('Data/*', 'Data'), ('icon.ico', '.')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             upx=True,  # UPX 압축 활성화
             upx_exclude=[],  # 특정 바이너리 압축 제외 가능
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='Collector_V1.0',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_dir='D:\\upx-5.0.0-win64',
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False,
          icon='icon.ico')
