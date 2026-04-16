"""Tests for Taobao/Tmall scraper and parser."""

from src.scraper.platform import PlatformScraper, get_scraper, PLATFORM_REGISTRY
from src.scraper.tb import TBScraper
from src.scraper.tb_parser import parse_tb_product_list, parse_tb_product_detail


class TestTBScraperProtocol:
    def test_tb_scraper_is_platform_scraper(self):
        scraper = TBScraper()
        assert isinstance(scraper, PlatformScraper)

    def test_tb_scraper_platform_name(self):
        scraper = TBScraper()
        assert scraper.platform_name == "tb"

    def test_registry_contains_tb(self):
        assert "tb" in PLATFORM_REGISTRY

    def test_get_scraper_returns_tb(self):
        scraper = get_scraper("tb")
        assert isinstance(scraper, TBScraper)


MOCK_TMALL_SEARCH_HTML = """
<div id="J_ItemList">
  <div class="product" data-id="600001">
    <div class="productImg"><a href="//detail.tmall.com/item.htm?id=600001"><img data-src="//img.alicdn.com/bao/uploaded/600001.jpg" /></a></div>
    <p class="productPrice"><em title="29.90">29.90</em></p>
    <p class="productTitle"><a href="//detail.tmall.com/item.htm?id=600001">味全每日C橙汁 300ml NFC鲜榨</a></p>
    <div class="productShop"><a href="//weiquanshipin.tmall.com">味全官方旗舰店</a></div>
  </div>
  <div class="product" data-id="600002">
    <div class="productImg"><a href="//detail.tmall.com/item.htm?id=600002"><img data-src="//img.alicdn.com/bao/uploaded/600002.jpg" /></a></div>
    <p class="productPrice"><em title="15.80">15.80</em></p>
    <p class="productTitle"><a href="//detail.tmall.com/item.htm?id=600002">农夫山泉NFC芒果混合汁 300ml</a></p>
    <div class="productShop"><a href="//nongfushanquan.tmall.com">农夫山泉旗舰店</a></div>
  </div>
</div>
"""

MOCK_TMALL_DETAIL_WITH_TEXT = """
<div id="J_AttrUL">
  <ul>
    <li title="配料表: 橙汁(NFC)">配料表: 橙汁(NFC)</li>
    <li title="品牌: 味全">品牌: 味全</li>
  </ul>
</div>
"""

MOCK_TMALL_DETAIL_WITH_IMAGES = """
<div id="description">
  <div class="content">
    <img src="//img.alicdn.com/imgextra/ingredients_tb_001.jpg" />
    <img src="//img.alicdn.com/imgextra/banner_tb.jpg" />
  </div>
</div>
"""


class TestTBParser:
    def test_parse_product_list(self):
        products = parse_tb_product_list(MOCK_TMALL_SEARCH_HTML)
        assert len(products) == 2

    def test_parse_product_fields(self):
        products = parse_tb_product_list(MOCK_TMALL_SEARCH_HTML)
        p = products[0]
        assert "味全" in p["name"]
        assert p["price"] == 29.9
        assert "600001" in p["product_url"]
        assert p["shop_name"] == "味全官方旗舰店"

    def test_parse_product_list_empty(self):
        products = parse_tb_product_list("<div></div>")
        assert products == []

    def test_parse_detail_text_ingredients(self):
        detail = parse_tb_product_detail(MOCK_TMALL_DETAIL_WITH_TEXT)
        assert detail["ingredient_text"] == "橙汁(NFC)"

    def test_parse_detail_images(self):
        detail = parse_tb_product_detail(MOCK_TMALL_DETAIL_WITH_IMAGES)
        assert len(detail["image_urls"]) >= 1

    def test_parse_detail_empty(self):
        detail = parse_tb_product_detail("<div></div>")
        assert detail["ingredient_text"] is None
        assert detail["image_urls"] == []
