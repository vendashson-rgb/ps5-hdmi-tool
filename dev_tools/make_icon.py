"""Gera icon.ico (multi-resolucao) a partir de logo.png. Rodar uma vez (ou de novo se trocar o logo).

Le e grava em ../images/ (pasta de assets do programa).
"""
import pathlib

from PIL import Image

IMAGES_DIR = pathlib.Path(__file__).parent.parent / "images"

img = Image.open(IMAGES_DIR / "logo.png").convert("RGBA")
sizes = [16, 24, 32, 48, 64, 128, 256]
img.save(IMAGES_DIR / "icon.ico", format="ICO", sizes=[(s, s) for s in sizes])
print("icon.ico gerado com tamanhos:", sizes)
