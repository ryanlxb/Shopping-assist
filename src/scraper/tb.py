"""Taobao/Tmall scraper using Playwright with stealth mode and DOM extraction."""

import asyncio
import json
import logging
import random
from pathlib import Path
from urllib.parse import quote

from playwright.async_api import async_playwright

from src.scraper.platform import register_platform

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15",
]

COOKIE_PATH = Path("data/cookies/tb_cookies.json")

# JS to extract product data directly from Taobao search page DOM
_JS_EXTRACT_PRODUCTS = r"""() => {
    const cards = document.querySelectorAll('[class*="Card--"]');
    const results = [];
    for (const card of cards) {
        try {
            const titleEls = card.querySelectorAll('span, div');
            let bestTitle = '';
            for (const el of titleEls) {
                const t = el.innerText.trim();
                if (t.length > bestTitle.length && t.length > 10 && t.length < 150
                    && /[\u4e00-\u9fff]/.test(t)
                    && !/^\u5165\u9009/.test(t)
                    && !/\u56de\u5934\u5ba2/.test(t)) {
                    bestTitle = t;
                }
            }
            if (!bestTitle) continue;
            bestTitle = bestTitle.split('\n')[0].trim();

            const intEl = card.querySelector('[class*="priceInt"]');
            const floatEl = card.querySelector('[class*="priceFloat"]');
            let price = null;
            if (intEl) {
                const priceStr = intEl.innerText.trim() + (floatEl ? floatEl.innerText.trim() : '');
                price = parseFloat(priceStr);
                if (isNaN(price)) price = null;
            }

            const allLinks = card.querySelectorAll('a[href]');
            let productUrl = '';
            for (const link of allLinks) {
                const h = link.href;
                if (h.includes('item.taobao.com') || h.includes('detail.tmall.com') || h.includes('item.htm')) {
                    productUrl = h; break;
                }
            }
            if (!productUrl) {
                for (const link of allLinks) {
                    if (link.href.includes('click.simba') || link.href.includes('s.click')) {
                        productUrl = link.href; break;
                    }
                }
            }
            if (!productUrl && allLinks.length > 0) productUrl = allLinks[0].href;

            let shop = '';
            const shopEl = card.querySelector('[class*="shopName"]');
            if (shopEl) shop = shopEl.innerText.trim();

            const img = card.querySelector('img[src*="alicdn"]') || card.querySelector('img[src]');
            const imgSrc = img ? (img.src || '') : '';

            if (bestTitle.length > 10) {
                results.push({
                    name: bestTitle.substring(0, 100),
                    price: price,
                    product_url: productUrl.substring(0, 500),
                    shop_name: shop.substring(0, 60),
                    thumbnail_url: imgSrc.substring(0, 300),
                });
            }
        } catch(e) {}
    }
    return results;
}"""


@register_platform("tb")
class TBScraper:
    platform_name: str = "tb"

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
            logger.warning("playwright-stealth not installed")

        if COOKIE_PATH.exists():
            try:
                cookies = json.loads(COOKIE_PATH.read_text())
                await context.add_cookies(cookies)
            except Exception:
                logger.warning("Failed to load TB cookies")

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
            logger.warning("Failed to save TB cookies")

    async def search(self, keyword: str, limit: int = 30) -> list[dict]:
        """Search Taobao for products by keyword using DOM extraction."""
        context = await self._new_context()
        try:
            page = await context.new_page()

            search_url = f"https://s.taobao.com/search?q={quote(keyword)}"
            logger.info(f"Searching Taobao: {keyword}")

            await page.goto(search_url, wait_until="domcontentloaded")
            await self._random_delay(8.0, 12.0)

            for _ in range(5):
                await page.evaluate("window.scrollBy(0, window.innerHeight)")
                await self._random_delay(1.5, 3.0)

            products = await page.evaluate(_JS_EXTRACT_PRODUCTS)

            await self._save_cookies(context)
            logger.info(f"Found {len(products)} products on Taobao for '{keyword}'")

            return products[:limit]

        except Exception as e:
            logger.error(f"Taobao search failed for '{keyword}': {e}")
            raise
        finally:
            await context.close()

    async def get_detail(self, product_url: str) -> dict:
        """Fetch Tmall product detail page and extract ingredient info."""
        from src.scraper.tb_parser import parse_tb_product_detail

        context = await self._new_context()
        try:
            page = await context.new_page()

            await self._random_delay()
            logger.info(f"Fetching Tmall detail: {product_url}")

            await page.goto(product_url, wait_until="domcontentloaded")
            await self._random_delay(2.0, 4.0)

            for _ in range(5):
                await page.evaluate("window.scrollBy(0, window.innerHeight)")
                await self._random_delay(0.5, 1.5)

            html = await page.content()
            detail = parse_tb_product_detail(html)

            await self._save_cookies(context)
            return detail

        except Exception as e:
            logger.error(f"Tmall detail fetch failed for {product_url}: {e}")
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
