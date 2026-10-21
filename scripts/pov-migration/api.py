"""Calls to the new install's API, for the skills and label steps. Standard library only."""

import base64
import http.client
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Network failures worth another try; HTTP errors come back as a status instead.
RETRYABLE_ERRORS = (
    urllib.error.URLError,
    http.client.HTTPException,
    ssl.SSLError,
    TimeoutError,
    ConnectionError,
)


class Stop(Exception):
    """The run cannot go on (token rejected, app unreachable); rerunning later is safe."""


class Target:
    """One install's API, called with the user's token."""

    def __init__(self, domain: str, token: str):
        url = domain.rstrip("/") if "://" in domain else f"https://{domain.rstrip('/')}"
        host = urllib.parse.urlparse(url).hostname
        if not url.startswith("https://") and host not in ("localhost", "127.0.0.1", "::1"):
            sys.exit(f"refusing to send the token over plain http to {host}; use https")
        self.base, self.token = url, token

    def call(
        self, method: str, path: str, query: dict | None = None, body: dict | None = None
    ) -> tuple[int, Any]:
        url = self.base + path
        if query:
            url += "?" + urllib.parse.urlencode({k: v for k, v in query.items() if v is not None})
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method)
        # Unredirected: a redirect to another host must not carry the token there.
        req.add_unredirected_header("Authorization", f"Bearer {self.token}")
        req.add_header("Accept", "application/json")
        if data is not None:
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                raw, ctype, status = resp.read(), resp.headers.get("Content-Type", ""), resp.status
        except urllib.error.HTTPError as e:
            raw, ctype, status = e.read(), e.headers.get("Content-Type", ""), e.code
        if "json" in ctype:
            try:
                return status, json.loads(raw or b"null")
            except json.JSONDecodeError:
                pass
        return status, {"_non_json": raw[:120].decode(errors="replace")}


def call_with_retry(
    t: Target,
    method: str,
    path: str,
    query: dict | None = None,
    body: dict | None = None,
    tries: int = 5,
):
    """Retries network errors, 5xx and 429 with backoff; raises Stop on 401/403 or when retries run out."""
    status, payload = None, None
    for attempt in range(1, tries + 1):
        try:
            status, payload = t.call(method, path, query, body)
        except RETRYABLE_ERRORS as e:
            status, payload = None, f"{type(e).__name__}: {e}"
        if status in (401, 403):
            raise Stop(
                f"the app said {status}: the token expired or lacks permission. Save a fresh token and rerun"
            )
        if status is not None and status < 500 and status != 429:
            return status, payload
        if attempt < tries:
            wait = min(30, 2**attempt)
            print(
                f"  {method} {path}: {status or payload}; retrying in {wait}s ({attempt}/{tries})"
            )
            time.sleep(wait)
    raise Stop(f"the app kept failing ({status or payload}); rerun when it is reachable")


def load_token(args) -> str:
    """The login JWT from AUTOHEAL_TOKEN or --token-file. A pasted 'Bearer ' prefix is dropped."""
    token = os.environ.get("AUTOHEAL_TOKEN", "")
    if not token and getattr(args, "token_file", None):
        token = Path(args.token_file).expanduser().read_text()
    token = token.strip().removeprefix("Bearer ").strip()
    if not token:
        sys.exit("no token: set AUTOHEAL_TOKEN or pass --token-file")
    return token


def token_expires_at(token: str) -> datetime | None:
    """The JWT's exp claim, read without verifying it (the server does that)."""
    try:
        payload = token.split(".")[1]
        claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        return datetime.fromtimestamp(int(claims["exp"]), UTC)
    except (IndexError, ValueError, KeyError, TypeError):
        return None


def check_token(token: str, need_minutes: int = 30):
    """Refuse an API key or an expired token; warn when it may run out partway through a long step."""
    if token.startswith(("ahpat_", "ahsa_")):
        print(
            "STOPPED: this is an API key. The skills and project checks only accept a login token from the browser"
        )
        print(
            "  (sign in to the new install, copy the Authorization header of any /api request, save it to the token file)"
        )
        sys.exit(2)
    exp = token_expires_at(token)
    if exp is None:
        return
    left = (exp - datetime.now(UTC)).total_seconds() / 60
    if left <= 0:
        sys.exit(f"the token expired at {exp:%Y-%m-%d %H:%M} UTC; save a fresh one and rerun")
    if left < need_minutes:
        print(
            f"  WARNING: the token expires in {left:.0f} min ({exp:%H:%M} UTC); a long run may stop partway (rerun is safe)"
        )


def target(args, need_minutes: int = 30) -> Target:
    token = load_token(args)
    check_token(token, need_minutes)
    return Target(args.domain, token)


def stops_cleanly(fn):
    """Turn Stop into exit 3: an outside problem, and rerunning the same command is safe."""

    def run(args):
        try:
            return fn(args)
        except Stop as e:
            print(f"STOPPED: {e}. Rerunning is safe.")
            sys.exit(3)

    return run


def api_args(p, required: bool = True):
    """The options every API command takes."""
    p.add_argument(
        "--domain", required=required, help="the new install, e.g. app.example.com (or a full URL)"
    )
    p.add_argument(
        "--token-file",
        help="file holding the login JWT (else AUTOHEAL_TOKEN); a 'Bearer ' prefix is fine",
    )
