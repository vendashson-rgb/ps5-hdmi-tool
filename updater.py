"""Checagem e download de atualizacoes via GitHub Releases.

So faz 1 chamada de rede (API do GitHub, release mais recente), numa
thread separada, alguns segundos depois do programa abrir -- nunca trava a
interface, e qualquer erro (sem internet, GitHub fora do ar, repositorio
sem releases, etc.) e silenciosamente ignorado: isso e um bonus de "ja
teria uma versao mais nova", nao uma funcao essencial, entao nunca deve
incomodar o usuario com um erro so porque ele esta sem internet.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass

from version import APP_VERSION

GITHUB_REPO = "vendashson-rgb/ps5-hdmi-tool"
GITHUB_API_LATEST_RELEASE = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
RELEASES_PAGE_URL = f"https://github.com/{GITHUB_REPO}/releases"
ASSET_NAME = "PS5_HDMI_Tool_Setup.exe"
REQUEST_TIMEOUT_S = 6
DOWNLOAD_TIMEOUT_S = 30
DOWNLOAD_CHUNK = 256 * 1024

_USER_AGENT = "PS5-HDMI-Tool-Updater"


def _parse_version(v: str) -> tuple[int, ...]:
    """'v1.0.16' / '1.0.16' -> (1, 0, 16). Pedacos nao numericos viram 0,
    nunca levanta excecao -- usado so pra comparar, uma versao malformada
    simplesmente perde a comparacao."""
    v = v.strip()
    if v[:1] in ("v", "V"):
        v = v[1:]
    parts = []
    for p in v.split("."):
        digits = "".join(ch for ch in p if ch.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts) if parts else (0,)


@dataclass
class UpdateInfo:
    version: str
    download_url: str
    size: int


def check_for_update() -> UpdateInfo | None:
    """Consulta a API do GitHub pela release mais recente. Retorna None se
    nao houver internet, a API falhar, o repositorio nao tiver releases,
    ou a versao remota nao for mais nova que APP_VERSION -- nunca levanta
    excecao, quem chama nao precisa de try/except."""
    try:
        req = urllib.request.Request(
            GITHUB_API_LATEST_RELEASE,
            headers={"Accept": "application/vnd.github+json", "User-Agent": _USER_AGENT},
        )
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_S) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None

    remote_version = data.get("tag_name") or ""
    if not remote_version:
        return None
    if _parse_version(remote_version) <= _parse_version(APP_VERSION):
        return None

    asset_url = None
    asset_size = 0
    for asset in data.get("assets", []) or []:
        if asset.get("name") == ASSET_NAME:
            asset_url = asset.get("browser_download_url")
            asset_size = asset.get("size") or 0
            break
    if not asset_url:
        return None

    return UpdateInfo(version=remote_version, download_url=asset_url, size=asset_size)


def download_update(info: UpdateInfo, dest_path: str, progress_cb=None) -> None:
    """Baixa o instalador da atualizacao pra dest_path.
    progress_cb(bytes_baixados, total_bytes), se passado, e chamado a cada
    pedaco -- quem chama cuida de mandar isso pra thread principal (ex.:
    via self.after(0, ...), igual o resto do programa ja faz pra
    progresso de leitura/gravacao de NOR)."""
    req = urllib.request.Request(info.download_url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(req, timeout=DOWNLOAD_TIMEOUT_S) as resp:
        total = int(resp.headers.get("Content-Length") or info.size or 0)
        downloaded = 0
        with open(dest_path, "wb") as f:
            while True:
                chunk = resp.read(DOWNLOAD_CHUNK)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if progress_cb:
                    progress_cb(downloaded, total)
