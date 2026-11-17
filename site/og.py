"""Gera as imagens de compartilhamento (WhatsApp, redes) do Radar: site/og/<nome>.png, 1200x630.
Roda no Mac (usa fontes do sistema); as imagens vão junto no repositório.
Uso: python3 site/og.py
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

RAIZ = Path(__file__).resolve().parent
FONTES = Path("/System/Library/Fonts/Supplemental")
AZUL, AZUL_ESC, BEGE, OURO = (40, 60, 89), (30, 44, 66), (245, 239, 227), (184, 134, 11)

IMAGENS = {
    "ap": ("AMAPÁ", "Santana e Porto Grande"),
    "santana": ("SANTANA", "Câmara Municipal de Santana-AP"),
    "porto-grande": ("PORTO GRANDE", "Câmara Municipal de Porto Grande-AP"),
}


def fonte(nome, tam):
    return ImageFont.truetype(str(FONTES / nome), tam)


def caber(draw, texto, nome, tam, largura):
    while tam > 40 and draw.textlength(texto, font=fonte(nome, tam)) > largura:
        tam -= 4
    return fonte(nome, tam)


def gerar(nome, cidade, sub):
    im = Image.new("RGB", (1200, 630), AZUL)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 560, 1200, 630], fill=AZUL_ESC)
    logo = Image.open(RAIZ / "logo-previas.png").convert("RGBA")
    logo = logo.resize((round(logo.width * 56 / logo.height), 56), Image.LANCZOS)
    im.paste(logo, (72, 64), logo)
    x = 72 + logo.width + 22
    d.line([x, 70, x, 114], fill=(120, 132, 150), width=2)
    d.text((x + 22, 72), "Radar", font=fonte("Arial Bold.ttf", 36), fill=BEGE)
    d.text((68, 170), "RADAR", font=fonte("Arial Black.ttf", 120), fill=(255, 255, 255))
    d.text((68, 300), cidade, font=caber(d, cidade, "Arial Black.ttf", 120, 1064), fill=OURO)
    d.text((72, 450), "Presença, propostas e votos dos vereadores.", font=fonte("Arial Bold.ttf", 34), fill=BEGE)
    d.text((72, 497), sub, font=fonte("Arial.ttf", 28), fill=(200, 205, 214))
    d.text((72, 580), "Só dados oficiais · sem nota e sem opinião", font=fonte("Arial Bold.ttf", 26), fill=BEGE)
    d.text((1128, 580), "previas26.com.br", font=fonte("Arial Bold.ttf", 26), fill=OURO, anchor="ra")
    (RAIZ / "og").mkdir(exist_ok=True)
    im.save(RAIZ / "og" / f"{nome}.png", optimize=True)


if __name__ == "__main__":
    for n, (c, s) in IMAGENS.items():
        gerar(n, c, s)
        print("site/og/" + n + ".png")
