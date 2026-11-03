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

# 核心场景页、更多场景页用的识图局部（截图 1920×1080）
for name, src, box in [("story_split", "rec_case", (380, 70, 1040, 1080)),     # 拓片 + 字框
                       ("story_match", "rec_case", (1420, 100, 1920, 1000)),  # 右栏：逐字给出今字
                       ("assist_panel", "rec_assist", (1420, 60, 1920, 1080)),  # 释读辅助：辞例
                       ("trace_crop", "trace", (708, 166, 1212, 670))]:  # 描红字格
    Image.open(A / "shots" / f"{src}.png").convert("RGB").crop(box).save(A / f"{name}.png")


def text_png(key, text, size, color, bold=False, max_w=None, line_gap=1.25, font=FONT_TITLE, track=0.0):
    """把一段文字渲染成透明 PNG（4 倍采样），返回 (宽, 高) 英寸。track = 字间距（字号的倍数）。"""
    S = 4
    f = ImageFont.truetype(font, size * S)
    gap = track * size * S
    lines = text.split("\n")
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
    span = lambda l: f.getlength(l) + gap * max(len(l) - 1, 0)
    w = int(max(span(l) for l in lines)) + 8 * S
    h = lh * len(lines) + 6 * S
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i, l in enumerate(lines):
        x = 4 * S
        for ch in (l if gap else [l]):
            d.text((x, 3 * S + i * lh), ch, font=f, fill=color + (255,),
                   stroke_width=int(0.6 * S) if bold else 0, stroke_fill=color + (255,))
            x += f.getlength(ch) + gap
    im.save(T / f"{key}.png")
    return {"w": w / S / 96, "h": h / S / 96}   # 按 96 px/in 换算成英寸


# 文字清单：键 → (文字, 字号 pt(96dpi 像素), 颜色, 粗, 最大宽 px)
TEXTS = {
    "cover_sub": ("金文数字化传承与互动体验平台", 40, INK, False, None),
    "cover_tag": ("让青铜铭文可观、可识、可读、可感", 24, CINNABAR, False, None),
    "end_1": ("让书写在青铜器上的文字活起来", 50, INK, True, None),
    "end_thanks": ("敬请各位老师批评指正", 34, INK, False, None),
    "slogan": ("可观　可识　可读　可感", 30, CINNABAR, True, None),
}
TITLES = {
    "t2": "读懂铭文，追溯文明之源",
    "t3": "国家高度重视文字传承",
    "t4": "走进博物馆，读懂青铜铭文",
    "t5": "古文字资料整理",
    "t6": "识读模型训练",
    "t7": "研究与测评",
    "t8": "一套字库，多种用途",
    "t9": "网站演示",
    "t10": "落地应用",
}
SUMS = {
    "s2": "让公众尤其是青少年读懂金文，是我们做这件事的起点",
    "s3": "然而在博物馆里，多数观众仍读不懂展柜中的铭文",
    "s4": "模型拆字、字库匹配，把铭文变成看得懂的现代汉字",
    "s5": "每个字形、每张拓片都注明了出处",
    "s6": "模型提供释读初稿，最终结论由专家审定",
    "s7": "团队持续开展古文字识读研究",
    "s8": "同一套字库，也能用来学源流、听古音、练书写、做研究",
    "s9": "演示内容均为网站实际操作录屏",
    "s10": "作品可在展位、手机端、课堂和海外中文教学中使用",
}
meta = {}
for k, (txt, sz, col, b, mw) in TEXTS.items():
    meta[k] = text_png(k, txt, sz, col, b, mw)
for k, txt in TITLES.items():
    meta[k] = text_png(k, txt, 38, INK, True)
for k, txt in SUMS.items():
    meta[k] = text_png(k, txt, 22, INK, False)
# 第 3 页大号引文：朱砂、放宽字距，讲时逐字读
meta["quote_moe"] = text_png("quote_moe", "开展追溯甲骨文、金文、\n篆书等文字发展演变", 58, CINNABAR, True, line_gap=1.45, track=0.12)
# 封面中山王篆书标题下的逐字释文（常用字，评委一眼能认）
for ch in "吉金智识":
    meta["gloss_" + ch] = text_png("gloss_" + ch, ch, 48, CINNABAR, True)
for ch in "看听写考中国古今關雎鳩在河之洲":
    meta["big_" + ch] = text_png("big_" + ch, ch, 72, INK, True)
# 构拟（IPA）用 Segoe UI 渲染成图片，避免放映机缺字
IPA = {"guan": "kroːn", "ju": "sʰa", "jiu": "ku", "zai": "zlɯːʔ", "he": "ɡaːl", "zhi": "tjɯ", "zhou": "tju"}
for k, v in IPA.items():
    meta["ipa_" + k] = text_png("ipa_" + k, v, 30, CINNABAR, False, font="C:/Windows/Fonts/segoeuii.ttf")
json.dump(meta, open(T / "meta.json", "w", encoding="utf8"), ensure_ascii=False, indent=1)
print("ok", len(meta))
