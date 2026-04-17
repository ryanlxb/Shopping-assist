"""Non-headless search verification using persistent browser profile.

Uses Chromium persistent context so fingerprint matches a real browser.
Manual captcha/login only needed once — state persists across runs.
"""

import asyncio
import sys
from pathlib import Path
from urllib.parse import quote

from playwright.async_api import async_playwright

PROFILE_DIR = Path("data/browser_profile")


async def verify_platform(platform: str):
    if platform == "tb":
        name = "淘宝"
        search_url = "https://s.taobao.com/search?q=" + quote("橙汁")
        js_extract = r"""() => {
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
                        const ps = intEl.innerText.trim() + (floatEl ? floatEl.innerText.trim() : '');
                        price = parseFloat(ps); if (isNaN(price)) price = null;
                    }
                    const allLinks = card.querySelectorAll('a[href]');
                    let productUrl = '';
                    for (const link of allLinks) {
                        const h = link.href;
                        if (h.includes('item.taobao.com') || h.includes('detail.tmall.com') || h.includes('item.htm')) {
                            productUrl = h; break;
                        }
                    }
                    if (!productUrl && allLinks.length > 0) productUrl = allLinks[0].href;
                    let shop = '';
                    const shopEl = card.querySelector('[class*="shopName"]');
                    if (shopEl) shop = shopEl.innerText.trim();
                    if (bestTitle.length > 10) {
                        results.push({ name: bestTitle.substring(0,100), price, product_url: productUrl.substring(0,500), shop_name: shop.substring(0,60) });
                    }
                } catch(e) {}
            }
            return results;
        }"""
    else:
        name = "京东"
        search_url = "https://search.jd.com/Search?keyword=" + quote("橙汁") + "&enc=utf-8"
        js_extract = r"""() => {
            const items = document.querySelectorAll('#J_goodsList .gl-item');
            const results = [];
            for (const item of items) {
                try {
                    const nameEl = item.querySelector('.p-name em');
                    if (!nameEl) continue;
                    const name = nameEl.innerText.trim();
                    if (!name || name.length < 4) continue;
                    let price = null;
                    const priceEl = item.querySelector('.p-price strong i:last-child') || item.querySelector('.p-price strong');
                    if (priceEl) { const pt = priceEl.innerText.replace(/[￥¥\s]/g,'').trim(); price = parseFloat(pt); if(isNaN(price)) price=null; }
                    const linkEl = item.querySelector('.p-img a');
                    let productUrl = '';
                    if (linkEl) { const h = linkEl.href||linkEl.getAttribute('href')||''; productUrl = h.startsWith('//')?'https:'+h:h; }
                    let shopName = '';
                    const shopEl = item.querySelector('.p-shop a');
                    if (shopEl) shopName = shopEl.innerText.trim();
                    results.push({ name: name.substring(0,100), price, product_url: productUrl.substring(0,500), shop_name: shopName.substring(0,60) });
                } catch(e) {}
            }
            return results;
        }"""

    print(f"\n{'='*60}")
    print(f"  {name} 搜索验证 (持久化浏览器)")
    print(f"{'='*60}")

    PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    pw = await async_playwright().start()
    ctx = await pw.chromium.launch_persistent_context(
        user_data_dir=str(PROFILE_DIR),
        headless=False,
        viewport={"width": 1920, "height": 1080},
        locale="zh-CN",
        args=["--disable-blink-features=AutomationControlled"],
    )

    page = ctx.pages[0] if ctx.pages else await ctx.new_page()

    # Step 1: 搜索
    print(f"\n[Step 1] 打开搜索页: {name} '橙汁'")
    await page.goto(search_url, wait_until="domcontentloaded")
    await asyncio.sleep(5)

    # Step 2: 等待验证/登录
    print("[Step 2] 如果弹出验证码/登录，请在浏览器中手动完成")
    print("         商品加载后脚本自动继续（最多等 3 分钟）\n")

    products = []
    for attempt in range(36):
        await asyncio.sleep(5)
        try:
            products = await page.evaluate(js_extract)
        except Exception:
            products = []
        if products:
            break
        if attempt % 6 == 5:
            for _ in range(3):
                await page.evaluate("window.scrollBy(0, window.innerHeight)")
                await asyncio.sleep(1)
            print(f"  ... 已等待 {(attempt+1)*5}s，还没检测到商品")

    if not products:
        await page.screenshot(path=f"data/debug_{platform}_verify.png", full_page=True)
        print(f"\n❌ {name} 搜索未获取到商品，截图已保存")
        await ctx.close()
        await pw.stop()
        return False

    print(f"\n✅ {name} 搜索成功! 获取到 {len(products)} 个商品")
    print("-" * 50)
    for i, p in enumerate(products[:5]):
        print(f"  [{i+1}] {p['name'][:45]}  ¥{p.get('price','?')}  {p.get('shop_name','')[:15]}")

    # Step 3: 详情页配料提取
    target = None
    for p in products:
        url = p.get("product_url", "")
        if url and ("item" in url or "detail" in url):
            target = p
            break
    if not target:
        target = products[0]

    print(f"\n[Step 3] 进入详情页提取配料: {target['name'][:40]}")
    detail_url = target["product_url"]
    print(f"  URL: {detail_url[:80]}")

    try:
        await page.goto(detail_url, wait_until="domcontentloaded")
        await asyncio.sleep(8)

        # Try clicking specs tab (JD)
        if platform == "jd":
            try:
                spec_tab = page.locator("text=规格与包装")
                if await spec_tab.count() > 0:
                    await spec_tab.first.click()
                    await asyncio.sleep(2)
            except Exception:
                pass

        for _ in range(5):
            await page.evaluate("window.scrollBy(0, window.innerHeight)")
            await asyncio.sleep(1.5)

        html = await page.content()

        if platform == "tb":
            from src.scraper.tb_parser import parse_tb_product_detail
            detail = parse_tb_product_detail(html)
        else:
            from src.scraper.parser import parse_product_detail
            detail = parse_product_detail(html)

        print(f"\n  配料文字: {detail.get('ingredient_text') or '(无)'}")
        print(f"  详情图片: {len(detail.get('image_urls', []))} 张")
        if detail.get("image_urls"):
            for u in detail["image_urls"][:3]:
                print(f"    - {u[:70]}")

        if detail.get("ingredient_text"):
            print(f"\n🎉 {name} 全链路验证通过! 文字配料表已提取")
        elif detail.get("image_urls"):
            print(f"\n🎉 {name} 全链路验证通过! 配料图片已获取 (需 OCR)")
        else:
            await page.screenshot(path=f"data/debug_{platform}_detail.png", full_page=True)
            print(f"\n⚠ 搜索成功但该商品未提取到配料 (截图已保存)")
    except Exception as e:
        print(f"\n⚠ 详情页出错: {e}")

    await ctx.close()
    await pw.stop()
    return True


async def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "tb"
    if target == "all":
        tb_ok = await verify_platform("tb")
        jd_ok = await verify_platform("jd")
        print(f"\n{'='*60}")
        print(f"  淘宝: {'✅' if tb_ok else '❌'}")
        print(f"  京东: {'✅' if jd_ok else '❌'}")
    else:
        await verify_platform(target)


if __name__ == "__main__":
    asyncio.run(main())
