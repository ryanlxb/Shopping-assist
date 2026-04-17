"""Taobao scraper — DOM JS extraction with CDP/launch browser support."""

import logging
from urllib.parse import quote

from src.scraper.browser import BrowserManager, download_product_images
from src.scraper.platform import register_platform

logger = logging.getLogger(__name__)

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

    def __init__(self, headless: bool = True, cdp_enabled: bool = True, cdp_port: int = 9222):
        self._bm = BrowserManager(
            platform_name="tb",
            headless=headless,
            cdp_enabled=cdp_enabled,
            cdp_port=cdp_port,
        )

    async def search(self, keyword: str, limit: int = 30) -> list[dict]:
        session = await self._bm.new_page()
        try:
            search_url = f"https://s.taobao.com/search?q={quote(keyword)}"
            logger.info(f"Searching Taobao: {keyword}")

            await session.page.goto(search_url, wait_until="domcontentloaded")
            await BrowserManager.random_delay(8.0, 12.0)
            await BrowserManager.scroll_page(session.page)

            products = await session.page.evaluate(_JS_EXTRACT_PRODUCTS)

            await self._bm.save_cookies(session.context)
            logger.info(f"Found {len(products)} products on Taobao for '{keyword}'")
            return products[:limit]

        except Exception as e:
            logger.error(f"Taobao search failed for '{keyword}': {e}")
            raise
        finally:
            await session.page.close()
            if session.owns_context:
                await session.context.close()

    async def get_detail(self, product_url: str) -> dict:
        from src.scraper.tb_parser import parse_tb_product_detail

        session = await self._bm.new_page()
        try:
            await BrowserManager.random_delay()
            logger.info(f"Fetching Taobao detail: {product_url}")

            await session.page.goto(product_url, wait_until="domcontentloaded")
            await BrowserManager.random_delay(2.0, 4.0)

            await BrowserManager.scroll_page(session.page)

            html = await session.page.content()
            detail = parse_tb_product_detail(html)

            await self._bm.save_cookies(session.context)
            return detail

        except Exception as e:
            logger.error(f"Taobao detail fetch failed for {product_url}: {e}")
            return {"ingredient_text": None, "image_urls": []}
        finally:
            await session.page.close()
            if session.owns_context:
                await session.context.close()

    async def download_images(self, image_urls: list[str], product_id: str) -> list[str]:
        return await download_product_images(image_urls, product_id)

    async def close(self):
        await self._bm.close()
