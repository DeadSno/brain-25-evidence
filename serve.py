#!/usr/bin/env python3
"""Start local HTTP server for headless browser testing.

Usage:
    python serve.py          # Start server on port 8000
    python serve.py 8080     # Start on custom port
"""
import http.server
import sys
from pathlib import Path

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
DIRECTORY = Path(__file__).resolve().parent / "docs"

TEXT_TYPES = {"html", "css", "js", "json", "txt", "xml", "svg", "csv", "md"}


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIRECTORY), **kwargs)

    def guess_type(self, path):
        ctype = super().guess_type(path)
        ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
        if ext in TEXT_TYPES and "charset=" not in ctype:
            ctype += "; charset=utf-8"
        return ctype

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()


if __name__ == "__main__":
    with http.server.HTTPServer(("", PORT), Handler) as httpd:
        print(f"Serving {DIRECTORY} at http://localhost:{PORT}")
        print("Press Ctrl+C to stop")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")