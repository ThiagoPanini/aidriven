"""HTTPS-only fetch wrapper with retry/backoff."""

from __future__ import annotations

import logging
import ssl
import time
import urllib.error
import urllib.request
from typing import Any

logger = logging.getLogger(__name__)

_RETRY_DELAYS = (1.0, 2.0, 4.0)  # seconds between attempts 1→2, 2→3, 3→fail


def fetch_bytes(url: str, *, headers: dict[str, str] | None = None) -> bytes:
    """Fetch *url* over HTTPS and return the response body as bytes.

    Rules:
    - URL must start with ``https://`` — otherwise raises ``ValueError``.
    - Uses ``ssl.create_default_context()`` for certificate verification.
    - Retries up to 3 times (total 3 attempts) with exponential back-off
      (1 s / 2 s / 4 s) on:
        - Network / connection errors
        - HTTP 5xx responses
        - HTTP 429 Too Many Requests
    - Fails-fast (no retry) on all other HTTP 4xx responses.
    """
    if not url.startswith("https://"):
        raise ValueError(f"Only HTTPS URLs are allowed; got: {url!r}")

    ctx = ssl.create_default_context()
    req_headers = headers or {}
    last_exc: Exception | None = None

    for attempt, delay in enumerate([0.0, *list(_RETRY_DELAYS)]):
        if delay > 0:
            logger.debug("Retrying %s in %.0f s (attempt %d/3)…", url, delay, attempt)
            time.sleep(delay)
        try:
            request = urllib.request.Request(url, headers=req_headers)
            with urllib.request.urlopen(request, context=ctx) as resp:
                data: bytes = resp.read()
                return data
        except urllib.error.HTTPError as exc:
            status: int = exc.code
            if status == 429 or 500 <= status < 600:
                logger.debug("HTTP %d from %s — transient, will retry", status, url)
                last_exc = exc
                continue
            # 4xx (except 429) — fail fast
            raise
        except (urllib.error.URLError, OSError) as exc:
            logger.debug("Network error fetching %s: %s — will retry", url, exc)
            last_exc = exc
            continue

    assert last_exc is not None  # guaranteed — loop always sets it before continuing
    raise last_exc


def fetch_json(url: str, *, headers: dict[str, str] | None = None) -> Any:
    """Fetch *url* and parse the body as JSON."""
    import json

    return json.loads(fetch_bytes(url, headers=headers).decode())
