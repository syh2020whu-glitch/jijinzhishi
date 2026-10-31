"""
1690 个金文 SVG → 若干张精灵图集 + 坐标表，供 index.html 星河开屏直接切片。

输出:
  assets/atlas/glyphs-{n}.png  灰度+Alpha PNG，每张 2048²（16×16 格），白色字形
  assets/atlas/glyphs.json     {"cell":128,"cols":16,"sheets":7,"chars":{"王":[sheet,col,row],...}}

开屏时浏览器现场解析 14MB SVG 要 15 秒以上；预烘焙后只需下载几 MB PNG 再切片。
拓片式 SVG（黑底镂空字）在这里就反相成镂空字形，运行期不再判断。
光晕和朝代色仍在运行期加（烘焙光晕会让 PNG 体积翻几倍）。

用法:  python build/build_atlas.py
"""
import io
import json
import math
import os
import sys
from pathlib import Path

import numpy as np
import resvg_py
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parent.parent
SVG_DIR = ROOT / "jinwen_svg"
OUT_DIR = ROOT / "assets" / "atlas"

CELL = 128  # 与 index.html 桌面端纹理尺寸一致，字形铺满整格
COLS = 16   # 每张 2048²，手机解码也不吃力


def invert_rubbing(alpha: np.ndarray) -> np.ndarray:
    """与 index.html invertRubbingTile 同一规则：bbox 填充率 ≥ 0.5 视为拓片，反相内部。"""
    solid = alpha > 127
    if not solid.any():
        return alpha
    ys, xs = np.nonzero(solid)
    box = (xs.max() - xs.min() + 1) * (ys.max() - ys.min() + 1)
    if solid.sum() / box < 0.5:
        return alpha
    labels, _ = ndimage.label(~solid)
    edge = np.unique(np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]]))
    outside = np.isin(labels, edge[edge > 0])
    return np.where(outside, 0, 255 - alpha).astype(np.uint8)


def make_cell(svg_path: Path) -> Image.Image:
    png = resvg_py.svg_to_bytes(svg_path=str(svg_path), width=CELL, height=CELL)
    glyph = Image.open(io.BytesIO(bytes(png))).convert("RGBA")
    if glyph.size != (CELL, CELL):
        glyph = glyph.resize((CELL, CELL), Image.LANCZOS)
    alpha = np.asarray(glyph.split()[-1], dtype=np.uint8)
    return Image.fromarray(invert_rubbing(alpha), "L")


def main() -> int:
    index = json.loads((SVG_DIR / "index.json").read_text(encoding="utf-8"))
    chars = list(index.keys())
    per_sheet = COLS * COLS
    n_sheets = math.ceil(len(chars) / per_sheet)
    sheets = [Image.new("L", (COLS * CELL, COLS * CELL), 0) for _ in range(n_sheets)]

    mapping = {}
    missing = []
    slot = 0
    for ch in chars:
        meta = index[ch]
        svg_path = SVG_DIR / meta.get("file", f"{ch}.svg")
        if not svg_path.exists():
            svg_path = SVG_DIR / f"{ch}.svg"
        if not svg_path.exists():
            missing.append(ch)
            continue
        try:
            cell = make_cell(svg_path)
        except Exception as e:  # noqa: BLE001
            missing.append(ch)
            print(f"[skip] {ch.encode('unicode_escape').decode()}: {e}", file=sys.stderr)
            continue
        sheet, k = divmod(slot, per_sheet)
        col, row = k % COLS, k // COLS
        sheets[sheet].paste(cell, (col * CELL, row * CELL))
        mapping[ch] = [sheet, col, row]
        slot += 1
        if slot % 200 == 0:
            print(f"  {slot}/{len(chars)}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for old in OUT_DIR.glob("glyphs*.png"):
        old.unlink()
    used = math.ceil(slot / per_sheet)
    total = 0
    for i in range(used):
        alpha = sheets[i]
        if i == used - 1:
            rows_used = math.ceil((slot - i * per_sheet) / COLS)
            alpha = alpha.crop((0, 0, COLS * CELL, rows_used * CELL))
        atlas = Image.merge("LA", [Image.new("L", alpha.size, 255), alpha])
        path = OUT_DIR / f"glyphs-{i}.png"
        atlas.save(path, "PNG", optimize=True)
        total += path.stat().st_size

    meta_out = {"cell": CELL, "cols": COLS, "sheets": used, "count": len(mapping), "chars": mapping}
    (OUT_DIR / "glyphs.json").write_text(
        json.dumps(meta_out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )

    print(f"sheets={used}  cells={len(mapping)}  missing={len(missing)}  total={total / 1024:.0f} KB")
    return 0


if __name__ == "__main__":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    raise SystemExit(main())
