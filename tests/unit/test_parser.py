"""Tests for HTML parser — extracting product metadata from JD pages."""

from src.scraper.parser import parse_product_list, parse_product_detail


MOCK_SEARCH_HTML = """
<div id="J_goodsList">
  <ul class="gl-warp">
    <li class="gl-item" data-sku="100012345">
      <div class="p-img"><a href="//item.jd.com/100012345.html"><img data-lazy-img="//img.jd.com/n1/100012345.jpg" /></a></div>
      <div class="p-price"><strong class="J_price"><i>￥</i>12.90</strong></div>
      <div class="p-name"><a href="//item.jd.com/100012345.html"><em>农夫山泉 NFC橙汁 300ml</em></a></div>
      <div class="p-shop"><a href="//mall.jd.com/index-1000001.html">农夫山泉自营旗舰店</a></div>
    </li>
    <li class="gl-item" data-sku="100067890">
      <div class="p-img"><a href="//item.jd.com/100067890.html"><img data-lazy-img="//img.jd.com/n1/100067890.jpg" /></a></div>
      <div class="p-price"><strong class="J_price"><i>￥</i>8.50</strong></div>
      <div class="p-name"><a href="//item.jd.com/100067890.html"><em>汇源 100%橙汁 1L</em></a></div>
      <div class="p-shop"><a href="//mall.jd.com/index-1000002.html">汇源饮品旗舰店</a></div>
    </li>
  </ul>
</div>
"""

MOCK_DETAIL_HTML_WITH_TEXT = """
<div class="Ptable">
  <div class="Ptable-item">
    <h3>主体</h3>
    <dl>
      <dt>配料表</dt>
      <dd>橙汁(NFC)</dd>
    </dl>
    <dl>
      <dt>产品名称</dt>
      <dd>NFC橙汁</dd>
    </dl>
  </div>
</div>
"""

MOCK_DETAIL_HTML_WITH_IMAGES = """
<div id="J-detail-content">
  <div class="ssd-module-wrap">
    <img src="//img.jd.com/ingredients_001.jpg" alt="配料表" />
    <img src="//img.jd.com/nutrition_001.jpg" alt="营养成分表" />
    <img src="//img.jd.com/banner.jpg" alt="广告图" />
  </div>
</div>
"""


class TestParseProductList:
    def test_extracts_all_products(self):
        products = parse_product_list(MOCK_SEARCH_HTML)
        assert len(products) == 2

    def test_extracts_product_fields(self):
        products = parse_product_list(MOCK_SEARCH_HTML)
        p = products[0]
        assert p["name"] == "农夫山泉 NFC橙汁 300ml"
        assert p["price"] == 12.9
        assert "100012345" in p["product_url"]
        assert p["shop_name"] == "农夫山泉自营旗舰店"

    def test_handles_empty_html(self):
        products = parse_product_list("<div></div>")
        assert products == []

    def test_extracts_thumbnail(self):
        products = parse_product_list(MOCK_SEARCH_HTML)
        assert "100012345" in products[0]["thumbnail_url"]


class TestParseProductDetail:
    def test_extracts_text_ingredients(self):
        detail = parse_product_detail(MOCK_DETAIL_HTML_WITH_TEXT)
        assert detail["ingredient_text"] == "橙汁(NFC)"

    def test_extracts_detail_images(self):
        detail = parse_product_detail(MOCK_DETAIL_HTML_WITH_IMAGES)
        assert len(detail["image_urls"]) >= 1

    def test_handles_no_ingredients(self):
        detail = parse_product_detail("<div></div>")
        assert detail["ingredient_text"] is None
        assert detail["image_urls"] == []
