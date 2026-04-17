"""JD (京东) scraper — DOM JS extraction with CDP/launch browser support."""

import logging
from urllib.parse import quote

from src.scraper.browser import BrowserManager, download_product_images
from src.scraper.platform import register_platform

logger = logging.getLogger(__name__)

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


@register_platform("jd")
class JDScraper:
    platform_name: str = "jd"

    def __init__(self, headless: bool = True, cdp_enabled: bool = True, cdp_port: int = 9222):
        self._bm = BrowserManager(
            platform_name="jd",
            headless=headless,
            cdp_enabled=cdp_enabled,
            cdp_port=cdp_port,
        )

    async def search(self, keyword: str, limit: int = 30) -> list[dict]:
        session = await self._bm.new_page()
        try:
            search_url = f"https://search.jd.com/Search?keyword={quote(keyword)}&enc=utf-8"
            logger.info(f"Searching JD: {keyword}")

            await session.page.goto(search_url, wait_until="domcontentloaded")
            await BrowserManager.random_delay(8.0, 12.0)
            await BrowserManager.scroll_page(session.page)

            products = await session.page.evaluate(_JS_EXTRACT_PRODUCTS)

            await self._bm.save_cookies(session.context)
            logger.info(f"Found {len(products)} products on JD for '{keyword}'")
            return products[:limit]

        except Exception as e:
            logger.error(f"JD search failed for '{keyword}': {e}")
            raise
        finally:
            await session.page.close()
            if session.owns_context:
                await session.context.close()

    async def get_detail(self, product_url: str) -> dict:
        from src.scraper.parser import parse_product_detail

        session = await self._bm.new_page()
        try:
            await BrowserManager.random_delay()
            logger.info(f"Fetching JD detail: {product_url}")

            await session.page.goto(product_url, wait_until="domcontentloaded")
            await BrowserManager.random_delay(2.0, 4.0)

            try:
                spec_tab = session.page.locator("text=规格与包装")
                if await spec_tab.count() > 0:
                    await spec_tab.first.click()
                    await BrowserManager.random_delay(1.0, 2.0)
            except Exception:
                pass

            await BrowserManager.scroll_page(session.page)

            html = await session.page.content()
            detail = parse_product_detail(html)

            await self._bm.save_cookies(session.context)
            return detail

        except Exception as e:
            logger.error(f"JD detail fetch failed for {product_url}: {e}")
            return {"ingredient_text": None, "image_urls": []}
        finally:
            await session.page.close()
            if session.owns_context:
                await session.context.close()

    async def download_images(self, image_urls: list[str], product_id: str) -> list[str]:
        return await download_product_images(image_urls, product_id)

    async def close(self):
        await self._bm.close()
