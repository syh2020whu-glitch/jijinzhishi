"""浅色版素材：宣纸底、墨色标题字、标题/总结文字图。python build/ppt/make_assets_light.py"""
import json
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).parent
A = ROOT / "assets"
T = A / "text"
T.mkdir(exist_ok=True)
W, H = 1920, 1080
random.seed(11)

PAPER = (244, 239, 228)
INK = (42, 36, 24)
CINNABAR = (166, 58, 44)
PATINA = (78, 138, 122)
FONT_TITLE = "C:/Windows/Fonts/STZHONGS.TTF"   # 华文中宋，只在渲染图片时用，PPT 里不依赖字体


def paper(seed, glyph_alpha=(0.05, 0.09), n=0):
    random.seed(seed)
    base = np.full((H, W, 3), PAPER, dtype=np.float32)
    # 纸纹：低频噪声 + 四角略暗
    noise = np.random.default_rng(seed).normal(0, 1, (H // 8, W // 8))
    noise = np.array(Image.fromarray(((noise - noise.min()) / (noise.max() - noise.min()) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)).astype(np.float32)
    base += (noise[..., None] - 128) * 0.05
    y, x = np.mgrid[0:H, 0:W]
    d = np.sqrt(((x / W - 0.5) * 1.2) ** 2 + (y / H - 0.5) ** 2)
    base -= (np.clip(d / 0.8, 0, 1) ** 2 * 14)[..., None]
    img = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).convert("RGBA")
    glyphs = sorted((A / "glyph").glob("*_2A2418.png"))
    for _ in range(n):
        g = Image.open(random.choice(glyphs)).convert("RGBA")
        s = random.randint(90, 220)
        g = g.resize((s, s), Image.LANCZOS)
        a = np.array(g)
        a[..., 3] = (a[..., 3] * random.uniform(*glyph_alpha)).astype(np.uint8)
        # 只落在四边，中间留给内容
        if random.random() < 0.5:
            x0 = random.choice([random.randint(-40, 120), random.randint(W - 260, W - 60)])
            y0 = random.randint(-40, H - 100)
        else:
            x0 = random.randint(-40, W - 100)
            y0 = random.choice([random.randint(-40, 60), random.randint(H - 240, H - 80)])
        img.alpha_composite(Image.fromarray(a), (x0, y0))
    return img


paper(1, n=26).convert("RGB").save(A / "bg_light.jpg", quality=92)
paper(2, glyph_alpha=(0.06, 0.11), n=34).convert("RGB").save(A / "bg_light_cover.jpg", quality=92)

# 标题字「吉金智識」改墨色（原图是金色描线）
t = Image.open(A / "semi" / "image2.jpeg").convert("RGB")
arr = np.array(t).astype(np.float32)
lum = arr.max(axis=2)
alpha = np.clip((lum - 30) * 2.2, 0, 255).astype(np.uint8)
rgba = np.dstack([np.full_like(arr, INK, dtype=np.uint8), alpha])
Image.fromarray(rgba, "RGBA").save(A / "title_art_ink.png")
rgba = np.dstack([np.full_like(arr, CINNABAR, dtype=np.uint8), alpha])
Image.fromarray(rgba, "RGBA").save(A / "title_art_red.png")

# 明信片阴影（浅底）
pc = Image.open(A / "shots" / "postcard.png").convert("RGBA")
pad = 40
sh = Image.new("RGBA", (pc.width + pad * 2, pc.height + pad * 2), (0, 0, 0, 0))
m = Image.new("L", sh.size, 0)
ImageDraw.Draw(m).rectangle((pad, pad + 12, pad + pc.width, pad + pc.height + 12), fill=110)
m = m.filter(ImageFilter.GaussianBlur(18))
sh.putalpha(m)
sh.alpha_composite(pc, (pad, pad))
sh.save(A / "postcard_shadow_light.png")


def text_png(key, text, size, color, bold=False, max_w=None, line_gap=1.25, font=FONT_TITLE):
    """把一段文字渲染成透明 PNG（4 倍采样），返回 (宽, 高) 英寸。PPT 里按 300dpi 放。"""
    S = 4
    f = ImageFont.truetype(font, size * S)
    lines = [text]
    if max_w:
        lines, cur = [], ""
        for ch in text:
            if ch == "\n":
                lines.append(cur); cur = ""; continue
            if f.getlength(cur + ch) > max_w * S and cur:
                lines.append(cur); cur = ch
            else:
                cur += ch
        lines.append(cur)
    lh = int(size * S * line_gap)
    w = int(max(f.getlength(l) for l in lines)) + 8 * S
    h = lh * len(lines) + 6 * S
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i, l in enumerate(lines):
        d.text((4 * S, 3 * S + i * lh), l, font=f, fill=color + (255,),
               stroke_width=int(0.6 * S) if bold else 0, stroke_fill=color + (255,))
    im.save(T / f"{key}.png")
    return {"w": w / S / 96, "h": h / S / 96}   # 按 96 px/in 换算成英寸


# 文字清单：键 → (文字, 字号 pt(96dpi 像素), 颜色, 粗, 最大宽 px)
TEXTS = {
    "cover_sub": ("以字为桥：让古文字可看、可听、可写、可考", 40, INK, False, None),
    "cover_tag": ("金文数字化传承与互动体验平台", 24, CINNABAR, False, None),
    "end_1": ("字在器上，已经三千年。", 60, INK, True, None),
    "end_2": ("今天，它也在眼前、在耳边、在手里。", 40, CINNABAR, False, None),
    "end_thanks": ("请各位老师批评指正", 34, INK, False, None),
}
TITLES = {
    "t2": "最早的“中国”写在何尊上",
    "t3": "国家重视古文字，公众仍难亲近",
    "t4": "以字为桥，连起三千年",
    "t5": "字的源流与内涵",
    "t6": "我们整理的材料",
    "t7": "识读模型的训练",
    "t8": "四个模块：看、听、写、考",
    "t9": "在趣味互动中记住金文",
    "t10": "落地应用",
}
SUMS = {
    "s2": "让公众尤其是青少年读懂金文，是我们做这件事的起点",
    "s3": "材料不缺，缺的是一条让公众走得进去的路",
    "s4": "一头是器上的字，一头是身边的人，中间四个环节",
    "s5": "字形不断演化，字义里留着先人对天地人伦的理解",
    "s6": "每一个字都能追到出处",
    "s7": "机器给出初稿和疑字，释读由学者定夺",
    "s8": "公众、课堂、研究使用同一套字库，深浅不同",
    "s9": "小游戏只是手段：多动一次手，多记住一个字",
    "s10": "从屏幕上的字，到手里的明信片、课堂上的一节课",
}
meta = {}
for k, (txt, sz, col, b, mw) in TEXTS.items():
    meta[k] = text_png(k, txt, sz, col, b, mw)
for k, txt in TITLES.items():
    meta[k] = text_png(k, txt, 38, INK, True)
for k, txt in SUMS.items():
    meta[k] = text_png(k, txt, 22, INK, False)
for ch in "看听写考中国古今":
    meta["big_" + ch] = text_png("big_" + ch, ch, 72, INK, True)
json.dump(meta, open(T / "meta.json", "w", encoding="utf8"), ensure_ascii=False, indent=1)
print("ok", len(meta))
