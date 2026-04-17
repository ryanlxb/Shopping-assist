"""JD (京东) scraper using Playwright with stealth mode and DOM extraction."""

import asyncio
import json
import logging
import random
from pathlib import Path
from urllib.parse import quote

from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
]

COOKIE_PATH = Path("data/cookies/jd_cookies.json")

# JS to extract product data directly from JD search page DOM
_JS_EXTRACT_PRODUCTS = r"""() => {
    const items = document.querySelectorAll('#J_goodsList .gl-item');
    const results = [];
    for (const item of items) {
        try {
            const nameEl = item.querySelector('.p-name em');
            if (!nameEl) continue;
            const name = nameEl.innerText.trim();
            if (!name || name.length < 4) continue;

            let price = null;
            const priceEl = item.querySelector('.p-price strong i:last-child')
                         || item.querySelector('.p-price strong');
            if (priceEl) {
                const priceText = priceEl.innerText.replace(/[￥¥\s]/g, '').trim();
                price = parseFloat(priceText);
                if (isNaN(price)) price = null;
            }

            const linkEl = item.querySelector('.p-img a');
            let productUrl = '';
            if (linkEl) {
                const h = linkEl.href || linkEl.getAttribute('href') || '';
                productUrl = h.startsWith('//') ? 'https:' + h : h;
            }

            let shopName = '';
            const shopEl = item.querySelector('.p-shop a');
            if (shopEl) shopName = shopEl.innerText.trim();

            let thumbnailUrl = '';
            const imgEl = item.querySelector('.p-img img');
            if (imgEl) {
                const src = imgEl.dataset.lazyImg || imgEl.src || '';
                thumbnailUrl = src.startsWith('//') ? 'https:' + src : src;
            }

            results.push({
                name: name.substring(0, 100),
                price: price,
                product_url: productUrl.substring(0, 500),
                shop_name: shopName.substring(0, 60),
                thumbnail_url: thumbnailUrl.substring(0, 300),
            });
        } catch(e) {}
    }
    return results;
}"""


from src.scraper.platform import register_platform


@register_platform("jd")
class JDScraper:
    platform_name: str = "jd"

    def __init__(self, headless: bool = True):
        self.headless = headless
        self._playwright = None
        self._browser = None

    async def _ensure_browser(self):
        if self._browser is None:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=self.headless)
        return self._browser

    async def _new_context(self):
        browser = await self._ensure_browser()
        ua = random.choice(USER_AGENTS)
        context = await browser.new_context(
            user_agent=ua,
            viewport={"width": 1920, "height": 1080},
            locale="zh-CN",
        )
        try:
            from playwright_stealth import Stealth
            stealth = Stealth(navigator_platform_override="MacIntel")
            await stealth.apply_stealth_async(context)
        except ImportError:
            logger.warning("playwright-stealth not installed, proceeding without stealth")

        if COOKIE_PATH.exists():
            try:
                cookies = json.loads(COOKIE_PATH.read_text())
                await context.add_cookies(cookies)
            except Exception:
                logger.warning("Failed to load saved cookies")

        return context

    async def _random_delay(self, min_s: float = 3.0, max_s: float = 8.0):
        delay = random.uniform(min_s, max_s)
        await asyncio.sleep(delay)

    async def _save_cookies(self, context):
        try:
            COOKIE_PATH.parent.mkdir(parents=True, exist_ok=True)
            cookies = await context.cookies()
            COOKIE_PATH.write_text(json.dumps(cookies, ensure_ascii=False))
        except Exception:
            logger.warning("Failed to save cookies")

    async def search(self, keyword: str, limit: int = 30) -> list[dict]:
        """Search JD for products by keyword using DOM extraction."""
        context = await self._new_context()
        try:
            page = await context.new_page()

            search_url = f"https://search.jd.com/Search?keyword={quote(keyword)}&enc=utf-8"
            logger.info(f"Searching JD: {keyword}")

            await page.goto(search_url, wait_until="domcontentloaded")
            await self._random_delay(8.0, 12.0)

            for _ in range(5):
                await page.evaluate("window.scrollBy(0, window.innerHeight)")
                await self._random_delay(1.5, 3.0)

            products = await page.evaluate(_JS_EXTRACT_PRODUCTS)

            await self._save_cookies(context)
            logger.info(f"Found {len(products)} products on JD for '{keyword}'")

            return products[:limit]

        except Exception as e:
            logger.error(f"JD search failed for '{keyword}': {e}")
            raise
        finally:
            await context.close()

    async def get_detail(self, product_url: str) -> dict:
        """Fetch product detail page and extract ingredient info."""
        from src.scraper.parser import parse_product_detail

        context = await self._new_context()
        try:
            page = await context.new_page()

            await self._random_delay()
            logger.info(f"Fetching detail: {product_url}")

            await page.goto(product_url, wait_until="domcontentloaded")
            await self._random_delay(2.0, 4.0)

            # Click on the specs tab if available
            try:
                spec_tab = page.locator("text=规格与包装")
                if await spec_tab.count() > 0:
                    await spec_tab.first.click()
                    await self._random_delay(1.0, 2.0)
            except Exception:
                pass

            # Scroll to load detail images
            for _ in range(5):
                await page.evaluate("window.scrollBy(0, window.innerHeight)")
                await self._random_delay(0.5, 1.5)

            html = await page.content()
            detail = parse_product_detail(html)

            await self._save_cookies(context)
            return detail

        except Exception as e:
            logger.error(f"Detail fetch failed for {product_url}: {e}")
            return {"ingredient_text": None, "image_urls": []}
        finally:
            await context.close()

    async def download_images(self, image_urls: list[str], product_id: str) -> list[str]:
        """Download images and return local file paths."""
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

    async def close(self):
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
