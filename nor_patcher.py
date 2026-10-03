"""
Aplicacao do patch de conversao de chip HDMI (Realtek <-> Nuvoton/Panasonic).

*** LEIA ANTES DE USAR EM QUALQUER PLACA DE CLIENTE ***

O campo 0x1C41FE-0x1C41FF e uma tabela fixa que depende so de (chip HDMI em
0x1C4062, byte de revisao do Wi-Fi em 0x1C4068) -- NAO depende do MAC.
Descoberto em 2026-10-02 comparando dumps reais com mesmo chip+REV Wi-Fi mas
MAC diferente (ver NOTES.md). So temos o valor certo pra 3 combinacoes
confirmadas (KNOWN_CHECKSUMS abaixo); pra qualquer outra combinacao ainda nao
vista, o patch deixa o valor ANTIGO (desatualizado) e avisa. Ha relato de
terceiros de que um bloco inconsistente nessa area causa o sintoma "sai da
tela de checagem azul, vai pra tela branca, conecta controle, mas sem
imagem" -- ou seja, deixar o valor antigo pode nao funcionar de verdade.

Use em placa de cliente SOMENTE quando o checksum foi resolvido (ver
PatchResult.checksum_left_stale) -- senao, bancada/teste apenas.
"""

from __future__ import annotations

from dataclasses import dataclass

from nor_parser import (
    OFFSET_CHIP_SELECT,
    OFFSET_WIFI_REV_HINT,
    CHIP_REALTEK,
    CHIP_NUVOTON_PANASONIC,
)

OFFSET_ZERO_BLOCK_1 = 0x1C40C6
ZERO_BLOCK_1_LEN = 20  # ate 0x1C40D9 inclusive

OFFSET_ZERO_BYTE = 0x1C4923

OFFSET_COUNTER = 0x1C49BE  # 2 bytes, big-endian, incrementa +1 a cada conversao

OFFSET_CHECKSUM_UNKNOWN = 0x1C41FE  # 2 bytes -- tabela fixa, ver KNOWN_CHECKSUMS

# Tabela confirmada em 2026-10-02 (ver NOTES.md): (chip_destino, byte REV
# Wi-Fi ja existente na placa) -> valor correto do checksum. Cada entrada foi
# validada em pelo menos 2 amostras reais com MAC diferente batendo igual.
KNOWN_CHECKSUMS: dict[tuple[int, int], bytes] = {
    (CHIP_REALTEK, 0x11): bytes.fromhex("4586"),
    (CHIP_REALTEK, 0x21): bytes.fromhex("3290"),
    (CHIP_NUVOTON_PANASONIC, 0x21): bytes.fromhex("348f"),
    (CHIP_NUVOTON_PANASONIC, 0x12): bytes.fromhex("ada0"),
    (CHIP_NUVOTON_PANASONIC, 0x11): bytes.fromhex("e70e"),
}

TARGET_REALTEK = "realtek"
TARGET_NUVOTON = "nuvoton"

TARGET_BYTE = {
    TARGET_REALTEK: CHIP_REALTEK,
    TARGET_NUVOTON: CHIP_NUVOTON_PANASONIC,
}
TARGET_LABEL = {
    TARGET_REALTEK: "Realtek RTD2175P",
    TARGET_NUVOTON: "Nuvoton/Panasonic MN864739",
}


@dataclass
class PatchChange:
    offset: int
    old: bytes
    new: bytes
    description: str


@dataclass
class PatchResult:
    data: bytes
    changes: list[PatchChange]
    checksum_left_stale: bool


def apply_patch(original: bytes, target: str) -> PatchResult:
    if target not in TARGET_BYTE:
        raise ValueError(f"Alvo invalido: {target!r} (use {list(TARGET_BYTE)})")

    buf = bytearray(original)
    changes: list[PatchChange] = []

    # 1. Seletor do chip HDMI
    old = bytes([buf[OFFSET_CHIP_SELECT]])
    new_val = TARGET_BYTE[target]
    buf[OFFSET_CHIP_SELECT] = new_val
    changes.append(PatchChange(
        OFFSET_CHIP_SELECT, old, bytes([new_val]),
        f"Seletor de CI HDMI -> {TARGET_LABEL[target]}"
    ))

    # 2. Zerar bloco de 20 bytes
    old = bytes(buf[OFFSET_ZERO_BLOCK_1:OFFSET_ZERO_BLOCK_1 + ZERO_BLOCK_1_LEN])
    for i in range(ZERO_BLOCK_1_LEN):
        buf[OFFSET_ZERO_BLOCK_1 + i] = 0xFF
    changes.append(PatchChange(
        OFFSET_ZERO_BLOCK_1, old, b"\xFF" * ZERO_BLOCK_1_LEN,
        "Zerar bloco de pareamento (20 bytes)"
    ))

    # 3. Zerar byte isolado
    old = bytes([buf[OFFSET_ZERO_BYTE]])
    buf[OFFSET_ZERO_BYTE] = 0xFF
    changes.append(PatchChange(
        OFFSET_ZERO_BYTE, old, b"\xFF",
        "Zerar flag de pareamento (1 byte)"
    ))

    # 4. Incrementar contador de 2 bytes (big-endian), com carry
    old_counter = bytes(buf[OFFSET_COUNTER:OFFSET_COUNTER + 2])
    val = (old_counter[0] << 8) | old_counter[1]
    val = (val + 1) & 0xFFFF
    new_counter = bytes([(val >> 8) & 0xFF, val & 0xFF])
    buf[OFFSET_COUNTER] = new_counter[0]
    buf[OFFSET_COUNTER + 1] = new_counter[1]
    changes.append(PatchChange(
        OFFSET_COUNTER, old_counter, new_counter,
        "Incrementar contador de gravacao (+1)"
    ))

    # 5. Checksum: consulta a tabela fixa (chip_destino, REV Wi-Fi atual da placa).
    # O byte de REV Wi-Fi nao e alterado pela conversao, entao le o valor que
    # ja esta no arquivo original.
    wifi_rev_byte = buf[OFFSET_WIFI_REV_HINT]
    old_checksum = bytes(buf[OFFSET_CHECKSUM_UNKNOWN:OFFSET_CHECKSUM_UNKNOWN + 2])
    new_checksum = KNOWN_CHECKSUMS.get((new_val, wifi_rev_byte))

    if new_checksum is not None:
        buf[OFFSET_CHECKSUM_UNKNOWN] = new_checksum[0]
        buf[OFFSET_CHECKSUM_UNKNOWN + 1] = new_checksum[1]
        changes.append(PatchChange(
            OFFSET_CHECKSUM_UNKNOWN, old_checksum, new_checksum,
            f"Checksum -> valor conhecido pra {TARGET_LABEL[target]} + "
            f"REV Wi-Fi 0x{wifi_rev_byte:02X} (tabela confirmada, ver NOTES.md)"
        ))
        checksum_left_stale = False
    else:
        changes.append(PatchChange(
            OFFSET_CHECKSUM_UNKNOWN, old_checksum, old_checksum,
            f"Checksum NAO resolvido pra REV Wi-Fi 0x{wifi_rev_byte:02X} "
            "(combinacao ainda nao vista) -- mantido valor antigo, RISCO"
        ))
        checksum_left_stale = True

    return PatchResult(data=bytes(buf), changes=changes, checksum_left_stale=checksum_left_stale)
