"""Tests for BrowserManager — CDP connection and launch fallback."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.scraper.browser import BrowserManager, BrowserSession, download_product_images


class TestBrowserManagerInit:
    def test_default_cdp_enabled(self):
        bm = BrowserManager(platform_name="jd")
        assert bm.cdp_enabled is True
        assert bm.cdp_port == 9222

    def test_cdp_disabled(self):
        bm = BrowserManager(platform_name="tb", cdp_enabled=False)
        assert bm.cdp_enabled is False

    def test_cookie_path(self):
        bm = BrowserManager(platform_name="jd")
        assert "jd_cookies.json" in str(bm._cookie_path)


class TestCDPProbe:
    @pytest.mark.asyncio
    async def test_probe_success(self):
        bm = BrowserManager(platform_name="jd")
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"Browser": "Chrome/147", "webSocketDebuggerUrl": "ws://..."}

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_resp
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await bm._probe_cdp()
            assert result is True

    @pytest.mark.asyncio
    async def test_probe_failure(self):
        bm = BrowserManager(platform_name="jd")

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.side_effect = Exception("connection refused")
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await bm._probe_cdp()
            assert result is False


class TestEnsureBrowser:
    @pytest.mark.asyncio
    async def test_launch_fallback_when_cdp_disabled(self):
        bm = BrowserManager(platform_name="jd", cdp_enabled=False)

        mock_browser = MagicMock()
        mock_browser.is_connected.return_value = True

        mock_pw = AsyncMock()
        mock_pw.chromium.launch.return_value = mock_browser

        with patch("src.scraper.browser.async_playwright") as mock_apw:
            mock_apw_instance = AsyncMock()
            mock_apw_instance.start.return_value = mock_pw
            mock_apw.return_value = mock_apw_instance

            browser = await bm.ensure_browser()
            assert browser == mock_browser
            assert bm._is_cdp is False
            mock_pw.chromium.launch.assert_called_once()

        await bm.close()

    @pytest.mark.asyncio
    async def test_cdp_connect_when_probe_succeeds(self):
        bm = BrowserManager(platform_name="jd", cdp_enabled=True, cdp_port=9222)

        mock_browser = MagicMock()
        mock_browser.is_connected.return_value = True

        mock_pw = AsyncMock()
        mock_pw.chromium.connect_over_cdp.return_value = mock_browser

        with patch("src.scraper.browser.async_playwright") as mock_apw, \
             patch.object(bm, "_probe_cdp", return_value=True):
            mock_apw_instance = AsyncMock()
            mock_apw_instance.start.return_value = mock_pw
            mock_apw.return_value = mock_apw_instance

            browser = await bm.ensure_browser()
            assert browser == mock_browser
            assert bm._is_cdp is True
            mock_pw.chromium.connect_over_cdp.assert_called_once()

        await bm.close()


class TestSaveCookies:
    @pytest.mark.asyncio
    async def test_noop_in_cdp_mode(self):
        bm = BrowserManager(platform_name="jd")
        bm._is_cdp = True
        ctx = AsyncMock()
        await bm.save_cookies(ctx)
        ctx.cookies.assert_not_called()


class TestBrowserSession:
    def test_dataclass_fields(self):
        session = BrowserSession(
            context=MagicMock(),
            page=MagicMock(),
            owns_context=True,
        )
        assert session.owns_context is True
