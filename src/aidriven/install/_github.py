"""GitHub default-branch HEAD SHA resolution with TTL caching."""

from __future__ import annotations

import json
import logging
import time
from typing import TYPE_CHECKING

from aidriven.install._http import fetch_json

if TYPE_CHECKING:
    from pathlib import Path
from aidriven.install._paths import user_cache_dir

logger = logging.getLogger(__name__)

_OWNER = "ThiagoPanini"
_RESOURCES_REPO = "aidriven-resources"
_DEFAULT_BRANCH = "main"
_TTL_SECONDS = 3600  # 1 hour


def _head_cache_path() -> Path:
    return user_cache_dir() / "manifest" / "_head.json"


def resolve_head_sha(*, force: bool = False, no_cache: bool = False) -> str:
    """Resolve the current HEAD commit SHA of the default branch.

    Caches the result at ``~/.cache/aidriven/manifest/_head.json`` for 1 hour.
    Pass ``force=True`` or ``no_cache=True`` to bypass the cache.
    """
    bypass = force or no_cache
    cache_path = _head_cache_path()

    if not bypass and cache_path.exists():
        try:
            data: dict[str, object] = json.loads(cache_path.read_text(encoding="utf-8"))
            fetched_at_raw = data.get("fetched_at", 0)
            fetched_at = float(str(fetched_at_raw))
            sha = str(data.get("sha", ""))
            if sha and (time.time() - fetched_at) < _TTL_SECONDS:
                logger.debug("Using cached HEAD SHA: %s", sha)
                return sha
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            logger.debug("Invalid HEAD cache at %s — re-fetching", cache_path)

    url = f"https://api.github.com/repos/{_OWNER}/{_RESOURCES_REPO}/commits/{_DEFAULT_BRANCH}"
    logger.debug("Resolving HEAD SHA from %s", url)
    payload = fetch_json(url, headers={"Accept": "application/vnd.github+json"})
    sha = str(payload["sha"])

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(
        json.dumps({"sha": sha, "fetched_at": time.time()}, indent=2),
        encoding="utf-8",
    )
    return sha
