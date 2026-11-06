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
    """丝网印刷风格（用户 2026-11-06 选定）：一个大号“吉”字单色朱砂、偏右下出血，
    左上竖排“吉金智識”加竖线和小印，避免居中对称的模板感；米色长提手。"""
    import random
    w, h = 820, 1260
    DY = 300          # 包身下移，给长提手留位置
    rnd = random.Random(7)
    c = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(c)
    canvas = (226, 214, 190)
    body = (60, 170 + DY, w - 60, h - 10)
    d.rectangle(body, fill=canvas)
    # 布纹：经纬两向细线 + 随机杂点
    for y in range(body[1], body[3], 5):
        d.line((body[0], y, body[2], y), fill=(219, 206, 181), width=1)
    for x in range(body[0], body[2], 7):
        d.line((x, body[1], x, body[3]), fill=(222, 210, 186), width=1)
    for _ in range(2500):
        x, y = rnd.randint(body[0], body[2] - 1), rnd.randint(body[1], body[3] - 1)
        d.point((x, y), fill=(206, 192, 165))
    # 包口折边与缝线
    d.rectangle((body[0], body[1], body[2], body[1] + 46), fill=(218, 205, 179))
    for x in range(body[0] + 10, body[2] - 10, 22):
        d.line((x, body[1] + 54, x + 11, body[1] + 54), fill=(176, 160, 130), width=2)

    # 长提手：两条织带从包口内侧伸出，顶部圆弧；接缝处方框加交叉线加固
    strap = (205, 188, 156)
    for xl, xr in ((170, 330), (490, 650)):
        top = 30
        d.line((xl, body[1] + 70, xl, top + 80), fill=strap, width=34)
        d.line((xr, body[1] + 70, xr, top + 80), fill=strap, width=34)
        d.arc((xl - 17, top, xr + 17, top + 200), 180, 360, fill=strap, width=34)
        for x in (xl, xr):
            bx0, by0, bx1, by1 = x - 17, body[1] + 8, x + 17, body[1] + 60
            d.rectangle((bx0, by0, bx1, by1), outline=(160, 144, 114), width=2)
            d.line((bx0, by0, bx1, by1), fill=(160, 144, 114), width=2)
            d.line((bx0, by1, bx1, by0), fill=(160, 144, 114), width=2)

    # 大“吉”：朱砂单色，丝印颗粒（随机漏白），偏右下，超出包身的部分裁掉
    g = glyph("吉")
    g = g.crop(g.getchannel("A").getbbox())             # 去掉字形四周留白
    g = g.resize((round(g.width * 720 / g.height), 720), Image.LANCZOS)   # 字高 720，“口”下半被包底裁掉
    a = g.getchannel("A")
    grain = Image.effect_noise(g.size, 64).point(lambda v: 0 if v > 205 else 255)
    a = Image.composite(a, Image.new("L", g.size, 0), grain)
    red = Image.new("RGBA", g.size, CINNABAR + (255,))
    red.putalpha(a)
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    layer.alpha_composite(red, (340, 170 + DY + 95))     # 偏右下：字头在包口下约 95，左缘 340
    clip = Image.new("L", (w, h), 0)
    ImageDraw.Draw(clip).rectangle(body, fill=255)
    layer.putalpha(Image.composite(layer.getchannel("A"), Image.new("L", (w, h), 0), clip))
    c.alpha_composite(layer)

    # 左上：竖排“吉金智識”，右侧一条竖线，下方小印
    f = font(46)
    for i, ch in enumerate("吉金智識"):
        d.text((121, body[1] + 105 + i * 62), ch, font=f, fill=INK, anchor="mm")
    d.line((161, body[1] + 81, 161, body[1] + 351), fill=INK, width=3)
    s = fit(Image.open(A / "seal_吉.png").convert("RGBA"), 52, 52)
    c.alpha_composite(s, (95, body[1] + 362))
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
