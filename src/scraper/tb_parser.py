"""HTML parser for Tmall/Taobao search results and product detail pages."""

from bs4 import BeautifulSoup


def parse_tb_product_list(html: str) -> list[dict]:
    """Parse Tmall search result page HTML and extract product metadata."""
    soup = BeautifulSoup(html, "lxml")
    products = []

    items = soup.select("#J_ItemList .product")
    if not items:
        return []

    for item in items:
        try:
            # Name
            title_el = item.select_one(".productTitle a")
            name = title_el.get_text(strip=True) if title_el else None
            if not name:
                continue

            # Price
            price_el = item.select_one(".productPrice em")
            price_text = price_el.get("title", "") or price_el.get_text(strip=True) if price_el else ""
            try:
                price = float(price_text)
            except (ValueError, TypeError):
                price = None

            # Product URL
            link_el = item.select_one(".productImg a") or item.select_one(".productTitle a")
            href = link_el.get("href", "") if link_el else ""
            product_url = _normalize_url(href)

            # Shop name
            shop_el = item.select_one(".productShop a")
            shop_name = shop_el.get_text(strip=True) if shop_el else None

            # Thumbnail
            img_el = item.select_one(".productImg img")
            thumb_src = ""
            if img_el:
                thumb_src = img_el.get("data-src", "") or img_el.get("src", "")
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


def parse_tb_product_detail(html: str) -> dict:
    """Parse Tmall product detail page and extract ingredient info and images."""
    soup = BeautifulSoup(html, "lxml")

    ingredient_text = _extract_ingredient_text(soup)
    image_urls = _extract_detail_images(soup)

    return {
        "ingredient_text": ingredient_text,
        "image_urls": image_urls,
    }


def _extract_ingredient_text(soup: BeautifulSoup) -> str | None:
    """Try to find text-based ingredient info in Tmall attribute list."""
    # Pattern 1: #J_AttrUL li elements
    attr_ul = soup.select_one("#J_AttrUL")
    if attr_ul:
        for li in attr_ul.find_all("li"):
            text = li.get_text(strip=True)
            if "配料" in text:
                # Format: "配料表: xxx" or "配料: xxx"
                for sep in (":", "："):
                    if sep in text:
                        return text.split(sep, 1)[1].strip()
                return text

    # Pattern 2: .attributes-list or .tm-clear
    for selector in (".attributes-list li", ".tm-clear li", "#J_DetailMeta li"):
        for li in soup.select(selector):
            text = li.get_text(strip=True)
            if "配料" in text:
                for sep in (":", "："):
                    if sep in text:
                        return text.split(sep, 1)[1].strip()

    return None


def _extract_detail_images(soup: BeautifulSoup) -> list[str]:
    """Extract product detail images from Tmall description area."""
    urls = []

    for container_id in ("#description", "#J_DivItemDesc", ".ke-post"):
        container = soup.select_one(container_id)
        if container:
            for img in container.find_all("img"):
                src = img.get("src", "") or img.get("data-src", "")
                if src:
                    urls.append(_normalize_url(src))
            if urls:
                return urls

    return urls


def _normalize_url(url: str) -> str:
    """Normalize protocol-relative URLs."""
    url = url.strip()
    if url.startswith("//"):
        return f"https:{url}"
    return url
