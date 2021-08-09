# -*- mode: python -*-

block_cipher = None


a = Analysis(['sbmlTranslator.py'],
             pathex=['.'],
             binaries=[],
             datas=[('libsbml', '.')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=['PyQt4', 'PyQt4.QtCore', 'PyQt4.QtGui','matplotlib','IPython','PIL','pytz'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
a.datas += [('config/namingConventions.json','config/namingConventions.json','DATA'),
            ('config/reactionDefinitions.json','config/reactionDefinitions.json','DATA')]
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='sbmlTranslator',
          debug=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=True )
#exe = EXE(pyz,
#          a.scripts,
#          exclude_binaries=True,
#          name='sbmlTranslator',
#          debug=False,
#          strip=False,
#          upx=True,
#          console=True )
#coll = COLLECT(exe,
#               a.binaries,
#               a.zipfiles,
#               a.datas,
#               strip=False,
#               upx=True,
#               name='sbmlTranslator')
