"""Локальный сервер docs/ с UTF-8 заголовками (лечит кракозябры)."""
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

DOCS = Path(__file__).resolve().parent
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000


class UTF8Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DOCS), **kwargs)

    def end_headers(self):
        path = self.translate_path(self.path)
        if path.endswith(".html"):
            self.send_header("Content-Type", "text/html; charset=utf-8")
        elif path.endswith(".js"):
            self.send_header("Content-Type", "application/javascript; charset=utf-8")
        elif path.endswith(".css"):
            self.send_header("Content-Type", "text/css; charset=utf-8")
        elif path.endswith(".json"):
            self.send_header("Content-Type", "application/json; charset=utf-8")
        super().end_headers()


if __name__ == "__main__":
    os.chdir(DOCS)
    server = HTTPServer(("localhost", PORT), UTF8Handler)
    print(f"Сервер: http://localhost:{PORT}/ (docs/)")
    print("Стоп: Ctrl+C")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nСервер остановлен")
        server.server_close()