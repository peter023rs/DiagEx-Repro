"""Dependency-free local HTTP server for the review workbench."""

from __future__ import annotations

import json
import mimetypes
import threading
import webbrowser
from collections.abc import Callable
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

from diagex.review.core import (
    ReviewConflictError,
    ReviewIncompleteError,
    ReviewStore,
    ReviewValidationError,
)

STATIC_DIR = Path(__file__).with_name("static")


def _json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def make_handler(store: ReviewStore) -> type[BaseHTTPRequestHandler]:
    class ReviewHandler(BaseHTTPRequestHandler):
        server_version = "DiagExReview/1.0"

        def log_message(self, fmt: str, *args: Any) -> None:
            # Keep the terminal focused on actionable review events/errors.
            if args and str(args[1]).startswith(("4", "5")):
                super().log_message(fmt, *args)

        def _headers(self, status: int, content_type: str, length: int) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(length))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'",
            )
            self.end_headers()

        def _send_json(self, value: Any, status: int = HTTPStatus.OK) -> None:
            payload = _json_bytes(value)
            self._headers(status, "application/json; charset=utf-8", len(payload))
            self.wfile.write(payload)

        def _send_file(self, path: Path, content_type: str | None = None) -> None:
            if not path.is_file():
                self._send_json({"error": "not found"}, HTTPStatus.NOT_FOUND)
                return
            payload = path.read_bytes()
            mime = content_type or mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            self._headers(HTTPStatus.OK, mime, len(payload))
            self.wfile.write(payload)

        def _route(self) -> str:
            return unquote(urlsplit(self.path).path)

        def do_GET(self) -> None:  # noqa: N802
            route = self._route()
            if route in {"/", "/index.html"}:
                self._send_file(STATIC_DIR / "index.html", "text/html; charset=utf-8")
                return
            if route == "/api/health":
                self._send_json({"ok": True, "revision": store.state["revision"]})
                return
            if route == "/api/state":
                self._send_json(store.public_state())
                return
            if route.startswith("/api/pages/"):
                parts = route.strip("/").split("/")
                if len(parts) != 4 or parts[3] not in {"source", "inference"}:
                    self._send_json({"error": "invalid page asset"}, HTTPStatus.BAD_REQUEST)
                    return
                try:
                    page_index = int(parts[2])
                    page = next(
                        item for item in store.session["pages"]
                        if int(item["page_index"]) == page_index
                    )
                except (ValueError, StopIteration):
                    self._send_json({"error": "unknown page"}, HTTPStatus.NOT_FOUND)
                    return
                name = page[f"{parts[3]}_image"]
                candidate = (store.out_dir / "pages" / name).resolve()
                pages_root = (store.out_dir / "pages").resolve()
                if candidate.parent != pages_root:
                    self._send_json({"error": "invalid page path"}, HTTPStatus.BAD_REQUEST)
                    return
                self._send_file(candidate, "image/png")
                return
            if route.startswith("/static/"):
                name = route.removeprefix("/static/")
                if not name or "/" in name or "\\" in name or name.startswith("."):
                    self._send_json({"error": "invalid static path"}, HTTPStatus.BAD_REQUEST)
                    return
                self._send_file(STATIC_DIR / name)
                return
            self._send_json({"error": "not found"}, HTTPStatus.NOT_FOUND)

        def _read_json(self) -> dict[str, Any]:
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError as exc:
                raise ValueError("invalid Content-Length") from exc
            if length <= 0 or length > 5 * 1024 * 1024:
                raise ValueError("request body must be between 1 byte and 5 MiB")
            value = json.loads(self.rfile.read(length))
            if not isinstance(value, dict):
                raise ValueError("request body must be a JSON object")
            return value

        def do_POST(self) -> None:  # noqa: N802
            route = self._route()
            try:
                body = self._read_json()
                if route == "/api/action":
                    self._send_json(store.append_action(body))
                    return
                if route == "/api/finish":
                    expected = int(body.get("expected_revision", -1))
                    if expected != int(store.state["revision"]):
                        raise ReviewConflictError(
                            f"stale review revision {expected}; current revision is {store.state['revision']}"
                        )
                    self._send_json({"report": store.finish(), "state": store.public_state()})
                    return
                self._send_json({"error": "not found"}, HTTPStatus.NOT_FOUND)
            except ReviewConflictError as exc:
                self._send_json({"error": str(exc), "state": store.public_state()}, HTTPStatus.CONFLICT)
            except ReviewIncompleteError as exc:
                self._send_json(
                    {"error": str(exc), "details": exc.details},
                    HTTPStatus.UNPROCESSABLE_ENTITY,
                )
            except ReviewValidationError as exc:
                self._send_json(
                    {"error": str(exc), "report": exc.report},
                    HTTPStatus.UNPROCESSABLE_ENTITY,
                )
            except (KeyError, ValueError, json.JSONDecodeError) as exc:
                self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            except Exception as exc:  # noqa: BLE001
                self._send_json({"error": f"internal review error: {exc}"}, HTTPStatus.INTERNAL_SERVER_ERROR)

    return ReviewHandler


def serve_review(
    store: ReviewStore,
    *,
    host: str = "127.0.0.1",
    port: int = 8765,
    open_browser: bool = True,
    on_ready: Callable[[str], None] | None = None,
) -> str:
    """Serve until interrupted; returns the bound URL after shutdown."""
    server = ThreadingHTTPServer((host, port), make_handler(store))
    actual_port = int(server.server_address[1])
    display_host = "127.0.0.1" if host in {"0.0.0.0", "::"} else host
    url = f"http://{display_host}:{actual_port}/"
    if on_ready is not None:
        on_ready(url)
    if open_browser:
        threading.Timer(0.25, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return url
