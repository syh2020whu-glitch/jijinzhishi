"""录 40 秒静音演示：寻姓 → 听音 → 铸辞 → 识图。先起 serve.py（8080），再：python build/ppt/record.py
产出 assets/demo.mp4（H.264，PowerPoint 可直接嵌）。"""
import shutil
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8080/demo.html"
ROOT = Path(__file__).parent
TMP = ROOT / "dl" / "video"
TMP.mkdir(parents=True, exist_ok=True)
for f in TMP.glob("*.webm"):
    f.unlink()

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
    ctx = browser.new_context(viewport={"width": 1600, "height": 900},
                              record_video_dir=str(TMP), record_video_size={"width": 1600, "height": 900})
    page = ctx.new_page()

    def go(h, wait):
        page.goto(BASE + h)
        page.wait_for_timeout(wait)

    go("#/", 4500)                                   # 0–4.5s 星河首页
    go("#/learn?tab=wall", 1500)                      # 寻姓
    page.fill("#nameInput", "")
    page.type("#nameInput", "周", delay=350)
    page.wait_for_timeout(600)
    page.press("#nameInput", "Enter")
    page.wait_for_timeout(5000)
    go("#/learn?tab=listen", 2000)                    # 听音
    try:
        page.click("#playIpa")
    except Exception:
        pass
    page.wait_for_timeout(3500)
    go("#/play?tab=ritual", 2000)                     # 铸辞
    page.click("#ritualNext1")
    page.wait_for_timeout(1500)
    recs = page.locator("#blessFamilies button.rec")
    for i in range(min(2, recs.count())):
        recs.nth(i).click()
        page.wait_for_timeout(700)
    page.click("#blessBtn")
    page.wait_for_timeout(4500)
    try:
        page.click(".greet-card")
        page.wait_for_timeout(2500)
    except Exception:
        pass
    go("#/work?tab=rec", 2500)                        # 识图
    card = page.locator("[data-case]", has_text="㝅伯鼎")
    (card.first if card.count() else page.locator("[data-case]").first).click()
    page.wait_for_timeout(4500)
    gray = page.locator(".ocr-box-item:has(.gray-dot) .gray-dot")
    if gray.count():
        gray.first.click()
        page.wait_for_timeout(4500)
    page.screenshot(path=str(ROOT / "assets" / "demo_poster.png"))
    ctx.close()
    browser.close()

webm = next(TMP.glob("*.webm"))
ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
out = ROOT / "assets" / "demo.mp4"
subprocess.run([ffmpeg, "-y", "-i", str(webm), "-ss", "0.8", "-an", "-vf", "fps=25,format=yuv420p",
                "-c:v", "libx264", "-preset", "medium", "-crf", "23", "-movflags", "+faststart", str(out)],
               check=True, capture_output=True)
probe = subprocess.run([ffmpeg, "-i", str(out)], capture_output=True, text=True)
print([l.strip() for l in probe.stderr.splitlines() if "Duration" in l or "Video:" in l])
print("wrote", out, out.stat().st_size // 1024, "KB")
