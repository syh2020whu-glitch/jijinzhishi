"""
把 data/laoyin_seed.json 里的上古音构拟（IPA）用 meSpeak 离线合成为 MP3，
前端只需 fetch 几 KB 的音频，不再加载 3 MB 的 WASM 合成器。

输出:
  assets/audio/ipa/<char>.mp3
  assets/audio/ipa/manifest.json   {"王": {"file": "王.mp3", "ipa": "...", "mode": "ipa"}, ...}

依赖: playwright (chromium)、build/vendor/{mespeak.js,mespeak_config.json,voice-en.json,lame.min.js}
用法:  python build/prerender_ipa.py
"""
import base64
import http.server
import json
import os
import sys
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
SEED = ROOT / "data" / "laoyin_seed.json"
OUT_DIR = ROOT / "assets" / "audio" / "ipa"
KBPS = 40


def serve(directory: Path):
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(directory), **kw)

        def log_message(self, *a, **kw):
            pass

    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Quiet)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def main() -> int:
    seed = json.loads(SEED.read_text(encoding="utf-8"))
    entries = [e for e in seed["entries"] if e.get("status") != "ipa_pending" and e.get("ipa")]
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    httpd = serve(BUILD)
    port = httpd.server_address[1]
    manifest = {}
    total = 0
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel=os.environ.get("PW_CHANNEL", "chrome"))
            page = browser.new_page()
            page.on("console", lambda m: print("[page]", m.text, file=sys.stderr) if m.type == "error" else None)
            page.goto(f"http://127.0.0.1:{port}/tts_page.html")
            page.evaluate("() => window.ttsReady")
            for e in entries:
                ch, ipa = e["char"], e["ipa"]
                res = page.evaluate("([ipa, kbps]) => window.renderIpa(ipa, kbps)", [ipa, KBPS])
                if not res:
                    print(f"[fail] {ch.encode('unicode_escape').decode()} {ipa}", file=sys.stderr)
                    continue
                data = base64.b64decode(res["mp3"])
                fname = f"{ch}.mp3"
                (OUT_DIR / fname).write_bytes(data)
                total += len(data)
                manifest[ch] = {"file": fname, "ipa": ipa, "mode": res["mode"], "ms": res["ms"]}
            browser.close()
    finally:
        httpd.shutdown()

    (OUT_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
    latin = sum(1 for v in manifest.values() if v["mode"] == "latin")
    print(f"clips={len(manifest)}/{len(entries)}  latin-fallback={latin}  total={total / 1024:.0f} KB")
    return 0


if __name__ == "__main__":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    raise SystemExit(main())
