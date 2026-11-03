"""VR“看器”页四件真实三维扫描青铜器（尊、鼎、簋、觚）的截图，给海报“沉浸体验”用。

先把 VR 分支导出：
    git archive claude/vr-galaxy-fb0eec | tar -x -C <临时目录>
    python build/poster/shot_vessels.py <临时目录>
输出 build/poster/assets/vessel_{zun,ding,gui,gu}.jpg 和 vessel_xray.jpg（透视看内底铭文）。
glb 模型不能用 file:// 加载，脚本里临时起一个只服务该目录的本地 http 服务。
"""
import functools
import http.server
import sys
import threading
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

SITE = Path(sys.argv[1]).resolve()
OUT = Path(__file__).resolve().parent / "assets"


HIDE_UI = """
for (const el of document.body.children) if (!['stage', 'inside'].includes(el.id) && el.tagName !== 'SCRIPT') el.style.visibility = 'hidden';
for (const el of document.querySelectorAll('.hot')) el.style.display = 'none';
for (const el of document.querySelectorAll('#inside > *')) if (el.tagName !== 'CANVAS') el.style.visibility = 'hidden';
"""


def center_box(size, cy=0.5, k=0.96):
    """取画面中间的正方形（边长 = 0.96 × 高）。截图前已隐藏页面上的文字面板和标注。"""
    w, h = size
    side = int(h * k)
    x0, y0 = w // 2 - side // 2, int(h * cy) - side // 2
    return (x0, y0, x0 + side, y0 + side)


def main():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(SITE))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{httpd.server_address[1]}/vessel.html"
    try:
        with sync_playwright() as pw:
            b = pw.chromium.launch(channel="msedge", args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
            pg = b.new_page(viewport={"width": 1280, "height": 900}, device_scale_factor=2)
            pg.goto(url)
            pg.wait_for_timeout(2500)
            for k in ["zun", "ding", "gui", "gu"]:
                pg.evaluate(f"document.querySelector('#tabs button[data-v={k}]').click()")  # 面板已隐藏，用 JS 点
                pg.wait_for_function("document.getElementById('mv').loaded === true", timeout=60000)
                pg.evaluate("document.getElementById('mv').autoRotate = false")
                pg.wait_for_timeout(1500)
                pg.evaluate(HIDE_UI)
                tmp = OUT / f"_v_{k}.png"
                pg.screenshot(path=tmp)
                im = Image.open(tmp).convert("RGB")
                im.crop(center_box(im.size)).resize((800, 800), Image.LANCZOS).save(OUT / f"vessel_{k}.jpg", quality=90)
                tmp.unlink()
            # 透视：尊的器壁变透明，露出内底铭文（重新打开页面，让面板恢复可点）
            pg.goto(url)
            pg.wait_for_function("document.getElementById('mv').loaded === true", timeout=60000)
            pg.wait_for_timeout(1500)
            pg.click("#btnInside")
            pg.wait_for_timeout(2500)
            pg.fill("#xray", "85")
            pg.dispatch_event("#xray", "input")
            pg.wait_for_timeout(2500)
            pg.evaluate(HIDE_UI)
            pg.screenshot(path=OUT / "_v_xray.png")
            im = Image.open(OUT / "_v_xray.png").convert("RGB")
            im.crop(center_box(im.size, cy=0.47, k=0.8)).resize((800, 800), Image.LANCZOS).save(OUT / "vessel_xray.jpg", quality=90)
            (OUT / "_v_xray.png").unlink()
            b.close()
    finally:
        httpd.shutdown()
    print("ok", sorted(p.name for p in OUT.glob("vessel_*.jpg")))


if __name__ == "__main__":
    main()
