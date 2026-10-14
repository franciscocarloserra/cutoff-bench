#!/usr/bin/env python3
"""Serve this dir for local dev + POST /log appends browser telemetry to LOG."""
import json, os, http.server

PORT = int(os.environ.get("PORT", 7810))
LOG = "/tmp/cutoff-bench-console.jsonl"
MAX_BODY = 20000

class H(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/log":
            return self.send_error(404)
        body = self.rfile.read(min(int(self.headers.get("Content-Length", 0)), MAX_BODY))
        with open(LOG, "a") as f:
            f.write(body.decode(errors="replace").strip() + "\n")
        self.send_response(204); self.end_headers()

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

os.chdir(os.path.dirname(os.path.abspath(__file__)))
http.server.ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
