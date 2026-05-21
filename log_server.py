#!/usr/bin/env python3
"""Serve index.html + agent logs; accept POST writes for the monitor UI."""

from __future__ import annotations

import json
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PORT = 8765


class MonitorHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.end_headers()

    def do_POST(self) -> None:
        if self.path not in ("/", "/write"):
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON")
            return

        rel = data.get("file", "").replace("\\", "/").lstrip("/")
        if not rel or ".." in rel.split("/"):
            self.send_error(400, "Invalid file path")
            return

        target = (ROOT / rel).resolve()
        if not str(target).startswith(str(ROOT.resolve())):
            self.send_error(403, "Path outside project")
            return

        content = data.get("content", "")
        mode = data.get("mode", "w")
        target.parent.mkdir(parents=True, exist_ok=True)

        if mode == "a":
            with target.open("a", encoding="utf-8") as f:
                f.write(content)
        else:
            target.write_text(content, encoding="utf-8")

        payload = json.dumps({"ok": True, "file": rel, "bytes": len(content)}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args) -> None:
        if args and str(args[0]).startswith("GET /agent_logs"):
            return
        super().log_message(format, *args)


def main() -> None:
    host = "127.0.0.1"
    server = HTTPServer((host, PORT), MonitorHandler)
    print(f"SPRK monitor: http://{host}:{PORT}/index.html")
    print(f"Project root: {ROOT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
        sys.exit(0)


if __name__ == "__main__":
    main()
