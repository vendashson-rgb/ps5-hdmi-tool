"""
Leitura do container SLB2 (formato interno da Sony usado nas particoes
emc_ipl_a/emc_ipl_b da NOR do PS5) -- so o necessario pra extrair a entrada
de versao do firmware do EMC (coprocessador da Southbridge).

Offsets/formato conferidos contra o codigo-fonte do PS5 Wee Tools
(andy-man/ps5-wee-tools) e validados com validacao cruzada tripla (MD5 da
particao, tabela externa de versoes, e o campo fw_current que ja tinhamos)
nas nossas 4 amostras reais com essa particao -- ver NOTES.md.
"""

from __future__ import annotations

import struct

SLB2_MAGIC = b"SLB2"
SLB2_BLOCK = 0x200
_HEADER_SIZE = 4 + 4 + 4 + 4 + 4 + 12  # magic+version+flags+entries+blocks+reserved(3x4)
_ENTRY_SIZE = 4 + 4 + 8 + 32  # start+size+reserved(8)+name(32)


def parse(data: bytes) -> dict | None:
    """Decodifica o header SLB2 e a lista de entradas. None se o magic nao bater."""
    if data[:4] != SLB2_MAGIC:
        return None
    version, flags, entries, blocks = struct.unpack_from("<IIII", data, 4)
    out = []
    for i in range(entries):
        off = _HEADER_SIZE + _ENTRY_SIZE * i
        if off + _ENTRY_SIZE > len(data):
            break
        start, size = struct.unpack_from("<II", data, off)
        name = data[off + 16:off + 16 + 32].split(b"\x00", 1)[0].decode("ascii", "ignore")
        out.append({"name": name, "start": start, "offset": start * SLB2_BLOCK, "size": size})
    return {"entries": out, "blocks": blocks, "declared_size": blocks * SLB2_BLOCK}


def get_entry(data: bytes, name: str) -> bytes | None:
    info = parse(data)
    if not info:
        return None
    for entry in info["entries"]:
        if entry["name"] == name:
            start, size = entry["offset"], entry["size"]
            return data[start:start + size]
    return None
