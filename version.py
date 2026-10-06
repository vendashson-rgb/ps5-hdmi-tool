"""Fonte unica da versao do programa em tempo de execucao (ex.: usada pela
checagem de atualizacao em updater.py, pra comparar com a versao mais
recente publicada no GitHub).

*** IMPORTANTE ***
Precisa ser atualizado JUNTO com version_info.txt (StringFileInfo/
FileVersion/ProductVersion e filevers/prodvers) e installer.iss
(MyAppVersion/VersionInfoVersion) toda vez que a versao for incrementada --
sao 3 arquivos com o mesmo numero, nenhum le o outro automaticamente.
"""

APP_VERSION = "1.0.16"
