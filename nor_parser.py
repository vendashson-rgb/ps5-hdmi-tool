"""
Leitura e interpretacao de dumps de NOR de PS5 Slim (EDM-xxx, J20H1xx).

Todos os offsets abaixo foram confirmados comparando dumps reais de varias
placas (revisoes 1.1, 1.3, 1.4 e 1.5; chips Realtek RTD2175P e
Nuvoton/Panasonic MN864739). Ver NOTES.md para o historico de cada um.

Offsets que NAO estao confirmados (revisao de placa legivel, modelo/revisao
do modulo Wi-Fi, versao de firmware) nao sao expostos aqui -- nao adivinhamos
offset nesse projeto.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

from i18n import t

EXPECTED_SIZE = 0x200000  # 2 MB -- W25Q16JV e equivalentes

OFFSET_CHIP_SELECT = 0x1C4062
CHIP_REALTEK = 0x01
CHIP_NUVOTON_PANASONIC = 0xFF

# Nome curto por chip, usado em nomes de arquivo (ex.: "REALTEK_FOR_NUVOTON.bin").
CHIP_SLUG = {
    CHIP_REALTEK: "REALTEK",
    CHIP_NUVOTON_PANASONIC: "NUVOTON",
}

OFFSET_MAC = 0x1C4020
MAC_LEN = 6

OFFSET_ID_BLOCK = 0x1C7200
ID_BLOCK_MAX_LEN = 64  # janela de busca; o campo real e bem menor

# Sub-campos do bloco acima. Offsets conferidos contra o codigo-fonte do
# PS5 NOR Modifier (TheCod3r, github.com/TheCod3rYouTube/PS5NorModifier --
# projeto para o PS5 original, nao o Slim) e validados batendo exatamente
# nas nossas 5 amostras reais de PS5 Slim (mesmo offset, campos limpos e
# consistentes em todas). Juntos formam exatamente o `raw_id_block` acima
# (16 + 17 = 33 bytes, seguido de padding 0xFF) -- aqui so nomeamos cada
# metade separadamente para exibir com rotulo correto.
OFFSET_MOBO_SERIAL = 0x1C7200
MOBO_SERIAL_LEN = 16
OFFSET_BOARD_SERIAL = 0x1C7210
BOARD_SERIAL_LEN = 17

OFFSET_CONVERSION_FIELDS = {
    # offset: (nome, bytes_originais_esperados_documentados, acao)
    0x1C40C6: "zerar (20 bytes, ate 0x1C40D9) na conversao",
    0x1C4923: "zerar (1 byte) na conversao",
}
OFFSET_CRC_UNKNOWN = 0x1C41FE  # 2 bytes -- algoritmo ainda nao identificado
OFFSET_WRITE_COUNTER = 0x1C49BE  # 2 bytes -- incrementa em +1 a cada conversao

# *** EXPERIMENTAL -- NAO CONFIRMADO ***
# Candidato a revisao do modulo Wi-Fi/Bluetooth, achado comparando 5 placas
# originais (ver NOTES.md, secao "Em investigacao"). 0x11 aparece tanto em
# REV 1.1 quanto em REV 1.4 -- so temos 1 amostra de cada, entao mapeamos
# para "1.4" por pedido do usuario (ele vai confirmar fisicamente em breve).
# Exibir sempre marcado como nao confirmado.
OFFSET_WIFI_REV_HINT = 0x1C4068
_WIFI_REV_HINT_RAW = {
    0x11: "backend.parser.wifi_rev_ambiguous",
    0x12: "1.3",
    0x21: "1.5",
}


@dataclass
class NorInfo:
    size: int
    size_ok: bool
    sha256: str
    chip_raw: int
    chip_name: str
    mac: str | None
    raw_id_block: str | None
    mobo_serial: str | None
    board_serial: str | None
    cfi_code: str | None
    wifi_rev_hint: str | None
    warnings: list[str] = field(default_factory=list)


def _find_run_end(data: bytes, start: int, max_len: int) -> int:
    """Retorna o indice (relativo a start) onde comeca um run de 0xFF, ou max_len."""
    for i in range(max_len):
        if data[start + i] == 0xFF:
            return i
    return max_len


def detect_chip(data: bytes) -> tuple[int, str]:
    raw = data[OFFSET_CHIP_SELECT]
    if raw == CHIP_REALTEK:
        return raw, "Realtek RTD2175P"
    if raw == CHIP_NUVOTON_PANASONIC:
        return raw, "Nuvoton/Panasonic MN864739"
    return raw, t("backend.parser.chip_unknown", raw=f"{raw:02X}")


def format_mac(data: bytes) -> str:
    mac_bytes = data[OFFSET_MAC:OFFSET_MAC + MAC_LEN]
    return ":".join(f"{b:02X}" for b in mac_bytes)


def extract_id_block(data: bytes) -> str | None:
    """Campo ASCII bruto logo apos o inicio do bloco 0x1C7200 (serie + dados adjacentes).

    Isto NAO e necessariamente so o numero de serie -- e o texto legivel cru
    encontrado ali. Mostrar como 'identificador bruto', nao como campo oficial.
    """
    chunk = data[OFFSET_ID_BLOCK:OFFSET_ID_BLOCK + ID_BLOCK_MAX_LEN]
    end = _find_run_end(chunk, 0, len(chunk))
    if end == 0:
        return None
    raw = chunk[:end]
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError:
        return None
    return text


def _extract_fixed_ascii(data: bytes, offset: int, length: int) -> str | None:
    """Decodifica um campo ASCII de tamanho fixo, cortando no primeiro 0xFF."""
    chunk = data[offset:offset + length]
    end = _find_run_end(chunk, 0, len(chunk))
    if end == 0:
        return None
    try:
        return chunk[:end].decode("ascii")
    except UnicodeDecodeError:
        return None


def extract_mobo_serial(data: bytes) -> str | None:
    """Identificador da placa-mae, 16 bytes em 0x1C7200 (ver nota de credito acima)."""
    return _extract_fixed_ascii(data, OFFSET_MOBO_SERIAL, MOBO_SERIAL_LEN)


def extract_board_serial(data: bytes) -> str | None:
    """Numero de serie do console, 17 bytes em 0x1C7210 (ver nota de credito acima)."""
    return _extract_fixed_ascii(data, OFFSET_BOARD_SERIAL, BOARD_SERIAL_LEN)


def extract_cfi_code(data: bytes) -> str | None:
    """Procura a string 'CFI-' perto do bloco de identificacao e devolve o texto legivel.

    Importante: ainda NAO confirmamos que isto corresponde 1:1 a revisao da
    placa (EDM-xxx) nem ao modulo Wi-Fi. E so um codigo de texto real que
    encontramos no dump -- mostrar como informacao adicional, nunca como
    "revisao da placa" ate confirmar com o usuario.
    """
    marker = b"CFI-"
    window = data[OFFSET_ID_BLOCK:OFFSET_ID_BLOCK + 128]
    idx = window.find(marker)
    if idx == -1:
        return None
    start = OFFSET_ID_BLOCK + idx
    end = _find_run_end(data, start, 32)
    raw = data[start:start + end]
    try:
        return raw.decode("ascii").strip()
    except UnicodeDecodeError:
        return None


def extract_wifi_rev_hint(data: bytes) -> str | None:
    """EXPERIMENTAL: ve NOTES.md. Nao confirmado -- so para demonstracao."""
    raw = data[OFFSET_WIFI_REV_HINT]
    mapped = _WIFI_REV_HINT_RAW.get(raw)
    if mapped is None:
        return t("backend.parser.wifi_rev_unknown", raw=f"{raw:02X}")
    if mapped.startswith("backend."):
        return t(mapped)
    return mapped


def parse_nor(data: bytes) -> NorInfo:
    warnings: list[str] = []

    size = len(data)
    size_ok = size == EXPECTED_SIZE
    if not size_ok:
        warnings.append(t("backend.parser.size_warning", size=size, expected=EXPECTED_SIZE))

    sha256 = hashlib.sha256(data).hexdigest()

    chip_raw, chip_name = detect_chip(data) if size >= OFFSET_CHIP_SELECT + 1 else (
        -1, t("backend.parser.truncated")
    )
    if chip_raw not in (CHIP_REALTEK, CHIP_NUVOTON_PANASONIC):
        warnings.append(t("backend.parser.chip_byte_warning"))

    mac = format_mac(data) if size >= OFFSET_MAC + MAC_LEN else None
    raw_id = extract_id_block(data) if size >= OFFSET_ID_BLOCK + ID_BLOCK_MAX_LEN else None
    mobo_serial = extract_mobo_serial(data) if size >= OFFSET_MOBO_SERIAL + MOBO_SERIAL_LEN else None
    board_serial = extract_board_serial(data) if size >= OFFSET_BOARD_SERIAL + BOARD_SERIAL_LEN else None
    cfi = extract_cfi_code(data) if size >= OFFSET_ID_BLOCK + 128 else None
    wifi_rev_hint = extract_wifi_rev_hint(data) if size >= OFFSET_WIFI_REV_HINT + 1 else None
    if wifi_rev_hint is not None:
        warnings.append(t("backend.parser.wifi_rev_warning"))

    return NorInfo(
        size=size,
        size_ok=size_ok,
        sha256=sha256,
        chip_raw=chip_raw,
        chip_name=chip_name,
        mac=mac,
        raw_id_block=raw_id,
        mobo_serial=mobo_serial,
        board_serial=board_serial,
        cfi_code=cfi,
        wifi_rev_hint=wifi_rev_hint,
        warnings=warnings,
    )


def compare_dumps(a: bytes, b: bytes) -> tuple[bool, int, list[int]]:
    """Compara dois dumps byte a byte. Retorna (sao_iguais, qtd_diferencas, primeiros_offsets)."""
    if len(a) != len(b):
        return False, -1, []
    diffs = [i for i in range(len(a)) if a[i] != b[i]]
    return (len(diffs) == 0), len(diffs), diffs[:20]
