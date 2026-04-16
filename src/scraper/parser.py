"""HTML parser for JD search results and product detail pages."""

from bs4 import BeautifulSoup


def parse_product_list(html: str) -> list[dict]:
    """Parse JD search result page HTML and extract product metadata."""
    soup = BeautifulSoup(html, "lxml")
    products = []

    goods_list = soup.select("div#J_goodsList ul.gl-warp li.gl-item")
    if not goods_list:
        return []

    for item in goods_list:
        try:
            # Name
            name_el = item.select_one(".p-name em")
            name = name_el.get_text(strip=True) if name_el else None
            if not name:
                continue

            # Price — get text from <strong> which contains both <i>￥</i> and the number
            price_strong = item.select_one(".p-price strong")
            if price_strong is None:
                price_strong = item.select_one(".p-price")
            price_text = price_strong.get_text(strip=True) if price_strong else ""
            price_text = price_text.replace("￥", "").replace("¥", "").strip()
            try:
                price = float(price_text)
            except (ValueError, TypeError):
                price = None

            # Product URL
            link_el = item.select_one(".p-img a")
            href = link_el.get("href", "") if link_el else ""
            product_url = _normalize_url(href)

            # Shop name
            shop_el = item.select_one(".p-shop a")
            shop_name = shop_el.get_text(strip=True) if shop_el else None

            # Thumbnail
            img_el = item.select_one(".p-img img")
            thumb_src = ""
            if img_el:
                thumb_src = img_el.get("data-lazy-img", "") or img_el.get("src", "")
            thumbnail_url = _normalize_url(thumb_src)

            products.append({
                "name": name,
                "price": price,
                "product_url": product_url,
                "shop_name": shop_name,
                "thumbnail_url": thumbnail_url,
            })
        except Exception:
            continue

    return products


def parse_product_detail(html: str) -> dict:
    """Parse JD product detail page and extract ingredient info and images."""
    soup = BeautifulSoup(html, "lxml")

    ingredient_text = _extract_ingredient_text(soup)
    image_urls = _extract_detail_images(soup)

    return {
        "ingredient_text": ingredient_text,
        "image_urls": image_urls,
    }


def _extract_ingredient_text(soup: BeautifulSoup) -> str | None:
    """Try to find text-based ingredient information in the Ptable."""
    ptable = soup.select_one(".Ptable")
    if not ptable:
        return None

    for dt in ptable.find_all("dt"):
        text = dt.get_text(strip=True)
        if "配料" in text:
            dd = dt.find_next_sibling("dd")
            if dd:
                return dd.get_text(strip=True)

    return None


def _extract_detail_images(soup: BeautifulSoup) -> list[str]:
    """Extract product detail images that may contain ingredient info."""
    urls = []

    detail_content = soup.select_one("#J-detail-content")
    if not detail_content:
        return []

    for img in detail_content.find_all("img"):
        src = img.get("src", "") or img.get("data-lazyload", "")
        if src:
            urls.append(_normalize_url(src))

    return urls


def _normalize_url(url: str) -> str:
    """Normalize protocol-relative URLs."""
    url = url.strip()
    if url.startswith("//"):
        return f"https:{url}"
    return url
