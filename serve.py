# Threaded static server so demo.html, the galaxy iframe, and jinwen SVGs
# can load at the same time. Python's default http.server is single-thread
# and drops the page when ~1690 glyphs hit it at once.
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

HOST = "127.0.0.1"
PORT = 8000


class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        if self.path.split("?", 1)[0].endswith(".svg"):
            self.send_header("Cache-Control", "public, max-age=86400")
        super().end_headers()

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    try:
        httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    except OSError:
        print(f"http://{HOST}:{PORT}/demo.html", flush=True)
        raise SystemExit(0)
    print(f"http://{HOST}:{PORT}/demo.html", flush=True)
    httpd.serve_forever()
