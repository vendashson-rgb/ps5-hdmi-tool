import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from nor_patcher import apply_patch, TARGET_NUVOTON  # noqa: E402

NOR_DIR = pathlib.Path(r"C:\Users\O Honorio\Documents\Realtek -- Nuvoton\NOR's")

d = (NOR_DIR / "EDM-044 REALTEK HDMI E J20H104 REV. 1.4.bin").read_bytes()
real = (NOR_DIR / "EDM-44 REALTEK --- PANASONIC HDMI E J20H104 REV .bin").read_bytes()

result = apply_patch(d, TARGET_NUVOTON)
diffs = [i for i in range(len(result.data)) if result.data[i] != real[i]]
print("bytes diferentes entre nosso patch e o arquivo real convertido:", len(diffs))
for o in diffs[:20]:
    print(f"  0x{o:06X}: nosso={result.data[o]:02X} real={real[o]:02X}")
