"""决赛现场展示海报：套组委会模板（竖版 800×1800 mm），出 72 dpi jpg（2268×5102）。

python build/poster/make_poster.py                  # 两个主标题方案各出一张
python build/poster/make_poster.py --title A        # 只出方案 A
python build/poster/make_poster.py --url https://…  # 固定域名定了以后，生成真二维码（需 pip install qrcode）

模板 jpg 不入库，默认读仓库根目录的“文化中国”总决赛现场展示海报设计模板.jpg（4724×10628，150 dpi）。
版面在模板原尺寸上排，最后缩到 72 dpi。配色、字体、素材与 build/ppt 同一套。
全稿不放校名、人名；文案不拿金文和其他古文字比较。
"""
import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent
A = REPO / "build" / "ppt" / "assets"
OUT = ROOT / "out"
TEMPLATE = REPO / "“文化中国”总决赛现场展示海报设计模板.jpg"
Image.MAX_IMAGE_PIXELS = None

# ── 配色：与 PPT 相同（宣纸、墨、朱砂、铜绿、金），另加模板标签的藏青 ──
PAPER = (244, 239, 228)
PANEL = (251, 248, 241)
PANEL2 = (239, 232, 216)
LINE = (217, 207, 187)
INK = (42, 36, 24)
TEXT = (58, 51, 40)
MUTED = (122, 110, 92)
CINNABAR = (166, 58, 44)
PATINA = (78, 138, 122)
GOLD = (184, 145, 63)
DARK = (43, 38, 32)
NAVY = (11, 61, 86)   # 模板“参赛队伍名称：”的颜色

FONTS = "C:/Windows/Fonts/"
F_TITLE = FONTS + "STZHONGS.TTF"   # 华文中宋：标题（PPT 标题图同款）
F_BODY = FONTS + "msyh.ttc"        # 微软雅黑：正文
F_BOLD = FONTS + "msyhbd.ttc"
F_NUM = FONTS + "cambriab.ttf"     # Cambria：数字、英文
F_EN = FONTS + "cambriai.ttf"

TITLES = {
    "A": "“中国”二字，最早写在这件青铜器上",
    "B": "以字为桥，连起三千年",
}

W = 4724                      # 模板宽（150 dpi）
PX0, PX1 = 300, W - 300       # 内容面板左右
CX0, CX1 = 470, W - 470       # 面板内文字区
CW = CX1 - CX0
OUT_SIZE = (2268, 5102)       # 800×1800 mm @ 72 dpi

_font_cache = {}


def font(path, size):
    key = (path, size)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(path, size)
    return _font_cache[key]


NO_LINE_START = set("，。、；：？！”’）》」』…·%")


def wrap(text, f, max_w):
    """按宽度折行，标点不放行首。"""
    lines = []
    for para in text.split("\n"):
        cur = ""
        for ch in para:
            if cur and f.getlength(cur + ch) > max_w and ch not in NO_LINE_START:
                lines.append(cur)
                cur = ch
            else:
                cur += ch
        lines.append(cur)
    return lines


