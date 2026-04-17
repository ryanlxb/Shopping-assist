"""Tests for STORY-010 sorting and STORY-005 blacklist filtering logic."""

from unittest.mock import MagicMock, patch

from src.app import _load_products


def _make_product(name, price, ingredients=None):
    """Create a mock product with ingredients."""
    p = MagicMock()
    p.name = name
    p.price = price
    p.platform = "jd"
    ing_list = []
    for ing_name in (ingredients or []):
        ing = MagicMock()
        ing.name = ing_name
        ing_list.append(ing)
    p.ingredients = ing_list
    return p


class TestSortingLogic:
    def _setup_session(self, products):
        session = MagicMock()
        query = MagicMock()
        query.filter_by.return_value = query
        query.options.return_value = query
        query.all.return_value = products
        session.query.return_value = query
        return session

    @patch("src.app._classify_ingredient")
    def test_sort_price_asc(self, mock_classify):
        mock_classify.side_effect = lambda name, rules: {"name": name, "category": "normal", "kb_type": None, "kb_desc": None}
        products = [_make_product("A", 15.0), _make_product("B", 8.0), _make_product("C", 12.0)]
        session = self._setup_session(products)

        result = _load_products(session, task_id=1, sort_by="price_asc")
        prices = [r["product"].price for r in result]
        assert prices == [8.0, 12.0, 15.0]

    @patch("src.app._classify_ingredient")
    def test_sort_price_desc(self, mock_classify):
        mock_classify.side_effect = lambda name, rules: {"name": name, "category": "normal", "kb_type": None, "kb_desc": None}
        products = [_make_product("A", 8.0), _make_product("B", 15.0)]
        session = self._setup_session(products)

        result = _load_products(session, task_id=1, sort_by="price_desc")
        prices = [r["product"].price for r in result]
        assert prices == [15.0, 8.0]

    @patch("src.app._classify_ingredient")
    def test_sort_score_desc(self, mock_classify):
        def classify(name, rules):
            cat = "whitelist" if "NFC" in name else "blacklist" if "防腐" in name else "normal"
            return {"name": name, "category": cat, "kb_type": None, "kb_desc": None}
        mock_classify.side_effect = classify

        products = [
            _make_product("Bad", 10.0, ["防腐剂A", "防腐剂B"]),
            _make_product("Good", 12.0, ["NFC橙汁", "NFC苹果汁"]),
        ]
        session = self._setup_session(products)

        result = _load_products(session, task_id=1, sort_by="score_desc")
        scores = [r["ingredient_score"] for r in result]
        assert scores[0] > scores[1]

    @patch("src.app._classify_ingredient")
    def test_no_price_sorted_last_asc(self, mock_classify):
        mock_classify.side_effect = lambda name, rules: {"name": name, "category": "normal", "kb_type": None, "kb_desc": None}
        products = [_make_product("NoPrice", None), _make_product("Cheap", 5.0)]
        session = self._setup_session(products)

        result = _load_products(session, task_id=1, sort_by="price_asc")
        assert result[0]["product"].price == 5.0
        assert result[1]["product"].price is None

    @patch("src.app._classify_ingredient")
    def test_exclude_blacklist(self, mock_classify):
        def classify(name, rules):
            cat = "blacklist" if "bad" in name else "normal"
            return {"name": name, "category": cat, "kb_type": None, "kb_desc": None}
        mock_classify.side_effect = classify

        products = [
            _make_product("Clean", 10.0, ["water"]),
            _make_product("Dirty", 10.0, ["bad_stuff"]),
        ]
        session = self._setup_session(products)

        result = _load_products(session, task_id=1, exclude_blacklist=True)
        assert len(result) == 1
        assert result[0]["product"].name == "Clean"
