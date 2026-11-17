"""One JSON log line per HTTP request, on stdout.

KEEP THIS: one log line per request (status + duration) is what the workspace Monitoring tab charts.
Each finished request writes ONE line, e.g.
  {"method": "GET", "path": "/healthz", "status": 200, "durationMs": 1.4, "ua": "curl/8.5.0"}
uvicorn's own access log is turned off (--no-access-log) so each request is logged once.
No query string, bodies, cookies or Authorization headers are logged.

A plain ASGI middleware (not BaseHTTPMiddleware) so streamed responses pass through
untouched; the duration runs until the last byte of the response is sent.
"""

import json
import sys
import time


class RequestLogMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start = time.perf_counter()
        status = 500

        async def send_wrapper(message):
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            ua = ""
            for name, value in scope.get("headers") or []:
                if name == b"user-agent":
                    ua = value.decode("latin-1")
                    break
            line = {
                "method": scope.get("method"),
                "path": scope.get("path"),
                "status": status,
                "durationMs": round((time.perf_counter() - start) * 1000, 1),
                "ua": ua,
            }
            print(json.dumps(line), file=sys.stdout, flush=True)
