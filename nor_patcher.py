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

from i18n import t
from nor_parser import (
    OFFSET_CHIP_SELECT,
    OFFSET_WIFI_REV_HINT,
    OFFSET_MAC,
    MAC_LEN,
    OFFSET_WIFI_MAC,
    WIFI_MAC_LEN,
    OFFSET_MOBO_SERIAL,
    MOBO_SERIAL_LEN,
    OFFSET_BOARD_SERIAL,
    BOARD_SERIAL_LEN,
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
        t("backend.patch.chip_selector", target=TARGET_LABEL[target])
    ))

    # 2. Zerar bloco de 20 bytes
    old = bytes(buf[OFFSET_ZERO_BLOCK_1:OFFSET_ZERO_BLOCK_1 + ZERO_BLOCK_1_LEN])
    for i in range(ZERO_BLOCK_1_LEN):
        buf[OFFSET_ZERO_BLOCK_1 + i] = 0xFF
    changes.append(PatchChange(
        OFFSET_ZERO_BLOCK_1, old, b"\xFF" * ZERO_BLOCK_1_LEN,
        t("backend.patch.zero_block")
    ))

    # 3. Zerar byte isolado
    old = bytes([buf[OFFSET_ZERO_BYTE]])
    buf[OFFSET_ZERO_BYTE] = 0xFF
    changes.append(PatchChange(
        OFFSET_ZERO_BYTE, old, b"\xFF",
        t("backend.patch.zero_flag")
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
        t("backend.patch.counter")
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
            t("backend.patch.checksum_known", target=TARGET_LABEL[target],
              wifi_rev=f"{wifi_rev_byte:02X}")
        ))
        checksum_left_stale = False
    else:
        changes.append(PatchChange(
            OFFSET_CHECKSUM_UNKNOWN, old_checksum, old_checksum,
            t("backend.patch.checksum_unknown", wifi_rev=f"{wifi_rev_byte:02X}")
        ))
        checksum_left_stale = True

    return PatchResult(data=bytes(buf), changes=changes, checksum_left_stale=checksum_left_stale)


def apply_donor_identity(donor: bytes, customer: bytes) -> PatchResult:
    """Grava os dados de identidade do cliente (numeros de serie + MAC/MAC
    Wi-Fi) por cima de um arquivo-base (NOR completa de outro console, ja
    com o chip HDMI alvo e todos os outros campos corretos pra aquela
    familia de placa -- ex. EDM-040-J100-PANASONIC.BIN).

    O arquivo-base ja precisa ser uma NOR valida e completa pro chip e
    familia de placa certos -- esta funcao NAO confere isso, so transplanta
    os campos de identidade. Confira o chip/familia detectados no
    arquivo-base (parse_nor) antes de gravar numa placa de cliente.

    So carrega de volta o MAC/MAC Wi-Fi do cliente (alem do numero de
    serie) pra evitar que varios consoles convertidos com o mesmo
    arquivo-base saiam com o mesmo endereco MAC -- o que causaria conflito
    de rede se dois desses consoles acabarem na mesma rede.
    """
    buf = bytearray(donor)
    changes: list[PatchChange] = []

    fields = [
        (OFFSET_MOBO_SERIAL, MOBO_SERIAL_LEN, t("backend.patch.donor_mobo_serial")),
        (OFFSET_BOARD_SERIAL, BOARD_SERIAL_LEN, t("backend.patch.donor_board_serial")),
        (OFFSET_MAC, MAC_LEN, t("backend.patch.donor_mac")),
        (OFFSET_WIFI_MAC, WIFI_MAC_LEN, t("backend.patch.donor_wifi_mac")),
    ]
    for offset, length, description in fields:
        old = bytes(buf[offset:offset + length])
        new = customer[offset:offset + length]
        buf[offset:offset + length] = new
        changes.append(PatchChange(offset, old, bytes(new), description))

    return PatchResult(data=bytes(buf), changes=changes, checksum_left_stale=False)
