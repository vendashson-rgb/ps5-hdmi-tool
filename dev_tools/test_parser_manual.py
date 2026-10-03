"""Teste manual rapido do parser contra os dumps reais ja coletados.
Nao e um teste automatizado formal -- so para validar visualmente antes de seguir.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from nor_parser import parse_nor  # noqa: E402

NOR_DIR = pathlib.Path(r"C:\Users\O Honorio\Documents\Realtek -- Nuvoton\NOR's")

files = [
    "EDM-044 REALTEK HDMI E J20H104 REV. 1.4.bin",
    "EDM-050 REALTK HDMI E J20H104 REV. 1.5.bin",
    "EDM-051 NUVOTON HDMI E J20H104 REV. 1.5.BIN",
    "EDM-O33 PANASONIC HDMI E J20H100 REV 1.3.bin",
    "EDM-041 NUVOTON HDMI E J20H104 REV 1.1 .BIN",
    "EDM-44 REALTEK --- PANASONIC HDMI E J20H104 REV .bin",
    "EDM-030 CFI-1214A 01X .bin",
]

for fname in files:
    path = NOR_DIR / fname
    data = path.read_bytes()
    info = parse_nor(data)
    print(f"== {fname} ==")
    print(f"  tamanho: {info.size} bytes (ok={info.size_ok})")
    print(f"  chip: 0x{info.chip_raw:02X} -> {info.chip_name}")
    print(f"  MAC: {info.mac}")
    print(f"  id bruto (0x1C7200): {info.raw_id_block}")
    print(f"  CFI: {info.cfi_code}")
    print(f"  REV Wi-Fi (experimental): {info.wifi_rev_hint}")
    if info.warnings:
        print(f"  AVISOS: {info.warnings}")
    print()
