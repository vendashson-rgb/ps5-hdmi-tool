import pathlib

d = pathlib.Path(r"C:\Users\O Honorio\Documents\Realtek -- Nuvoton\NOR's")

samples = {
    "EDM-041 (NUV, REV 1.1)": (d / "EDM-041 NUVOTON HDMI E J20H104 REV 1.1 .BIN", "1.1"),
    "EDM-O33 (PAN, REV 1.3)": (d / "EDM-O33 PANASONIC HDMI E J20H100 REV 1.3.bin", "1.3"),
    "EDM-044 (RTK, REV 1.4)": (d / "EDM-044 REALTEK HDMI E J20H104 REV. 1.4.bin", "1.4"),
    "EDM-050 (RTK, REV 1.5)": (d / "EDM-050 REALTK HDMI E J20H104 REV. 1.5.bin", "1.5"),
    "EDM-051 (NUV, REV 1.5)": (d / "EDM-051 NUVOTON HDMI E J20H104 REV. 1.5.BIN", "1.5"),
}

data = {name: (path.read_bytes(), rev) for name, (path, rev) in samples.items()}

names = list(data.keys())
START, END = 0x1C0000, 0x1D2000

candidates = []
for off in range(START, END):
    by_rev = {}
    consistent = True
    for name in names:
        buf, rev = data[name]
        val = buf[off]
        if rev in by_rev and by_rev[rev] != val:
            consistent = False
            break
        by_rev[rev] = val
    if not consistent:
        continue
    # precisa realmente diferenciar: pelo menos 2 revisoes com valores diferentes
    if len(set(by_rev.values())) < 2:
        continue
    candidates.append((off, dict(by_rev)))

print(f"offsets candidatos (mesmo valor dentro da mesma REV, mas REVs diferentes com valores diferentes): {len(candidates)}")
for off, by_rev in candidates[:200]:
    ordered = {r: by_rev.get(r) for r in ["1.1", "1.3", "1.4", "1.5"]}
    print(f"0x{off:06X}: " + "  ".join(f"REV{r}=0x{v:02X}" if v is not None else f"REV{r}=?" for r, v in ordered.items()))
