import re
import pathlib

d = pathlib.Path(r"C:\Users\O Honorio\Documents\Realtek -- Nuvoton\NOR's")
files = list(d.glob("*.bin"))
print("arquivos encontrados:", len(files))

regions = [(0x0, 0x8000), (0x1C0000, 0x1D2000)]
for f in files:
    data = f.read_bytes()
    hits = []
    for s, e in regions:
        chunk = data[s:e]
        text = chunk.decode("ascii", errors="ignore")
        for m in re.finditer(r"[0-9]{1,2}\.[0-9]{2,3}", text):
            hits.append((s + m.start(), m.group()))
    print(f.name, "->", hits[:15])
