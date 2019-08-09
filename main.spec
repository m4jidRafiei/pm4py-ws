# -*- mode: python -*-

import sys
sys.setrecursionlimit(5000)

block_cipher = None


a = Analysis(['main.py'],
             pathex=['C:\\Users\\berti\\pm4py-ws'],
             binaries=[],
             datas=[('files/','files/')],
             hiddenimports=["sklearn.neighbors.typedefs", "sklearn.utils._cython_blas", "scipy._lib.messagestream", "sklearn.tree", "sklearn.neighbors.quad_tree", "sklearn.tree._utils"],
             hookspath=['.'],
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
          [],
          exclude_binaries=True,
          name='main',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='main')
