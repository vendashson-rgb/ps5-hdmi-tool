"""Gera os icones de bandeira (PT/EN/ES) usados no seletor de idioma do
programa (images/flags/*.png). Desenho simplificado via Pillow (sem baixar
nenhum asset externo) -- so precisa rodar de novo se mudar o tamanho/estilo.
"""
import pathlib

from PIL import Image, ImageDraw

OUT_DIR = pathlib.Path(__file__).parent.parent / "images" / "flags"
OUT_DIR.mkdir(parents=True, exist_ok=True)

W, H = 28, 18


def save(name: str, img: Image.Image):
    img.save(OUT_DIR / f"{name}.png")
    print(f"gerado {name}.png")


def flag_br() -> Image.Image:
    img = Image.new("RGB", (W, H), "#009739")
    d = ImageDraw.Draw(img)
    d.polygon([(W // 2, 1), (W - 2, H // 2), (W // 2, H - 1), (2, H // 2)], fill="#FEDD00")
    d.ellipse([W // 2 - 5, H // 2 - 5, W // 2 + 5, H // 2 + 5], fill="#002776")
    return img


def flag_us() -> Image.Image:
    img = Image.new("RGB", (W, H), "#B22234")
    d = ImageDraw.Draw(img)
    stripe_h = H / 13
    for i in range(13):
        if i % 2 == 1:
            d.rectangle([0, i * stripe_h, W, (i + 1) * stripe_h], fill="white")
    d.rectangle([0, 0, W * 0.4, H * 0.55], fill="#3C3B6E")
    return img


def flag_es() -> Image.Image:
    img = Image.new("RGB", (W, H), "#AA151B")
    d = ImageDraw.Draw(img)
    d.rectangle([0, H * 0.25, W, H * 0.75], fill="#F1BF00")
    return img


if __name__ == "__main__":
    save("pt", flag_br())
    save("en", flag_us())
    save("es", flag_es())
    print("Pronto.")
