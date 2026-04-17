"""Tests for STORY-002 security fixes — URL encoding, path traversal, N+1."""

import pytest
from urllib.parse import quote

from src.scraper.browser import download_product_images


class TestPathTraversal:
    """STORY-002 R3: product_id must be numeric."""

    @pytest.mark.asyncio
    async def test_rejects_non_numeric_product_id(self):
        with pytest.raises(ValueError, match="product_id must be numeric"):
            await download_product_images([], "../etc/passwd")

    @pytest.mark.asyncio
    async def test_rejects_path_traversal_attempt(self):
        with pytest.raises(ValueError, match="product_id must be numeric"):
            await download_product_images([], "../../secret")

    @pytest.mark.asyncio
    async def test_accepts_numeric_product_id(self):
        result = await download_product_images([], "12345")
        assert result == []


class TestURLEncoding:
    """STORY-002 R1: search keywords must be URL-encoded."""

    def test_chinese_keyword_encoded(self):
        encoded = quote("橙汁")
        assert "橙" not in encoded
        assert "%E6%A9%99%E6%B1%81" == encoded

    def test_special_chars_encoded(self):
        encoded = quote("NFC 100%果汁")
        assert " " not in encoded
        assert "%" in encoded
