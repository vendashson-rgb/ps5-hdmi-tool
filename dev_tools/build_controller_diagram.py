"""
Gera as imagens do diagrama do controle (images/controller/*.png) a partir do
SVG real do DualSense usado pelo dualshock-tools.github.io
(assets_src/dualsense-controller.svg, copiado de
github.com/dualshock-tools/dualshock-tools.github.io, licenca MIT,
copyright (c) 2024 the_al -- ver assets_src/LICENSE_dualshock-tools.txt).

So precisa rodar isto de novo se o SVG de origem mudar. O programa em si
(gui.py) so usa os .png ja gerados -- nao depende de resvg_py em producao.

Requer: pip install resvg-py pillow
"""

import pathlib
import re

import resvg_py
from PIL import Image

SRC_SVG = pathlib.Path(__file__).parent / "assets_src" / "dualsense-controller.svg"
OUT_DIR = pathlib.Path(__file__).parent.parent / "images" / "controller"

# Tamanho final de exibicao (ja renderizado nessa resolucao -- sem redimensionar
# depois no Tkinter). Mantem a proporcao do viewBox original (640 x 518).
WIDTH = 440
HEIGHT = round(WIDTH * 518 / 640)

LINE_COLOR = "#4da6ff"
HIGHLIGHT_COLOR = "#4edea3"

# chave usada no programa -> id do grupo <g id="..."> no SVG de origem
BUTTON_GROUPS = {
    "mute": "Mute_infill",
    "dpad_down": "Down_infill",
    "dpad_up": "Up_infill",
    "dpad_left": "Left_infill",
    "dpad_right": "Right_infill",
    "ps": "PS_infill",
    "triangle": "Triangle_infill",
    "cross": "Cross_infill",
    "circle": "Circle_infill",
    "square": "Square_infill",
    "options": "Options_infill",
    "create": "Create_infill",
    "r2": "R2_infill",
    "l2": "L2_infill",
    "r1": "R1_infill",
    "l1": "L1_infill",
    "touchpad": "Trackpad_infill",
    "l3": "L3_infill",
    "r3": "R3_infill",
}


def extract_path_d(svg_text: str, group_id: str) -> str:
    start_match = re.search(rf'<g id="{re.escape(group_id)}"[^>]*>', svg_text)
    if not start_match:
        raise RuntimeError(f"Nao achei o grupo <g id=\"{group_id}\"> no SVG de origem.")
    start = start_match.end()
    end = svg_text.index("</g>", start)
    chunk = svg_text[start:end]
    # \s antes do d evita casar com o "d" de dentro de id="..."
    d_match = re.search(r'\sd="([^"]+)"', chunk)
    if not d_match:
        raise RuntimeError(f"Nao achei nenhum <path d=\"...\"> dentro do grupo {group_id!r}.")
    return d_match.group(1)


def make_sprite_svg(d: str, fill: str) -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 518">'
        f'<g transform="translate(0,0.65) scale(0.70)"><path d="{d}" fill="{fill}"/></g>'
        "</svg>"
    )


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    svg_text = SRC_SVG.read_text(encoding="utf-8")

    idle_css = (
        f"svg * {{ fill: {LINE_COLOR}; }} "
        "#Button_infills, #Trackpad_infill, #L3_infill, #R3_infill, #TriggerPercentages "
        "{ display: none; }"
    )
    # So passa width -- deixa o resvg calcular a altura exata a partir do
    # viewBox, e usa essa altura real (em vez da nossa, que pode arredondar
    # diferente) em todos os sprites, pra garantir alinhamento perfeito.
    idle_png = resvg_py.svg_to_bytes(svg_path=str(SRC_SVG), width=WIDTH, style_sheet=idle_css)
    (OUT_DIR / "idle.png").write_bytes(idle_png)
    actual_height = Image.open(OUT_DIR / "idle.png").size[1]
    print(f"gerado idle.png ({WIDTH}x{actual_height})")

    bboxes = {}
    for key, group_id in BUTTON_GROUPS.items():
        d = extract_path_d(svg_text, group_id)
        sprite_svg = make_sprite_svg(d, HIGHLIGHT_COLOR)
        png_bytes = resvg_py.svg_to_bytes(svg_string=sprite_svg, width=WIDTH, height=actual_height)
        out_path = OUT_DIR / f"{key}.png"
        out_path.write_bytes(png_bytes)

        im = Image.open(out_path)
        bbox = im.split()[-1].getbbox()  # bbox dos pixels nao-transparentes
        if bbox is None:
            raise RuntimeError(f"Sprite {key!r} saiu totalmente transparente -- path errado?")
        bboxes[key] = bbox
        print(f"gerado {key}.png -- bbox {bbox}")

    # Salva as bounding boxes (em pixels, na mesma resolucao WIDTHxactual_height) pra
    # uso no programa (ex.: posicionar os pontinhos do touchpad dentro da
    # area real da tela, e futuramente deteccao de clique).
    bbox_file = OUT_DIR / "bboxes.py"
    with bbox_file.open("w", encoding="utf-8") as f:
        f.write('"""Gerado automaticamente por dev_tools/build_controller_diagram.py -- nao edite a mao."""\n\n')
        f.write(f"DIAGRAM_SIZE = ({WIDTH}, {actual_height})\n\n")
        f.write("BBOXES = {\n")
        for key, bbox in bboxes.items():
            f.write(f"    {key!r}: {bbox!r},\n")
        f.write("}\n")
    print(f"gerado {bbox_file.name}")
    print("Pronto.")


if __name__ == "__main__":
    main()
