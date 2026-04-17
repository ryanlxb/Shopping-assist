"""Shared browser manager — CDP connection with launch fallback."""

import asyncio
import json
import logging
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from playwright.async_api import Browser, BrowserContext, Page, Playwright, async_playwright

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
]


@dataclass
class BrowserSession:
    context: BrowserContext
    page: Page
    owns_context: bool


class BrowserManager:
    def __init__(
        self,
        platform_name: str,
        headless: bool = True,
        cdp_enabled: bool = True,
        cdp_port: int = 9222,
    ):
        self.platform_name = platform_name
        self.headless = headless
        self.cdp_enabled = cdp_enabled
        self.cdp_port = cdp_port
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._is_cdp = False
        self._cookie_path = Path(f"data/cookies/{platform_name}_cookies.json")

    async def _probe_cdp(self) -> bool:
        """Check if Chrome CDP endpoint is reachable."""
        import httpx

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"http://localhost:{self.cdp_port}/json/version",
                    timeout=2.0,
                )
                if resp.status_code == 200 and "Browser" in resp.json():
                    return True
        except Exception:
            pass
        return False

    async def ensure_browser(self) -> Browser:
        if self._browser and self._browser.is_connected():
            return self._browser

        self._playwright = await async_playwright().start()

        if self.cdp_enabled and await self._probe_cdp():
            try:
                self._browser = await self._playwright.chromium.connect_over_cdp(
                    f"http://localhost:{self.cdp_port}"
                )
                self._is_cdp = True
                logger.info(
                    f"[{self.platform_name}] Connected to Chrome via CDP on port {self.cdp_port}"
                )
                return self._browser
            except Exception as e:
                logger.warning(f"[{self.platform_name}] CDP connection failed: {e}, falling back to launch")

        self._browser = await self._playwright.chromium.launch(headless=self.headless)
        self._is_cdp = False
        logger.info(f"[{self.platform_name}] Launched Chromium (headless={self.headless})")
        return self._browser

    async def new_page(self) -> BrowserSession:
        browser = await self.ensure_browser()

        if self._is_cdp:
            if browser.contexts:
                ctx = browser.contexts[0]
            else:
                ctx = await browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    locale="zh-CN",
                )
            page = await ctx.new_page()
            return BrowserSession(context=ctx, page=page, owns_context=False)

        ua = random.choice(USER_AGENTS)
        ctx = await browser.new_context(
            user_agent=ua,
            viewport={"width": 1920, "height": 1080},
            locale="zh-CN",
        )
        try:
            from playwright_stealth import Stealth
            stealth = Stealth(navigator_platform_override="MacIntel")
            await stealth.apply_stealth_async(ctx)
        except ImportError:
            logger.warning("playwright-stealth not installed")

        if self._cookie_path.exists():
            try:
                cookies = json.loads(self._cookie_path.read_text())
                await ctx.add_cookies(cookies)
            except Exception:
                logger.warning(f"Failed to load {self.platform_name} cookies")

        page = await ctx.new_page()
        return BrowserSession(context=ctx, page=page, owns_context=True)

    async def save_cookies(self, context: BrowserContext):
        if self._is_cdp:
            return
        try:
            self._cookie_path.parent.mkdir(parents=True, exist_ok=True)
            cookies = await context.cookies()
            self._cookie_path.write_text(json.dumps(cookies, ensure_ascii=False))
        except Exception:
            logger.warning(f"Failed to save {self.platform_name} cookies")

    async def close(self):
        if self._browser:
            try:
                await self._browser.close()
            except Exception:
                pass
            self._browser = None
        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception:
                pass
            self._playwright = None

    @property
    def is_cdp(self) -> bool:
        return self._is_cdp

    @staticmethod
    async def random_delay(min_s: float = 3.0, max_s: float = 8.0):
        await asyncio.sleep(random.uniform(min_s, max_s))

    @staticmethod
    async def scroll_page(page: Page, times: int = 5, delay_range: tuple = (1.5, 3.0)):
        for _ in range(times):
            await page.evaluate("window.scrollBy(0, window.innerHeight)")
            await asyncio.sleep(random.uniform(*delay_range))


async def download_product_images(image_urls: list[str], product_id: str) -> list[str]:
    """Download images and return local file paths. Shared by all scrapers."""
    import httpx

    if not product_id.isdigit():
        raise ValueError(f"product_id must be numeric, got: {product_id!r}")

    saved_paths = []
    image_dir = Path(f"data/images/{product_id}")
    image_dir.mkdir(parents=True, exist_ok=True)

    async with httpx.AsyncClient() as client:
        for i, url in enumerate(image_urls):
            try:
                if url.startswith("//"):
                    url = f"https:{url}"
                resp = await client.get(url, timeout=30.0)
                resp.raise_for_status()

                ext = url.split(".")[-1].split("?")[0]
                if ext not in ("jpg", "jpeg", "png", "gif", "webp"):
                    ext = "jpg"
                file_path = image_dir / f"img_{i}.{ext}"
                file_path.write_bytes(resp.content)
                saved_paths.append(str(file_path))
            except Exception as e:
                logger.warning(f"Failed to download image {url}: {e}")

    return saved_paths
