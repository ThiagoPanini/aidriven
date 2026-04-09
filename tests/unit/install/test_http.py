"""Tests for HTTP retry classifier: transient vs fail-fast responses."""

from __future__ import annotations

import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from aidriven.install._http import fetch_bytes


def _http_error(code: int) -> urllib.error.HTTPError:
    return urllib.error.HTTPError(
        url="https://example.com",
        code=code,
        msg=f"HTTP {code}",
        hdrs=MagicMock(),
        fp=None,
    )


# ── Transient errors (retry up to 3 attempts) ─────────────────────────────────


class TestTransientErrors:
    """Network errors, 5xx, and 429 are retried up to 3 times."""

    @pytest.mark.parametrize(
        "status",
        [500, 502, 503, 504, 429],
        ids=["500", "502", "503", "504", "429"],
    )
    def test_retries_on_transient_http_status(self, status: int) -> None:
        """
        Given an HTTP response with a transient status code,
        When fetch_bytes is called,
        Then it retries up to 3 attempts before raising.
        """
        # ── Given ──
        error = _http_error(status)

        with (
            patch("aidriven.install._http.urllib.request.urlopen", side_effect=error) as mock_open,
            patch("aidriven.install._http.time.sleep"),
            pytest.raises(urllib.error.HTTPError) as exc_info,
        ):  # avoid real delays
            # ── When ──
            fetch_bytes("https://example.com/resource")

        # ── Then ──
        # 1 initial attempt + 3 retries = 4 total calls
        assert mock_open.call_count == 4
        assert exc_info.value.code == status

    def test_retries_on_network_error(self) -> None:
        """
        Given a connection error (URLError),
        When fetch_bytes is called,
        Then it retries up to 3 attempts.
        """
        # ── Given ──
        error = urllib.error.URLError("Connection refused")

        with (
            patch("aidriven.install._http.urllib.request.urlopen", side_effect=error) as mock_open,
            patch("aidriven.install._http.time.sleep"),
            pytest.raises(urllib.error.URLError),
        ):
            # ── When ──
            fetch_bytes("https://example.com/resource")

        # ── Then ──
        assert mock_open.call_count == 4  # 1 + 3 retries

    def test_backoff_delays_are_correct(self) -> None:
        """
        Given a transient error on each attempt,
        When fetch_bytes is called,
        Then sleep() is called with (1, 2, 4) second delays in order.
        """
        # ── Given ──
        error = _http_error(503)

        with (
            patch("aidriven.install._http.urllib.request.urlopen", side_effect=error),
            patch("aidriven.install._http.time.sleep") as mock_sleep,
            pytest.raises(urllib.error.HTTPError),
        ):
            # ── When ──
            fetch_bytes("https://example.com/resource")

        # ── Then ──
        # Delays: 0 (first), 1, 2, 4 — but sleep(0) is not called
        assert mock_sleep.call_count == 3
        delays = [c.args[0] for c in mock_sleep.call_args_list]
        assert delays == [1.0, 2.0, 4.0]


# ── Fail-fast errors (no retry) ───────────────────────────────────────────────


class TestFailFastErrors:
    """HTTP 404 and other 4xx (except 429) fail immediately without retry."""

    @pytest.mark.parametrize(
        "status",
        [400, 401, 403, 404, 422],
        ids=["400", "401", "403", "404", "422"],
    )
    def test_fails_fast_on_4xx(self, status: int) -> None:
        """
        Given an HTTP 4xx response (not 429),
        When fetch_bytes is called,
        Then it raises immediately without retrying.
        """
        # ── Given ──
        error = _http_error(status)

        with (
            patch("aidriven.install._http.urllib.request.urlopen", side_effect=error) as mock_open,
            patch("aidriven.install._http.time.sleep") as mock_sleep,
            pytest.raises(urllib.error.HTTPError) as exc_info,
        ):
            # ── When ──
            fetch_bytes("https://example.com/resource")

        # ── Then ──
        assert mock_open.call_count == 1  # No retry
        assert mock_sleep.call_count == 0
        assert exc_info.value.code == status


# ── HTTPS enforcement ─────────────────────────────────────────────────────────


class TestHttpsEnforcement:
    """Only HTTPS URLs are accepted."""

    def test_raises_on_http_url(self) -> None:
        """
        Given an http:// URL,
        When fetch_bytes is called,
        Then ValueError is raised without making any network call.
        """
        # ── Given ──
        url = "http://example.com/resource"

        with (
            patch("aidriven.install._http.urllib.request.urlopen") as mock_open,
            pytest.raises(ValueError, match="Only HTTPS URLs"),
        ):
            # ── When ──
            fetch_bytes(url)

        # ── Then ──
        mock_open.assert_not_called()

    def test_accepts_https_url(self) -> None:
        """
        Given an https:// URL that returns data,
        When fetch_bytes is called,
        Then the response body is returned.
        """
        # ── Given ──
        mock_resp = MagicMock()
        mock_resp.read.return_value = b"hello"
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("aidriven.install._http.urllib.request.urlopen", return_value=mock_resp):
            # ── When ──
            result = fetch_bytes("https://example.com/resource")

        # ── Then ──
        assert result == b"hello"