class Poster:
    def __init__(self, template):
        self.im = Image.open(template).convert("RGB").convert("RGBA")
        assert self.im.width == W, f"模板宽应为 {W}，实际 {self.im.width}"
        self.d = ImageDraw.Draw(self.im)

    # ── 基础绘制 ──
    def text(self, xy, s, path, size, color, anchor="la", bold=0, spacing=0):
        f = font(path, size)
        if spacing:
            x, y = xy
            total = sum(f.getlength(c) for c in s) + spacing * (len(s) - 1)
            if anchor[0] == "m":
                x -= total / 2
            elif anchor[0] == "r":
                x -= total
            for c in s:
                self.d.text((x, y), c, font=f, fill=color, anchor="l" + anchor[1], stroke_width=bold, stroke_fill=color)
                x += f.getlength(c) + spacing
            return total
        self.d.text(xy, s, font=f, fill=color, anchor=anchor, stroke_width=bold, stroke_fill=color)
        return f.getlength(s)

    def para(self, x, y, s, size, color, max_w, path=F_BODY, lh=1.6, align="left"):
        f = font(path, size)
        lines = wrap(s, f, max_w)
        for i, l in enumerate(lines):
            if align == "center":
                self.d.text((x + max_w / 2, y + i * size * lh), l, font=f, fill=color, anchor="ma")
            else:
                self.d.text((x, y + i * size * lh), l, font=f, fill=color)
        return y + len(lines) * size * lh

    def rect(self, box, fill=None, outline=None, width=1, radius=0):
        if radius:
            self.d.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)
        else:
            self.d.rectangle(box, fill=fill, outline=outline, width=width)

    def shadow_box(self, box, radius=0, blur=28, offset=12, alpha=60):
        x0, y0, x1, y1 = (round(v) for v in box)
        pad = blur * 3
        m = Image.new("L", (x1 - x0 + pad * 2, y1 - y0 + pad * 2), 0)
        ImageDraw.Draw(m).rounded_rectangle((pad, pad, pad + x1 - x0, pad + y1 - y0), radius=radius, fill=alpha)
        m = m.filter(ImageFilter.GaussianBlur(blur))
        sh = Image.new("RGBA", m.size, (90, 72, 46, 0))
        sh.putalpha(m)
        self.im.alpha_composite(sh, (x0 - pad, y0 - pad + offset))

    def paste(self, src, box, mode="contain", align="center"):
        """把图片放进框里：contain 等比缩放居中不裁；cover 等比铺满后裁切。返回实际位置。"""
        img = src if isinstance(src, Image.Image) else Image.open(src)
        img = img.convert("RGBA")
        x0, y0, x1, y1 = (round(v) for v in box)
        bw, bh = x1 - x0, y1 - y0
        r = (min if mode == "contain" else max)(bw / img.width, bh / img.height)
        img = img.resize((max(1, round(img.width * r)), max(1, round(img.height * r))), Image.LANCZOS)
        if mode == "cover":
            l, t = (img.width - bw) // 2, (img.height - bh) // 2
            img = img.crop((l, t, l + bw, t + bh))
        ix = x0 + (bw - img.width) // 2
        iy = y0 + ((bh - img.height) // 2 if align == "center" else 0)
        self.im.alpha_composite(img, (ix, iy))
        return ix, iy, ix + img.width, iy + img.height

    def dashed_line(self, p0, p1, color, width=4, dash=26, gap=18):
        (x0, y0), (x1, y1) = p0, p1
        n = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
        t = 0.0
        while t < n:
            t1 = min(t + dash, n)
            self.d.line((x0 + (x1 - x0) * t / n, y0 + (y1 - y0) * t / n, x0 + (x1 - x0) * t1 / n, y0 + (y1 - y0) * t1 / n), fill=color, width=width)
            t += dash + gap

    def tri(self, cx, cy, s, direction):
        if direction == "right":
            pts = [(cx - s / 2, cy - s * 0.6), (cx + s / 2, cy), (cx - s / 2, cy + s * 0.6)]
        else:
            pts = [(cx - s * 0.6, cy - s / 2), (cx + s * 0.6, cy - s / 2), (cx, cy + s / 2)]
        self.d.polygon(pts, fill=GOLD)

    def dot(self, cx, cy, d, color, icon=None, label=None, label_size=None):
        self.d.ellipse((cx - d / 2, cy - d / 2, cx + d / 2, cy + d / 2), fill=color, outline=PAPER, width=max(3, d // 30))
        if icon:
            s = int(d * 0.52)
            self.paste(icon, (int(cx - s / 2), int(cy - s / 2), int(cx + s / 2), int(cy + s / 2)))
        if label:
            self.text((cx, cy), label, F_NUM, label_size or int(d * 0.55), PAPER, anchor="mm")

    # ── PPT 同款版块标题：印章 + 中宋标题 + 英文小字 + 金色短线和通栏细线 ──
    def header(self, y, seal, title, en):
        s = 170
        self.paste(A / f"seal_{seal}.png", (CX0, y, CX0 + s, y + s))
        self.text((CX0 + s + 50, y + s * 0.42), title, F_TITLE, 120, INK, anchor="lm", bold=2)
        self.text((CX0 + s + 54, y + s * 0.42 + 95), en, F_EN, 46, MUTED, anchor="lm", spacing=6)
        ly = y + s + 40
        self.d.line((CX0, ly, CX1, ly), fill=LINE, width=3)
        self.rect((CX0, ly - 4, CX0 + s, ly + 5), fill=GOLD)
        return ly + 70


def qr_image(url, size):
    import qrcode  # 只在给了 --url 时需要
    q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, border=2, box_size=20)
    q.add_data(url)
    q.make(fit=True)
    return q.make_image(fill_color=INK, back_color="white").convert("RGBA").resize((size, size), Image.NEAREST)


def build(key, template, url):
    p = Poster(template)
    d = p.d

    # ── 模板上的“参赛队伍名称：”后面填队名（同色同字号） ──
    p.text((1385, 2691), "吉金智识", F_TITLE, 150, NAVY, anchor="lm", bold=2)

    # ── 内容面板：半透明宣纸色圆角大板，底部露出模板山水 ──
    PY0, PY1 = 2900, 9700
    p.shadow_box((PX0, PY0, PX1, PY1), radius=80, blur=40, offset=16, alpha=70)
    panel = Image.new("RGBA", p.im.size, (0, 0, 0, 0))
    ImageDraw.Draw(panel).rounded_rectangle((PX0, PY0, PX1, PY1), radius=80, fill=PANEL + (232,))
    p.im.alpha_composite(panel)
    d.rounded_rectangle((PX0 + 28, PY0 + 28, PX1 - 28, PY1 - 28), radius=60, outline=(214, 192, 140), width=4)

    # ══ 主标题 ══
    y = 3060
    title = TITLES[key]
    size = 200 if key == "A" else 230
    th = 215                    # 两个方案的标题行同高，后面版面不动
    tw = font(F_TITLE, size).getlength(title)
    seal = int(size * 0.95)
    tx = (W - tw - seal - 60) / 2
    p.text((tx, y + th / 2), title, F_TITLE, size, INK, anchor="lm", bold=4)
    p.paste(A / "seal_中.png", (int(tx + tw + 60), int(y + th / 2 - seal / 2), int(tx + tw + 60 + seal), int(y + th / 2 + seal / 2)))
    y += th + 70
    p.rect((W / 2 - 90, y, W / 2 + 90, y + 8), fill=GOLD)
    y += 60
    p.text((W / 2, y), "吉金智识　金文数字化传承与互动体验平台", F_TITLE, 96, CINNABAR, anchor="ma", bold=1, spacing=8)
    y += 96 + 110

    # ══ 何尊 + 项目简介 ══
    hy0, hh = y, 860
    p.paste(A / "hezun_vessel.png", (CX0, hy0, CX0 + 770, hy0 + hh))
    rx0 = CX0 + 800
    rw = int(hh * 1000 / 932)
    rb = p.paste(A / "hezun_rubbing.jpg", (rx0, hy0, rx0 + rw, hy0 + hh))
    k = rw / 1000
    bx, by, bw, bh = rb[0] + 405 * k, rb[1] + 180 * k, 110 * k, 235 * k
    d.rectangle((bx, by, bx + bw, by + bh), outline=CINNABAR, width=9)
    zx0 = rx0 + rw + 120
    zw = int(hh * 0.86 * 330 / 705)
    zb = (zx0, hy0, zx0 + zw, hy0 + int(hh * 0.86))
    p.dashed_line((bx + bw, by), (zb[0], zb[1]), CINNABAR, 4)
    p.dashed_line((bx + bw, by + bh), (zb[0], zb[3]), CINNABAR, 4)
    p.paste(A / "hezun_zhongguo.png", zb, mode="cover")
    d.rectangle(zb, outline=CINNABAR, width=9)
    p.text(((zb[0] + zb[2]) / 2, zb[3] + 18), "中或", F_TITLE, 88, CINNABAR, anchor="ma", bold=2)
    p.para(CX0, hy0 + hh + 30, "何尊（西周早期），铭文“宅兹中或”是“中国”一词目前所见最早的文字记录", 48, MUTED, zb[2] - CX0)

    ix0 = zb[2] + 130
    iw = CX1 - ix0
    p.text((ix0, hy0 + 10), "项目简介", F_TITLE, 104, INK, bold=2)
    p.text((ix0 + 450, hy0 + 72), "ABOUT", F_EN, 46, MUTED, anchor="ls", spacing=6)
    p.rect((ix0, hy0 + 150, ix0 + 140, hy0 + 158), fill=GOLD)
    p.para(ix0, hy0 + 205,
           "吉金智识是一个金文数字化传承与互动体验平台。我们整理古文字字形、自建金文数据库目录和拓片，"
           "训练古文字识读模型，帮助观众在博物馆里读懂青铜铭文。同一套字库，还能用来认源流、听古音、练书写、助研究。",
           60, TEXT, iw, lh=1.62)
    y = hy0 + hh + 150

    # ══ 扫码体验：三步 + 大二维码 ══
    y = p.header(y, "手", "扫码体验", "TRY IT IN THREE STEPS")
    qs = 1000
    qx1 = CX1
    qx0 = qx1 - qs
    rows_w = qx0 - 120 - CX0
    rh, rg = 340, 36
    steps = [
        ("扫码", "用手机扫描右侧二维码，打开吉金智识网站", A / "icons" / "qr_light.png", None),
        ("输入你的姓", "看看你的姓氏用金文怎么写，听一听它的上古读音", None, A / "glyph" / "周_2A2418.png"),
        ("领取 PDF 明信片", "挑选青铜器和吉语，铸一句金文祝福，下载后可自行打印", None, A / "postcard_shadow_light.png"),
    ]
    for i, (head, body, icon, pic) in enumerate(steps):
        ry = y + i * (rh + rg)
        p.shadow_box((CX0, ry, CX0 + rows_w, ry + rh), blur=18, offset=8, alpha=45)
        p.rect((CX0, ry, CX0 + rows_w, ry + rh), fill=PANEL, outline=LINE, width=3)
        p.rect((CX0, ry, CX0 + 14, ry + rh), fill=CINNABAR)
        p.dot(CX0 + 150, ry + rh / 2, 170, CINNABAR, label=str(i + 1), label_size=100)
        tx0 = CX0 + 290
        pic_w = 0
        if pic:
            pic_w = 300
            pb = (CX0 + rows_w - pic_w - 30, ry - 20 if "postcard" in str(pic) else ry + 15, CX0 + rows_w - 30, ry + rh + 20 if "postcard" in str(pic) else ry + rh - 15)
            if "glyph" in str(pic):
                p.rect((pb[0] + 20, pb[1] + 5, pb[2] - 20, pb[3] - 5), fill=PANEL2)
                p.paste(pic, (pb[0] + 40, pb[1] + 15, pb[2] - 40, pb[3] - 15))
                p.text((pb[0] + 2, pb[3] - 5), "周", F_TITLE, 52, CINNABAR, anchor="ld", bold=1)
            else:
                p.paste(pic, pb)
        elif icon:
            pic_w = 300
            p.dot(CX0 + rows_w - 30 - pic_w / 2, ry + rh / 2, 220, PATINA, icon=icon)
        p.text((tx0, ry + 60), head, F_TITLE, 96, INK, bold=2)
        p.para(tx0, ry + 190, body, 52, TEXT, rows_w - (tx0 - CX0) - pic_w - 60, lh=1.45)
        if i < 2:
            p.tri(CX0 + 150, ry + rh + rg / 2, 30, "down")
    qy0 = y
    p.shadow_box((qx0, qy0, qx1, qy0 + qs), blur=18, offset=8, alpha=55)
    p.rect((qx0, qy0, qx1, qy0 + qs), fill=(255, 255, 255), outline=PATINA, width=6)
    if url:
        p.paste(qr_image(url, qs - 80), (qx0 + 40, qy0 + 40, qx1 - 40, qy0 + qs - 40))
    else:
        # 固定域名未定：只留位，不放任何临时地址
        for t in range(0, qs - 160, 60):
            d.line((qx0 + 80 + t, qy0 + 80, qx0 + 80 + t + 30, qy0 + 80), fill=PATINA, width=4)
            d.line((qx0 + 80 + t, qy0 + qs - 80, qx0 + 80 + t + 30, qy0 + qs - 80), fill=PATINA, width=4)
            d.line((qx0 + 80, qy0 + 80 + t, qx0 + 80, qy0 + 80 + t + 30), fill=PATINA, width=4)
            d.line((qx1 - 80, qy0 + 80 + t, qx1 - 80, qy0 + 80 + t + 30), fill=PATINA, width=4)
        p.text(((qx0 + qx1) / 2, qy0 + qs / 2 - 50), "二维码位置", F_BOLD, 80, PATINA, anchor="mm")
        p.text(((qx0 + qx1) / 2, qy0 + qs / 2 + 60), "固定域名确定后替换", F_BODY, 52, MUTED, anchor="mm")
    p.text(((qx0 + qx1) / 2, qy0 + qs + 40), "扫码，带走你的金文明信片", F_TITLE, 66, CINNABAR, anchor="ma", bold=1)
    y += 3 * rh + 2 * rg + 110

    # ══ 核心场景：博物馆四步 ══
    y = p.header(y, "見", "走进博物馆，读懂青铜铭文", "CORE SCENARIO")
    gap = 90
    cw = (CW - 3 * gap) // 4
    ch = 690
    cards = [("拍下铭文", "观众在展柜前扫码，\n拍下器物上的铭文"),
             ("拆成单字", "模型找出铭文中的每一个字，\n逐个切分"),
             ("匹配今字", "到字库中逐字匹配，\n给出对应的现代汉字"),
             ("读懂历史", "连字成句、配上白话，\n读懂铭文记载的历史")]
    for i, (head, body) in enumerate(cards):
        x = CX0 + i * (cw + gap)
        box = (x, y, x + cw, y + ch)
        p.shadow_box(box, blur=20, offset=10, alpha=55)
        p.rect(box, fill=PANEL2 if i in (0, 3) else DARK)
        if i == 0:
            p.paste(A / "hezun_rubbing.jpg", (x + 30, y + 30, x + cw - 30, y + ch - 30), mode="cover")
            p.dot(x + cw - 120, y + ch - 120, 170, CINNABAR, icon=A / "icons" / "camera_light.png")
        elif i == 1:
            p.paste(A / "story_split.png", box)
        elif i == 2:
            p.paste(A / "story_match.png", box)
        else:
            p.text((x + 60, y + 80), "余其宅兹中国，", F_TITLE, 82, INK, bold=2)
            p.text((x + 60, y + 200), "自之乂民。", F_TITLE, 82, INK, bold=2)
            p.rect((x + 60, y + 345, x + 180, y + 353), fill=GOLD)
            p.para(x + 60, y + 400, "我要定居在天下的中心，从这里治理百姓。", 52, TEXT, cw - 120, lh=1.5)
            p.text((x + 60, y + ch - 70), "何尊铭文", F_BODY, 44, MUTED, anchor="ls")
        p.dot(x - 10, y - 10, 120, CINNABAR, label=str(i + 1), label_size=64)
        if i < 3:
            p.tri(x + cw + gap / 2, y + ch / 2, 40, "right")
        p.text((x + cw / 2, y + ch + 45), head, F_TITLE, 84, INK, anchor="ma", bold=2)
        p.para(x + 20, y + ch + 165, body, 50, TEXT, cw - 40, lh=1.45, align="center")
    y += ch + 165 + 2 * 50 * 1.45 + 100

    # ══ 四可：看 · 听 · 写 · 考 ══
    y = p.header(y, "樂", "让古文字可看、可听、可写、可考", "SEE · HEAR · WRITE · STUDY")
    four = [("看", "认源流", "看一个字怎样一步步\n演变成今天的样子"),
            ("听", "听古音", "听《诗经》“关关雎鸠”\n在上古的读法"),
            ("写", "练书写", "描红古文字，\n铸一句金文祝福"),
            ("考", "助研究", "模型框出拓片上的字，\n列出候选字和辞例")]
    cw4 = (CW - 3 * gap) // 4
    dd = 270
    for i, (c, head, body) in enumerate(four):
        cx = CX0 + i * (cw4 + gap) + cw4 / 2
        col = CINNABAR if i == 3 else PATINA
        d.ellipse((cx - dd / 2, y, cx + dd / 2, y + dd), fill=col)
        d.ellipse((cx - dd / 2 + 16, y + 16, cx + dd / 2 - 16, y + dd - 16), outline=PAPER, width=4)
        p.text((cx, y + dd / 2 + 6), c, F_TITLE, 180, PAPER, anchor="mm", bold=3)
        p.text((cx, y + dd + 45), head, F_TITLE, 78, INK, anchor="ma", bold=2)
        for j, l in enumerate(body.split("\n")):
            p.text((cx, y + dd + 160 + j * 72), l, F_BODY, 50, TEXT, anchor="ma")
    by = y + dd + 160 + 2 * 72 + 50
    # 看听写 = 创造性转化；考 = 创新性发展
    xa0, xa1 = CX0 + 40, CX0 + 3 * cw4 + 2 * gap - 40
    xb0, xb1 = CX0 + 3 * (cw4 + gap) + 40, CX1 - 40
    for x0, x1, col, lab in [(xa0, xa1, PATINA, "创造性转化"), (xb0, xb1, CINNABAR, "创新性发展")]:
        d.line((x0, by, x1, by), fill=col, width=6)
        d.line((x0, by - 30, x0, by), fill=col, width=6)
        d.line((x1, by - 30, x1, by), fill=col, width=6)
        mid = (x0 + x1) / 2
        lw = font(F_TITLE, 70).getlength(lab) + 80
        p.rect((mid - lw / 2, by - 45, mid + lw / 2, by + 45), fill=PANEL)
        p.text((mid, by), lab, F_TITLE, 70, col, anchor="mm", bold=1)
    y = by + 120

    # ══ 我们的积累：大数字（口径同 决赛讲稿-v3 第四节） ══
    y = p.header(y, "書", "我们的积累", "DATA AND MODEL")
    stats = [("58万", "张古文字字形图", "汇集 10 个字形来源"),
             ("25,285", "条自建金文数据库目录", "器名、释文、时代、著录号"),
             ("6,236", "张拓片", "逐字标注 61,268 个字框"),
             ("150余种", "拓片来源著录", "每张拓片都注明出处"),
             ("5,930", "个金文变体", "分属 1,690 个字头"),
             ("24.6万", "条音韵记录", "覆盖 7,909 个字"),
             ("242", "个百家姓见于金文", "宋本《百家姓》408 个单姓"),
             ("F1 0.803", "古文字识别赛道二等奖", "世界科学智能大赛")]
    sw, sh, sg = (CW - 3 * 60) // 4, 380, 60
    for i, (num, unit, note) in enumerate(stats):
        x = CX0 + (i % 4) * (sw + sg)
        yy = y + (i // 4) * (sh + 40)
        p.rect((x, yy, x + sw, yy + sh), fill=PANEL, outline=LINE, width=3)
        p.rect((x, yy, x + 14, yy + sh), fill=CINNABAR)
        # 数字用 Cambria，中文“万/余种”用中宋，混排
        nx = x + 60
        for part in _split_num(num):
            path = F_NUM if part.isascii() else F_TITLE
            sz = 150 if part.isascii() else 104
            p.text((nx, yy + 175), part, path, sz, CINNABAR, anchor="ls", bold=0 if part.isascii() else 2)
            nx += font(path, sz).getlength(part)
        p.text((x + 60, yy + 205), unit, F_BOLD, 56, INK)
        p.text((x + 60, yy + 295), note, F_BODY, 44, MUTED)

    OUT.mkdir(exist_ok=True)
    final = p.im.convert("RGB").resize(OUT_SIZE, Image.LANCZOS)
    path = OUT / f"吉金智识-决赛海报-{key}.jpg"
    final.save(path, quality=95, dpi=(72, 72), subsampling=0)
    print("wrote", path, final.size, "内容到底部 y =", int(y + 2 * sh + 40), "面板底 =", PY1)


def _split_num(s):
    """'58万' → ['58', '万']；'F1 0.803' 整段 ASCII。"""
    parts, cur = [], ""
    for ch in s:
        if cur and ch.isascii() != cur[-1].isascii():
            parts.append(cur)
            cur = ""
        cur += ch
    parts.append(cur)
    return parts


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", choices=["A", "B", "both"], default="both", help="A：“中国”二字…  B：以字为桥…")
    ap.add_argument("--template", default=str(TEMPLATE))
    ap.add_argument("--url", default=None, help="固定域名；不给则二维码只留位")
    a = ap.parse_args()
    for k in (["A", "B"] if a.title == "both" else [a.title]):
        build(k, a.template, a.url)
