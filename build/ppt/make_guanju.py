"""《关雎》首句"关关雎鸠，在河之洲"的上古音拟读 → assets/guanju.mp3。
构拟取郑张尚芳《上古音系》（据韵典网 ytenx.org 上古音系栏），用网站同一套 meSpeak 合成（build/tts_page.html）。
python build/ppt/make_guanju.py"""
import base64
import http.server
import json
import subprocess
import threading
from pathlib import Path

import imageio_ffmpeg
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).parent
BUILD = ROOT.parent
TMP = ROOT / "dl" / "guanju"
TMP.mkdir(parents=True, exist_ok=True)
LINE = [("關", "kroːn"), ("關", "kroːn"), ("雎", "sʰa"), ("鳩", "ku"),
        ("在", "zlɯːʔ"), ("河", "ɡaːl"), ("之", "tjɯ"), ("洲", "tju")]


class Quiet(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(BUILD), **kw)

    def log_message(self, *a, **kw):
        pass


httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Quiet)
threading.Thread(target=httpd.serve_forever, daemon=True).start()
clips = []
with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge")
    page = browser.new_page()
    page.goto(f"http://127.0.0.1:{httpd.server_address[1]}/tts_page.html")
    page.evaluate("() => window.ttsReady")
    for i, (ch, ipa) in enumerate(LINE):
        res = page.evaluate("([ipa, kbps]) => window.renderIpa(ipa, kbps)", [ipa, 64])
        f = TMP / f"{i}.mp3"
        f.write_bytes(base64.b64decode(res["mp3"]))
        clips.append(f)
        print(ch, ipa, res["mode"], res["ms"], "ms")
    browser.close()
httpd.shutdown()

# 字间停 0.18 秒，"鸠"后逗号停 0.6 秒
ff = imageio_ffmpeg.get_ffmpeg_exe()
inputs, parts = [], []
for i, f in enumerate(clips):
    inputs += ["-i", str(f)]
    gap = 0.6 if i == 3 else 0.18
    parts.append(f"[{i}:a]aresample=22050,aformat=channel_layouts=mono,apad=pad_dur={gap}[a{i}]")
graph = ";".join(parts) + ";" + "".join(f"[a{i}]" for i in range(len(clips))) + f"concat=n={len(clips)}:v=0:a=1[out]"
out = ROOT / "assets" / "guanju.mp3"
subprocess.run([ff, "-y", *inputs, "-filter_complex", graph, "-map", "[out]", "-b:a", "64k", str(out)], check=True, capture_output=True)
json.dump([{"char": c, "ipa": i} for c, i in LINE], open(TMP / "line.json", "w", encoding="utf8"), ensure_ascii=False)
print("wrote", out, out.stat().st_size // 1024, "KB")
