"""去掉漢典 SVG 渲染图边角残留的小水印：贴边带内、面积很小的连通块清空。用法：python clean_glyph.py 图...（原地改写）"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage

for f in sys.argv[1:]:
    im = Image.open(f).convert("RGBA")
    a = np.array(im)
    mask = a[..., 3] > 20
    lab, n = ndimage.label(mask, structure=np.ones((3, 3)))
    if not n:
        continue
    h, w = mask.shape
    areas = ndimage.sum(mask, lab, range(1, n + 1))
    total = areas.sum()
    band = 0.16
    for i, sl in enumerate(ndimage.find_objects(lab)):
        y0, y1, x0, x1 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop
        in_band = y1 < h * band or y0 > h * (1 - band) or x1 < w * band or x0 > w * (1 - band)
        if in_band and areas[i] < total * 0.03:
            a[lab == i + 1, 3] = 0
    Image.fromarray(a).save(f)
