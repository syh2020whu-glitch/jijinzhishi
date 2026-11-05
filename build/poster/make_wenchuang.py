"""文创样图（书签、帆布袋、印章贴纸、徽章），给海报“宣传成果 · 文创设计”用。
python build/poster/make_wenchuang.py  →  build/poster/assets/wc_*.png
素材全部取自仓库：字形图、篆书标题、器物插图、印章。是设计样稿，不是实物照片。
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent
A = REPO / "build" / "ppt" / "assets"
OUT = ROOT / "assets"
F_TITLE = "C:/Windows/Fonts/STZHONGS.TTF"
INK = (42, 36, 24)
CINNABAR = (166, 58, 44)
PAPER = (244, 239, 228)
GREEN = (38, 84, 58)
GOLD = (184, 145, 63)


def font(size):
    return ImageFont.truetype(F_TITLE, size)


def glyph(ch, color="2A2418"):
    return Image.open(A / "glyph" / f"{ch}_{color}.png").convert("RGBA")


def fit(im, w, h):
    im = im.copy()
    im.thumbnail((w, h), Image.LANCZOS)
    return im


def shadow(card, blur=18, off=12, alpha=90):
    pad = blur * 3
    sh = Image.new("RGBA", (card.width + pad * 2, card.height + pad * 2), (0, 0, 0, 0))
    m = Image.new("L", sh.size, 0)
    m.paste(card.getchannel("A").point(lambda v: alpha if v else 0), (pad, pad + off))
    sh.putalpha(m.filter(ImageFilter.GaussianBlur(blur)))
    sh.alpha_composite(card, (pad, pad))
    return sh


def bookmark(ch, gloss, bg, fg_color, seal):
    w, h = 300, 920
    c = Image.new("RGBA", (w, h), bg + (255,))
    d = ImageDraw.Draw(c)
    d.rectangle((14, 14, w - 15, h - 15), outline=GOLD, width=3)
    g = fit(glyph(ch, fg_color), 220, 330)
    c.alpha_composite(g, ((w - g.width) // 2, 90))
    y = 470
    for t in gloss:
        d.text((w // 2, y), t, font=font(46), fill=CINNABAR if bg != INK else (232, 199, 122), anchor="ma")
        y += 62
    s = fit(Image.open(A / f"seal_{seal}.png").convert("RGBA"), 70, 70)
    c.alpha_composite(s, (w - 100, h - 110))
    d.text((40, h - 70), "吉金智识", font=font(28), fill=(150, 140, 120) if bg != INK else (200, 190, 160))
    d.ellipse((w // 2 - 14, 30, w // 2 + 14, 58), outline=GOLD, width=4)   # 穿绳孔
    return c


def tote():
    w, h = 820, 960
    c = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(c)
    # 提手
    for x0 in (210, 470):
        d.arc((x0, 0, x0 + 140, 280), 180, 360, fill=(196, 182, 152), width=34)
    d.rounded_rectangle((40, 140, w - 40, h - 10), radius=18, fill=(233, 224, 204))
    for y in range(150, h - 20, 6):   # 帆布纹理
        d.line((50, y, w - 50, y), fill=(226, 216, 195), width=1)
    v = fit(Image.open(REPO / "assets" / "vessels" / "zun.png").convert("RGBA"), 360, 440)
    c.alpha_composite(v, ((w - v.width) // 2, 230))
    t = Image.open(A / "title_art_ink.png").convert("RGBA")
    t = fit(t, 560, 170)
    c.alpha_composite(t, ((w - t.width) // 2, 700))
    d.text((w // 2, 880), "吉 金 智 识", font=font(40), fill=CINNABAR, anchor="ma")
    return c


def stickers():
    w, h = 820, 560
    c = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(c)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=24, fill=(250, 248, 242), outline=(220, 210, 190), width=3)
    seals = ["吉", "智", "書", "和", "樂", "文", "古", "見"]
    seals = [s for s in seals if (A / f"seal_{s}.png").exists()]
    for i, s in enumerate(seals[:8]):
        x, y = 40 + (i % 4) * 195, 40 + (i // 4) * 250
        im = fit(Image.open(A / f"seal_{s}.png").convert("RGBA"), 170, 170)
        d.rounded_rectangle((x - 6, y - 6, x + 176, y + 176), radius=26, outline=(225, 215, 195), width=3)   # 模切线
        c.alpha_composite(im, (x, y))
    d.text((w // 2, h - 50), "印章贴纸", font=font(34), fill=(150, 140, 120), anchor="mm")
    return c


def badges():
    w, h = 820, 300
    c = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(c)
    for i, (ch, bg, fg) in enumerate([("壽", INK, "E8C77A"), ("永", GREEN, "E8C77A"), ("家", CINNABAR, "E8C77A"), ("寶", PAPER, "2A2418")]):
        cx = 105 + i * 205
        bgc = bg if bg != PAPER else (244, 239, 228)
        d.ellipse((cx - 95, 50, cx + 95, 240), fill=bgc, outline=GOLD, width=6)
        name = ch if (A / "glyph" / f"{ch}_{fg}.png").exists() else "吉"
        fgc = fg if (A / "glyph" / f"{name}_{fg}.png").exists() else "2A2418"
        g = fit(glyph(name, fgc), 120, 120)
        c.alpha_composite(g, (cx - g.width // 2, 145 - g.height // 2))
    return c


def main():
    OUT.mkdir(exist_ok=True)
    b1 = bookmark("吉", ["吉", "祥"], PAPER, "2A2418", "吉")
    b2 = bookmark("壽", ["眉", "寿"], INK, "E8C77A", "樂")
    for name, im in [("wc_bookmark1", b1), ("wc_bookmark2", b2), ("wc_tote", tote()), ("wc_stickers", stickers()), ("wc_badges", badges())]:
        shadow(im).save(OUT / f"{name}.png")
    print("ok", sorted(p.name for p in OUT.glob("wc_*.png")))


if __name__ == "__main__":
    main()
