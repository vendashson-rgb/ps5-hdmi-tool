# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('images', 'images'), ('drives', 'drives'), ('donor_files', 'donor_files')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

# Modo "onedir" (pasta), nao "onefile" -- um .exe sozinho precisa
# descompactar tudo numa pasta temporaria TODA vez que abre, o que deixava
# o programa demorando varios segundos so pra aparecer a janela. Em pasta,
# o .exe roda direto dos arquivos já extraídos (o instalador Inno Setup
# copia a pasta inteira), sem esse passo a cada abertura. upx=False pelo
# mesmo motivo -- UPX comprime o .exe no disco, mas tem que descomprimir
# ele na memoria toda vez que abre, e tambem dispara falso-positivo em
# alguns antivirus.
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PS5_HDMI_Tool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['images/icon.ico'],
    version='version_info.txt',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='PS5_HDMI_Tool',
)
